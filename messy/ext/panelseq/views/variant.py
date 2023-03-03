
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


class VariantViewer(BaseViewer):

    managing_roles = BaseViewer.managing_roles + [r.PANEL_MANAGE]
    modifying_roles = managing_roles + [r.PANEL_MODIFY]

    object_class = get_dbhandler().Variant
    fetch_func = get_dbhandler().get_variants_by_ids
    edit_route = 'messy-panelseq.variant-edit'
    view_route = 'messy-panelseq.variant-view'
    attachment_route = 'messy-panelseq.variant-attachment'

    form_fields = {

    }

    def index_helper(self):
        
        # get all variants
        variants = self.dbh.get_variants(groups=None)

        html, code = generate_variant_table(variants, self.request)

        # tidy-up table

        html = t.div()[t.h2('Variants')].add(html)

        return render_to_response("messy:templates/datatablebase.mako", {
            'html': html,
            'code': code,
        }, request=self.request)


def generate_variant_table(variants, request):

    table_body = t.tbody()

    not_guest = not request.user.has_roles(r.GUEST)
    can_manage = request.user.has_roles(* VariantViewer.modifying_roles)

    for vr in variants:
        table_body.add(
            t.tr(
                t.td(t.literal(f'<input type="checkbox" name="variant-ids" value="{vr.id}" />')
                     if not_guest else ''),
                t.td(t.a(vr.code,
                         href=request.route_url('messy-panelseq.variant-view', id=vr.id))),
                t.td(vr.chrom),
                t.td(vr.position),
                t.td(vr.gene),
                t.td(),
            )
        )

    variant_table = t.table(id='variant-table', class_='table table-condensed table-striped')[
        t.thead(
            t.tr(
                t.th('', style="width: 2em"),
                t.th('Code'),
                t.th('Chrom'),
                t.th('Position'),
                t.th('Gene'),
                t.th('Related panel')
            )
        )
    ]

    variant_table.add(table_body)

    if not_guest and can_manage:
        add_button = ('New variant',
                      request.route_url('messy-panelseq.variant-add'))

        bar = t.selection_bar('variant-ids',
                              action=request.route_url('messy-panelseq.variant-action'),
                              add=add_button)
        html, code = bar.render(variant_table)

    else:
        html = t.div(variant_table)
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