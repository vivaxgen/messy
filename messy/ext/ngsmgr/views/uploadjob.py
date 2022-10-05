
from rhombus.views import generate_sesskey, tokenize_sesskey
from messy.views import (m_roles, get_dbhandler, render_to_response,
                         form_submit_bar, select2_lookup)
from messy.views.uploadjob import UploadJobViewer
from messy.ext.ngsmgr.lib import roles as r
from messy.ext.ngsmgr.models.schema import FastqUploadJob, FastqPair
from rhombus.lib import tags as t
from rhombus.lib.fileutils import save_file

from pyramid.response import Response
from urllib.parse import unquote
import pandas as pd


class FastqUploadJobViewer(UploadJobViewer):

    object_class = FastqUploadJob
    fetch_func = get_dbhandler().get_fastquploadjobs_by_ids
    view_route = 'messy-ngsmgr.uploadjob.fastq-view'

    form_fields = {
        'collection_id': ('messy-ngsmgr-upload-fastqpair-collection_id', int),
        'ngsrun_id!': ('messy-ngsmgr-upload-fastqpair-ngsrun_id', int),
        'manifest_file': ('messy-ngsmgr-upload-fastqpair-manifest_file', ),
    }

    def add_helper(self, render=True):
        try:
            response = super().add_helper(render=False)
            if type(response) is not tuple:
                # adding new session is sucessfull, hence save the object
                return response

            else:
                html, jscode = response

        except ValueError as e:
            err_msg = str(e)
            html, jscode = self.generate_edit_form(self.obj,
                                                   update_dict=self.request.params)
            html.add('Problem in the manifest file:')
            html.add(err_msg)
            # assert 0

        if not render:
            return html, jscode

        return self.render_edit_form(html, jscode)

    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        rq = self.request
        dbh = self.dbh
        ffn = self.ffn

        html = t.div().add(
            t.h2('Upload Manager')
        )
        session_dirs = self.object_class.list_sessions(user=rq.user)
        if len(session_dirs) > 0:
            html.add(
                t.div('Current active upload session:'),
                t.ul(
                    * [
                        t.li(
                            t.a(t.time(job.start_time,
                                       datetime=job.start_time.isoformat(),
                                       tz='auto'),
                                href=rq.route_url('messy-ngsmgr.uploadjob.fastq-view',
                                                  id=job.id))
                        ) for job in session_dirs
                    ]
                )
            )

        else:
            html.add(t.p('Current user does not have any active session'))

        html.add(t.p('Create a new active session by uploading a manifest file:'))

        # check if we already have ngsrun_id and collection_id
        ngsrun = collection = None
        if update_dict:
            if ffn('ngsrun_id!') in update_dict:
                ngsrun = dbh.get_ngsruns_by_ids([update_dict[ffn('ngsrun_id!')]],
                                                groups=rq.user.groups)[0]
            if ffn('collection_id') in update_dict:
                collection = dbh.get_collections_by_ids([update_dict[ffn('collection_id')]],
                                                        groups=rq.user.groups)[0]

        eform = t.form(name='messy-ngsmgr-upload-fastqpair', method=t.POST,
                       enctype=t.FORM_MULTIPART, update_dict=update_dict,
                       action=rq.route_url('messy-ngsmgr.uploadjob.fastq-add')).add(
            self.hidden_fields(obj, sesskey=obj.id),    # this is not used, but necessary to show the form
            t.fieldset(
                t.input_select(self.ffn('collection_id'), 'Collection', offset=2, size=4,
                               value=collection.id if collection else '',
                               options=[(collection.id, collection.code)] if collection else []),
                t.input_select(self.ffn('ngsrun_id!'), 'NGS Run code', offset=2, size=4,
                               value=ngsrun.id if ngsrun else '',
                               options=[(ngsrun.id, ngsrun.code)] if ngsrun else [],
                               required=True),
                t.input_file(self.ffn('manifest_file'), 'Manifest', required=True, offset=2),
                name='messy-ngsmgr-upload-fastqpair-fieldset'
            ),
            t.custom_submit_bar(('Create session', 'add')).set_offset(2)
        )

        jscode = ''
        jscode += select2_lookup(tag=self.ffn('ngsrun_id!'), minlen=3,
                                 placeholder="Type an NGS Run code",
                                 parenttag="messy-ngsmgr-upload-fastqpair-fieldset",
                                 usetag=False,
                                 url=self.request.route_url('messy-ngsmgr.ngsrun-lookup'))
        html.add(eform)

        return html, jscode

    def update_object(self, obj, d):

        if obj.id is None:
            # this is a new upload session object
            obj.ngsrun_id = d.get('ngsrun_id', None)
            obj.collection_id = d.get('collection_id', None)
            obj.user_id = self.request.user.id

            obj.sesskey = generate_sesskey(self.request.user.id, obj.ngsrun_id)
            self.dbh.session().add(obj)

        # validate manifest file

        manifest_file = d['manifest_file']
        if manifest_file.filename.lower().endswith('.xlsx'):
            df = pd.read_excel(manifest_file.file)
        else:
            df = pd.read_table(manifest_file.file, sep=None)

        obj.validate_manifest(df, self.request.user, self.dbh)

    @m_roles(r.PUBLIC)
    def save(self):
        # commit the uploaded to database

        rq = self.request
        user = rq.user
        job = self.get_object()

        self.can_modify(job)
        job.commit(user)

        html = t.div(t.p('All uploaded files have been saved to database'))

        return render_to_response("messy:templates/generic_page.mako", {
            'html': html
        }, request=rq)

    @m_roles(r.PUBLIC)
    def status(self):

        rq = self.request
        job = self.get_object()

        self.can_modify(job)

        # check how many files has been completed
        completed = job.get_uploaded_count()

        html = t.div().add(
            t.h2('Upload Session'),
            t.p(f'Started at: {job.start_time} UTC'),
            t.p(f'Total files: {job.json["file_count"]}'),
            t.p(f'Uploaded: {completed}'),
            t.div(
                t.a('Save', href=rq.route_url('messy-ngsmgr.uploadjob.fastq-save',
                                              id=job.id),
                    class_='btn btn-primary')
                if completed == job.json["file_count"] else ''),
        )

        return Response(body=html.r(),
                        status="200",
                        content_type="text/html")

    def view_helper(self):
        """ this will be the busiest method of the class """

        job = self.obj
        rq = self.request

        # sanity check
        self.can_modify(job)

        html = t.div(id='status-view')

        code = ''
        # prepare list of fastq filenames

        return render_to_response("messy:ext/ngsmgr/templates/uploadpage.mako", {
            'html': html,
            'code': code,
            'status_url': unquote(rq.route_url('messy-ngsmgr.uploadjob.fastq-status',
                                  id=job.id)),
            'target_url': unquote(rq.route_url('messy-ngsmgr.uploadjob.fastq-target',
                                  id=job.id)),
        }, request=rq)

# EOF
