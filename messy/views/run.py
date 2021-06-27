
from messy.views import *
from pyramid.response import Response, FileIter
import dateutil


class RunViewer(BaseViewer):

    managing_roles = BaseViewer.managing_roles + [ SEQUENCINGRUN_MANAGE ]
    modifying_roles = managing_roles + [ SEQUENCINGRUN_MODIFY ]

    object_class = get_dbhandler().SequencingRun
    fetch_func = get_dbhandler().get_sequencingruns_by_ids
    edit_route = 'messy.run-edit'
    view_route = 'messy.run-view'

    form_fields = {
        'code':                     ('messy-run-code', ),
        'serial':                   ('messy-run-serial', ),
        'date?':                     ('messy-run-date', dateutil.parser.parse),
        'sequencing_provider_id':   ('messy-run-sequencing_provider_id', ),
        'sequencing_kit_id':        ('messy-run-sequencing_kit_id', ),
        'depthplots?':               ('messy-run-depthplots', lambda x: x.file.read() if x != b'' else None),
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

    @m_roles(PUBLIC)
    def depthplots(self):

        rq = self.request
        obj_id = int(rq.matchdict.get('id'))

        obj = self.get_object(obj_id, self.fetch_func)
        if not (fp := obj.depthplots_fp()):
            return error_page(request, 'Depth plot not available')

        return Response(app_iter=FileIter(fp),
                        content_type='application/pdf',
                        request=self.request)

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

        # processing depthplots url
        if obj.depthplots_fp():
            url_depthplots = literal(a('View', href=self.request.route_url('messy.run-depthplots', id=obj.id)))
            #view_link = '<div class="col-md-1">' + url_depthplots + '</div>'
        else:
            url_depthplots = 'Not available'
            view_link = ''

        eform = form( name='messy-run', method=POST, enctype=FORM_MULTIPART)[
            self.hidden_fields(obj),
            fieldset(
                input_text(self.form_fields['code'][0], 'Code', value=obj.code,
                    offset=2, static=readonly, update_dict=update_dict),
                input_text(self.form_fields['serial'][0], 'Serial', value=obj.serial,
                    offset=2, static=readonly, update_dict=update_dict),
                input_select(self.form_fields['sequencing_provider_id'][0], 'Sequencing Provider',
                    value = prov_inst.id if prov_inst else '', offset=2, size=5, static=readonly,
                    options = [ (prov_inst.id, f'{prov_inst.code} | {prov_inst.name}') ] if prov_inst else []),
                input_select_ek(self.form_fields['sequencing_kit_id'][0], 'Sequencing Kit',
                    value = obj.sequencing_kit_id, offset=2, size=5, static=readonly,
                    parent_ek = dbh.get_ekey('@SEQUENCING_KIT')),
                input_file(self.form_fields['depthplots?'][0], 'Depth plots', value=url_depthplots,
                           offset=2, size=3, static=readonly).set_view_link(url_depthplots),
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

    table_body = tbody()

    not_guest = not request.user.has_roles( GUEST )

    for run in runs:
        table_body.add(
            tr(
                td(literal('<input type="checkbox" name="run-ids" value="%d" />' % run.id)
                    if not_guest else ''),
                td( a(run.code, href=request.route_url('messy.run-view', id=run.id)) ),
                td( run.serial ),
                td( run.sequencing_kit ),
                td( run.remark[:60] + ('...' if len(run.remark) > 60 else '')),
            )
        )

    run_table = table(class_='table table-condensed table-striped')[
        thead(
            tr(
                th('', style="width: 2em"),
                th('Code'),
                th('Serial'),
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
