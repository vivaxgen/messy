
from messy.views import *
import json


class PlateViewer(BaseViewer):

    managing_roles = BaseViewer.managing_roles + [ PLATE_MODIFY ]

    class_func = get_dbhandler().Plate
    fetch_func = get_dbhandler().get_plates_by_ids
    edit_route = 'messy.plate-edit'
    view_route = 'messy.plate-view'

    form_fields = {
        'code':                 ('messy-plate-code', ),
        'group_id':             ('messy-plate-group_id', ),
        'specimen_type_id':     ('messy-plate-sequencing_kit_id', ),
        'experiment_type_id':   ('messy-plate-experiment_type_id', ),
        'remark':               ('messy-plate-remark', ),
    }

    @m_roles( PUBLIC )
    def index(self):

        if self.request.user.has_roles( SYSADM, DATAADM, SYSVIEW, DATAVIEW, PLATE_MODIFY, PLATE_VIEW ):
            plates = self.dbh.get_plates( groups = None )
        else:
            plates = self.dbh.get_plates( groups = self.request.user.groups )

        html, code = generate_plate_table(plates, self.request)

        html = div()[ h2('Plates') ].add( html )

        return render_to_response("messy:templates/generic_page.mako",
            {    'html': html,
                'code': code,
            },
            request = self.request)


    def update_object(self, obj, d):
        rq = self.request
        dbh = self.dbh

        try:
            obj.update( d )
            if obj.id is None:
                obj.user_id = rq.user.id
                dbh.session().add(obj)
            dbh.session().flush([obj])

        except RuntimeError as err:
            raise


    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        obj = obj or self.obj
        dbh = self.dbh

        eform = form( name='messy-plate', method=POST)[
            self.hidden_fields(obj),
            fieldset(
                input_text(self.form_fields['code'][0], 'Code', value=obj.code,
                    offset=2, static=readonly, update_dict=update_dict),
                input_select(self.form_fields['group_id'][0], 'Group', value=obj.group_id,
                    offset=2, size=2, options = [ (g.id, g.name) for g in dbh.get_group() ],
                    static=readonly, update_dict=update_dict),
                input_select_ek(self.form_fields['specimen_type_id'][0], 'Specimen Type',
                    value = obj.specimen_type_id, offset=2, size=5, static=readonly,
                    parent_ek = dbh.get_ekey('@SPECIMEN_TYPE')),
                input_select_ek(self.form_fields['experiment_type_id'][0], 'Experiment Type',
                    value = obj.experiment_type_id, offset=2, size=5, static=readonly,
                    parent_ek = dbh.get_ekey('@EXPERIMENT_TYPE')),
                input_textarea(self.form_fields['remark'][0], 'Remark', value=obj.remark,
                    offset=2, static=readonly, update_dict=update_dict),
                name = 'messy-plate-fieldset',
            ),
            fieldset(
                form_submit_bar(create) if not readonly else div(),
                name = 'footer'
            ),
        ]

        return div()[ h2('Plate'), eform], ''


    @m_roles( PUBLIC )
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

        return { 'success': False }


def generate_plate_table(plates, request):

    table_body = tbody()

    not_guest = not request.user.has_roles( GUEST )

    for plate in plates:
        table_body.add(
            tr(
                td(literal('<input type="checkbox" name="plate-ids" value="%d" />' % plate.id)
                    if not_guest else ''),
                td( a(plate.code, href=request.route_url('messy.plate-view', id=plate.id)) ),
                td( plate.user ),
                td( plate.specimen_type ),
                td( plate.experiment_type ),
                td( plate.remark[:60] + '...')
            )
        )

    plate_table = table(class_='table table-condensed table-striped')[
        thead(
            tr(
                th('', style="width: 2em"),
                th('Code'),
                th('User'),
                th('Specimen Type'),
                th('Experiment Type'),
                th('Remark'),
            )
        )
    ]

    plate_table.add( table_body )

    if not_guest:
        add_button = ( 'New plate',
                        request.route_url('messy.plate-add')
        )

        bar = selection_bar('plate-ids', action=request.route_url('messy.plate-action'),
                    add = add_button)
        html, code = bar.render(plate_table)

    else:
        html = div(plate_table)
        code = ''

    return html, code
