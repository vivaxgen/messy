
from messy.views import (BaseViewer, get_dbhandler, m_roles, ParseFormError, form_submit_bar,
                         render_to_response, form_submit_bar, select2_lookup, error_page,
                         Response, modal_delete, modal_error, Response, HTTPFound, AuthError,
                         validate_code)
import rhombus.lib.tags as t
from rhombus.lib.modals import popup
from rhombus.lib.exceptions import AuthError
from pyramid import response

from messy.ext.ngsmgr.lib import roles as r

from messy.lib.samplesheet_utils import generate_samplesheet
from messy.lib.converter import export_gisaid

import sqlalchemy.exc
import dateutil
import pandas as pd


class NGSRunViewer(BaseViewer):

    managing_roles = BaseViewer.managing_roles + [r.NGSRUN_MANAGE]
    modifying_roles = managing_roles + [r.NGSRUN_MODIFY]

    object_class = get_dbhandler().NGSRun
    fetch_func = get_dbhandler().get_ngsruns_by_ids
    edit_route = 'messy-ngsmgr.ngsrun-edit'
    view_route = 'messy-ngsmgr.ngsrun-view'
    attachment_route = 'messy-ngsmgr.ngsrun-attachment'

    form_fields = {
        'code*': ('messy-ngsmgr-ngsrun-code', validate_code),
        'serial*': ('messy-ngsmgr-ngsrun-serial', ),
        'date?': ('messy-ngsmgr-ngsrun-date', dateutil.parser.parse),
        'group_id': ('messy-ngsmgr-ngsrun-group_id', int),
        'ngs_provider_id*': ('messy-ngsmgr-ngsrun-ngs_provider_id', int),
        'ngs_kit_id': ('messy-ngsmgr-ngsrun-ngs_kit_id', ),
        'depthplots?': ('messy-ngsmgr-ngsrun-depthplots', ),  # lambda x: x.file.read() if x != b'' else None),
        'qcreport?': ('messy-ngsmgr-ngsrun-qcreport', ),
        'screenshot?': ('messy-ngsmgr-ngsrun-screenshot', ),
        'vcf?': ('messy-ngsmgr-ngsrun-vcf', ),
        'remark': ('messy-ngsmgr-ngsrun-remark', ),
    }

    @m_roles(r.PUBLIC)
    def index(self):

        group_id = int(self.request.params.get('group_id', 0))

        runs = self.dbh.get_ngsruns(groups=None, fetch=False).order_by(self.dbh.NGSRun.date.desc())

        html, code = generate_ngsrun_table(runs, self.request)
        html = t.div()[t.h2('Runs'), html]

        return render_to_response('messy:templates/datatablebase.mako', {
            'html': html,
            'code': code,
        }, request=self.request)

    def update_object(self, obj, d):
        rq = self.request
        dbh = self.dbh

        try:
            obj.update(d)
            if obj.id is None:
                dbh.session().add(obj)
            dbh.session().flush([obj])

        except sqlalchemy.exc.IntegrityError as err:
            dbh.session().rollback()
            detail = err.args[0]
            if 'UNIQUE' in detail or 'UniqueViolation' in detail:
                if 'ngsruns.code' in detail or 'uq_ngsruns_code' in detail:
                    raise ParseFormError(f'The run code: {d["code"]}  is '
                                         f'already being used. Please use other run code!',
                                         self.ffn('code*')) from err
                if 'ngsruns.serial' in detail or 'uq_ngsruns_serial' in detail:
                    raise ParseFormError(f'The run serial: {d["code"]}  is '
                                         f'already being used. Please use other run serial!',
                                         self.ffn('serial*')) from err

            raise RuntimeError(f'error updating object: {detail}')

        except RuntimeError:
            raise

    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        obj = obj or self.obj
        dbh = self.dbh
        rq = self.request
        ff = self.ffn

        # processing sequencing_provider_id
        prov_inst = obj.ngs_provider
        if update_dict:
            if (prov_inst_id := update_dict.get(ff('ngs_provider_id*'), 0)):
                prov_inst = dbh.get_institutions_by_ids(prov_inst_id, None)[0]

        eform = t.form(name='messy-run', method=t.POST, enctype=t.FORM_MULTIPART, readonly=readonly,
                       update_dict=update_dict)[
            self.hidden_fields(obj),
            t.fieldset(
                t.input_text(ff('code*'), 'Code', value=obj.code, offset=2),
                t.input_text(ff('serial*'), 'Serial', value=obj.serial, offset=2),
                t.input_text(ff('date?'), 'Running date', value=obj.date, offset=2, size=2, placeholder='YYYY/MM/DD'),
                t.input_select(ff('group_id'), 'Group', value=obj.group_id, offset=2, size=2,
                               options=[(g.id, g.name) for g in dbh.get_group(user_id=rq.user)]),
                t.input_select(ff('ngs_provider_id*'), 'NGS Provider',
                               value=prov_inst.id if prov_inst else '', offset=2, size=5,
                               options=[(prov_inst.id, f'{prov_inst.code} | {prov_inst.name}')] if prov_inst else []),
                t.input_select_ek(ff('ngs_kit_id'), 'NGS Kit',
                                  value=obj.ngs_kit_id, offset=2, size=5,
                                  parent_ek=dbh.get_ekey('@NGS_KIT')),

                t.input_file_attachment(ff('depthplots?'), 'Depth plots', value=obj.depthplots, offset=2, size=4)
                .set_view_link(self.attachment_link(obj, 'depthplots')),

                t.input_file_attachment(ff('qcreport?'), 'QC report', value=obj.qcreport, offset=2, size=4)
                .set_view_link(self.attachment_link(obj, 'qcreport')),

                t.input_file_attachment(ff('screenshot?'), 'Screenshot', value=obj.screenshot, offset=2, size=4)
                .set_view_link(self.attachment_link(obj, 'screenshot')),

                t.input_file_attachment(ff('vcf?'), 'VCF', value=obj.vcf, offset=2, size=4)
                .set_view_link(self.attachment_link(obj, 'vcf')),

                t.input_textarea(ff('remark'), 'Remark', value=obj.remark,
                                 offset=2, static=readonly, update_dict=update_dict),

                name='messy-ngsmgr-ngsrun-fieldset',
            ),
            t.fieldset(
                form_submit_bar(create) if not readonly else t.div(),
                name='footer'
            ),
        ]

        if not readonly:
            jscode = select2_lookup(tag=ff('ngs_provider_id*'), minlen=3,
                                    placeholder="Type an institution name",
                                    parenttag="messy-ngsmgr-ngsrun-fieldset", usetag=False,
                                    url=rq.route_url('messy.institution-lookup'))

        else:
            jscode = ''

        return t.div()[t.h2('NGS Run'), eform], jscode

    def view_helper(self, render=True):

        run_html, run_jscode = super().view_helper(render=False)

        run_html.add(
            t.hr,
            t.h4('Run Plate'),
        )

        runplate_html, runplate_js = generate_ngsrunplate_table(self.obj, self.request)
        run_html.add(runplate_html)
        run_jscode += runplate_js

        if len(self.obj.plates) > 0:
            run_html.add(
                t.hr,
                t.a('Generate sample sheet',
                    href=self.request.route_url('messy-ngsmgr.ngsrun-action',
                                                _query={'_method': 'generate_samplesheet',
                                                        'id': self.obj.id})),
                '|',
                t.a('Generate GISAID csv',
                    href=self.request.route_url('messy-ngsmgr.ngsrun-action',
                                                _query={'_method': 'generate_gisaidcsv',
                                                        'id': self.obj.id})),
            )

        return self.render_edit_form(run_html, run_jscode)

    def lookup_helper(self):
        q = self.request.params.get('q')
        if not q:
            return error_page(self.request, "q not provided")
        q = '%' + q.lower() + '%'

        runs = get_dbhandler().get_ngsruns_by_codes(q, groups=None, user=self.request.user)
        result = [
            {'id': r.id, 'text': r.code} for r in runs
        ]

        return result

    def can_modify(self, obj):
        return obj.can_modify(self.request.user)

    @m_roles(r.PUBLIC)
    def plateaction(self):

        rq = self.request
        dbh = get_dbhandler()

        _method = rq.params.get('_method')
        ngsrun_id = int(rq.params.get('ngsrun_id'))
        ngsrun = self.get_object(obj_id=ngsrun_id)

        if not ngsrun.can_modify(rq.user):
            raise AuthError("Your user account does not have the role for modifying NGSRun.")

        if _method == 'add-ngsrunplate':

            plate_id = int(rq.POST.get('messy-ngsrunplate-plate_id', -1))
            if plate_id < 0:
                return error_page(rq, 'Please select the plate you want to link!')
            adapterindex_id = int(rq.POST.get('messy-ngsrunplate-adapterindex_id', -1))
            if adapterindex_id < 0:
                return error_page(rq, 'Please select the adapter-index kit!')
            lane = int(rq.POST.get('messy-runplate-lane', 1))
            note = rq.POST.get('messy-runplate-none', '')

            runplate = dbh.NGSRunPlate(
                ngsrun_id=run_id,
                plate_id=plate_id,
                adapterindex_id=adapterindex_id,
                lane=lane,
                note=note
            )
            sess = dbh.session()
            sess.add(runplate)
            sess.flush([runplate])
            rq.session.flash(('success', 'New plate has been added.'))

            return HTTPFound(location=rq.route_url(self.view_route, id=run_id))

        elif _method == 'delete':

            runplate_ids = [int(x) for x in rq.POST.getall('runplate-ids')]
            runplates = dbh.get_runplates_by_ids(runplate_ids, groups=None, user=rq.user)

            if len(runplates) == 0:
                return Response(modal_error)

            return Response(
                modal_delete(
                    title='Unlink run plate(s)',
                    content=t.literal(
                        'You are going to unlink the following plate(s): '
                        '<ul>'
                        + ''.join('<li>%s</li>' % rp.plate.code for rp in runplates)
                        + '</ul>'
                    ), request=rq,
                ), request=rq
            )

        elif _method == 'delete/confirm':

            runplate_ids = [int(x) for x in rq.POST.getall('runplate-ids')]
            runplates = dbh.get_runplates_by_ids(runplate_ids, groups=None, user=rq.user)

            sess = dbh.session()
            count = 0
            for rp in runplates:
                sess.delete(rp)
                count += 1

            sess.flush()
            rq.session.flash(
                ('success', f'You have successfully unlink {count} plate.')
            )

            return HTTPFound(location=rq.referer)

        raise RuntimeError(f'Unknown method name: {_method}')

    def action_get(self):

        rq = self.request
        method = rq.params.get('_method', None)
        dbh = self.dbh

        if method == 'generate_samplesheet':
            seqrun = self.get_object(obj_id=rq.params.get('id'))
            if not seqrun.can_modify(rq.user):
                raise AuthError('Your user account is not authorized to generate samplesheet.')

            samplesheet = generate_samplesheet(seqrun)
            return response.Response(samplesheet,
                                     content_type='text/csv',
                                     content_disposition=f'inline; filename="SampleSheet_{seqrun.code}.csv"',
                                     request=rq)

        if method == 'generate_gisaidcsv':
            seqrun = self.get_object(obj_id=rq.params.get('id'))

            data = []
            gisaid_csv = export_gisaid(seqrun.get_related_samples())
            for k in sorted(gisaid_csv.keys()):
                data.append(gisaid_csv[k])
            df = pd.DataFrame.from_records(data)
            df['covv_seq_technology'] = dbh.EK.get(seqrun.sequencing_kit_id, dbh.session()).key.split('-', 1)[0]
            csv = df.to_csv(index=False)
            return response.Response(csv,
                                     content_type='text/csv',
                                     content_disposition=f'inline; filename="Metadata_{seqrun.code}.csv"',
                                     request=rq)

        raise ValueError('unknown method')


def generate_ngsrun_table(ngsruns, request):

    table_body = t.tbody()

    not_guest = not request.user.has_roles(r.GUEST)

    for ngsrun in ngsruns:
        table_body.add(
            t.tr(
                t.td(t.literal('<input type="checkbox" name="run-ids" value="%d" />' % ngsrun.id)
                     if not_guest else ''),
                t.td(t.a(ngsrun.code, href=request.route_url('messy-ngsmgr.ngsrun-view', id=ngsrun.id))),
                t.td(ngsrun.date),
                t.td(ngsrun.serial),
                t.td(ngsrun.ngs_kit),
                t.td(ngsrun.remark[:60] + ('...' if len(ngsrun.remark) > 60 else '')),
            )
        )

    run_table = t.table(id='run-table', class_='table table-condensed table-striped',
                        style='width:100%')[
        t.thead(
            t.tr(
                t.th('_', style="width: 2em"),
                t.th('Code'),
                t.th('Date'),
                t.th('Serial'),
                t.th('NGS Kit'),
                t.th('Remark'),
            )
        )
    ]

    run_table.add(table_body)

    if not_guest:
        add_button = ('New run', request.route_url('messy-ngsmgr.ngsrun-add'))

        bar = t.selection_bar('run-ids', action=request.route_url('messy-ngsmgr.ngsrun-action'),
                              add=add_button)
        html, code = bar.render(run_table)

    else:
        html = t.div(run_table)
        code = ''

    code += template_datatable_js
    return html, code


def generate_ngsrunplate_table(ngsrun, request):

    dbh = get_dbhandler()

    table_body = t.tbody()

    for ngsrunplate in ngsrun.plates:
        table_body.add(
            t.tr(
                t.td(t.literal(f'<input type="checkbox" name="ngsrunplate-ids" value="{ngsrunplate.id}" />')),
                t.td(t.a(ngsrunplate.plate.code,
                     href=request.route_url('messy.plate-view', id=ngsrunplate.plate.id))),
                t.td(ngsrunplate.plate.specimen_type),
                t.td(ngsrunplate.plate.experiment_type),
                t.td(ngsrunplate.adapterindex),
                t.td('1'),
                t.td(ngsrunplate.note[:30] if ngsrunplate.note else ''),
            )
        )

    ngsrunplate_table = t.table(class_='table table-condensed table-striped')[
        t.thead(
            t.tr(
                t.th('', style="width: 2em"),
                t.th('Plate Code'),
                t.th('Specimen'),
                t.th('Experiment'),
                t.th('Adapter-Index'),
                t.th('Lane'),
                t.th('Note')
            )
        )
    ]

    ngsrunplate_table += table_body

    if ngsrun.can_modify(request.user):

        bar = t.selection_bar(
            'ngsrunplate-ids', action=request.route_url('messy-ngsmgr.ngsrun-plateaction'), delete_label='Unlink',
            others=t.button('Link plate',
                            class_='btn btn-sm btn-success',
                            id='add-ngsrunplate',
                            name='_method',
                            value='add_ngsrunplate',
                            type='button'),
            hiddens=[('ngsrun_id', ngsrun.id), ]
        )
        html, code = bar.render(ngsrunplate_table)

        # prepare popup

        popup_content = t.fieldset(
            t.input_select('messy-ngsmgr-ngsrunplate-plate_id', 'Plate', value=None, offset=3, size=9),
            t.input_select_ek('messy-ngsmgr-ngsrunplate-adapterindex_id', 'Adapter Index', offset=3, size=9,
                              value=None, description=True, parent_ek=dbh.get_ekey('@ADAPTERINDEX')),
            t.input_text('messy-ngsmgr-ngsrunplate-lane', 'Lane', value='1', offset=3, size=2),
            t.input_text('messy-ngsmgr-ngsrunplate-note', 'Note', value='', offset=3, size=9),
            name='messy-ngsmgr-ngsrunplate-fieldset'
        )
        submit_button = t.submit_bar('Add plate', 'add-ngsrunplate')

        add_ngsrunplate_form = t.form(name='add-ngsrunplate-form', method=t.POST,
                                      action=request.route_url('messy-ngsmgr.ngsrun-plateaction'))[
            popup_content,
            t.literal(f'<input type="hidden" name="ngsrun_id" value="{ngsrun.id}">'),
            submit_button
        ]

        ngsrunplate_table = t.div(
            t.div(
                popup('Add plate', add_ngsrunplate_form, request=request),
                id='add-ngsrunplate-modal', class_='modal fade', tabindex='-1', role='dialog'
            ),
            html
        )

        ngsrunplate_js = (code + "$('#add-ngsrunplate').click( function(e) {$('#add-ngsrunplate-modal').modal('show');});"
                       + select2_lookup(tag='messy-runplate-plate_id', minlen=1,
                                        placeholder="Type plate code here",
                                        parenttag='messy-runplate-fieldset', usetag=False,
                                        url=request.route_url('messy.plate-lookup')))

        return ngsrunplate_table, ngsrunplate_js

    else:
        html = t.div(ngsrunplate_table)
        code = ''

        return html, code


template_datatable_js = """
$(document).ready(function() {
    $('#run-table').DataTable( {
        paging: false,
        fixedHeader: {
            headerOffset: $('#fixedNavbar').outerHeight()
        },
        order: [ [2, "desc"] ],
        columns: [
            { title: " ", "orderable": false, "width": "12px" },
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
