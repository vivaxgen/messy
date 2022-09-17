
from rhombus.lib.utils import cerr, cout, random_string, get_dbhandler
#from rhombus.lib.roles import SYSADM, DATAADM
from rhombus.views.generics import error_page
from rhombus.views import (BaseViewer, roles, m_roles, Response, FileIter, HTTPFound,
                           render_to_response, fileinstance_to_response, select2_lookup, ParseFormError,
                           form_submit_bar)
from rhombus.lib.modals import modal_delete, popup, modal_error
from rhombus.lib.exceptions import AuthError
import rhombus.lib.tags_b46 as t
import messy.lib.roles as r
import sqlalchemy.exc
from sqlalchemy import or_
import mimetypes


alnumdash = set(('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-'))
alnumdash_ext = alnumdash | set(('./'))


def validate_code(a_code, charset=alnumdash):
    """ check if a_code only contains alphanumerics and dash"""

    a_code = a_code.strip()
    validation = set((a_code))
    if not validation.issubset(charset):
        raise ValueError('Input can only contain alphanumerics and dash')
    return a_code


def validate_code_ext(a_code):
    """ check if a code only contains aphanumerics, dash, dot and slash
        which is suitable for code not related to pipeline processing
    """

    return validate_code(a_code, alnumdash_ext)


class BaseViewer(BaseViewer):

    @m_roles(r.PUBLIC)
    def files(self):
        pass

    @m_roles(r.PUBLIC)
    def fileaction(self):

        # upload file: POS
        # self.request.params
        # NestedMultiDict([
        # ('file_content', FieldStorage('file_content', 'toolbox.py')),
        # ('object_id', '3>\r\n<div class='),
        # ('_method', 'upload-file')])

        rq = self.request
        dbh = self.dbh

        _method = rq.params.get('_method', None)
        obj_id = int(rq.params.get('object_id'))
        obj = self.get_object(obj_id=obj_id)

        fid = rq.params.get('fid', None)
        if fid:
            fid = int(fid.removeprefix('/'))
            file_instance = obj.additional_files[fid]
            return fileinstance_to_response(file_instance)

        dbsess = dbh.session()

        if not obj.can_modify(rq.user):
            raise AuthError("Your user account does not the roles to modify this object.")

        if _method == 'upload-file':

            file_content = rq.POST.get('file_content')
            if type(file_content) == bytes:
                return error_page(rq, 'Please select the file first before clicking submit button')
            file_instance = dbh.FileAttachment()
            dbsess.add(file_instance)
            file_instance.update(file_content)
            dbsess.flush([file_instance])
            obj.additional_files[file_instance.id] = file_instance

            return HTTPFound(location=rq.referer)

        elif _method == 'delete':

            file_ids = [int(x) for x in rq.POST.getall('file-ids')]
            file_instances = dbh.FileAttachment.query(dbsess).filter(dbh.FileAttachment.id.in_(file_ids))
            file_instances = [file_instance for file_instance in file_instances
                              if (file_instance.id in obj.additional_files)]

            return Response(
                modal_delete(
                    title='Removing additional file(s)',
                    content=t.literal(
                        'You are going to remove the following file(s):'
                        '<ul>'
                        + ''.join(f'<li>{f.filename}</li>' for f in file_instances)
                        + '</ul>'
                    ),
                    request=rq,
                ),
                request=rq
            )

        elif _method == 'delete/confirm':

            file_ids = [int(x) for x in rq.POST.getall('file-ids')]
            file_instances = dbh.FileAttachment.query(dbsess).filter(dbh.FileAttachment.id.in_(file_ids))
            file_instances = [file_instance for file_instance in file_instances
                              if (file_instance.id in obj.additional_files)]

            deleted_filenames = []
            for file_instance in file_instances:
                obj.additional_files.remove(file_instance)
                deleted_filenames.append(file_instance.filename)
                dbsess.delete(file_instance)

            dbh.session.flush()
            rq.session.flash(
                ('success', 'File(s) that have been removed: ' + ', '.join(deleted_filenames)))

            return HTTPFound(location=rq.referer)

        raise NotImplementedError()


def generate_file_table(files, request, obj, route_name):

    not_guest = not request.user.has_roles(r.GUEST) or obj.can_modify(request.user)

    table_body = t.tbody()

    for a_file in files.values():
        table_body.add(
            t.tr(
                t.td(t.literal(f'<input type="checkbox" name="file-ids" value="{a_file.id}" />')),
                t.td(t.a(a_file.filename, href=request.route_url(route_name,
                                                                 _query={'object_id': obj.id,
                                                                         'fid': str(a_file.id)}))),
                t.td(a_file.size / 1000)
            )
        )

    file_table = t.table(class_='table table-condensed table-striped')[
        t.thead(
            t.tr(
                t.th('', style="width: 2em"),
                t.th('Filename'),
                t.th('Size (Kb)'),
            )
        )
    ]

    file_table.add(table_body)

    if not_guest:
        # add_button = ('Upload file', request.route_url(route_name, id=0))

        # prepare tool bar

        bar = t.selection_bar(
            'file-ids', action=request.route_url(route_name),
            others=t.button('Upload file',
                            class_='btn btn-sm btn-success',
                            id='upload-file',
                            name='_method',
                            value='upload_file',
                            type='button'),
            hiddens=[('object_id', obj.id), ]
        )
        html, code = bar.render(file_table)

        # prepare popup

        popup_content = t.div(class_='form-group form-inline')[
            t.div('File', t.literal('<input type="file" name="file_content">'))
        ]
        upload_button = t.submit_bar('Upload file', 'upload-file')

        upload_form = t.form(name='upload-form', action=request.route_url(route_name),
                             enctype=t.FORM_MULTIPART)[
            popup_content,
            t.literal(f'<input type="hidden" name="object_id" value="{obj.id}">'),
            upload_button
        ]

        file_table = t.div(
            t.div(
                popup('Upload file', upload_form, request=request),
                id='upload-file-modal', class_='modal fade', tabindex='-1', role='dialog'
            ),
            html
        )

        file_js = code + '''$('#upload-file').click( function(e) {$('#upload-file-modal').modal('show');});'''

        return (file_table, file_js)

    else:
        html = t.div(file_table)
        code = ''

    return html, code

# EOF
