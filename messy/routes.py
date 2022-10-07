from messy.lib.whoosh import IndexService, set_index_service

from rhombus.routes import add_route_view, add_route_view_class
from rhombus.lib.utils import cerr, cout

from pyramid.events import BeforeRender
from pyramid.renderers import JSON
import simplejson
import datetime


def includeme(config):
    """ this configuration must be included as the last order
    """

    config.add_subscriber(add_global, BeforeRender)

    config.add_static_view('static', 'static', cache_max_age=3600)

    # override assets here
    config.override_asset('rhombus:templates/base.mako', 'messy:templates/base.mako')
    config.override_asset('rhombus:templates/plainbase.mako', 'messy:templates/plainbase.mako')

    # add route and view for home ('/'), /login and /logout
    config.add_route('home', '/')
    config.add_view('messy.views.home.index', route_name='home')

    config.add_route('login', '/login')
    config.add_view('messy.views.home.login', route_name='login')

    config.add_route('logout', '/logout')
    config.add_view('messy.views.home.logout', route_name='logout')

    config.add_route('help', '/help/{path:.*}')
    config.add_view('messy.views.home.docs', route_name='help')

    # below are example for route for class-based viewer
    # the same thing can be achieved using add_view_route_class()

    include_rpc(config)

    config.add_route('upload', '/upload')
    config.add_view('messy.views.upload.UploadViewer', attr='index', route_name='upload')

    config.add_route('upload-commit', '/upload/commit')
    config.add_view('messy.views.upload.UploadViewer', attr='commit', route_name='upload-commit')

    config.add_route('tools', '/tools')
    config.add_view('messy.views.tools.ToolsViewer', attr='index', route_name='tools')

    add_route_view_class(
        config, 'messy.views.institution.InstitutionViewer', 'messy.institution',
        '/institution',
        '/institution/@@action',
        '/institution/@@add',
        ('/institution/@@lookup', 'lookup', 'json'),
        '/institution/{id}@@edit',
        '/institution/{id}@@save',
        ('/institution/{id}', 'view')
    )

    add_route_view_class(
        config, 'messy.views.collection.CollectionViewer', 'messy.collection',
        '/collection',
        '/collection/@@action',
        '/collection/@@add',
        '/collection/@@fileaction',
        '/collection/{id}@@edit',
        '/collection/{id}@@save',
        ('/collection/{id}@@attachment/{fieldname}', 'attachment'),
        ('/collection/{id}', 'view')
    )

    add_route_view_class(
        config, 'messy.views.sample.SampleViewer', 'messy.sample',
        '/sample',
        '/sample/@@action',
        '/sample/@@add',
        ('/sample/@@lookup', 'lookup', 'json'),
        '/sample/@@gridview',
        ('/sample/@@grid', 'grid', 'json'),
        '/sample/{id}@@edit',
        '/sample/{id}@@save',
        ('/sample/{id}@@attachment/{fieldname}', 'attachment'),
        ('/sample/{id}', 'view')
    )

    add_route_view_class(
        config, 'messy.views.plate.PlateViewer', 'messy.plate',
        '/plate',
        '/plate/@@action',
        '/plate/@@add',
        '/plate/@@fileaction',
        ('/plate@@lookup', 'lookup', 'json'),
        '/plate/{id}@@edit',
        '/plate/{id}@@save',
        ('/plate/{id}@@position', 'position', 'json'),
        ('/plate/{id}@@attachment/{fieldname}', 'attachment'),
        ('/plate/{id}', 'view')
    )

    add_route_view_class(
        config, 'messy.views.uploadjob.UploadJobViewer', 'messy.uploadjob',
        '/uploadjob',
        '/uploadjob/@@action',
        '/uploadjob/{id}@@status',      # generic status viewer
        '/uploadjob/{id}@@save',        # generic save method
        '/uploadjob/{id}@@target',
        ('/uploadjob/{id}', 'view'),
    )

    # add additional routes and views here

    # commit config
    config.commit()

    # whoosh

    set_index_service(IndexService(config.registry.settings['messy.whoosh.path']))

    # add addtional setup here


def add_global(event):
    from messy.views.menunav import main_menu
    event['main_menu'] = main_menu


def datetime_adapter(obj, request):
    return obj.isoformat()


def include_rpc(config):

    json_renderer = JSON()
    # import IPython; IPython.embed()

    json_renderer.add_adapter(datetime.datetime, datetime_adapter)
    config.add_renderer('jsonrenderer', json_renderer)
    config.add_jsonrpc_endpoint('rpc-msy-v1', '/rpc/v1', default_renderer='jsonrenderer')
    #config.add_jsonrpc_endpoint('rpc-msy-v1', '/rpc/v1')

    config.add_jsonrpc_method('messy.lib.rpc.list_institutions', endpoint='rpc-msy-v1', method='list_institutions')
    config.add_jsonrpc_method('messy.lib.rpc.data_status', endpoint='rpc-msy-v1', method='data_status')


# EOF
