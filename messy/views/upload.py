
from messy.views import (m_roles, get_dbhandler, error_page, render_to_response, HTTPFound,
                         select2_lookup)
from messy.views.rpc import generate_user_token
from messy.lib import uploads
from messy.lib import roles as r
from rhombus.views.generics import forwarding_page
from rhombus.lib import tags_b46 as t
from rhombus.lib.utils import random_string
import joblib
import pandas as pd
import os


# tokens

def get_user(token):
    """ return user associated with token """
    pass


def get_token(user):
    """ generate a string token to be associated with user """
    pass


class UploadViewer(object):

    def __init__(self, request):
        self.request = request
        self.dbh = get_dbhandler()

    @m_roles(r.PUBLIC)
    def index(self):

        request = self.request

        if request.method == 'POST':
            method = request.POST['_method']
            confirmpage_methods = {
                'generate_token': self.generate_token,
                'upload_samples': self.confirmpage_sample,
                'upload_institution': self.confirmpage_institution,
            }
            return confirmpage_methods[method]()

        jobid = request.params.get('jobid', None)
        if jobid:
            uploadjob = joblib.load(
                uploads.create_temp_file('upload', request.user.login, 'joblib', jobid)
            )
            if not uploadjob.check_user(self.request.user.id):
                raise RuntimeError('Current job is not owned by this user!')

            if isinstance(uploadjob, uploads.InstitutionUploadJob):
                return self.confirmpage_institution(uploadjob)
            elif isinstance(uploadjob, uploads.SampleUploadJob):
                return self.confirmpage_sample(uploadjob)

            return error_page(self.request, 'Invalid request!')

        html = t.div(t.h2('Upload'))

        eform, jscode = generate_token_form(request)
        html.add(eform)

        eform, jscode = sample_upload_form(request)
        html.add(eform)

        eform, jscode_ = plate_upload_form(request)
        html.add(eform)
        jscode = jscode + jscode_

        eform, jscode_ = institution_upload_form(request)
        html.add(eform)
        jscode = jscode + jscode_

        return render_to_response("messy:templates/generic_page.mako",
                                  {'html': html, 'code': jscode},
                                  request=request)

    @m_roles(r.PUBLIC)
    def commit(self):

        if self.request.method == 'POST':
            jobid = self.request.POST['jobid']
            if jobid:
                uploadjob = joblib.load(
                    uploads.create_temp_file('upload', self.request.user.login, 'joblib', jobid)
                )
                if not uploadjob.check_user(self.request.user.id):
                    raise RuntimeError('Current job is not owned by this user!')

                if isinstance(uploadjob, uploads.InstitutionUploadJob):
                    return self.commitpage_institution(uploadjob)
                elif isinstance(uploadjob, uploads.SampleUploadJob):
                    return self.commitpage_sample(uploadjob)

            return error_page(self.request, 'Invalid request!')

        return error_page(self.request, 'Nothing to be done anymore!')

    def generate_token(self):

        if self.request.method == 'POST':

            token = generate_user_token(self.request)
            html = t.div(t.h2('User Token'))[
                t.div('Token: ' + token),
            ]
            return render_to_response('messy:templates/generic_page.mako',
                                      {'html': html},
                                      request=self.request)

        return error_page(self)

    def confirmpage_sample(self, job=None):

        if self.request.method == 'POST':
            collection_id = int(self.request.params.get('messy-sample/collection_id', 0))
            collection = self.dbh.get_collections_by_ids([collection_id], None)[0]
            if not collection.can_upload(self.request.user):
                raise RuntimeError('Current user cannot upload sample to this collection')

            infile = self.request.params.get('messy-sample/infile', None)
            gisaid = self.request.params.get('messy-sample/gisaidfile', None)
            if infile is not None and infile != b'':
                job = uploads.SampleUploadJob(self.request.user.id, infile.filename, infile.file,
                                              collection_id)
            elif gisaid is not None and gisaid != b'':
                job = uploads.SampleGISAIDUploadJob(self.request.user.id, gisaid.filename, gisaid.file,
                                                    collection_id)
            else:
                return error_page(self.request, 'Please provide either sample file or GISAID file')
            randkey = job.randkey
            job_filename = uploads.create_temp_file('upload', self.request.user.login, 'joblib', randkey)
            joblib.dump(job, job_filename)

            return HTTPFound(
                location=self.request.route_url('upload', _query={'jobid': randkey}))

        if not job:
            return error_page(self.request, 'Invalid request!')

        params = job.confirm()
        html = t.div()[
            t.h3('Sample Upload Confirmation'),
            t.div(f"No of total samples: {params['samples']}"),
            t.div(f"No of existing samples by codes: {len(params['existing_codes'])}",
                  t.button('View', class_='btn btn-sm btn-link', type='button',
                           **{'data-toggle': 'collapse', 'data-target': '#codelist',
                              'aria-expanded': 'true', 'aria-controls': 'codelist'})),
            t.div(t.div(t.div(class_='card card-body')[' '.join(params['existing_codes'])],
                  class_='collapse', id='codelist')
                  ),
            t.div(f"No of exsiting samples by acc_codes: {len(params['existing_acc_codes'])}",
                  t.button('View', class_='btn btn-sm btn-link', type='button',
                           **{'data-toggle': 'collapse', 'data-target': '#acccodelist',
                              'aria-expanded': 'true', 'aria-controls': 'acccodelist'})),
            t.div(t.div(t.div(class_='card card-body')[' '.join(params['existing_acc_codes'])],
                  class_='collapse', id='acccodelist')
                  ),
            t.div(f"Warning messages: {len(params['err_msgs'])}"),
        ]

        # prepare confirmation list

        tbody = t.tbody(name='table-body')

        mismatch_institutions = [t for t in params['institutions'].items()
                                 if (t[1] and t[0].upper() != t[1].code.upper())]
        for idx, (inst_code, inst) in enumerate(mismatch_institutions):
            if inst:
                value = inst.id
                options = f'<option value="{inst.id}">{inst.code} | {inst.name}</option>'
            else:
                value = options = ''
            tbody.add(
                t.tr(
                    t.td(
                        t.literal(f'<select name="id-{idx}" id="inst_id-{idx}" value="{value}" class="selids" style="width:100%">{options}</select>'
                                  f'<input type="hidden" name="inst_code-{idx}" value="{inst_code}">'),
                        class_='pt-1 pb-0'
                    ),
                    t.td(inst_code)
                )
            )

        sform = t.form('messy/sample', method='POST', action=self.request.route_url('upload-commit')).add(
            t.input_hidden('jobid', value=job.randkey),
            t.custom_submit_bar(
                ('Add new item only', 'add'),
                ('Update existing only', 'update'),
                ('Add new and update existing', 'add_update'),
            ).set_offset(1).show_reset_button(False),
        )

        if len(mismatch_institutions) > 0:
            sform.add(
                t.h4('Confirmation'),
                t.table(class_='table table-condensed table-striped')[
                    t.thead(
                        t.tr(
                            t.th('Institute Code | Name'),
                            t.th('Institute Value in uploaded file')
                        )
                    ),
                    tbody,
                ]
            )

        html.add(sform)

        jscode = select2_lookup(tag=".selids", minlen=3, usetag=False,
                                placeholder="Type an institution name",
                                parenttag="table-body",
                                url=self.request.route_url('messy.institution-lookup'))

        if len(params['err_msgs']) > 0:
            html[t.h4('Warning messages')].add(* [t.div(msg) for msg in params['err_msgs']])

        return render_to_response("rhombus:templates/generics/formpage.mako",
                                  {'html': html, 'code': jscode},
                                  request=self.request)

    def commitpage_sample(self, job):
        method = self.request.POST['_method']

        # gather institution cache table
        inst_codes = []
        inst_ids = []
        for key, value in self.request.POST.items():
            if key.startswith('inst_id'):
                inst_ids.append((key, value))
            elif key.startswith('inst_code'):
                inst_codes.append((key, value))
        for inst_code, inst_id in zip(sorted(inst_codes), sorted(inst_ids)):
            if inst_code[0].split('-')[1] != inst_id[0].split('-')[1]:
                raise RuntimeError('mismatch order of institution code and id')
            job.institution_cache[inst_code[1]] = self.dbh.get_institution_by_ids(inst_id)[0]

        added, updated = job.commit(method)
        html = t.div()[
            t.h2('Uploaded Samples'),
            t.div(f"Added sample(s): {added}"),
            t.div(f"Updated sample(s): {updated}"),
        ]
        return render_to_response("messy:templates/generic_page.mako",
                                  {'html': html, },
                                  request=self.request)

    def confirmpage_institution(self, job=None):

        if self.request.method == 'POST':
            file_content = self.request.params.get('messy-institution/infile')
            job = uploads.InstitutionUploadJob(self.request.user.id, file_content.filename, file_content.file)
            randkey = job.randkey
            job_filename = uploads.create_temp_file('upload', self.request.user.login, 'joblib', randkey)
            joblib.dump(job, job_filename)

            return HTTPFound(
                location=self.request.route_url('upload', _query={'jobid': randkey}))

        if not job:
            return error_page(self.request, 'Invalid request!')

        params = job.confirm()
        html = t.div()[
            t.h3('Institution Upload Confirmation'),
            t.div(f"Existing item(s): {params['existing']}"),
            t.div(f"New item(s): {params['new']}"),
        ]
        html.add(
            t.form('messy/institution', method='POST', action=self.request.route_url('upload-commit')).add(
                t.input_hidden('jobid', value=job.randkey),
                t.custom_submit_bar(
                    ('Add new item only', 'add'),
                    ('Update existing only', 'update'),
                    ('Add new and update existing', 'add_update'),
                ).set_offset(1).show_reset_button(False)
            )
        )

        return render_to_response("messy:templates/generic_page.mako",
                                  {'html': html, },
                                  request=self.request)

    def commitpage_institution(self, job):

        method = self.request.POST['_method']
        added, updated = job.commit(method)
        html = t.div()[
            t.h2('Uploaded Institution'),
            t.div(f"Added institution(s): {added}"),
            t.div(f"Updated institution(s): {updated}"),
        ]
        return render_to_response("messy:templates/generic_page.mako",
                                  {'html': html, },
                                  request=self.request)


def generate_token_form(request):

    html = t.div(t.hr, t.h3('Token Generator', styles="bg-dark;"))
    eform = t.form(name='messy/token-generator', method=t.POST)
    eform.add(
        t.custom_submit_bar(('Generate token', 'generate_token')).set_offset(1).show_reset_button(False)
    )

    return html.add(eform), ''


def sample_upload_form(request):

    dbh = get_dbhandler()

    html = t.div(t.hr, t.h3('Samples'))
    sampleform = t.form(name='messy/sample', method=t.POST, enctype=t.FORM_MULTIPART)
    sampleform.add(
        t.fieldset(
            t.input_file('messy-sample/infile', 'CSV/TSV or JSON/YAML file',
                         offset=2, size=6,
                         info='Click <a href="/help/templates/index.rst" target="_blank">here</a>'
                              ' to see templates.'),
            t.div('or', offset=2),
            t.input_file('messy-sample/gisaidfile', 'GISAID CSV file',
                         offset=2, size=6,
                         info='Click <a href="/help/templates/index.rst" target="_blank">here</a>'
                              ' to see templates.'),
            t.input_select('messy-sample/collection_id', 'Collection',
                           value=None, offset=1, size=2,
                           options=[(c.id, c.code) for c in dbh.get_collections(groups=None)]),
            t.custom_submit_bar(('Upload', 'upload_samples')).set_offset(1),
        )
    )

    jscode = '''
    '''

    return html.add(sampleform), jscode


def plate_upload_form(request):

    dbh = get_dbhandler()

    html = t.div(t.hr, t.h3('Plate Layouts'))
    plateform = t.form(name='messy/plate', method=t.POST, enctype=t.FORM_MULTIPART)[
        t.fieldset(
            t.input_file('messy-plate/infile', 'CSV/TSV or JSON/YAML file',
                         offset=2, size=6,
                         info='Click <a href="/help/templates/index.rst" target="_blank">here</a>'
                         ' to see templates.'),
            t.custom_submit_bar(('Upload', 'upload_plates')).set_offset(1),
        )
    ]

    return html.add(plateform), ''


def institution_upload_form(request):

    dbh = get_dbhandler()

    html = t.div(t.hr, t.h3('Institutions'))
    eform = t.form(name='messy/institution', method=t.POST, enctype=t.FORM_MULTIPART)
    eform.add(
        t.fieldset(
            t.input_file('messy-institution/infile', 'CSV/TSV or JSON/YAML file',
                         offset=2, size=6,
                         info='Click <a href="/help/templates/index.rst" target="_blank">here</a>'
                         ' to see templates.'),
            t.custom_submit_bar(('Upload', 'upload_institution')).set_offset(1),
        )
    )

    jscode = '''
    '''

    return html.add(eform), jscode


def sample_upload(request):

    raise NotImplementedError()


def institution_upload(request):

    file_content = request.params.get('messy-institution/infile')
    job = uploads.InstitutionUploadJob(file_content.filename, file_content.file)


    dbh = get_dbhandler()
    dbh.Institution.bulk_load(dicts, dbh)

    return True, forwarding_page(request, 'Institution successfully updated', '/', 10)


upload_functions = {
    'upload_samples': sample_upload,
    'upload_institution': institution_upload,
}

# EOF
