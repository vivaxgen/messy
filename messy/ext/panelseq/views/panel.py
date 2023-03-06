
from rhombus.lib.utils import cerr, get_dbhandler

from messy.views import (form_submit_bar, render_to_response, ParseFormError, Response,
                         m_roles, not_roles, AuthError, HTTPFound, behave_editor)
from messy.ext.ngsmgr.views.panel import PanelViewer
from messy.ext.panelseq.lib import roles as r
from rhombus.lib import tags as t
from rhombus.lib.modals import popup, modal_error, modal_delete

from messy.ext.ngsmgr.models.schema import PanelType
from messy.ext.panelseq.models.schema import Region, Variant
from messy.ext.panelseq.lib.inputparser import (
    parse_regions,
    parse_variants
)
import sqlalchemy.exc


class PanelSeqViewer(PanelViewer):
    """ This viewer class extend base PanelViewer (from messy-ngsmgr) to provide
        positions informations
    """

    def index_helper(self):
        return super().index_helper()

    def view_helper(self, render=True) -> tuple[str, str] | Response:

        panel_html, panel_jscode = super().view_helper(render=False)

        # if type is Analysis, add variant table
        if self.obj.type == PanelType.ANALYSIS.value:
            variant_html, variant_jscode = generate_variant_table(self)
            panel_html += variant_html
            panel_jscode += variant_jscode

        # if type is Assay or Analysis, add region table
        if self.obj.type in [PanelType.ASSAY.value, PanelType.ANALYSIS.value]:
            region_html, region_jscode = generate_region_table(self)
            panel_html += region_html
            panel_jscode += region_jscode

        if not render:
            return (panel_html, panel_jscode)
        return self.render_edit_form(panel_html, panel_jscode)

    @m_roles(r.PUBLIC, not_roles(r.GUEST))
    def regionaction(self):

        rq = self.request
        dbh = get_dbhandler()

        _method = rq.params.get('_method')
        panel_id = int(rq.params.get('panel_id'))
        panel = self.get_object(obj_id=panel_id)

        if not panel.can_modify(rq.identity):
            raise AuthError("Your user account does not have the role for modifying this Panel.")

        match _method:

            case 'add-panelregion':

                species_id = int(rq.params.get('species_id'))

                bed_info = rq.POST.get('bed_info').strip()
                if bed_info:
                    # parse to [(chrom, begin, end)]
                    for line in bed_info.split('\n'):
                        tokens = line.split()
                        chrom, begin, end = tokens[0], int(tokens[1]), int(tokens[2])
                        region = Region.get_or_create(
                            type=PanelType.ASSAY.value,
                            chrom=chrom, begin=begin, end=end,
                            species_id=species_id
                        )
                        panel.regions[region.id] = region

                return HTTPFound(location=rq.route_url(self.view_route, id=panel_id))

            case 'delete':

                panelregion_ids = [int(x) for x in rq.POST.getall('panelregion-ids')]
                regions = [panel.regions[pr_id] for pr_id in panelregion_ids]

                if len(regions) == 0:
                    return Response(modal_error(content="Please select region(s) to be removed"))

                return Response(
                    modal_delete(
                        title='Remove region(s)',
                        content=t.literal(
                            'You are going to remove the following region(s): '
                            '<ul>'
                            + ''.join(f'<li>{reg.chrom} {reg.begin}-{reg.end}</li>'
                                      for reg in regions)
                            + '</ul>'
                        ), request=rq,
                    ), request=rq
                )

            case 'delete/confirm':

                panelregion_ids = [int(x) for x in rq.POST.getall('panelregion-ids')]

                sess = dbh.session()
                count = 0
                for pr_id in panelregion_ids:
                    del panel.regions[pr_id]
                    count += 1

                sess.flush()
                rq.session.flash(
                    ('success', f'You have successfully remove {count} regions.')
                )

                return HTTPFound(location=rq.referer)

        raise ValueError(f'Unknown method name: {_method}')

    @m_roles(r.PUBLIC, not_roles(r.GUEST))
    def variantaction(self):

        rq = self.request
        dbh = get_dbhandler()

        _method = rq.params.get('_method')
        panel_id = int(rq.params.get('panel_id'))
        panel = self.get_object(obj_id=panel_id)

        if not panel.can_modify(rq.identity):
            raise AuthError("Your user account does not have the role for modifying this Panel.")

        match _method:

            case 'add-panelvariant':

                species_id = int(rq.params.get('species_id'))

                pos_info = rq.POST.get('pos_info').strip()
                if pos_info:
                    df = parse_variants(pos_info, header="CHROM\tPOS\n")
                    variants = dbh.Variant.from_dataframe(df, dbh=dbh)
                    for variant in variants:
                        panel.variants[variant.id] = variant

                return HTTPFound(location=rq.route_url(self.view_route, id=panel_id))

            case 'delete':

                panelvariant_ids = [int(x) for x in rq.POST.getall('panelvariant-ids')]
                variants = [panel.variants[pv_id] for pv_id in panelvariant_ids]

                if len(regions) == 0:
                    return Response(modal_error(content="Please select region(s) to be removed"))

                return Response(
                    modal_delete(
                        title='Remove region(s)',
                        content=t.literal(
                            'You are going to remove the following region(s): '
                            '<ul>'
                            + ''.join(f'<li>{reg.chrom} {reg.begin}-{reg.end}</li>'
                                      for reg in regions)
                            + '</ul>'
                        ), request=rq,
                    ), request=rq
                )

            case 'delete/confirm':

                panelregion_ids = [int(x) for x in rq.POST.getall('panelregion-ids')]

                sess = dbh.session()
                count = 0
                for pr_id in panelregion_ids:
                    del panel.regions[pr_id]
                    count += 1

                sess.flush()
                rq.session.flash(
                    ('success', f'You have successfully remove {count} regions.')
                )

                return HTTPFound(location=rq.referer)

        raise ValueError(f'Unknown method name: {_method}')


    def update_object_XXX(self, obj, d):
        pass

    def edit_form_XXX(self, obj=None, create=False, readonly=False, update_dict=None):
        pass


# the following functions (generate_region_table and generate_variant_table) are still
# templates and have not been tested properly

def generate_region_table(viewer, html_anchor=None):
    """ this appplies for ASSAY panels """

    panel = viewer.obj
    request = viewer.request
    dbh = viewer.dbh

    html = t.div(t.hr, t.h6('Regions'))

    table_body = t.tbody()

    for pr_id, region in panel.regions.items():
        table_body.add(
            t.tr(
                t.td(t.literal(f'<input type="checkbox" name="panelregion-ids" value="{pr_id}" />')),
                t.td(region.code),
                t.td(region.chrom),
                t.td(region.begin),
                t.td(region.end),
            )
        )

    region_table = t.table(class_='table table-condensed table-striped')[
        t.thead(
            t.tr(
                t.th('', style="width: 2em"),
                t.th('Region Code'),
                t.th('Chrom'),
                t.th('Begin'),
                t.th('End'),
            )
        )
    ]

    region_table += table_body

    if panel.can_modify(request.identity):

        bar = t.selection_bar(
            'panelregion-ids', action=request.route_url('messy-ngsmgr.panel-regionaction'),
            name='regionselection_bar', delete_label='Remove',
            others=t.button('Add region',
                            class_='btn btn-sm btn-success',
                            id='add-panelregion',
                            name='_method',
                            value='add_panelregion',
                            type='button'),
            hiddens=[('panel_id', panel.id), ]
        )
        region_html, region_jscode = bar.render(region_table)

        # prepare popup for adding regions

        popup_content = t.div(class_='form-group form-inline')[
            t.div('BED File', t.literal('<input type="file" name="file_content">')),
            t.input_select_ek('species_id', 'Species',
                              value=panel.species_id,
                              parent_ek=dbh.get_ekey('@SPECIES'),
                              offset=2, size=3),
            t.input_textarea(name='bed_info', label='BED Information',
                             info='Format: CHROM&lt;TAB&gt;BEGIN&lt;TAB&gt;END'),
        ]
        submit_button = t.submit_bar('Add region', 'add-panelregion')

        add_panelregion_form = t.form(name='add-panelregion-form', method=t.POST,
                                      action=request.route_url('messy-ngsmgr.panel-regionaction'))[
            popup_content,
            t.input_hidden(name='panel_id', value=panel.id),
            submit_button
        ]

        region_table = t.div(
            t.div(
                popup('Add region', add_panelregion_form, request=request),
                id='add-panelregion-modal', class_='modal fade', tabindex='-1', role='dialog'
            ),
            region_html
        )

        region_jscode += "; $('#add-panelregion').click( function(e) {$('#add-panelregion-modal').modal('show');});"

        return html.add(region_table), region_jscode

    html = t.div(region_table)
    code = ''

    return html, code


def generate_variant_table(viewer, html_anchor=None):
    """ this appplies for ASSAY panels """

    panel = viewer.obj
    request = viewer.request
    dbh = viewer.dbh

    html = t.div(t.hr, t.h6('Variants'))

    table_body = t.tbody()

    for pv_id, variant in panel.variants.items():
        table_body.add(
            t.tr(
                t.td(t.literal(f'<input type="checkbox" name="panelvariant-ids" value="{variant.id}" />')),
                t.td(variant.code),
                t.td(variant.chrom),
                t.td(variant.position),
                t.td(variant.gene),
            )
        )

    variant_table = t.table(class_='table table-condensed table-striped')[
        t.thead(
            t.tr(
                t.th('', style="width: 2em"),
                t.th('Variant Code'),
                t.th('Chrom'),
                t.th('Position'),
                t.th('Gene'),
            )
        )
    ]

    variant_table += table_body

    if panel.can_modify(request.identity):

        bar = t.selection_bar(
            'panelvariant-ids', action=request.route_url('messy-ngsmgr.panel-variantaction'),
            name='variantselection_bar', delete_label='Remove',
            others=t.button('Add variant',
                            class_='btn btn-sm btn-success',
                            id='add-panelvariant',
                            name='_method',
                            value='add_panelvariant',
                            type='button'),
            hiddens=[('panel_id', panel.id), ]
        )
        variant_html, variant_jscode = bar.render(variant_table)

        # prepare popup for adding variants

        popup_content = t.div(class_='form-group form-inline')[
            t.div('Pos File', t.literal('<input type="file" name="file_content">')),
            t.input_select_ek('species_id', 'Species',
                              value=panel.species_id,
                              parent_ek=dbh.get_ekey('@SPECIES'),
                              offset=2, size=3),
            t.input_textarea(name='pos_info', label='Pos Info',
                             info='Format: CHROM&lt;TAB&gt;POSITION&lt;TAB&gt;'),
        ]
        submit_button = t.submit_bar('Add variant', 'add-panelvariant')

        add_panelvariant_form = t.form(name='add-panelvariant-form', method=t.POST,
                                       action=request.route_url('messy-ngsmgr.panel-variantaction'))[
            popup_content,
            t.input_hidden(name='panel_id', value=panel.id),
            submit_button
        ]

        variant_table = t.div(
            t.div(
                popup('Add variant', add_panelvariant_form, request=request),
                id='add-panelvariant-modal', class_='modal fade', tabindex='-1', role='dialog'
            ),
            variant_html
        )

        variant_jscode += "; $('#add-panelvariant').click( function(e) {$('#add-panelvariant-modal').modal('show');});"
        variant_jscode += behave_editor('pos_info', soft_tabs=False)

        return html.add(variant_table), variant_jscode

    html = t.div(variant_table)
    code = ''

    return html, code

# EOF
