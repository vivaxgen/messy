
from rhombus.lib.utils import cerr, get_dbhandler

from messy.views import (BaseViewer, form_submit_bar, render_to_response, ParseFormError)
from messy.ext.panelseq.lib import roles as r
from rhombus.lib import tags as t

from messy.ext.panelseq.models.markers import PanelType
import sqlalchemy.exc


class PanelViewer(BaseViewer):

    managing_roles = BaseViewer.managing_roles + [r.PANEL_MANAGE]
    modifying_roles = [r.PANEL_MODIFY] + managing_roles

    object_class = get_dbhandler().Panel
    fetch_func = get_dbhandler().get_panels_by_ids
    edit_route = 'messy-panelseq.panel-edit'
    view_route = 'messy-panelseq.panel-view'
    attachment_route = 'messy-panelseq.panel-attachment'

    form_fields = {
        'code!': ('messy-panelseq.panel-code', ),
        'type': ('messy-panelseq.panel-type', int),
        'remark': ('messy-panelseq.panel-remark', ),
        'species_id': ('messy-panelseq.panel-species_id', int)
    }

    def index_helper(self):

        # all users can view Panels

        panels = self.dbh.get_panels()
        html, code = generate_panel_table(panels, self.request)

        html = t.div(t.h2('Panels'), html)

        return render_to_response("messy:templates/generic_page.mako", {
            'html': html,
            'code': code,
        }, request=self.request)

    def update_object(self, obj, d):

        dbh = self.dbh

        try:
            obj.update(d)
            if obj.id is None:
                dbh.session().add(obj)
            dbh.session().flush([obj])

        except sqlalchemy.exc.IntegrityError as err:
            dbh.session().rollback()
            detail = err.args[0]
            if 'UNIQUE' in detail or 'UniqueViolation' in detail:
                if 'panels.code' in detail or 'uq_panels_code' in detail:
                    raise ParseFormError(f'The panel code: {d["code"]} is '
                                         f'already being used. Please use other panel code!',
                                         'messy-panelseq-panel-code') from err

            raise RuntimeError(f'error updating object: {detail}')

    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        rq = self.request
        obj = obj or self.obj
        dbh = self.dbh

        ff = self.ffn
        eform = t.form(name='messy-panelseq.panel', method=t.POST, enctype=t.FORM_MULTIPART, readonly=readonly,
                       update_dict=update_dict)
        eform.add(
            self.hidden_fields(obj),
            t.fieldset(
                t.inline_inputs(
                    t.input_text(ff('code!'), 'Code', value=obj.code, offset=2, size=3, maxlength=24),
                    t.input_select(ff('type'), 'Type', value=obj.type, offset=1, size=2,
                                   options=[(t.value, t.name) for t in PanelType]),
                    t.input_select_ek(ff('species_id'), 'Species',
                                      value=obj.species_id or dbh.get_ekey('pv').id,
                                      offset=1, size=2, parent_ek=dbh.get_ekey('@SPECIES')),
                ),
                t.inline_inputs(
                    t.input_textarea(ff('remark'), 'Remark', value=obj.remark, offset=2),
                ),
                name="messy-panelseq.panel-fieldset"
            ),
            t.fieldset(
                form_submit_bar(create) if not readonly else t.div(),
                name='footer'
            ),
        )

        jscode = ''

        return t.div()[t.h2('Panel'), eform], jscode


def generate_panel_table(panels, request):

    table_body = t.tbody()

    can_manage = request.user.has_roles(* PanelViewer.modifying_roles)

    for panel in panels:
        table_body.add(
            t.tr(
                t.td(t.literal('<input type="checkbox" name="panel-ids" value="%d" />' % panel.id)
                     if can_manage else ''),
                t.td(t.a(panel.code, href=request.route_url('messy-panelseq.panel-view', id=panel.id))),
                t.td(PanelType(panel.type).name),
                t.td(panel.remark or '-'),
            )
        )

    panel_table = t.table(class_='table table-condensed table-striped')[
        t.thead(
            t.tr(
                t.th('', style="width: 2em"),
                t.th('Panel code'),
                t.th('Type'),
                t.th('Remark'),
            )
        )
    ]

    panel_table.add(table_body)

    if can_manage:
        add_button = ('New panel',
                      request.route_url('messy-panelseq.panel-add'))

        bar = t.selection_bar('panel-ids', action=request.route_url('messy-panelseq.panel-action'),
                              add=add_button)
        html, code = bar.render(panel_table)

    else:
        html = t.div(panel_table)
        code = ''

    return html, code

# EOF
