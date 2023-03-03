
from rhombus.lib.utils import (
    cerr,
    get_dbhandler,
)

from messy.views import (
    AuthError,
    BaseViewer,
    form_submit_bar,
    HTTPFound,
    m_roles,
    not_roles,
    ParseFormError,
    render_to_response,
    Response,
)

from messy.ext.panelseq.lib import roles as r
from rhombus.lib import tags as t

from rhombus.lib.modals import (
    modal_delete,
    modal_error,
    popup,
)

import sqlalchemy.exc


class RegionViewer(BaseViewer):

    managing_roles = BaseViewer.managing_roles + [r.PANEL_MANAGE]
    modifying_roles = managing_roles + [r.PANEL_MODIFY]

    object_class = get_dbhandler().Region
    fetch_func = get_dbhandler().get_regions_by_ids
    edit_route = 'messy-panelseq.region-edit'
    view_route = 'messy-panelseq.region-view'
    attachment_route = 'messy-panelseq.region-attachment'

    form_fields = {

    }

    def index_helper(self):
        
        # get all regions
        regions = self.dbh.get_regions(groups=None)

        html, code = generate_region_table(regions, self.request)

        # tidy-up table

        html = t.div()[t.h2('Regions')].add(html)

        return render_to_response("messy:templates/datatablebase.mako", {
            'html': html,
            'code': code,
        }, request=self.request)


def generate_region_table(regions, request):

    table_body = t.tbody()

    not_guest = not request.user.has_roles(r.GUEST)
    can_manage = request.user.has_roles(* RegionViewer.modifying_roles)

    for reg in regions:
        table_body.add(
            t.tr(
                t.td(t.literal(f'<input type="checkbox" name="region-ids" value="{reg.id}" />')
                     if not_guest else ''),
                t.td(t.a(reg.code,
                         href=request.route_url('messy-panelseq.region-view', id=reg.id))),
                t.td(reg.chrom),
                t.td(reg.begin),
                t.td(reg.end),
                t.td(*[t.a(panel.code, href=request.route_url('messy-ngsmgr.panel-view', id=panel.id))
                       for panel in reg.panels.values()]
                     )
            )
        )

    region_table = t.table(id='region-table', class_='table table-condensed table-striped')[
        t.thead(
            t.tr(
                t.th('', style="width: 2em"),
                t.th('Code'),
                t.th('Chrom'),
                t.th('Begin'),
                t.th('End'),
                t.th('Related panel')
            )
        )
    ]

    region_table.add(table_body)

    if not_guest and can_manage:
        add_button = ('New region',
                      request.route_url('messy-panelseq.region-add'))

        bar = t.selection_bar('region-ids',
                              action=request.route_url('messy-panelseq.region-action'),
                              add=add_button)
        html, code = bar.render(region_table)

    else:
        html = t.div(region_table)
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