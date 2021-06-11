
from messy.views import *


class SampleViewer(BaseViewer):

    managing_roles = BaseViewer.managing_roles + [ SAMPLE_MANAGE ]
    modifying_roles = managing_roles + [ SAMPLE_MODIFY ]

    object_class = get_dbhandler().Sample
    fetch_func = get_dbhandler().get_samples_by_ids
    edit_route = 'messy.sample-edit'
    view_route = 'messy.sample-view'


    @m_roles( PUBLIC )
    def index(self):

        samples = self.dbh.get_samples(groups=None, fetch=False)

        html, code = generate_sample_table(samples, self.request)

        html = div()[ h2('Samples'), html ]

        return render_to_response("messy:templates/generic_page.mako",
            { 'html': html
            },
            request = self.request)


    def update_object(self, obj, d):
        rq = self.request
        dbh = self.dbh

        try:
            obj.update(d)
            # check if obj is already registered
            raise
            if obj.id:
                # check whether users is in sample collection group
                group = obj.collection.group
                if not self.request.user.in_group( group ):
                    raise RuntimeError('User not in collection group!')

        except RuntimeError as err:
            raise


    def parse_form(self, f, d=None):
        d = super().parse_form(f, d,
            [
                ('collection_id', 'messy-sample-collection_id'),
                ('code', 'messy-sample-code'),
                ('lab_code', 'messy-sample-lab_code'),
                ('sequence_name', 'messy-sample-sequence_name'),
                ('location', 'messy-sample-location'),
                ('location_info', 'messy-sample-location_info'),
                ('collection_date', 'messy-sample-collection_date'),
                ('passage', 'messy-sample-passage'),
            ]
        )

        return d

    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        obj = obj or self.obj
        dbh = self.dbh
        req = self.request

        orig_inst = obj.originating_institution
        samp_inst = obj.sampling_institution
        if update_dict:
            orig_inst = dbh.get_institutions_by_ids(
                        [update_dict['messy-sample-originating_institution_id']], None)[0]
            samp_inst = dbh.get_institutions_by_ids(
                        [update_dict['messy-sample-sampling_institution_id']], None)[0]

        eform = form( name='messy-sample', method=POST)[
            self.hidden_fields(obj),
            fieldset(
                input_select('messy-sample-collection_id', 'Collection', value=obj.collection_id,
                    offset=2, size=2,
                    options = [ (c.id, c.code) for c in dbh.get_collections(
                            groups = None if req.user.has_roles( SYSADM, DATAADM ) else req.user.groups
                        ) ],
                    static=readonly),
                input_text('messy-sample-code', 'Code', value=obj.code,
                    offset=2, static=readonly, update_dict=update_dict),
                input_text('messy-sample-lab_code', 'Lab Code', value=obj.lab_code,
                    offset=2, static=readonly, update_dict=update_dict),
                input_text('messy-sample-sequence_name', 'Sequence name', value=obj.sequence_name,
                    offset=2, static=readonly, update_dict=update_dict),
                input_text('messy-sample-location', 'Location', value=obj.location,
                    offset=2, static=readonly, update_dict=update_dict),
                input_text('messy-sample-location_info', 'Additional location', value=obj.location_info,
                    offset=2, static=readonly, update_dict=update_dict),
                input_text('messy-sample-collection_date', 'Collection date', value=obj.collection_date,
                    offset=2, static=readonly, update_dict=update_dict),
                input_select('messy-sample-originating_institution_id', 'Originating Institution',
                    value = orig_inst.id if orig_inst else None, offset=2, size=5, static=readonly,
                    options = [ (orig_inst.id, f'{orig_inst.code} | {orig_inst.name}') ] if orig_inst else [],
                    update_dict=update_dict ),
                input_text('messy-sample-originating_code', 'Originating Code', value=obj.originating_code,
                    offset=2, static=readonly, update_dict=update_dict),
                input_select('messy-sample-sampling_institution_id', 'Sampling Institution',
                    value = samp_inst.id if samp_inst else None, offset=2, size=5, static=readonly,
                    options = [ (samp_inst.id, f'{samp_inst.code} | {samp_inst.name}')] if samp_inst else [],
                    update_dict=update_dict ),
                input_text('messy-sample-sampling_code', 'Sampling Code', value=obj.sampling_code,
                    offset=2, static=readonly, update_dict=update_dict),
                name='messy-sample-fieldset'
            ),
            fieldset(
                form_submit_bar(create) if not readonly else div(),
                name = 'footer'
            ),
        ]

        if not readonly:
            jscode = select2_lookup(tag='messy-sample-originating_institution_id', minlen=3,
                            placeholder="Type an institution name",
                            parenttag="messy-sample-fieldset", usetag=False,
                            url=self.request.route_url('messy.institution-lookup')) +\
                        select2_lookup(tag='messy-sample-sampling_institution_id', minlen=3,
                            placeholder="Type an institution name",
                            parenttag="messy-sample-fieldset", usetag=False,
                            url=self.request.route_url('messy.institution-lookup'))            
        else:
            jscode = ''

        return div()[ h2('Sample'), eform], jscode


def generate_sample_table(samples, request):

    table_body = tbody()

    not_guest = not request.user.has_roles( GUEST )

    for sample in samples:
        table_body.add(
            tr(
                td(literal('<input type="checkbox" name="sample-ids" value="%d" />' % sample.id)
                    if not_guest else ''),
                td( a(sample.code, href=request.route_url('messy.sample-view', id=sample.id)) ),
                td( sample.collection.code),
                td( sample.category ),
                td( sample.lab_code ),
                td( sample.sequence_name),
                td( sample.location),
                td( sample.collection_date),
            )
        )

    sample_table = table(class_='table table-condensed table-striped')[
        thead(
            tr(
                th('', style="width: 2em"),
                th('Code'),
                th('Collection'),
                th('Category'),
                th('Lab Code'),
                th('Name'),
                th('Location'),
                th('Collection Date'),
            )
        )
    ]

    sample_table.add( table_body )

    if not_guest:
        add_button = ( 'New sample',
                        request.route_url('messy.sample-add')
        )

        bar = selection_bar('sample-ids', action=request.route_url('messy.sample-action'),
                    add = add_button)
        html, code = bar.render(sample_table)

    else:
        html = div(sample_table)
        code = ''

    return html, code