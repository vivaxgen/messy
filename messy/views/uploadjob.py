
from rhombus.lib.utils import cerr
from rhombus.lib.fileutils import get_file_size
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
        user = rq.user
        job = self.get_object()

        self.can_modify(job)

        html = div().add(

        )


    @m_roles(r.PUBLIC)
    def target(self):

        rq = self.request
        user = rq.user
        idkey = rq.matchdict.get('id')

        # sanity check,
        job = sess = self.get_object()
        from pprint import pprint
        pprint(rq.GET)
        pprint(rq.POST)
        pprint(rq.headers)

        if ~user.has_roles(* self.managing_roles) and job.user_id != user.id:
            raise PermissionError('Current user does not own the upload session!')

        if rq.POST.get('filepond'):
            return Response(sess.sesskey)

        if (rq.method == 'PATCH'
            and rq.params.get('patch') == sess.sesskey
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
                                headers=[('Error-Message', 'ERROR - File not in the manifest')])

            path = uploaditem.get_fullpath()

            if offset == 0:
                # remove previous file if exist
                path.unlink(missing_ok=True)
                uploaditem.total_size = int(rq.headers['Upload-Length'])
                mode = 'wb'
            else:
                mode = 'r+b'

            with open(path, mode) as fout:
                prev_size = get_file_size(fout)
                fout.seek(0, 2)
                fout.write(rq.body)
                curr_size = get_file_size(fout)

            if curr_size == uploaditem.total_size:
                uploaditem.completed = 1
                cerr(f'[********** COMPLETED ****************]')
            else:
                cerr(f'[**********{curr_size} < {uploaditem.total_size}]')
            cerr(f'[>>>>>>>>>>>>>>>>body-length: {len(rq.body)} with prev-size: {prev_size} and curr-size: {curr_size}]')
            return Response('ok')

        if rq.method == 'DELETE':
            # ignore this
            return Response()

        raise ValueError('protocol unknown')


# EOF
