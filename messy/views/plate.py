
from messy.views import (BaseViewer, r, get_dbhandler, m_roles, ParseFormError, form_submit_bar,
                         render_to_response, form_submit_bar, select2_lookup, error_page,
                         Response, modal_delete, modal_error, Response)
import rhombus.lib.tags_b46 as t

import sqlalchemy.exc
import dateutil
import json


class PlateViewer(BaseViewer):

    managing_roles = BaseViewer.managing_roles + [r.PLATE_MANAGE]
    modifying_roles = [r.PLATE_MODIFY] + managing_roles

    object_class = get_dbhandler().Plate
    fetch_func = get_dbhandler().get_plates_by_ids
    edit_route = 'messy.plate-edit'
    view_route = 'messy.plate-view'
    attachment_route = 'messy.plate-attachment'

    form_fields = {
        'code*': ('messy-plate-code', ),
        'group_id': ('messy-plate-group_id', ),
        'date': ('messy-plate-date', dateutil.parser.parse),
        'specimen_type_id': ('messy-plate-sequencing_kit_id', ),
        'experiment_type_id': ('messy-plate-experiment_type_id', ),
        'attachment': ('messy-plate-attachment', ),
        'remark': ('messy-plate-remark', ),
    }

    @m_roles(r.PUBLIC)
    def index(self):

        if self.request.user.has_roles(r.SYSADM, r.DATAADM, r.SYSVIEW, r.DATAVIEW, r.PLATE_MODIFY, r.PLATE_VIEW):
            plates = self.dbh.get_plates(groups=None)
        else:
            plates = self.dbh.get_plates(groups=self.request.user.groups)

        html, code = generate_plate_table(plates, self.request)

        html = t.div()[t.h2('Plates')].add(html)

        return render_to_response("messy:templates/generic_page.mako", {
            'html': html,
            'code': code,
        }, request=self.request)

    def update_object(self, obj, d):
        rq = self.request
        dbh = self.dbh

        try:
            obj.update(d)
            if obj.id is None:
                obj.user_id = rq.user.id
                dbh.session().add(obj)
            dbh.session().flush([obj])

        except sqlalchemy.exc.IntegrityError as err:
            dbh.session().rollback()
            detail = err.args[0]
            if 'UNIQUE' in detail or 'UniqueViolation' in detail:
                if 'plates.code' in detail or 'uq_plates_code' in detail:
                    raise ParseFormError(f"The plate code: {d['code']} is already being used.",
                                         self.ffn('code*')) from err
            raise RuntimeError('unhandled error updating Plate object')

        except RuntimeError:
            raise

    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        obj = obj or self.obj
        dbh = self.dbh
        ff = self.ffn

        eform = t.form(name='messy-plate', method=t.POST, enctype=t.FORM_MULTIPART, readonly=readonly,
                       update_dict=update_dict)[
            self.hidden_fields(obj),
            t.fieldset(
                t.input_text(ff('code*'), 'Code', value=obj.code, offset=2),
                t.input_text(ff('date'), 'Date', value=obj.date, offset=2, size=2),
                t.input_select(ff('group_id'), 'Group', value=obj.group_id, offset=2, size=3,
                               options=[(g.id, g.name) for g in dbh.get_group()]),
                t.input_select_ek(ff('specimen_type_id'), 'Specimen Type', offset=2, size=3,
                                  value=obj.specimen_type_id, parent_ek=dbh.get_ekey('@SPECIMEN_TYPE')),
                t.input_select_ek(ff('experiment_type_id'), 'Experiment Type', offset=2, size=3,
                                  value=obj.experiment_type_id, parent_ek=dbh.get_ekey('@EXPERIMENT_TYPE')),
                t.input_textarea(ff('remark'), 'Remark', value=obj.remark, offset=2),
                t.input_file_attachment(ff('attachment'), 'Attachment', value=obj.attachment, offset=2, size=4)
                .set_view_link(self.attachment_link(obj, 'attachment')),
                name='messy-plate-fieldset',
            ),
            t.fieldset(
                form_submit_bar(create) if not readonly else t.div(),
                name='footer'
            ),
        ]

        return t.div()[t.h2('Plate'), eform], ''

    def view_helper(self, render=True):

        plate_html, plate_jscode = super().view_helper(render=False)

        plate_html.add(
            t.hr,
            t.h4('Plate Layout'),
        )

        if not self.obj.has_layout:
            plate_html.add(t.p('No layout defined.'))
        else:
            plate_html.add(t.p('View layout'))

        return self.render_edit_form(plate_html, plate_jscode)

    @m_roles(r.PUBLIC)
    def position(self):
        """ well REST interface """

        if self.request.GET:
            pass
        elif self.request.POST:
            pass
        elif self.request.PUT:
            pass
        elif self.request.DELETE:
            pass

        return {'success': False}


def generate_plate_table(plates, request):

    table_body = t.tbody()

    not_guest = not request.user.has_roles(r.GUEST)

    for plate in plates:
        table_body.add(
            t.tr(
                t.td(t.literal(f'<input type="checkbox" name="plate-ids" value="{plate.id}" />')
                     if not_guest else ''),
                t.td(t.a(plate.code, href=request.route_url('messy.plate-view', id=plate.id))),
                t.td(plate.user),
                t.td(plate.date),
                t.td(plate.specimen_type),
                t.td(plate.experiment_type),
                t.td(plate.remark[:60] + '...')
            )
        )

    plate_table = t.table(class_='table table-condensed table-striped')[
        t.thead(
            t.tr(
                t.th('', style="width: 2em"),
                t.th('Code'),
                t.th('User'),
                t.th('Date'),
                t.th('Specimen Type'),
                t.th('Experiment Type'),
                t.th('Remark'),
            )
        )
    ]

    plate_table.add(table_body)

    if not_guest:
        add_button = ('New plate', request.route_url('messy.plate-add'))

        bar = t.selection_bar('plate-ids', action=request.route_url('messy.plate-action'),
                              add=add_button)
        html, code = bar.render(plate_table)

    else:
        html = t.div(plate_table)
        code = ''

    return html, code

# EOF
