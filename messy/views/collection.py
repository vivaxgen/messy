
from messy.views import *
import json


class CollectionViewer(BaseViewer):

    managing_roles = BaseViewer.managing_roles + [ COLLECTION_MODIFY ]

    class_func = get_dbhandler().Collection
    fetch_func = get_dbhandler().get_collections_by_ids
    edit_route = 'messy.collection-edit'
    view_route = 'messy.collection-view'

    form_fields = {
            'code':             ('messy-collection-code',),
            'group_id':         ('messy-collection-group_id', int),
            'description':      ('messy-collection-description',),
            'institution_ids':  ('messy-collection-institution_ids', list, int),
            'contact':          ('messy-collection-contact',),
            'remark':           ('messy-collection-remark'),
            'data':             ('messy-collection-data', json.loads),
    }


    def __init__(self, request):
        super().__init__(request)
        self.collection = None


    @m_roles( PUBLIC )
    def index(self):

        group_id = int(self.request.params.get('group_id', 0))
        if group_id:
            if self.request.user.in_group(group_id):
                collections = self.dbh.get_collections( groups = [(None, group_id)] )
            else:
                return error_page('You do not have access to view collections that belong to this group.')
          
        elif self.request.user.has_roles( SYSADM, DATAADM, SYSVIEW, DATAVIEW ):
            collections = self.dbh.get_collections( groups = None )
        else:
            collections = self.dbh.get_collections( groups = self.request.user.groups )

        html, code = generate_collection_table(collections, self.request)

        html = div()[ h2('Collections') ].add( html )

        return render_to_response("messy:templates/generic_page.mako",
            {    'html': html,
                'code': code,
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

        except sqlalchemy.exc.IntegrityError as err:
            dbh.session().rollback()
            detail = err.args[0]
            if 'UNIQUE' in detail:
                field = detail.split()[-1]
                if field == 'collections.code':
                    raise ParseFormError('The collection code: %s is '
                        'already being used. Please use other collection code!'
                        % d['code'], 'messy-collection-code') from err

            raise RuntimeError('error updating object')


    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        obj = obj or self.collection
        dbh = self.dbh

        # dealing with messy-collection-institution_ids field
        institution_options = [ (i.id, i.code) for i in obj.institutions ]
        institution_ids = [ x[0] for x in institution_options ]
        if update_dict is not None:
            institution_ids = update_dict.getall('messy-collection-institution_ids')
            institutions = [ dbh.get_institutions_by_ids([i], None)[0] for i in institution_ids ]
            institution_options = [ (i.id, i.code) for i in institutions ]

        eform = form( name='messy-collection', method=POST)
        eform.add(
            self.hidden_fields(obj),
            fieldset(
                input_text('messy-collection-code', 'Code', value=obj.code,
                    offset=2, static=readonly, update_dict=update_dict),
                input_select('messy-collection-group_id', 'Group', value=obj.group_id,
                    offset=2, size=2, options = [ (g.id, g.name) for g in dbh.get_group() ],
                    static=readonly, update_dict=update_dict),
                input_text('messy-collection-description', 'Description', value=obj.description,
                    offset=2, static=readonly, update_dict=update_dict),
                input_select('messy-collection-institution_ids', 'Institution',
                    value = institution_ids, offset=2, size=3, static=readonly, multiple=True,
                    options = institution_options),
                input_text('messy-collection-contact', 'Contact', value=obj.contact,
                    offset=2, static=readonly, update_dict=update_dict),
                input_textarea('messy-collection-remark', 'Remark', value=obj.remark,
                    offset=2, static=readonly, update_dict=update_dict),
                input_textarea('messy-collection-data', 'Data', value=json.dumps(obj.data, indent=2),
                    offset=2, static=readonly, update_dict=update_dict),
                name="messy-collection-fieldset"
            ),
            fieldset(
                form_submit_bar(create) if not readonly else div(),
                name = 'footer'
            ),
        )

        if not readonly:
            jscode = select2_lookup(tag="messy-collection-institution_ids", minlen=3,
                        placeholder="Type an institution name",
                        parenttag="messy-collection-fieldset",
                        url=self.request.route_url('messy.institution-lookup'))
        else:
            jscode = ''

        return div()[ h2('Collection'), eform], jscode


def generate_collection_table(collections, request):

    table_body = tbody()

    not_guest = not request.user.has_roles( GUEST )

    for collection in collections:
        table_body.add(
            tr(
                td(literal('<input type="checkbox" name="collection-ids" value="%d" />' % collection.id)
                    if not_guest else ''),
                td( a(collection.code, href=request.route_url('messy.collection-view', id=collection.id)) ),
                td( collection.description or '-' ),
                td( a(collection.samples.count(),
                        href=request.route_url('messy.sample', _query = {'q': '%d[collection_id]' % collection.id}))),
                td( a(collection.group.name,
                        href=request.route_url('messy.collection', _query = {'group_id': collection.group.id}))),
            )
        )

    collection_table = table(class_='table table-condensed table-striped')[
        thead(
            tr(
                th('', style="width: 2em"),
                th('Collection code'),
                th('Description'),
                th('Sample size'),
                th('Group'),
            )
        )
    ]

    collection_table.add( table_body )

    if not_guest:
        add_button = ( 'New collection',
                        request.route_url('messy.collection-add')
        )

        bar = selection_bar('collection-ids', action=request.route_url('messy.collection-action'),
                    add = add_button)
        html, code = bar.render(collection_table)

    else:
        html = div(collection_table)
        code = ''

    return html, code


