
from rhombus.lib.utils import cerr
from rhombus.lib.fileutils import get_file_size
from rhombus.lib import tags as t
from rhombus.views import generate_sesskey
from messy.models.dbschema import UploadJob
from messy.views import (BaseViewer, m_roles, get_dbhandler, render_to_response,
                           form_submit_bar, select2_lookup)
from messy.lib import roles as r

from pyramid.response import Response
from pyramid.exceptions import HTTPBadRequest

import json
from time import sleep


class UploadJobViewer(BaseViewer):

    __subdir__ = 'uploads/generics/'
    __root_storage_path__ = None

    object_class = UploadJob

    def index_helper(self):

        rq = self.request

        html, code = self.add_helper(render=False)

        return render_to_response(self.template_edit,
                                  {
                                      'html': html,
                                      'code': code,
                                  },
                                  request=self.request)

    def can_modify(self, job):
        user = self.request.user
        if ~user.has_roles(* self.managing_roles) and job.user_id != user.id:
            raise PermissionError('Current user does not own the upload session!')

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

    @m_roles(r.PUBLIC)
    def target(self):

        rq = self.request
        user = rq.user
        idkey = rq.matchdict.get('id')


        job = sess = self.get_object()

        # sanity check,
        if ~user.has_roles(* self.managing_roles) and job.user_id != user.id:
            raise PermissionError('Current user does not own the upload session!')

        if rq.POST.get('filepond'):
            # create a random sesskey based on user.id and job.id
            return Response(generate_sesskey(user.id, job.id))

        if (rq.method == 'PATCH'
            and (key := rq.params.get('patch'))
                and 'Upload-Name' in rq.headers):

            # check for filename
            filename = rq.headers['Upload-Name']
            offset = int(rq.headers['Upload-Offset'])
            try:
                uploaditem = sess.filenames[filename]
            except KeyError:
                return Response(json=dict(message="File not in the manifest"),
                                status="403",
                                content_type="text/plain",
                                headers=[('Error-Message',
                                         'ERR - File not in the manifest')])

            path = uploaditem.get_fullpath()

            if offset == 0:
                # remove previous file if exist
                path.unlink(missing_ok=True)
                uploaditem.total_size = int(rq.headers['Upload-Length'])
                uploaditem.key = key
                mode = 'wb'
            else:
                mode = 'r+b'

            with open(path, mode) as fout:

                # check continuity of the transfer
                prev_size = get_file_size(fout)
                if offset != prev_size:
                    return Response(json=dict(message="File offset is not correct"),
                                    status="400",
                                    content_type="text/plain",
                                    headers=[('Error-Message',
                                              'ERR - File offset is not correct')])

                # move file pointer to the end of file and append the content from body
                fout.seek(0, 2)
                fout.write(rq.body)
                curr_size = get_file_size(fout)

            if curr_size == uploaditem.total_size:
                uploaditem.completed = 1

            return Response('ok')

        if rq.method == 'DELETE':
            # ignore this
            return Response()

        return Response(json=dict(message="Protocol not implemented"),
                        status="400",
                        content_type="text/plain",
                        headers=[('Error-Message',
                                  'ERR - Protocol not implemented')])


# EOF
