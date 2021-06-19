
from messy.views import *
from messy.views.rpc import generate_user_token
from messy.lib import uploads
from rhombus.views.generics import forwarding_page
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

    @m_roles( PUBLIC )
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

        html = div(h2('Upload'))

        eform, jscode = generate_token_form(request)
        html.add(eform)     

        eform, jscode = sample_upload_form(request)
        html.add(eform)

        eform, jscode_ = institution_upload_form(request)
        html.add(eform)
        jscode = jscode + jscode_

        return render_to_response("messy:templates/generic_page.mako",
                {   'html': html,
                    'code': jscode,
                },
                request = request)

    @m_roles( PUBLIC )
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
            html = div(h2('User Token'))[
                div('Token: ' + token),
            ]
            return render_to_response('messy:templates/generic_page.mako',
                    {   'html': html
                    }, request=self.request)

        return error_page(self)


    def confirmpage_sample(self, job = None):

        if self.request.method == 'POST':
            collection_id = int( self.request.params.get('messy-sample/collection_id', 0))
            collection = self.dbh.get_collections_by_ids([collection_id], None)[0]
            if not collection.can_upload(self.request.user):
                raise RuntimeError('Current user cannot upload sample to this collection')

            infile = self.request.params.get('messy-sample/infile', None)
            gisaid = self.request.params.get('messy-sample/gisaidfile', None)
            if infile is not None and infile != b'':
                job = uploads.SampleUploadJob( self.request.user.id, infile.filename, infile.file, collection_id )
            elif gisaid is not None and gisaid != b'':
                job = uploads.SampleGISAIDUploadJob( self.request.user.id, gisaid.filename, gisaid.file, collection_id)
            else:
                return error_page(self.request, 'Please provide either sample file or GISAID file')
            randkey = job.randkey
            job_filename = uploads.create_temp_file('upload', self.request.user.login, 'joblib', randkey)
            joblib.dump(job, job_filename)

            return HTTPFound(
                location = self.request.route_url('upload', _query = { 'jobid': randkey}))

        if not job:
            return error_page(self.request, 'Invalid request!')

        params = job.confirm()
        html = div() [
            h3('Sample Upload Confirmation'),
            div( f"No of samples: {params['samples']}" ),
            div( f"Error messages: {len(params['err_msgs'])}" ),
        ]
        html.add(
            form('messy/sample', method='POST', action=self.request.route_url('upload-commit')).add(
                input_hidden('jobid', value=job.randkey),
                custom_submit_bar(
                    ('Add new item only', 'add'),
                    ('Update existing only', 'update'),
                    ('Add new and update existing', 'add_update'),
                ).set_offset(1).show_reset_button(False)
            )
        )
        html[h4('Error messages')].add( * [div(msg) for msg in params['err_msgs']] )

        return render_to_response("messy:templates/generic_page.mako",
            {   'html': html,
            },
            request = self.request)

    def commitpage_sample(self, job):
        method = self.request.POST['_method']
        added, updated = job.commit(method)
        html = div()[
            h2('Uploaded Samples'),
            div(f"Added sample(s): {added}"),
            div(f"Updated sample(s): {updated}"),
        ]
        return render_to_response("messy:templates/generic_page.mako",
                {   'html': html,
                },
                request = self.request)


    def confirmpage_institution(self, job = None):
        
        if self.request.method == 'POST':
            file_content = self.request.params.get('messy-institution/infile')
            job = uploads.InstitutionUploadJob( self.request.user.id, file_content.filename, file_content.file )
            randkey = job.randkey
            job_filename = uploads.create_temp_file('upload', self.request.user.login, 'joblib', randkey)
            joblib.dump(job, job_filename)

            return HTTPFound(
                location = self.request.route_url('upload', _query = { 'jobid': randkey}))

        if not job:
            return error_page(self.request, 'Invalid request!')

        params = job.confirm()
        html = div() [
            h3('Institution Upload Confirmation'),
            div(f"Existing item(s): {params['existing']}"),
            div(f"New item(s): {params['new']}"),
        ]
        html.add(
            form('messy/institution', method='POST', action=self.request.route_url('upload-commit')).add(
                input_hidden('jobid', value=job.randkey),
                custom_submit_bar(
                    ('Add new item only', 'add'),
                    ('Update existing only', 'update'),
                    ('Add new and update existing', 'add_update'),
                ).set_offset(1).show_reset_button(False)
            )
        )

        return render_to_response("messy:templates/generic_page.mako",
            {   'html': html,
            },
            request = self.request)


    def commitpage_institution(self, job):

        method = self.request.POST['_method']
        added, updated = job.commit(method)
        html = div()[
            h2('Uploaded Institution'),
            div(f"Added institution(s): {added}"),
            div(f"Updated institution(s): {updated}"),
        ]
        return render_to_response("messy:templates/generic_page.mako",
                {   'html': html,
                },
                request = self.request)


def generate_token_form(request):

    html = div(HR, h3('Token Generator', styles="bg-dark;"))
    eform = form( name='messy/token-generator', method=POST)
    eform.add(
        custom_submit_bar( ('Generate token', 'generate_token') ).set_offset(1).show_reset_button(False)
        )

    return html.add(eform), ''


def sample_upload_form(request):

    dbh = get_dbhandler()

    html = div(HR, h3('Samples'))
    sampleform = form( name='messy/sample', method=POST, enctype=FORM_MULTIPART)
    sampleform.add(
        fieldset(
            input_file('messy-sample/infile', 'CSV or JSON/YAML file',
                offset=2, size=6,
                info = 'Click <a href="/help/templates/index.rst" target="_blank">here</a>'
                        ' to see templates.'),
            div('or', offset=2),
            input_file('messy-sample/gisaidfile', 'GISAID CSV file',
                offset=2, size=6,
                info = 'Click <a href="/help/templates/index.rst" target="_blank">here</a>'
                        ' to see templates.'),
            input_select('messy-sample/collection_id', 'Collection',
                value = None, offset=1, size=2,
                options = [ (c.id, c.code) for c in dbh.get_collections(groups=None)] ),
            custom_submit_bar( ('Upload', 'upload_samples') ).set_offset(1),
        )
    )

    jscode = '''
    '''

    return html.add(sampleform), jscode


def institution_upload_form(request):

    dbh = get_dbhandler()

    html = div(HR, h3('Institution'))
    eform = form( name='messy/institution', method=POST, enctype=FORM_MULTIPART)
    eform.add(
        fieldset(
            input_file('messy-institution/infile', 'CSV or JSON/YAML file',
                offset=2, size=6,
                info = 'Click <a href="/help/templates/index.rst" target="_blank">here</a>'
                        ' to see templates.'),
            custom_submit_bar( ('Upload', 'upload_institution') ).set_offset(1),
        )
    )

    jscode = '''
    '''

    return html.add(eform), jscode


def sample_upload(request):

    raise NotImplementedError()


def institution_upload(request):

    file_content = request.params.get('messy-institution/infile')
    job = uploads.InstitutionUploadJob( file_content.filename, file_content.file )


    dbh = get_dbhandler()
    dbh.Institution.bulk_load(dicts, dbh)

    return True, forwarding_page(request, 'Institution successfully updated', '/', 10)



upload_functions = {
    'upload_samples': sample_upload,
    'upload_institution': institution_upload,
}