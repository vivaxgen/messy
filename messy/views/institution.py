
from messy.views import *


class InstitutionViewer(BaseViewer):

    managing_roles = BaseViewer.managing_roles + [ INSTITUTION_MANAGE ]
    modifying_roles = managing_roles + [ INSTITUTION_MODIFY ]

    object_class = get_dbhandler().Institution
    fetch_func = get_dbhandler().get_institutions_by_ids
    edit_route = 'messy.institution-edit'
    view_route = 'messy.institution-view'

    form_fields = { 
        'code':     ('messy-institution-code', ),
        'name':     ('messy-institution-name', ),
        'address':  ('messy-institution-address', ),
        'zipcode':  ('messy-institution-zipcode', ),
        'contact':  ('messy-institution-contact', ),
        'remark':   ('messy-institution-remark', ),
    }

    def __init__(self, request):
        super().__init__(request)
        self.institution = None


    @m_roles( PUBLIC )
    def index(self):

        institutions = self.dbh.get_institutions()

        html, code = generate_institution_table(institutions, self.request)

        html = div()[ h2('Institutions') ].add( html )

        return render_to_response("messy:templates/generic_page.mako",
            {   'html': html,
                'code': code,
            },
            request = self.request)


    def lookup_helper(self):
        q = self.request.params.get('q')
        if not q:
            return error_page(self.request, "q not provided")
        q = '%' + q.lower() + '%'

        dbh = get_dbhandler()
        institutions = dbh.Institution.query(dbh.session()).filter(
            or_( dbh.Institution.code.ilike(q), dbh.Institution.name.ilike(q)))

        result = [
            { 'id': i.id, 'text': i.render() }
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
            obj.update( d )
            if obj.id is None:
                dbh.session().add(obj)
            dbh.session().flush([obj])

        except sqlalchemy.exc.IntegrityError as err:
            dbh.session().rollback()
            detail = err.args[0]
            eform, jscode = self.edit_form(obj)
            if 'UNIQUE' in detail:
                field = detail.split()[-1]
                print(field)
                if field == 'institutions.code':
                    raise ParseFormError('The institution code: %s is '
                        'already being used. Please use other institution code!'
                        % d['code'], 'messy-institution-code') from err

            raise RuntimeError('error updating object')


    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        obj = obj or self.institution
        dbh = self.dbh

        eform = form( name='messy-institution', method=POST)
        eform.add(
            self.hidden_fields(obj),
            fieldset(
                input_text(self.form_fields['code'][0], 'Code', value=obj.code,
                    offset=2, static=readonly, update_dict=update_dict),
                input_text(self.form_fields['name'][0], 'Name', value=obj.name,
                    offset=2, static=readonly, update_dict=update_dict),
                input_text(self.form_fields['address'][0], 'Address', value=obj.address,
                    offset=2, static=readonly, update_dict=update_dict),
                input_text(self.form_fields['zipcode'][0], 'Zipcode', value=obj.zipcode,
                    offset=2, static=readonly, update_dict=update_dict),
                input_text(self.form_fields['contact'][0], 'Contact', value=obj.contact,
                    offset=2, static=readonly, update_dict=update_dict),
                input_textarea(self.form_fields['remark'][0], 'Remark', value=obj.remark,
                    offset=2, static=readonly, update_dict=update_dict)
            ),
            fieldset(
                form_submit_bar(create) if not readonly else div(),
                name = 'footer'
            ),
        )

        jscode = '''
        '''

        return div()[ h2('Institution'), eform], jscode


def generate_institution_table(institutions, request):

    table_body = tbody()

    not_guest = not request.user.has_roles( GUEST )

    for institution in institutions:
        table_body.add(
            tr(
                td(literal('<input type="checkbox" name="institution-ids" value="%d" />' % institution.id)
                    if not_guest else ''),
                td( a(institution.code, href=request.route_url('messy.institution-view', id=institution.id)) ),
                td( institution.name ),
                td( institution.address),
                td( institution.zipcode),
            )
        )

    institution_table = table(class_='table table-condensed table-striped')[
        thead(
            tr(
                th('', style="width: 2em"),
                th('Code'),
                th('Name'),
                th('Address'),
                th('Zipcode'),
            )
        )
    ]

    institution_table.add( table_body )

    if not_guest:
        add_button = ( 'New institution',
                        request.route_url('messy.institution-add')
        )

        bar = selection_bar('institution-ids', action=request.route_url('messy.institution-action'),
                    add = add_button)
        html, code = bar.render(institution_table)

    else:
        html = div(institution_table)
        code = ''

    return html, code
