
from messy.views import (BaseViewer, r, get_dbhandler, m_roles, ParseFormError, form_submit_bar,
                         render_to_response, form_submit_bar, select2_lookup, error_page,
                         Response, modal_delete, modal_error, Response)
import rhombus.lib.tags_b46 as t

import sqlalchemy.exc
from pyramid.response import Response, FileIter
import dateutil


class RunViewer(BaseViewer):

    managing_roles = BaseViewer.managing_roles + [r.SEQUENCINGRUN_MANAGE]
    modifying_roles = managing_roles + [r.SEQUENCINGRUN_MODIFY]

    object_class = get_dbhandler().SequencingRun
    fetch_func = get_dbhandler().get_sequencingruns_by_ids
    edit_route = 'messy.run-edit'
    view_route = 'messy.run-view'
    attachment_route = 'messy.run-attachment'

    form_fields = {
        'code*': ('messy-run-code', ),
        'serial*': ('messy-run-serial', ),
        'date?': ('messy-run-date', dateutil.parser.parse),
        'sequencing_provider_id*': ('messy-run-sequencing_provider_id', int),
        'sequencing_kit_id': ('messy-run-sequencing_kit_id', ),
        'depthplots?': ('messy-run-depthplots', ),  # lambda x: x.file.read() if x != b'' else None),
        'qcreport?': ('messy-run-qcreport', ),
        'screenshot?': ('messy-run-screenshot', ),
        'remark': ('messy-run-remark', ),
    }

    @m_roles(r.PUBLIC)
    def index(self):

        group_id = int(self.request.params.get('group_id', 0))

        runs = self.dbh.get_sequencingruns(groups=None)

        html, code = generate_run_table(runs, self.request)
        html = t.div()[t.h2('Runs'), html]

        return render_to_response("messy:templates/generic_page.mako", {
            'html': html
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
                if 'sequencingruns.code' in detail or 'uq_sequencingruns_code' in detail:
                    raise ParseFormError(f'The run code: {d["code"]}  is '
                                         f'already being used. Please use other run code!',
                                         self.ffn('code*')) from err
                if 'sequencingruns.serial' in detail or 'uq_sequencingruns_serial' in detail:
                    raise ParseFormError(f'The run serial: {d["code"]}  is '
                                         f'already being used. Please use other run serial!',
                                         self.ffn('serial*')) from err

            raise RuntimeError(f'error updating object: {detail}')

        except RuntimeError:
            raise

    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        obj = obj or self.obj
        dbh = self.dbh
        ff = self.ffn

        # processing sequencing_provider_id
        prov_inst = obj.sequencing_provider
        if update_dict:
            if (prov_inst_id := update_dict.get(ff('sequencing_provider_id*'), 0)):
                prov_inst = dbh.get_institutions_by_ids(prov_inst_id, None)[0]

        eform = t.form(name='messy-run', method=t.POST, enctype=t.FORM_MULTIPART, readonly=readonly,
                       update_dict=update_dict)[
            self.hidden_fields(obj),
            t.fieldset(
                t.input_text(ff('code*'), 'Code', value=obj.code, offset=2),
                t.input_text(ff('serial*'), 'Serial', value=obj.serial, offset=2),
                t.input_text(ff('date?'), 'Running date', value=obj.date, offset=2, size=2),
                t.input_select(ff('sequencing_provider_id*'), 'Sequencing Provider',
                               value=prov_inst.id if prov_inst else '', offset=2, size=5,
                               options=[(prov_inst.id, f'{prov_inst.code} | {prov_inst.name}')] if prov_inst else []),
                t.input_select_ek(ff('sequencing_kit_id'), 'Sequencing Kit',
                                  value=obj.sequencing_kit_id, offset=2, size=5,
                                  parent_ek=dbh.get_ekey('@SEQUENCING_KIT')),

                t.input_file_attachment(ff('depthplots?'), 'Depth plots', value=obj.depthplots, offset=2, size=4)
                .set_view_link(self.attachment_link(obj, 'depthplots')),

                t.input_file_attachment(ff('qcreport?'), 'QC report', value=obj.qcreport, offset=2, size=4)
                .set_view_link(self.attachment_link(obj, 'qcreport')),

                t.input_file_attachment(ff('screenshot?'), 'Screenshot', value=obj.screenshot, offset=2, size=4)
                .set_view_link(self.attachment_link(obj, 'screenshot')),

                t.input_textarea(ff('remark'), 'Remark', value=obj.remark,
                                 offset=2, static=readonly, update_dict=update_dict),

                name='messy-run-fieldset',
            ),
            t.fieldset(
                form_submit_bar(create) if not readonly else t.div(),
                name='footer'
            ),
        ]

        if not readonly:
            jscode = select2_lookup(tag=ff('sequencing_provider_id*'), minlen=3,
                                    placeholder="Type an institution name",
                                    parenttag="messy-run-fieldset", usetag=False,
                                    url=self.request.route_url('messy.institution-lookup'))

        else:
            jscode = ''

        return t.div()[t.h2('Sequencing Run'), eform], jscode

    def lookup_helper(self):
        q = self.request.params.get('q')
        if not q:
            return error_page(self.request, "q not provided")
        q = '%' + q.lower() + '%'

        runs = get_dbhandler().get_sequencingruns_by_codes(q, groups=None, user=self.request.user)
        result = [
            {'id': r.id, 'text': r.code} for r in runs
        ]

        return result


def generate_run_table(runs, request):

    table_body = t.tbody()

    not_guest = not request.user.has_roles(r.GUEST)

    for run in runs:
        table_body.add(
            t.tr(
                t.td(t.literal('<input type="checkbox" name="run-ids" value="%d" />' % run.id)
                     if not_guest else ''),
                t.td(t.a(run.code, href=request.route_url('messy.run-view', id=run.id))),
                t.td(run.date),
                t.td(run.serial),
                t.td(run.sequencing_kit),
                t.td(run.remark[:60] + ('...' if len(run.remark) > 60 else '')),
            )
        )

    run_table = t.table(class_='table table-condensed table-striped')[
        t.thead(
            t.tr(
                t.th('', style="width: 2em"),
                t.th('Code'),
                t.th('Date'),
                t.th('Serial'),
                t.th('Sequencing Kit'),
                t.th('Remark'),
            )
        )
    ]

    run_table.add(table_body)

    if not_guest:
        add_button = ('New run', request.route_url('messy.run-add'))

        bar = t.selection_bar('run-ids', action=request.route_url('messy.run-action'),
                              add=add_button)
        html, code = bar.render(run_table)

    else:
        html = t.div(run_table)
        code = ''

    return html, code

# EOF
