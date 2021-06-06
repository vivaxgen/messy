
from messy.views import *


class RunViewer(BaseViewer):

    managing_roles = BaseViewer.managing_roles + [ SEQUENCINGRUN_MODIFY ]

    class_func = get_dbhandler().SequencingRun
    fetch_func = get_dbhandler().get_sequencingruns_by_ids
    edit_route = 'messy.run-edit'
    view_route = 'messy.run-view'

    form_fields = {
        'code':                     ('messy-run-code', ),
        'serial':                   ('messy-run-serial', ),
        'sequencing_provider_id':   ('messy-run-sequencing_provider_id', ),
        'sequencing_kit_id':        ('messy-run-sequencing_kit_id', ),
        'depthplots':               ('messy-run-depthplots', ),
        'qcreport':                 ('messy-run-qcreport', ),
        'remark':                   ('messy-run-remark', ),
    }

    @m_roles( PUBLIC )
    def index(self):

        group_id = int(self.request.params.get('group_id', 0))

        runs = self.dbh.get_sequencingruns( groups = None )

        html, code = generate_run_table(runs, self.request)
        html = div()[ h2('Runs'), html ]

        return render_to_response("messy:templates/generic_page.mako",
            { 'html': html
            },
            request = self.request)


    def update_object(self, obj, d):
        rq = self.request
        dbh = self.dbh

        try:
            obj.update( d )
            if obj.id is None:
                dbh.session().add(obj)
            dbh.session().flush([obj])

        except RuntimeError as err:
            raise


    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        obj = obj or self.obj
        dbh = self.dbh

        # processing sequencing_provider_id
        prov_inst = obj.sequencing_provider
        if update_dict:
            prov_inst = dbh.get_institutions_by_ids(
                    update_dict[self.form_fields['sequencing_provider_id'][0]], None)[0]

        eform = form( name='messy-run', method=POST)[
            self.hidden_fields(obj),
            fieldset(
                input_text(self.form_fields['code'][0], 'Code', value=obj.code,
                    offset=2, static=readonly, update_dict=update_dict),
                input_text(self.form_fields['serial'][0], 'Serial', value=obj.run_code,
                    offset=2, static=readonly, update_dict=update_dict),
                input_select(self.form_fields['sequencing_provider_id'][0], 'Sequencing Provider',
                    value = prov_inst.id if prov_inst else '', offset=2, size=5, static=readonly,
                    options = [ (prov_inst.id, f'{prov_inst.code} | {prov_inst.name}') ] if prov_inst else []),
                input_select_ek(self.form_fields['sequencing_kit_id'][0], 'Sequencing Kit',
                    value = obj.sequencing_kit_id, offset=2, size=5, static=readonly,
                    parent_ek = dbh.get_ekey('@SEQUENCING_KIT')),
                input_textarea(self.form_fields['remark'][0], 'Remark', value=obj.remark,
                    offset=2, static=readonly, update_dict=update_dict),
                name = 'messy-run-fieldset',
            ),
            fieldset(
                form_submit_bar(create) if not readonly else div(),
                name = 'footer'
            ),
        ]

        if not readonly:
            jscode = select2_lookup(tag=self.form_fields['sequencing_provider_id'][0], minlen=3,
                            placeholder="Type an institution name",
                            parenttag="messy-run-fieldset", usetag=False,
                            url=self.request.route_url('messy.institution-lookup'))

        else:
            jscode = ''

        return div()[ h2('Sequencing Run'), eform], jscode


def generate_run_table(runs, request):

    table_body = tbody()

    not_guest = not request.user.has_roles( GUEST )

    for run in runs:
        table_body.add(
            tr(
                td(literal('<input type="checkbox" name="run-ids" value="%d" />' % run.id)
                    if not_guest else ''),
                td( a(run.code, href=request.route_url('messy.run-view', id=run.id)) ),
                td( run.run_code ),
                td( run.sequencing_kit ),
                td( run.remark[:60] + '...')
            )
        )

    run_table = table(class_='table table-condensed table-striped')[
        thead(
            tr(
                th('', style="width: 2em"),
                th('Code'),
                th('Run Code'),
                th('Sequencing Kit'),
                th('Remark'),
            )
        )
    ]

    run_table.add( table_body )

    if not_guest:
        add_button = ( 'New run',
                        request.route_url('messy.run-add')
        )

        bar = selection_bar('run-ids', action=request.route_url('messy.run-action'),
                    add = add_button)
        html, code = bar.render(run_table)

    else:
        html = div(run_table)
        code = ''

    return html, code
