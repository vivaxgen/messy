
from messy.views import (BaseViewer, r, get_dbhandler, m_roles, ParseFormError, form_submit_bar,
                         render_to_response, form_submit_bar, select2_lookup, or_, error_page)
import rhombus.lib.tags_b46 as t
import sqlalchemy.exc


class InstitutionViewer(BaseViewer):

    managing_roles = BaseViewer.managing_roles + [r.INSTITUTION_MANAGE]
    modifying_roles = managing_roles + [r.INSTITUTION_MODIFY]

    object_class = get_dbhandler().Institution
    fetch_func = get_dbhandler().get_institutions_by_ids
    edit_route = 'messy.institution-edit'
    view_route = 'messy.institution-view'

    form_fields = {
        'code': ('messy-institution-code', ),
        'name': ('messy-institution-name', ),
        'address': ('messy-institution-address', ),
        'zipcode': ('messy-institution-zipcode', ),
        'contact': ('messy-institution-contact', ),
        'remark': ('messy-institution-remark', ),
    }

    def __init__(self, request):
        super().__init__(request)
        self.institution = None

    @m_roles(r.PUBLIC)
    def index(self):

        institutions = self.dbh.get_institutions()

        html, code = generate_institution_table(institutions, self.request)

        html = t.div()[t.h2('Institutions')].add(html)

        return render_to_response("messy:templates/generic_page.mako", {
            'html': html,
            'code': code,
        }, request=self.request)

    def lookup_helper(self):
        q = self.request.params.get('q')
        if not q:
            return error_page(self.request, "q not provided")
        q = '%' + q.lower() + '%'

        dbh = get_dbhandler()
        institutions = dbh.Institution.query(dbh.session()).filter(
            or_(dbh.Institution.code.ilike(q), dbh.Institution.name.ilike(q)))

        result = [
            {'id': i.id, 'text': i.render()}
            for i in institutions
        ]

        return result

    def action_get(self):
        pass

    def action_post(self):
        pass

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
            eform, jscode = self.edit_form(obj)
            if 'UNIQUE' in detail or 'UniqueViolation' in detail:
                if 'institutions.code' in detail or 'uq_institutions_code' in detail:
                    raise ParseFormError(f'The institution code: {d["code"]} is '
                                         f'already being used. Please use other institution code!',
                                         self.ffn('code')) from err

            raise RuntimeError('error updating object')

    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        obj = obj or self.institution
        dbh = self.dbh

        ff = self.ffn
        eform = t.form(name='messy-institution', method=t.POST, readonly=readonly)
        eform.add(
            self.hidden_fields(obj),
            t.fieldset(
                t.input_text(ff('code'), 'Code', value=obj.code,
                             offset=2, update_dict=update_dict),
                t.input_text(ff('name'), 'Name', value=obj.name,
                             offset=2, update_dict=update_dict),
                t.input_text(ff('address'), 'Address', value=obj.address,
                             offset=2, update_dict=update_dict),
                t.input_text(ff('zipcode'), 'Zipcode', value=obj.zipcode,
                             offset=2, update_dict=update_dict),
                t.input_text(ff('contact'), 'Contact', value=obj.contact,
                             offset=2, update_dict=update_dict),
                t.input_textarea(ff('remark'), 'Remark', value=obj.remark,
                                 offset=2, update_dict=update_dict)
            ),
            t.fieldset(
                form_submit_bar(create) if not readonly else t.div(),
                name='footer'
            ),
        )

        jscode = '''
        '''

        div = t.div()[t.h2('Institution'), eform]

        # if in editing mode, show lookup field to help filling in
        if not readonly:
            lookup_form = t.form(name='messy-institution-lookup')[
                t.fieldset(
                    t.input_select('institution-lookup-ids', 'Check institution',
                                   offset=2, size=6),
                    name='messy-institution-lookup-fieldset'
                )
            ]

            div[t.br, t.br, lookup_form]
            jscode += select2_lookup(tag='institution-lookup-ids', minlen=3,
                                     placeholder="Type any word",
                                     parenttag='messy-institution-lookup-fieldset',
                                     url=self.request.route_url('messy.institution-lookup'))

        return div, jscode


def generate_institution_table(institutions, request):

    table_body = t.tbody()

    not_guest = not request.user.has_roles(r.GUEST)

    for institution in institutions:
        table_body.add(
            t.tr(
                t.td(t.literal('<input type="checkbox" name="institution-ids" value="%d" />' % institution.id)
                     if not_guest else ''),
                t.td(t.a(institution.code, href=request.route_url('messy.institution-view', id=institution.id))),
                t.td(institution.name),
                t.td(institution.address),
                t.td(institution.zipcode),
            )
        )

    institution_table = t.table(class_='table table-condensed table-striped')[
        t.thead(
            t.tr(
                t.th('', style="width: 2em"),
                t.th('Code'),
                t.th('Name'),
                t.th('Address'),
                t.th('Zipcode'),
            )
        )
    ]

    institution_table.add(table_body)

    if not_guest:
        add_button = ('New institution',
                      request.route_url('messy.institution-add'))

        bar = t.selection_bar('institution-ids', action=request.route_url('messy.institution-action'),
                              add=add_button)
        html, code = bar.render(institution_table)

    else:
        html = t.div(institution_table)
        code = ''

    return html, code

# EOF
