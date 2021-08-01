
from rhombus.lib.utils import cerr, cout, random_string, get_dbhandler
#from rhombus.lib.roles import SYSADM, DATAADM
from rhombus.views.generics import error_page
from rhombus.views import *
from rhombus.lib.modals import *
import rhombus.lib.tags_b46 as t
import messy.lib.roles as r
from sqlalchemy.orm import make_transient, make_transient_to_detached
import sqlalchemy.exc
from sqlalchemy import or_

from messy.lib.roles import *
from rhombus.lib.tags import *


class BaseViewer(BaseViewer):

    @m_roles(r.PUBLIC)
    def files(self):
        pass

    @m_roles(r.PUBLIC)
    def fileaction(self):
        raise NotImplementedError()


def generate_file_table(files, request, object_id, route_name):

    not_guest = not request.user.has_roles(r.GUEST)

    table_body = t.tbody()

    for a_file in files:
        table_body.add(
            t.tr(
                t.td(t.literal(f'<input type="checkbox" name="file-ids" value="{a_file.id}" />')),
                t.td(a_file.filename),
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
            hiddens=[('object_id', object_id), ]
        )
        html, code = bar.render(file_table)

        # prepare popup

        popup_content = t.div(class_='form-group form-inline')[
            t.div('File', t.literal("<input type='file'>"))
        ]
        upload_button = t.submit_bar('Upload file', 'upload-file')

        upload_form = t.form(name='upload-form', action=request.route_url(route_name),
                             enctype=t.FORM_MULTIPART)[
            popup_content,
            t.literal(f'<input type="hidden" name="object_id" value="{object_id}>'),
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
