
from rhombus.lib.utils import cerr
from rhombus.lib.fileutils import get_file_size
from rhombus.lib import tags as t
from rhombus.views import generate_sesskey
from messy.models.dbschema import UploadJob
from messy.views import (BaseViewer, m_roles, get_dbhandler, render_to_response,
                         form_submit_bar, select2_lookup, modal_delete, modal_error,
                         HTTPFound)
from messy.lib import roles as r

from pyramid.response import Response
from pyramid.exceptions import HTTPBadRequest

import json
from time import sleep


class UploadJobViewer(BaseViewer):

    __subdir__ = 'uploads/generics/'
    __root_storage_path__ = None

    object_class = UploadJob
    fetch_func = get_dbhandler().get_uploadjobs_by_ids

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
        if not user.has_roles(* self.managing_roles) and job.user_id != user.id:
            raise PermissionError('Current user does not own the upload session!')

    def action_post(self):

        rq = self.request
        dbh = self.dbh

        match _method := rq.POST.get('_method'):

            case 'delete':

                job_ids = [int(x) for x in rq.POST.getall('uploadjob-ids')]
                jobs = dbh.get_uploadjobs_by_ids(job_ids, groups=None, user=rq.user)

                if len(jobs) == 0:
                    return Response(
                        modal_error(
                            content="Please select upload jobs to be removed!")
                    )

                return Response(
                    modal_delete(
                        title='Removing upload job(s)',
                        content=t.literal(
                            'You are going to remove the following upload job(s): '
                            '<ul>'
                            + ''.join(f'<li>{j.start_time} | {j.get_status()}</li>'
                                      for j in jobs)
                            + '</ul>'
                        ), request=rq,
                    ), request=rq
                )

            case 'delete/confirm':

                job_ids = [int(x) for x in rq.POST.getall('uploadjob-ids')]
                jobs = dbh.get_uploadjobs_by_ids(job_ids, groups=None, user=rq.user)

                sess = dbh.session()
                count = left = 0
                for j in jobs:
                    if j.can_modify(rq.user):
                        j.clear()
                        sess.delete(j)
                        count += 1
                    else:
                        left += 1

                sess.flush()

                rq.session.flash(
                    ('success', f'You have successfully removed {count} uploadjob(s), '
                                f'kept {left} uploadjob(s).')
                )

                return HTTPFound(location=rq.referer)

        raise ValueError(f'unknown method: {_method}')

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

        if job.json is None:
            return Response(body="This upload session is invalid. Please remove!",
                            status='200', content_type="text/html")

        self.can_modify(job)

        # check how many files has been completed
        completed = job.get_uploaded_count()

        html = t.div().add(
            t.h2('Upload Session'),
            t.p(f'Started at: {job.start_time} UTC'),
            t.p(f'Total files: {job.json["file_count"]}'),
            t.p(f'Uploaded: {completed}'),
            t.div(
                t.a('Save', href=rq.route_url('messy.uploadjob-save',
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

        if rq.method == 'HEAD' and (key := rq.params.get('patch')):
            # asking for the last offset
            uploaditem = self.dbh.UploadItem.get_by_key(key, self.dbh)
            with open(uploaditem.get_fullpath(), 'rb') as fout:
                offset = get_file_size(fout)
            return Response(str(offset))

        return Response(json=dict(message="Protocol not implemented"),
                        status="400",
                        content_type="text/plain",
                        headers=[('Error-Message',
                                  'ERR - Protocol not implemented')])


def generate_uploadjob_table(uploadjobs, request):

    table_body = t.tbody()

    for job in uploadjobs:
        table_body.add(
            t.tr(
                t.td(
                    t.literal(
                        f'<input type="checkbox" name="uploadjob-ids" value="{job.id}" />'
                    )
                ),
                t.td(t.a(job.start_time,
                         href=request.route_url('messy.uploadjob-view',
                                                id=job.id)
                         )
                     ),
                t.td(job.user.login),
                t.td(job.get_status())
            )
        )

    job_table = t.table(id='uploadjob-table', class_='table table-condensed table-striped',
                        style='width:100%')[
        t.thead(
            t.tr(
                t.th('', style='width: 2em'),
                t.th('Started at'),
                t.th('Started by'),
                t.th('Status'),
            )
        )
    ]

    job_table.add(table_body)

    bar = t.selection_bar('uploadjob-ids', action=request.route_url('messy.uploadjob-action'))
    html, code = bar.render(job_table)

    return html, code

# EOF
