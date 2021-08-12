
from messy.views import (BaseViewer, r, get_dbhandler, m_roles, ParseFormError, form_submit_bar,
                         render_to_response, form_submit_bar, select2_lookup, or_, error_page,
                         Response, modal_delete, modal_error, HTTPFound)
import rhombus.lib.tags_b46 as t
import sqlalchemy.exc
import json


class CollectionViewer(BaseViewer):

    managing_roles = BaseViewer.managing_roles + [r.COLLECTION_MANAGE]
    modifying_roles = [r.COLLECTION_MODIFY] + managing_roles

    object_class = get_dbhandler().Collection
    fetch_func = get_dbhandler().get_collections_by_ids
    edit_route = 'messy.collection-edit'
    view_route = 'messy.collection-view'
    attachment_route = 'messy.collection-attachment'

    form_fields = {
        'code*': ('messy-collection-code',),
        'group_id': ('messy-collection-group_id', int),
        'description': ('messy-collection-description', ),
        'institution_ids': ('messy-collection-institution_ids', list, int),
        'contact': ('messy-collection-contact', ),
        'remark': ('messy-collection-remark', ),
        'attachment': ('messy-collection-attachment', ),
        'data': ('messy-collection-data', json.loads),
    }

    @m_roles(r.PUBLIC)
    def index(self):

        group_id = int(self.request.params.get('group_id', 0))
        if group_id:
            if self.request.user.in_group(group_id):
                collections = self.dbh.get_collections(groups=[(None, group_id)])
            else:
                return error_page('You do not have access to view collections that belong to this group.')

        elif self.request.user.has_roles(r.SYSADM, r.DATAADM, r.SYSVIEW, r.DATAVIEW, r.COLLECTION_MANAGE):
            collections = self.dbh.get_collections(groups=None, ignore_acl=True)
        else:
            collections = self.dbh.get_collections(groups=self.request.user.groups)

        html, code = generate_collection_table(collections, self.request)

        html = t.div()[t.h2('Collections')].add(html)

        return render_to_response("messy:templates/generic_page.mako", {
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
                if 'collections.code' in detail or 'uq_collections_code' in detail:
                    raise ParseFormError(f'The collection code: {d["code"]}  is '
                                         f'already being used. Please use other collection code!',
                                         'messy-collection-code') from err

            raise RuntimeError(f'error updating object: {detail}')

        except sqlalchemy.exc.DataError as err:
            dbh.session().rollback()
            detail = err.args[0]

            raise RuntimeError(detail)

    def edit_form(self, obj=None, create=False, readonly=False, update_dict=None):

        rq = self.request
        obj = obj or self.obj
        dbh = self.dbh

        # dealing with messy-collection-institution_ids field
        institution_options = [(i.id, i.code) for i in obj.institutions]
        institution_ids = [x[0] for x in institution_options]
        if update_dict is not None:
            institution_ids = update_dict.getall('messy-collection-institution_ids')
            institutions = [dbh.get_institutions_by_ids([i], None)[0] for i in institution_ids]
            institution_options = [(i.id, i.code) for i in institutions]

        ff = self.ffn
        eform = t.form(name='messy-collection', method=t.POST, enctype=t.FORM_MULTIPART, readonly=readonly,
                       update_dict=update_dict)
        eform.add(
            self.hidden_fields(obj),
            t.fieldset(
                t.input_text(ff('code*'), 'Code', value=obj.code, offset=2),
                t.input_select(ff('group_id'), 'Group', value=obj.group_id, offset=2, size=2,
                               options=[(g.id, g.name) for g in dbh.get_group(user_id=rq.user)]),
                t.input_text(ff('description'), 'Description', value=obj.description,
                             offset=2),
                t.input_select(ff('institution_ids'), 'Institution', value=institution_ids, offset=2,
                               size=3, multiple=True, options=institution_options),
                t.input_text(ff('contact'), 'Contact', value=obj.contact, offset=2),
                t.input_textarea(ff('remark'), 'Remark', value=obj.remark, offset=2),
                t.input_file_attachment(ff('attachment'), 'Attachment', value=obj.attachment, offset=2, size=4)
                .set_view_link(self.attachment_link(obj, 'attachment')),
                t.input_textarea(ff('data'), 'Data', value=json.dumps(obj.data, indent=2), offset=2),
                name="messy-collection-fieldset"
            ),
            t.fieldset(
                form_submit_bar(create) if not readonly else t.div(),
                name='footer'
            ),
        )

        if not readonly:
            jscode = select2_lookup(tag="messy-collection-institution_ids", minlen=3,
                                    placeholder="Type an institution name",
                                    parenttag="messy-collection-fieldset",
                                    url=rq.route_url('messy.institution-lookup'))
        else:
            jscode = ''

        return t.div()[t.h2('Collection'), eform], jscode

    def action_post(self):

        rq = self.request
        dbh = self.dbh
        _method = rq.POST.get('_method')

        if _method == 'delete':

            collection_ids = [int(x) for x in rq.params.getall('collection-ids')]
            collections = dbh.get_collections_by_ids(collection_ids, groups=None, user=rq.user)

            if len(collections) == 0:
                return Response(modal_error)

            return Response(
                modal_delete(
                    title='Removing collection(s)',
                    content=t.literal(
                        'You are going to remove the following collection(s): '
                        '<ul>'
                        + ''.join(f'<li>{c.code}</li>' for c in collections)
                        + '</ul>'
                    ), request=rq,

                ), request=rq
            )

        elif _method == 'delete/confirm':

            collection_ids = [int(x) for x in rq.params.getall('collection-ids')]
            collections = dbh.get_collections_by_ids(collection_ids, groups=None, user=rq.user)

            sess = dbh.session()
            count = left = 0
            for c in collections:
                if c.can_modify(rq.user):
                    sess.delete(c)
                    count += 1
                else:
                    left += 1

            sess.flush()
            rq.session.flash(
                ('success', f'You have successfully removed {count} collection(s), '
                            f'kept {left} collections.')
            )

            return HTTPFound(location=rq.referer)

        raise RuntimeError('No defined action')


def generate_collection_table(collections, request):

    table_body = t.tbody()

    not_guest = not request.user.has_roles(r.GUEST)

    for collection in collections:
        table_body.add(
            t.tr(
                t.td(t.literal('<input type="checkbox" name="collection-ids" value="%d" />' % collection.id)
                     if not_guest else ''),
                t.td(t.a(collection.code, href=request.route_url('messy.collection-view', id=collection.id))),
                t.td(collection.description or '-'),
                t.td(t.a(collection.samples.count(),
                         href=request.route_url('messy.sample', _query={'q': '%d[collection_id]' % collection.id}))),
                t.td(t.a(collection.group.name,
                         href=request.route_url('messy.collection', _query={'group_id': collection.group.id}))),
            )
        )

    collection_table = t.table(class_='table table-condensed table-striped')[
        t.thead(
            t.tr(
                t.th('', style="width: 2em"),
                t.th('Collection code'),
                t.th('Description'),
                t.th('Sample size'),
                t.th('Group'),
            )
        )
    ]

    collection_table.add(table_body)

    if not_guest:
        add_button = ('New collection',
                      request.route_url('messy.collection-add'))

        bar = t.selection_bar('collection-ids', action=request.route_url('messy.collection-action'),
                              add=add_button)
        html, code = bar.render(collection_table)

    else:
        html = t.div(collection_table)
        code = ''

    return html, code
