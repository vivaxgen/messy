
from messy.views import (BaseViewer, r, get_dbhandler, m_roles, ParseFormError, form_submit_bar,
                         render_to_response, form_submit_bar, select2_lookup, error_page,
                         Response, modal_delete, modal_error, Response, HTTPFound)
import rhombus.lib.tags_b46 as t
import sqlalchemy.exc
import dateutil


class SampleViewer(BaseViewer):

    managing_roles = BaseViewer.managing_roles + [r.SAMPLE_MANAGE]
    modifying_roles = managing_roles + [r.SAMPLE_MODIFY]

    object_class = get_dbhandler().Sample
    fetch_func = get_dbhandler().get_samples_by_ids
    edit_route = 'messy.sample-edit'
    view_route = 'messy.sample-view'
    attachment_route = 'messy.sample-attachment'

    form_fields = {
        'collection_id': ('messy-sample-collection_id', ),
        'code*': ('messy-sample-code', ),
        'acc_code': ('messy-sample-acc_code', ),
        'category_id': ('messy-sample-category_id', ),
        'sequence_name': ('messy-sample-sequence_name', ),
        'location': ('messy-sample-location', ),
        'location_info': ('messy-sample-location_info', ),
        'collection_date': ('messy-sample-collection_date', dateutil.parser.parse),
        'received_date': ('messy-sample-received_date', dateutil.parser.parse),
        'specimen_type_id': ('messy-sample-specimen_type_id', ),
        'passage_id': ('messy-sample-passage_id', ),
        'ct_method_id': ('messy-sample-ct_method_id', ),
        'ct_value1': ('messy-sample-ct_value1', float),
        'ct_value2': ('messy-sample-ct_value2', float),
        'species_id': ('messy-sample-species_id', ),
        'host_id': ('messy-sample-host_id', ),
        'host_info': ('messy-sample-host_info', ),
        'host_gender': ('messy-sample-host_gender', ),
        'host_age?': ('messy-sample-host_age', float),
        'host_occupation_id': ('messy-sample-host_occupation_id', ),
        'host_status_id': ('messy-sample-host_status_id', ),
        'host_severity': ('messy-sample-host_severity', int),
        'viral_load': ('messy-sample-viral_load', float),
        'treatment': ('messy-sample-treatment', ),
        'last_vaccinated_date?': ('messy-sample-last_vaccinated_date', dateutil.parser.parse),
        'last_vaccinated_info': ('messy-sample-last_vaccinated_info', ),
        'outbreak': ('messy-sample-outbreak', ),
        'host_dob?': ('messy-sample-host_dob', dateutil.parser.parse),
        'host_nik': ('messy-sample-host_nik', ),
        'host_nar': ('messy-sample-host_nar', ),
        'originating_institution_id*': ('messy-sample-originating_institution_id', ),
        'originating_code': ('messy-sample-originating_code', ),
        'sampling_institution_id': ('messy-sample-sampling_institution_id', ),
        'sampling_code': ('messy-sample-sampling_code', ),
        'attachment': ('messy-sample-attachment'),
    }

    @m_roles(r.PUBLIC)
    def index(self):

        samples = self.dbh.get_samples(groups=None, user=self.request.user, fetch=False)

        html, code = generate_sample_table(samples, self.request)

        html = t.div()[t.h2('Samples'), html]

        return render_to_response("messy:templates/generic_page.mako",
                                  {
                                      'html': html,
                                      'code': code,
                                  },
                                  request=self.request)

    def update_object(self, obj, d):
        rq = self.request
        dbh = self.dbh

        try:
            # fill default value to all empty variable
            if 'sampling_institution_id' not in d:
                d['sampling_institution_id'] = d['originating_institution_id']
                d['sampling_code'] = d['originating_code']

            if obj.any_modified(d, {'acc_code', 'location', 'collection_date', 'species', 'host'}):
                update_sequence_name = True
            else:
                update_sequence_name = False

            obj.update(d)
            # check if obj is already registered
            if obj.id is None:
                # check whether users is in sample collection group
                if not rq.user.has_roles(r.SYSADM, r.DATAADM, r.SAMPLE_MANAGE):
                    collection = dbh.get_collections_by_ids(obj.collection_id, rq.user.groups)
                    if len(collection) == 0:
                        raise ParseFormError('Either the user is not in a member of collection group '
                                             'or the collection does not exist.',
                                             self.form_fields['collection_id'][0])
                dbh.session().add(obj)

            # fill other values based on existing data
            if update_sequence_name:
                obj.update_sequence_name()

            dbh.session().flush([obj])

        except sqlalchemy.exc.IntegrityError as err:
            dbh.session().rollback()
            detail = err.args[0]
            eform, jscode = self.edit_form(obj)
            if 'UNIQUE' in detail or 'UniqueViolation' in detail:
                if 'samples.code' in detail or 'uq_samples_code' in detail:
                    raise ParseFormError(f"The sample code: {d['code']} is already being used.",
                                         self.ffn('code*')) from err
                if 'samples.acc_code' in detail or 'uq_samples_acc_code' in detail:
                    raise ParseFormError(f"The accession code: {d['acc_code']} is already being used.",
                                         self.ffn('acc_code')) from err
                if 'samples.sequence_name' in detail or 'uq_samples_sequence_name' in detail:
                    raise ParseFormError(f"The sequence name: {d['sequence_name']} is already being used.",
                                         self.ffn('sequence_name')) from err

            raise RuntimeError('unhandled error updating Sample object')

        except RuntimeError:
            raise

    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        obj = obj or self.obj
        dbh = self.dbh
        req = self.request
        ff = self.ffn

        orig_inst = obj.originating_institution
        samp_inst = obj.sampling_institution
        if update_dict:
            if ff('originating_institution_id*') in update_dict:
                orig_inst = dbh.get_institutions_by_ids(
                    [update_dict[ff('originating_institution_id*')]], None)[0]
            if ff('sampling_institution_id') in update_dict:
                samp_inst = dbh.get_institutions_by_ids(
                    [update_dict[ff('sampling_institution_id')]], None)[0]

        eform = t.form(name='messy-sample', method=t.POST, enctype=t.FORM_MULTIPART, readonly=readonly,
                       update_dict=update_dict)[
            self.hidden_fields(obj),
            t.fieldset(
                t.hr,

                t.inline_inputs(
                    t.input_select('messy-sample-collection_id', 'Collection', value=obj.collection_id,
                                   offset=2, size=2,
                                   options=[(c.id, c.code) for c in dbh.get_collections(
                                       groups=None if req.user.has_roles(r.SYSADM, r.DATAADM)
                                       else req.user.groups)]),
                    t.input_text(ff('code*'), '* Code', value=obj.code, offset=1, size=3,
                                 popover='Code|Unique code to be used in lab'),
                    t.input_text(ff('acc_code'), 'Acc Code', value=obj.acc_code, offset=1, size=3,
                                 popover='Accession Code|Unique code to be used in sequence name'),
                ),

                t.inline_inputs(
                    t.input_text(ff('received_date'), '* Received Date', value=obj.received_date,
                                 offset=2, size=2, placeholder='YYYY/MM/DD'),
                    t.input_select_ek(ff('category_id'), 'Category',
                                      value=obj.category_id or dbh.get_ekey('R-RA').id,
                                      offset=1, size=3, parent_ek=dbh.get_ekey('@CATEGORY')),
                    t.input_select_ek(ff('species_id'), 'Species',
                                      value=obj.species_id or dbh.get_ekey('betacoronavirus-ncov19').id,
                                      offset=1, size=3, parent_ek=dbh.get_ekey('@SPECIES')),
                ),

                t.inline_inputs(
                    t.input_text(ff('collection_date'), '* Collection date', value=obj.collection_date,
                                 offset=2, size=2, placeholder='YYYY/MM/DD'),
                    t.input_text(ff('location'), '* Location', value=obj.location, offset=1, size=7,
                                 placeholder='Asia/Indonesia/'),
                ),

                t.input_text(ff('location_info'), 'Additional location', value=obj.location_info,
                             offset=2, size=10, placeholder='Any location info'),

                t.inline_inputs(
                    t.input_select(ff('originating_institution_id*'), '* Originating Institution',
                                   value=orig_inst.id if orig_inst else None, offset=2, size=5,
                                   options=[(orig_inst.id, f'{orig_inst.code} | {orig_inst.name}')] if orig_inst else [],
                                   popover='Originating institution|Institution that sent the sample'),
                    t.input_text(ff('originating_code'), 'Originating Code', value=obj.originating_code,
                                 offset=2, size=3),
                ),

                t.hr,

                t.input_text(ff('sequence_name'), 'Sequence name', value=obj.sequence_name, readonly=True,
                             offset=2, size=10, placeholder='Sequence name will be automatically-generated'),

                t.inline_inputs(
                    t.input_select_ek(ff('specimen_type_id'), 'Specimen type',
                                      value=obj.specimen_type_id or dbh.get_ekey('np+op').id,
                                      offset=2, size=2, parent_ek=dbh.get_ekey('@SPECIMEN_TYPE')),
                    t.input_text(ff('ct_value1'), 'Ct val 1&2',
                                 value=-1 if obj.ct_value1 is None else obj.ct_value1, offset=1, size=1,
                                 popover='Ct value target 1 & target 2|Ct value for target 1 (usually RdRp/ORF1) '
                                         'and target 2 (usually E)'),
                    t.input_text(ff('ct_value2'), None,
                                 value=-1 if obj.ct_value2 is None else obj.ct_value2, offset=1, size=1),
                    t.input_select_ek(ff('ct_method_id'), None,
                                      value=obj.ct_method_id or dbh.get_ekey('rtpcr').id,
                                      offset=1, size=2, parent_ek=dbh.get_ekey('@CT_METHOD')),
                    t.input_select_ek(ff('passage_id'), 'Passage',
                                      value=obj.passage_id or dbh.get_ekey('original').id,
                                      offset=1, size=2, parent_ek=dbh.get_ekey('@PASSAGE')),
                ),

                t.inline_inputs(

                    t.input_select_ek(ff('host_id'), 'Host',
                                      value=obj.host_id or dbh.get_ek_id('human', '@SPECIES'),
                                      offset=2, size=2, parent_ek=dbh.get_ekey('@SPECIES')),
                    t.input_text(ff('host_info'), 'Host Info', value=obj.host_info, offset=2, size=6),
                ),

                t.inline_inputs(
                    t.input_text(ff('host_age?'), 'Host Age', value=obj.host_age, offset=2, size=1),
                    t.input_text(ff('host_gender'), 'Gender', value=obj.host_gender, offset=1, size=1,
                                 placeholder='M/F/U'),
                    t.input_select_ek(ff('host_occupation_id'), 'Occupation',
                                      value=obj.host_occupation_id or dbh.get_ekey('other').id,
                                      offset=1, size=4, parent_ek=dbh.get_ekey('@HOST_OCCUPATION')),
                    t.input_text(ff('viral_load'), 'Viral Load',
                                 value=-1 if obj.viral_load is None else obj.viral_load, offset=1, size=1),
                ),

                t.inline_inputs(
                    t.input_select_ek(ff('host_status_id'), 'Host Status',
                                      value=obj.host_status_id or dbh.get_ekey('unknown').id,
                                      offset=2, size=2, parent_ek=dbh.get_ekey('@HOST_STATUS')),
                    t.input_text(ff('host_severity'), 'Severity',
                                 value=-1 if obj.host_severity is None else obj.host_severity,
                                 offset=1, size=1),
                    t.input_text(ff('treatment'), 'Treatment', value=obj.treatment,
                                 offset=1, size=5),
                ),

                t.inline_inputs(
                    t.input_text(ff('last_vaccinated_date?'), 'Last Vaccination Date', value=obj.last_vaccinated_date,
                                 offset=2, size=2),
                    t.input_text(ff('last_vaccinated_info'), 'Last Vaccination Info', value=obj.last_vaccinated_info,
                                 offset=2, size=6),
                ),

                t.input_text(ff('outbreak'), 'Outbreak info', value=obj.outbreak,
                             offset=2, size=10),

                t.inline_inputs(
                    t.input_select(ff('sampling_institution_id'), 'Sampling Institution',
                                   value=samp_inst.id if samp_inst else None, offset=2, size=5,
                                   options=[(samp_inst.id, f'{samp_inst.code} | {samp_inst.name}')] if samp_inst else [],
                                   popover='Sampling institution|Institution that collected the sample, leave empty for '
                                           'the same as originating institution'),
                    t.input_text(ff('sampling_code'), 'Sampling Code', value=obj.sampling_code,
                                 offset=2, size=3),
                ),

                t.inline_inputs(
                    t.input_text(ff('host_dob?'), 'Host Date of Birth', value=obj.host_dob, offset=2, size=2),
                    t.input_text(ff('host_nik'), 'NIK', value=obj.host_nik, offset=1, size=3),
                    t.input_text(ff('host_nar'), 'NAR', value=obj.host_nar, offset=1, size=3),
                ),

                t.input_file_attachment(ff('attachment'), 'Attachment', value=obj.attachment, offset=2, size=4)
                .set_view_link(self.attachment_link(obj, 'attachment')),

                name='messy-sample-fieldset'
            ),
            t.fieldset(
                form_submit_bar(create) if not readonly else t.div(),
                name='footer'
            ),
        ]

        jscode = """$(function () {$('[data-toggle="popover"]').popover()});"""

        if not readonly:
            jscode += select2_lookup(tag='messy-sample-originating_institution_id', minlen=3,
                                     placeholder="Type an institution name",
                                     parenttag="messy-sample-fieldset", usetag=False,
                                     url=self.request.route_url('messy.institution-lookup')) +\
                select2_lookup(tag='messy-sample-sampling_institution_id', minlen=3,
                               placeholder="Type an institution name",
                               parenttag="messy-sample-fieldset", usetag=False,
                               url=self.request.route_url('messy.institution-lookup'))

        return t.div()[t.h2('Sample'), eform], jscode

    def lookup_helper(self):
        q = self.request.params.get('q')
        if not q:
            return error_page(self.request, "q not provided")
        q = '%' + q.lower() + '%'

        samples = get_dbhandler().get_samples_by_codes(q, groups=None, user=self.request.user)
        result = [
            {'id': s.id, 'text': f'{s.code} | {s.collection.code}'} for s in samples
        ]

        return result

    def action_post(self):

        request = self.request
        method = request.params.get('_method')
        dbh = get_dbhandler()

        if method == 'delete':

            sample_ids = [int(x) for x in request.params.getall('sample-ids')]
            samples = dbh.get_samples_by_ids(sample_ids, groups=None, user=request.user)

            if len(samples) == 0:
                return Response(modal_error)

            return Response(
                modal_delete(
                    title='Removing sample(s)',
                    content=t.literal(
                        'You are going to remove the following sample(s): '
                        '<ul>'
                        + ''.join('<li>%s</li>' % s.code for s in samples)
                        + '</ul>'
                    ), request=request,

                ), request=request
            )

        elif method == 'delete/confirm':

            sample_ids = [int(x) for x in request.params.getall('sample-ids')]
            samples = dbh.get_samples_by_ids(sample_ids, groups=None, user=request.user)

            sess = dbh.session()
            count = 0
            for s in samples:
                sess.delete(s)
                count += 1

            sess.flush()
            request.session.flash(
                ('success', 'You have successfully removed %d sample(s).' % count)
            )

            return HTTPFound(location=request.referer)

        return error_page(request, 'action post not implemented')

    def get_object(self):
        """obj_id either integer or 'code=?'"""
        rq = self.request
        dbh = self.dbh
        obj_id = rq.matchdict.get('id')
        if obj_id.startswith('code='):
            func = dbh.get_samples_by_codes
            obj_id = obj_id.removeprefix('code=')
        else:
            func = dbh.get_samples_by_ids
            obj_id = int(obj_id)
        res = func([obj_id],
                   groups=None if rq.user.has_roles(* self.viewing_roles)
                   else rq.user.groups,
                   user=rq.user)
        if len(res) == 0:
            raise RuntimeError('Cannot find object! Please check object id!')

        self.obj = res[0]
        return self.obj


def generate_sample_table(samples, request):

    table_body = t.tbody()

    not_guest = not request.user.has_roles(r.GUEST)

    for sample in samples:
        table_body.add(
            t.tr(
                t.td(t.literal('<input type="checkbox" name="sample-ids" value="%d" />' % sample.id)
                     if not_guest else ''),
                t.td(t.a(sample.code, href=request.route_url('messy.sample-view', id=sample.id))),
                t.td(sample.collection.code),
                t.td(sample.category),
                t.td(sample.acc_code),
                t.td(sample.sequence_name),
                t.td(sample.location),
                t.td(sample.collection_date),
                t.td(f'{sample.host_age:4.1f}'),
            )
        )

    sample_table = t.table(class_='table table-condensed table-striped')[
        t.thead(
            t.tr(
                t.th('', style="width: 2em"),
                t.th('Code'),
                t.th('Collection'),
                t.th('Category'),
                t.th('Acc Code'),
                t.th('Name'),
                t.th('Location'),
                t.th('Collection Date'),
                t.th('Age'),
            )
        )
    ]

    sample_table.add(table_body)

    if not_guest:
        add_button = ('New sample',
                      request.route_url('messy.sample-add'))

        bar = t.selection_bar('sample-ids', action=request.route_url('messy.sample-action'),
                              add=add_button)
        html, code = bar.render(sample_table)

    else:
        html = t.div(sample_table)
        code = ''

    return html, code

# EOF
