
from rhombus.lib.utils import get_dbhandler
from rhombus.views import boolean_checkbox
from messy.views import (BaseViewer, t, render_to_response, error_page, form_submit_bar,
                         ParseFormError, generate_file_table, select2_lookup, Response,
                         modal_error, HTTPFound, modal_delete, behave_editor)
from messy.ext.ngsmgr.lib import roles as r
from messy.ext.ngsmgr.models.schema import PanelType
import sqlalchemy.exc
import json


class PanelViewer(BaseViewer):

    managing_roles = BaseViewer.managing_roles + [r.PANEL_MANAGE]
    modifying_roles = [r.PANEL_MODIFY] + managing_roles

    object_class = get_dbhandler().Panel
    fetch_func = get_dbhandler().get_panels_by_ids
    edit_route = 'messy-ngsmgr.panel-edit'
    view_route = 'messy-ngsmgr.panel-view'
    attachment_route = 'messy-ngsmgr.panel-attachment'

    form_fields = {
        'code!': ('messy-ngsmgr-panel-code', ),
        'remark': ('messy-ngsmgr-panel-remark', ),
        'species_id': ('messy-ngsmgr-panel-species_id', ),
        'group_id': ('messy-ngsmgr-panel-group_id', int),
        'type': ('messy-ngsmgr-panel-type', int),
        'related_panel_id': ('messy-ngsmgr-panel-related_panel_id', ),
        'refctrl': ('messy-ngsmgr-panel-refctrl', boolean_checkbox),
        'public': ('messy-ngsmgr-panel-public', boolean_checkbox),
        'json': ('messy-ngsmgr-panel-json', json.loads),
    }

    def can_modify(self, obj=None):
        obj = obj or self.obj
        if obj is not None and obj.can_modify(self.request.user):
            return True
        return super().can_modify(obj) and self.request.user.in_group

    def index_helper(self):

        # get all panels
        panels = self.dbh.get_panels()

        html, code = generate_panel_table(panels, self.request)

        # tidy-up the page

        html = t.div()[t.h2('Panels')].add(html)

        return render_to_response("messy:templates/datatablebase.mako", {
            'html': html,
            'code': code,
        }, request=self.request)

    def lookup_helper(self):
        q = self.request.params.get('q')
        if not q:
            return error_page(self.request, "q not provided")
        q = '%' + q.lower() + '%'

        dbh = self.dbh
        panels = dbh.Panel.query(dbh.session()).filter(dbh.Panel.code.ilike(q))

        result = [
            {'id': p.id, 'text': p.code}
            for p in panels
        ]

        return result

    def update_object(self, obj, d):

        dbh = self.dbh
        ff = self.ffn

        try:
            obj.update(d)
            if obj.id is None:
                dbh.session().add(obj)
            if not self.can_modify(obj):
                raise PermissionError(
                    'You do not have the correct permission to modify the updated Panel.')
            dbh.session().flush([obj])

        except sqlalchemy.exc.IntegrityError as err:
            dbh.session().rollback()
            detail = err.args[0]
            if 'UNIQUE' in detail or 'UniqueViolation' in detail:
                if 'panels.code' in detail or 'uq_panels_code' in detail:
                    raise ParseFormError(f'The panel code: {d["code"]} is '
                                         f'already being used. Please use other panel code!',
                                         ff('code!')) from err

            raise RuntimeError(f'error updating object: {detail}')

        except sqlalchemy.exc.DataError as err:
            dbh.session().rollback()
            detail = err.args[0]

            raise RuntimeError(detail)

    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        rq = self.request
        obj = obj or self.obj
        dbh = self.dbh

        ff = self.ffn
        eform = t.form(name='messy-ngsmgr-panel', method=t.POST, enctype=t.FORM_MULTIPART,
                       readonly=readonly, update_dict=update_dict)
        eform.add(
            self.hidden_fields(obj),
            t.fieldset(
                t.input_text(ff('code!'), 'Code', value=obj.code, offset=2),
                t.input_select(
                    ff('group_id'), 'Group', value=obj.group_id, offset=2, size=2,
                    options=[(g.id, g.name) for g in
                             dbh.get_group(user_id=rq.user,
                                           additional_ids=[obj.group_id] if obj.group_id else None)
                             ]
                ),
                t.input_text(ff('remark'), 'Remark', value=obj.remark,
                             offset=2),
                t.input_select(
                    ff('type'), 'Type', value=obj.type or 1, offset=2, size=2,
                    options=[(pt.value, pt.name) for pt in PanelType]
                ),
                t.input_select(
                    ff('related_panel_id'), 'Related Panel',
                    value=obj.related_panel_id if obj.related_panel_id else None,
                    options=[(obj.related_panel_id, f'{obj.related_panel.code}')]
                    if obj.related_panel_id else [],
                    offset=2, size=3),
                t.input_select_ek(ff('species_id'), 'Species',
                                  value=obj.species_id or dbh.get_ekey('pv').id,
                                  offset=2, size=3, parent_ek=dbh.get_ekey('@SPECIES')),
                t.input_textarea(ff('json'), 'Data', value=json.dumps(obj.json, indent=2),
                                 offset=2),
                t.inline_inputs(
                    t.checkboxes('messy-ngsmgr-panel-status', 'Panel status', [
                        (ff('refctrl'), 'Reference/Control',
                            obj.refctrl),
                        (ff('public'), 'Public',
                            obj.public),
                    ], offset=2),
                ),
                name="messy-ngsmgr-panel-fieldset"
            ),

            t.fieldset(
                form_submit_bar(create) if not readonly else t.div(),
                name='footer'
            ),
        )

        jscode = behave_editor(ff('json'))

        if not readonly:
            jscode += select2_lookup(tag=ff('related_panel_id'), minlen=3,
                                     placeholder="Type panel code",
                                     parenttag="messy-ngsmgr-panel-fieldset", usetag=False,
                                     url=self.request.route_url('messy-ngsmgr.panel-lookup'))

        return t.div()[t.h2('Panel'), eform], jscode

    def view_helper(self, render=True) -> tuple[str, str] | Response:

        panel_html, panel_jscode = super().view_helper(render=False)

        panel_html.add(
            t.hr,
            t.h6('Additional Files')
        )

        file_html, file_jscode = generate_file_table(self.obj.additional_files, self.request,
                                                     self.obj, 'messy-ngsmgr.panel-fileaction')

        panel_html.add(file_html)
        panel_jscode += file_jscode

        if not render:
            return (panel_html, panel_jscode)
        return self.render_edit_form(panel_html, panel_jscode)

    def action_post(self):

        rq = self.request
        dbh = self.dbh
        _method = rq.POST.get('_method')

        if _method == 'delete':

            panel_ids = [int(x) for x in rq.POST.getall('panel-ids')]
            panels = dbh.get_panels_by_ids(panel_ids, groups=None, user=rq.user)

            if len(panels) == 0:
                return Response(modal_error(content="Please select panel(s) to be removed"))

            return Response(
                modal_delete(
                    title='Removing Panel(s)',
                    content=t.literal(
                        'You are going to remove the following panel(s): '
                        '<ul>'
                        + ''.join(
                            f'<li>{p.code} | {p.type} | '
                            for p in panels)
                        + '</ul>'
                        'All associated regions and variants will be removed. '
                        'Do you want to continue?'
                    ), request=rq,
                ), request=rq
            )

        elif _method == 'delete/confirm':

            panel_ids = [int(x) for x in rq.POST.getall('panel-ids')]
            panels = dbh.get_panels_by_ids(panel_ids, groups=None, user=rq.user)

            sess = dbh.session()
            count = left = 0
            for panel in panels:
                if panel.can_modify(rq.user):
                    sess.delete(panel)
                    count += 1
                else:
                    left += 1

            sess.flush()
            rq.session.flash(
                ('success',
                 f'You have removed {count} panel(s) sucessfully' +
                 (f', {left} panel(s) unsucessfully.' if left else '.'))
            )

            return HTTPFound(location=rq.referer)

        raise RuntimeError('unknown method')


def generate_panel_table(panels, request):

    table_body = t.tbody()

    not_guest = not request.user.has_roles(r.GUEST)
    can_manage = request.user.has_roles(* PanelViewer.modifying_roles)

    for p in panels:
        table_body.add(
            t.tr(
                t.td(t.literal(f'<input type="checkbox" name="panel-ids" value="{p.id}" />')
                     if not_guest else ''),
                t.td(t.a(p.code,
                         href=request.route_url('messy-ngsmgr.panel-view', id=p.id))),
                t.td(PanelType(p.type).name),
                t.td(p.species),
                t.td(p.related_panel.code if p.related_panel else ''),
            )
        )

    panel_table = t.table(id='panel-table', class_='table table-condensed table-striped')[
        t.thead(
            t.tr(
                t.th('', style="width: 2em"),
                t.th('Code'),
                t.th('Type'),
                t.th('Species'),
                t.th('Related Panel'),
            )
        )
    ]

    panel_table.add(table_body)

    if not_guest and can_manage:
        add_button = ('New panel',
                      request.route_url('messy-ngsmgr.panel-add'))

        bar = t.selection_bar('panel-ids',
                              action=request.route_url('messy-ngsmgr.panel-action'),
                              add=add_button)
        html, code = bar.render(panel_table)

    else:
        html = t.div(panel_table)
        code = ''

    code += template_datatable_js
    return html, code


template_datatable_js = """
$(document).ready(function() {
    $('#panel-table').DataTable( {
        paging: false,
        fixedHeader: {
            headerOffset: $('#fixedNavbar').outerHeight()
        },
        orderClasses: false,
        columns: [
            { title: ' ', orderable: false, width: '12px' },
            { },
            { },
            { },
            { },
        ]
    } );
} );
"""


# EOF
