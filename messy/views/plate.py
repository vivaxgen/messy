
from messy.views import (BaseViewer, r, get_dbhandler, m_roles, ParseFormError, form_submit_bar,
                         render_to_response, form_submit_bar, select2_lookup, error_page,
                         Response, modal_delete, modal_error, Response, HTTPFound,
                         generate_file_table, AuthError, validate_code)
import rhombus.lib.tags_b46 as t
from messy.lib import plate_utils

from more_itertools import chunked, unzip
import sqlalchemy.exc
import dateutil
import json


class PlateViewer(BaseViewer):

    template_edit = 'messy:templates/gridbase.mako'

    managing_roles = BaseViewer.managing_roles + [r.PLATE_MANAGE]
    modifying_roles = [r.PLATE_MODIFY] + managing_roles

    object_class = get_dbhandler().Plate
    fetch_func = get_dbhandler().get_plates_by_ids
    edit_route = 'messy.plate-edit'
    view_route = 'messy.plate-view'
    attachment_route = 'messy.plate-attachment'

    form_fields = {
        'code*': ('messy-plate-code', validate_code),
        'group_id': ('messy-plate-group_id', ),
        'date': ('messy-plate-date', dateutil.parser.parse),
        'specimen_type_id': ('messy-plate-sequencing_kit_id', ),
        'experiment_type_id': ('messy-plate-experiment_type_id', ),
        'storage': ('messy-plate-storage'),
        'attachment': ('messy-plate-attachment', ),
        'remark': ('messy-plate-remark', ),
    }

    @m_roles(r.PUBLIC)
    def index(self):

        if self.request.user.has_roles(r.SYSADM, r.DATAADM, r.SYSVIEW, r.DATAVIEW, r.PLATE_MODIFY, r.PLATE_VIEW):
            plates = self.dbh.get_plates(groups=None, fetch=False).order_by(self.dbh.Plate.date.desc())
        else:
            plates = self.dbh.get_plates(groups=self.request.user.groups, fetch=False).order_by(self.dbh.Plate.date.desc())

        html, code = generate_plate_table(plates, self.request)

        html = t.div()[t.h2('Plates')].add(html)

        return render_to_response("messy:templates/datatablebase.mako", {
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

        rq = self.request
        obj = obj or self.obj
        dbh = self.dbh
        ff = self.ffn

        eform = t.form(name='messy-plate', method=t.POST, enctype=t.FORM_MULTIPART, readonly=readonly,
                       update_dict=update_dict)[
            self.hidden_fields(obj),
            t.fieldset(
                t.input_text(ff('code*'), 'Code', value=obj.code, offset=2, size=4),
                t.input_text(ff('date'), 'Experiment Date', value=obj.date, offset=2, size=2, placeholder='YYYY/MM/DD'),
                t.input_select(ff('group_id'), 'Group', value=obj.group_id, offset=2, size=3,
                               options=[(g.id, g.name) for g in dbh.get_group(user_id=rq.user)]),
                t.input_select_ek(ff('specimen_type_id'), 'Specimen Type', offset=2, size=3,
                                  value=obj.specimen_type_id, parent_ek=dbh.get_ekey('@SPECIMEN_TYPE')),
                t.input_select_ek(ff('experiment_type_id'), 'Experiment Type', offset=2, size=3,
                                  value=obj.experiment_type_id, parent_ek=dbh.get_ekey('@EXPERIMENT_TYPE')),
                t.input_text(ff('storage'), 'Storage Location', value=obj.storage, offset=2, size=4),
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
            t.h6('Additional files'),
        )

        file_html, file_jscode = generate_file_table(self.obj.additional_files, self.request,
                                                     self.obj, 'messy.plate-fileaction')

        plate_html.add(file_html)
        plate_jscode += file_jscode

        plate_html.add(
            t.hr,
            t.h4('Plate Layout'),
        )

        if not self.obj.has_layout():
            plate_html.add(t.p('No layout defined.'))
            plate_html[
                t.form(name='messy-platelayout', action=self.request.route_url('messy.plate-action', id=self.obj.id),
                       method=t.POST)[
                    t.input_select('messy-plate-layout', 'Layout',
                                   value=None, offset=1, size=1,
                                   options=[(str(x), str(x)) for x in plate_utils.plate_layouts]),
                    t.input_hidden('id', self.obj.id),
                    t.custom_submit_bar(('Create', 'create_layout')).set_offset(1),
                    '- or -',
                    t.fieldset(
                        t.input_select('messy-plate-source_plate_id', 'Copy from',
                                       value=None, offset=1, size=3),
                        name='messy-copyplate-fieldset'
                    ),
                    t.custom_submit_bar(('Copy', 'copy_layout')).set_offset(1),
                ]
            ]
            layout_js = (select2_lookup(tag='messy-plate-source_plate_id', minlen=2,
                                        placeholder="Type plate code here",
                                        parenttag='messy-copyplate-fieldset', usetag=False,
                                        url=self.request.route_url('messy.plate-lookup')))

        elif not self.request.GET.get('tabular', False):

            plate_html.add(
                t.p(
                    t.a('View in tabular form',
                        href=self.request.route_url(self.view_route, id=self.obj.id,
                                                    _query={'tabular': 1})),
                    ' | ',
                    t.a('Print layout',
                        href=self.request.route_url('messy.plate-action',
                                                    _query={'id': self.obj.id,
                                                            '_method': 'print_layout'}))
                )
            )

            layout = len(self.obj.positions)
            r, c = plate_utils.plate_layouts[layout]

            plate_html.add(t.h5('Sample Codes'))
            plate_html.add(t.div(id='layout_index'))
            layout_js = template_grid_js.format(name='layout_index', plate_id=self.obj.id, plate_layout='true',
                                                column=c, row=r, additional_options=template_sample_link_js)

            plate_html.add(t.h5('Sample Value'))
            plate_html.add(t.div(id='layout_value'))
            layout_js += template_grid_js.format(name='layout_value', plate_id=self.obj.id, plate_layout='true',
                                                 column=c, row=r, additional_options='')
            plate_html.add(t.h5('Sample Volume'))
            plate_html.add(t.div(id='layout_volume'))
            layout_js += template_grid_js.format(name='layout_volume', plate_id=self.obj.id, plate_layout='true',
                                                 column=c, row=r, additional_options='')

        else:
            n = len(self.obj.positions)
            plate_html.add(t.p(t.a('View in plate form', href=self.request.route_url(self.view_route, id=self.obj.id))))
            plate_html.add(t.div(id='tabular'))
            layout_js = template_grid_js.format(name='tabular', plate_id=self.obj.id, plate_layout='false',
                                                column=4, row=n, additional_options=template_additional_options_js)

        return self.render_edit_form(plate_html, plate_jscode + layout_js)

    @m_roles(r.PUBLIC)
    def position(self):
        """ well REST interface """
        _m = self.request.method
        rq = self.request
        dbh = get_dbhandler()
        plate = self.get_object()
        N = len(plate.positions)
        r, c = layout = plate_utils.plate_layouts[N]

        if _m == t.GET:
            name = rq.GET.get('name', 'layout_index')

            positions = list(plate.positions)

            if name == 'layout_index':
                codes = list(chunked([p.sample.code for p in positions], r))
                # transpose and return
                return list(zip(*codes))

            elif name == 'layout_value':
                values = list(chunked([p.value for p in positions], r))
                return list(zip(*values))

            elif name == 'layout_volume':
                volumes = list(chunked([p.volume for p in positions], r))
                return list(zip(*volumes))

            elif name == 'tabular':
                return list([[p.position, p.sample.code, p.value, p.volume, p.note if p.note else '']
                            for idx, p in enumerate(plate.positions, 1)])

            return []

        elif _m == t.POST:
            """
            request.POST is MultiDict([('data', '[{"row":"3","data":{"3":"def"}}]'), ('name', '')])
            """
            if not plate.can_modify(rq.user):
                return {'success': False}

            updates = json.loads(rq.POST.get('data'))
            name = rq.POST.get('name')

            update_list = convert_data_to_indexes(updates, layout)
            indexes, values = zip(*update_list)
            if max(indexes) > N:
                return {'success': False}

            if name == 'layout_index':

                # check every samples in indexes, return error if any sample is invalid
                values = list(set(values))
                if len(values) != dbh.get_samples_by_codes(values, groups=None, fetch=False, ignore_acl=True).count():
                    return {'success': False}

                for (idx, val) in update_list:
                    print(idx, val)
                    plate.positions[idx].sample_id = dbh.get_samples_by_codes(val, groups=None, ignore_acl=True)[0].id

                return {'success': True}

            elif name == 'layout_value':
                for (idx, val) in update_list:
                    plate.positions[idx].value = float(val)
                return {'success': True}

            elif name == 'layout_volume':
                for (idx, val) in update_list:
                    plate.positions[idx].volume = float(val)
                return {'success': True}

            elif name == 'tabular':
                for row in updates:
                    idx = int(row['row'])
                    for _c, value in row['data'].items():
                        if _c == '1':
                            if len(r := dbh.get_samples_by_codes(value, groups=None, ignore_acl=True)) == 1:
                                plate.positions[idx].sample_id = r[0].id
                            else:
                                return {'success': False}
                        elif _c == '2':
                            plate.positions[idx].value = float(value)
                        elif _c == '3':
                            plate.positions[idx].volume = float(value)
                        elif _c == '4':
                            if (value := value.strip()):
                                value = value[:31]
                            else:
                                value = None
                            plate.positions[idx].note = value[:31]
                return {'success': True}

        elif _m == t.PUT:
            pass

        elif _m == t.DELETE:
            pass

        return {'success': False}

    def action_post(self):

        rq = self.request
        dbh = self.dbh
        _method = rq.POST.get('_method')

        if _method == 'create_layout':
            plate = self.get_object(obj_id=rq.params.get('id'))
            if not plate.can_modify(rq.user):
                raise AuthError()
            layout = int(rq.POST.get('messy-plate-layout'))
            plate_utils.create_positions(plate, layout)
            rq.session.flash(('success', f'Plate layout {layout}-well has been created'))
            return HTTPFound(location=rq.route_url(self.view_route, id=plate.id))

        elif _method == 'copy_layout':
            plate = self.get_object(obj_id=rq.params.get('id'))
            if not plate.can_modify(rq.user):
                raise AuthError()
            source_plate_id = int(rq.POST.get('messy-plate-source_plate_id'))
            source_plate = dbh.get_plates_by_ids([source_plate_id], groups=None)[0]
            plate_utils.copy_positions(plate, source_plate)
            rq.session.flash(('success', f'Plate layout has been copied from {source_plate.code}'))
            return HTTPFound(location=rq.route_url(self.view_route, id=plate.id))

        elif _method == 'delete':

            plate_ids = [int(x) for x in rq.params.getall('plate-ids')]
            plates = dbh.get_plates_by_ids(plate_ids, groups=None, user=rq.user)

            if len(plates) == 0:
                return Response(modal_error)

            return Response(
                modal_delete(
                    title='Removing plate(s)',
                    content=t.literal(
                        'You are going to remove the following plate(s): '
                        '<ul>'
                        + ''.join(f'<li>{p.code}</li>' for p in plates)
                        + '</ul>'
                    ), request=rq,

                ), request=rq
            )

        elif _method == 'delete/confirm':

            plate_ids = [int(x) for x in rq.params.getall('plate-ids')]
            plates = dbh.get_plates_by_ids(plate_ids, groups=None, user=rq.user)

            sess = dbh.session()
            count = left = 0
            for p in plates:
                if p.can_modify(rq.user):
                    sess.delete(p)
                    count += 1
                else:
                    left += 1

            sess.flush()
            rq.session.flash(
                ('success', f'You have successfully removed {count} sample(s), kept {left} samples.')
            )

            return HTTPFound(location=rq.referer)

        raise RuntimeError('No defined action')

    def action_get(self):

        rq = self.request
        dbh = self.dbh
        _method = rq.GET.get('_method')

        if _method == 'print_layout':
            plate = self.get_object(obj_id=rq.params.get('id'))
            return render_to_response("messy:templates/generic_plainpage.mako", {
                'html': generate_print_layout(plate, rq)
            }, request=rq)

        raise ValueError('undefined method')

    def lookup_helper(self):
        q = self.request.params.get('q')
        if not q:
            return error_page(self.request, "q not provided")
        q = '%' + q.lower() + '%'

        runs = get_dbhandler().get_plates_by_codes(q, groups=None, user=self.request.user)
        result = [
            {'id': r.id, 'text': r.code} for r in runs
        ]

        return result


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

    plate_table = t.table(id='plate-table', class_='table table-condensed table-striped',
                          style='width:100%')[
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

    code += template_datatable_js
    return html, code


def generate_print_layout(plate, request):
    """ generate a plain html containing the layout that is suitable for printing """

    N = len(plate.positions)
    r, c = plate_utils.plate_layouts[N]
    positions = list(plate.positions)

    tbody = t.tbody()
    for r_idx in range(r):
        tr = t.tr(t.td(t.b(chr(65 + r_idx))))
        for c_idx in range(c):
            tr.add(t.td(positions[r * c_idx + r_idx].sample.code, t.br, t.br, t.br))
        tbody.add(tr)

    layout_table = t.table(class_='table table-condensed table-striped', style='width:100%')[
        t.thead(
            t.tr(t.th(''))[
                [t.th(x + 1) for x in range(c)]
            ]
        )
    ]

    layout_table.add(tbody)
    html = t.div(
        t.h3(
            f'Plate Code: {plate.code} / {plate.date} / {plate.experiment_type}'
        ),
        layout_table
    )

    return html


def convert_data_to_indexes(a_list, plate_layout):
    """convert data from jspreadsheet to [ (index, value), ...]

    plate layout is:
            1   2   3   4   5   6
        A   1   5   9   13  17  21
        B   2   6   10  14  18  22
        C   3   7   11  15  19  23
        D   4   8   12  16  20  24
    """
    indexes = []
    r, c = plate_layout
    for row in a_list:
        _r = int(row['row'])
        for _c, value in row['data'].items():
            indexes.append((_r + r * int(_c), value))
    return indexes


# template_grid_js requires name, plate_layout, column, row, plate_id
template_grid_js = """
{name} = jspreadsheet(document.getElementById('{name}'), {{
    plate_layout:{plate_layout},
    defaultColWidth:80,
    allowInsertRow:false,
    allowInsertColumn:false,
    allowDeleteRow:false,
    allowDeleteColumn:false,
    allowRenameColumn:false,
    allowComments:false,
    columnSorting:false,
    minDimensions:[{column},{row}],
    name:'{name}',
    url:'/plate/{plate_id}@@position?name={name}',
    persistance:'/plate/{plate_id}@@position',
{additional_options}
}});
"""

# additional options

# change header for tabular form
template_additional_options_js = """
    columns: [
        { title: 'Position', width: 75, readOnly: true },
        { title: 'Sample Code', width:100 },
        { title: 'Value', width: 75},
        { title: 'Volume', width: 75 },
        { title: 'Note', width: 175 },
    ],
    updateTable: function (instance, cell, col, row, val, id) {
        if (col == 1) {
            cell.innerHTML = '<a href="/sample/code=' + val + '" style="text-decoration:none;">' + val + '</a>';
        }
    },
"""

# set text to hyperlink for index layout
template_sample_link_js = """
    updateTable: function (instance, cell, col, row, val, id) {
        cell.innerHTML = '<a href="/sample/code=' + val + '" style="text-decoration:none;">' + val + '</a>';
    }
"""

template_datatable_js = """
$(document).ready(function() {
    $('#plate-table').DataTable( {
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
            { },
            { },
        ]
    } );
} );
"""

# EOF
