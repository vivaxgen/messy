
from rhombus.lib.utils import cerr, cout, random_string
#from rhombus.lib.roles import SYSADM, DATAADM
from rhombus.views.generics import error_page
from rhombus.views import *

from messy.lib.roles import *

from sqlalchemy.orm import make_transient, make_transient_to_detached
import sqlalchemy.exc
from sqlalchemy import or_
import time, copy


class ParseFormError(RuntimeError):

    def __init__(self, msg, field):
        super().__init__(msg)
        self.field = field


class BaseViewer_XXX(object):

    template_edit = 'rhombus:templates/generics/formpage.mako'
    managing_roles = [ SYSADM, DATAADM ]
    viewing_roles = [ PUBLIC ] + managing_roles

    class_func = None
    fetch_func = None
    edit_route = None
    view_route = None

    form_fields = {}

    def __init__(self, request):
        self.request = request
        self.dbh = get_dbhandler()


    @m_roles( PUBLIC )
    def view(self):
        return self.view_helper(self.fetch_func, self.edit_route, self.managing_roles)

    def view_helper(self, func, edit_route, allowed_roles):

        rq = self.request
        obj_id = int(rq.matchdict.get('id'))

        obj = self.get_object(obj_id, func)
        eform, jscode = self.edit_form(obj, readonly=True)
        if rq.user.has_roles(* self.managing_roles):
            eform.get('footer').add(
                a('Edit', class_ = 'btn btn-primary offset-md-1',
                    href=rq.route_url(edit_route, id=obj.id)) )
        return self.render_edit_form(eform, jscode)


    @m_roles( PUBLIC )
    def action(self):

        if self.request.POST:
            return self.action_post(request)
        return self.action_get(request)


    @m_roles( PUBLIC )
    def add(self):
        return self.add_helper(self.class_func, self.edit_route, self.view_route)

    def add_helper(self, func, edit_route, view_route):

        rq = self.request
        if rq.method == 'POST':


            obj = func()
            try:
                self.update_object( obj, self.parse_form(rq.params) )

            except ParseFormError as e:
                err_msg = str(e)
                field = e.field
                eform, jscode = self.edit_form(obj, update_dict = rq.params)
                eform.get(field).add_error(err_msg)
                return self.render_edit_form(eform, jscode)

            return HTTPFound(
                location = self.request.route_url(
                    edit_route if rq.params['_method'].endswith('_edit')
                        else view_route,
                    id=obj.id))

        dbh = self.dbh
        with dbh.session().no_autoflush:

            eform, jscode = self.edit_form(func(), create=True)

        return self.render_edit_form(eform, jscode)


    @m_roles(PUBLIC)
    def edit(self):
        return self.edit_helper(self.fetch_func, self.edit_route, self.view_route)

    def edit_helper(self, func, edit_route, view_route):

        rq = self.request
        obj_id = int(rq.matchdict.get('id'))

        if rq.method == 'POST':
            obj = self.get_object(obj_id, func)
            try:
                ok = check_stamp(rq, obj)
                if ok is not True:
                    return ok
                self.update_object(obj, self.parse_form(rq.params))

            except ParseFormError as e:
                err_msg = str(e)
                field = e.field
                eform, jscode = self.edit_form(obj, update_dict = rq.params)
                eform.get(field).add_error(err_msg)
                return self.render_edit_form(eform, jscode)               

            return HTTPFound(
                location = self.request.route_url(
                    edit_route if rq.params['_method'].endswith('_edit')
                        else view_route,
                    id=obj.id))

        obj = self.get_object(obj_id, func)
        eform, jscode = self.edit_form(obj)

        return self.render_edit_form(eform, jscode)


    def parse_form(self, form, d=None, fields={}):
        d = d or dict()
        fields = fields or self.form_fields
        d['_stamp_'] = float(form['messy-stamp'])

        for key, f in fields.items():
            if f[0] in form: 
                if len(f) == 2:
                    try:
                        d[key] = f[1](form[f[0]])
                    except Exception as e:
                        raise ParseFormError(str(e), f[0]) from e
                elif len(f) == 3:
                    if f[1] == list:
                        try:
                            d[key] = [ f[2](x) for x in form.getall(f[0])]
                        except Exception as e:
                            raise ParseFormError(str(e), f[0]) from e
                    else:
                        raise ParseFormError('Error in parsing input', f[0])
                else:
                    d[key] = form[f[0]]

        return d


    def hidden_fields(self, obj):
        request = self.request
        return fieldset (
            input_hidden(name='messy-stamp', value='%15f' % obj.stamp.timestamp() if obj.stamp else -1),
            input_hidden(name='messy-sesskey', value=generate_sesskey(request.user.id, obj.id)),
            name="messy-hidden"
        )


    def render_edit_form(self, eform, jscode):
        return render_to_response(self.template_edit,
            {   'html': eform,
                'code': jscode,
            }, request = self.request
        )


    def get_object(self, obj_id, func):
        rq = self.request
        res = func([obj_id],
                groups = None if rq.user.has_roles( * self.viewing_roles )
                                else rq.user.groups)
        if len(res) == 0:
            raise RuntimeError('Cannot find object! Please check object id!')

        return res[0]

    def set_object(self, obj):
        raise NotImplementedError



def xxxgenerate_sesskey(user_id, obj_id=None):
    node_id_part = '%08x' % obj_id if obj_id else 'XXXXXXXX'
    return '%08x%s%s' % (user_id, random_string(8), node_id_part)


def xxxcheck_stamp(request, obj):
    print( "\n>> Time stamp >>", obj.stamp.timestamp(), float(request.params['messy-stamp']), "\n")
    if (request.method == 'POST' and 
        abs( obj.stamp.timestamp() - float(request.params['messy-stamp']) ) > 0.01):
            return error_page(request,
                'Data entry has been modified by %s at %s. Please cancel and re-edit your entry.'
                % (obj.lastuser.login, obj.stamp)
            )
    return True

def xxxform_submit_bar(create=True):
    if create:
        return custom_submit_bar(('Add', 'save'), ('Add and continue editing', 'save_edit')).set_offset(2)
    return custom_submit_bar(('Save', 'save'), ('Save and continue editing', 'save_edit')).set_offset(2)

def xxxselect2_lookup(**keywords):
    """ requires minlen, tag, placeholder, parenttag """
    if keywords.get('usetag', True):
        keywords['template'] = "templateSelection: function(data, container) { return data.text.split('|', 1); },"
    else:
        keywords['template'] = ''
    return  '''
  $('#%(tag)s').select2( {
        minimumInputLength: %(minlen)d,
        placeholder: '%(placeholder)s',
        dropdownParent: $("#%(parenttag)s"),
        %(template)s
        ajax: {
            url: "%(url)s",
            dataType: 'json',
            data: function(params) { return { q: params.term }; },
            processResults: function(data, params) { return { results: data }; }
        },
    });
''' % keywords
