
from rhombus.lib.utils import (
    cerr,
    get_dbhandler,
)

from messy.views import (
    AuthError,
    BaseViewer,
    behave_editor,
    form_submit_bar,
    HTTPFound,
    m_roles,
    not_roles,
    ParseFormError,
    render_to_response,
    Response,
)

from messy.ext.panelseq.lib import roles as r

from messy.ext.panelseq.lib.inputparser import parse_variants

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
        'code': ('messy-panelseq-variant-code', ),
        'chrom!': ('messy-panelseq-variant-chrom', ),
        'position!': ('messy-panelseq-variant-position', int),
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

    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        rq = self.request
        obj = obj or self.obj
        dbh = self.dbh

        ff = self.ffn
        eform = t.form(name='messy-panelseq-variant', method=t.POST, enctype=t.FORM_MULTIPART,
                       readonly=readonly, update_dict=update_dict)
        eform.add(
            self.hidden_fields(obj),
            t.fieldset(
                t.input_text(ff('code'), 'Code', value=obj.code, offset=2,
                             placeholder='Leave empty for automatic CHROM:POSITION code'),
                t.input_text(ff('chrom!'), 'Chromosome', value=obj.chrom,
                             offset=2),
                t.input_text(ff('position!'), 'Position', value=obj.position,
                             offset=2),
                name="messy-ngsmgr-variant-fieldset"
            ),

            t.fieldset(
                form_submit_bar(create) if not readonly else t.div(),
                name='footer'
            ),
        )

        return t.div()[t.h2('Variant'), eform], ''

    def action_post(self):

        rq = self.request
        dbh = self.dbh
        _method = rq.POST.get('_method')

        match _method:

            case 'add-variant':

                species_id = int(rq.params.get('species_id'))

                pos_info = rq.POST.get('pos_info')
                df = parse_variants(pos_info, header="CHROM\tPOS\n")
                variants = dbh.Variant.from_dataframe(df, dbh=dbh)
                for v in variants:
                    dbh.session().add(v)

                return HTTPFound(location=rq.referer)

            case 'delete':

                variant_ids = [int(x) for x in rq.POST.getall('variant-ids')]
                variants = dbh.get_variants_by_ids(variant_ids, groups=None, user=rq.user)

                if not any(variants):
                    return Response(modal_error(content="Please select variant(s) to be removed"))

                return Response(
                    modal_delete(
                        title='Removing Variant(s)',
                        content=t.literal(
                            'You are going to remove the following panel(s): '
                            '<ul>'
                            + ''.join(
                                f'<li>{v.code} | {v.chrom} | {v.position} | {print_related_panels(v)}'
                                for v in variants)
                            + '</ul>'
                            'Any variants associated with panel(s) cannot be removed. '
                            'Do you want to continue?'
                        ), request=rq,
                    ), request=rq
                )

            case 'delete/confirm':

                variant_ids = [int(x) for x in rq.POST.getall('variant-ids')]
                variants = dbh.get_variants_by_ids(variant_ids, groups=None, user=rq.user)

                sess = dbh.session()
                count = left = 0
                for variant in variants:
                    if not any(variant.panels) and variant.can_modify(rq.user):
                        sess.delete(variant)
                        count += 1
                    else:
                        left += 1

                sess.flush()
                rq.session.flash(
                    ('success',
                     f'You have removed {count} variant(s) sucessfully' +
                     (f', {left} variant(s) unsucessfully.' if left else '.'))
                )

                return HTTPFound(location=rq.referer)

        raise ValueError(f'Unknown method name: {_method}')


def print_related_panels(variant, request=None):

    if request:
        return t.span(*[t.a(panel.code,
                            href=request.route_url('messy-ngsmgr.panel-view', id=panel.id)
                            ) for panel in variant.panels.values()
                        ])
    else:
        return " | ".join(panel.code for panel in variant.panels.values())


def generate_variant_table(variants, request):

    dbh = get_dbhandler()

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
                t.td(print_related_panels(vr, request=request)),
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
        add_button = t.button('New variant',
                              class_='btn btn-sm btn-success',
                              id='add-variant',
                              name='_method',
                              value='add_variant',
                              type='button')

        bar = t.selection_bar('variant-ids',
                              action=request.route_url('messy-panelseq.variant-action'),
                              others=add_button)

        html, jscode = bar.render(variant_table)

        #prepare popup for adding variants

        popup_content = t.div(class_='form-group form-inline')[
            t.div('Pos File', t.literal('<input type="file" name="file_content">')),
            t.input_select_ek('species_id', 'Species',
                              value=None,
                              parent_ek=dbh.get_ekey('@SPECIES'),
                              offset=2, size=3),
            t.input_textarea(name='pos_info', label='Pos Info',
                             info='Format: CHROM&lt;TAB&gt;POSITION&lt;TAB&gt;'),
        ]
        submit_button = t.submit_bar('Add variant', 'add-variant')

        add_variant_form = t.form(name='add-variant-form', method=t.POST,
                                  action=request.route_url('messy-panelseq.variant-action'))[
            popup_content,
            submit_button
        ]

        html = t.div(
            t.div(
                popup('Add variant', add_variant_form, request=request),
                id='add-variant-modal', class_='modal fade', tabindex='-1', role='dialog'
            ),
            html
        )

        jscode += "; $('#add-variant').click( function(e) {$('#add-variant-modal').modal('show');});"
        jscode += behave_editor('pos_info', soft_tabs=False)

    else:
        html = t.div(variant_table)
        jscode = ''

    jscode += template_datatable_js
    return html, jscode


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