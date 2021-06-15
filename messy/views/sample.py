
from messy.views import *
import dateutil


class SampleViewer(BaseViewer):

    managing_roles = BaseViewer.managing_roles + [ SAMPLE_MANAGE ]
    modifying_roles = managing_roles + [ SAMPLE_MODIFY ]

    object_class = get_dbhandler().Sample
    fetch_func = get_dbhandler().get_samples_by_ids
    edit_route = 'messy.sample-edit'
    view_route = 'messy.sample-view'

    form_fields = {
        'collection_id': ('messy-sample-collection_id', ),
        'code': ('messy-sample-code', ),
        'lab_code': ('messy-sample-lab_code', ),
        'category_id': ('messy-sample-category_id', ),
        'sequence_name': ('messy-sample-sequence_name', ),
        'location': ('messy-sample-location', ),
        'location_info': ('messy-sample-location_info', ),
        'collection_date': ('messy-sample-collection_date', dateutil.parser.parse),
        'received_date': ('messy-sample-received_date', dateutil.parser.parse),
        'specimen_type_id': ('messy-sample-specimen_type_id', ),
        'passage_id': ('messy-sample-passage_id', ),
        'species_id': ('messy-sample-species_id', ),
        'host_id': ('messy-sample-host_id', ),
        'host_info': ('messy-sample-host_info', ),
        'host_gender': ('messy-sample-host_gender', ),
        'host_age': ('messy-sample-host_age', float),
        'host_status_id': ('messy-sample-host_status_id', ),
        'host_severity': ('messy-sample-host_severity', int),
        'host_dob': ('messy-sample-host_dob', dateutil.parser.parse),
        'host_nik': ('messy-sample-host_nik', ),
        'host_nar': ('messy-sample-host_nar', ),
        'host_occupation_id': ('messy-sample-host_occupation_id', ),
        'originating_institution_id': ('messy-sample-originating_institution_id', ),
        'originating_code': ('messy-sample-originating_code', ),
        'sampling_institution_id': ('messy-sample-sampling_institution_id', ),
        'sampling_code': ('messy-sample-sampling_code', ),
    }

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
            if obj.id:
                # check whether users is in sample collection group
                group = obj.collection.group
                if not self.request.user.in_group( group ):
                    raise RuntimeError('User not in collection group!')

        except RuntimeError as err:
            raise


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

        ff = self.form_fields

        eform = form( name='messy-sample', method=POST)[
            self.hidden_fields(obj),
            fieldset(
                input_select('messy-sample-collection_id', 'Collection', value=obj.collection_id,
                    offset=2, size=2,
                    options = [ (c.id, c.code) for c in dbh.get_collections(
                            groups = None if req.user.has_roles( SYSADM, DATAADM ) else req.user.groups
                        ) ],
                    static=readonly),
                input_text(ff['code'][0], 'Code', value=obj.code,
                    offset=2, static=readonly, update_dict=update_dict),
                input_text(ff['lab_code'][0], 'Lab Code', value=obj.lab_code,
                    offset=2, static=readonly, update_dict=update_dict),
                input_text(ff['received_date'][0], 'Received Date', value=obj.received_date,
                    offset=2, static=readonly, update_dict=update_dict),
                input_select_ek(ff['category_id'][0], 'Category',
                    value = obj.category_id, offset=2, size=5, static=readonly,
                    parent_ek = dbh.get_ekey('@CATEGORY')),

                input_text(ff['location'][0], 'Location', value=obj.location,
                    offset=2, static=readonly, update_dict=update_dict),
                input_text(ff['location_info'][0], 'Additional location', value=obj.location_info,
                    offset=2, static=readonly, update_dict=update_dict),
                input_text(ff['collection_date'][0], 'Collection date', value=obj.collection_date,
                    offset=2, static=readonly, update_dict=update_dict),
                input_text(ff['sequence_name'][0], 'Sequence name', value=obj.sequence_name,
                    offset=2, static=readonly, update_dict=update_dict),

                input_text(ff['host_age'][0], 'Host Age', value=obj.host_age,
                    offset=2, static=readonly,  update_dict=update_dict),
                input_select_ek(ff['host_status_id'][0], 'Host Status',
                    value = obj.host_status_id, offset=2, size=5, static=readonly,
                    parent_ek = dbh.get_ekey('@HOST_STATUS')),
                input_text(ff['host_severity'][0], 'Host Severity', value=obj.host_severity,
                    offset=2, static=readonly, update_dict=update_dict),
                input_select_ek(ff['host_occupation_id'][0], 'Host Occupation',
                    value = obj.host_occupation_id, offset=2, size=5, static=readonly,
                    parent_ek = dbh.get_ekey('@HOST_OCCUPATION')),
                input_text(ff['host_dob'][0], 'Host Date of Birth', value=obj.host_dob,
                    offset=2, static=readonly, update_dict=update_dict),
                input_text(ff['host_nik'][0], 'Host NIK', value=obj.host_nik,
                    offset=2, static=readonly, update_dict=update_dict),
                input_text(ff['host_nar'][0], 'Host NAR Number', value=obj.host_nar,
                    offset=2, static=readonly, update_dict=update_dict),
                input_select_ek(ff['passage_id'][0], 'Passage',
                    value = obj.passage_id, offset=2, size=5, static=readonly,
                    parent_ek = dbh.get_ekey('@PASSAGE')),

                input_select(ff['originating_institution_id'][0], 'Originating Institution',
                    value = orig_inst.id if orig_inst else None, offset=2, size=5, static=readonly,
                    options = [ (orig_inst.id, f'{orig_inst.code} | {orig_inst.name}') ] if orig_inst else [],
                    update_dict=update_dict ),
                input_text(ff['originating_code'][0], 'Originating Code', value=obj.originating_code,
                    offset=2, static=readonly, update_dict=update_dict),
                input_select(ff['sampling_institution_id'][0], 'Sampling Institution',
                    value = samp_inst.id if samp_inst else None, offset=2, size=5, static=readonly,
                    options = [ (samp_inst.id, f'{samp_inst.code} | {samp_inst.name}')] if samp_inst else [],
                    update_dict=update_dict ),
                input_text(ff['sampling_code'][0], 'Sampling Code', value=obj.sampling_code,
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
                td( f'{sample.host_age:4.1f}' ),
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
                th('Age'),
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