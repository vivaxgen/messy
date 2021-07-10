from messy.lib.whoosh import IndexService, set_index_service

from rhombus import add_route_view, add_route_view_class
from rhombus.lib.utils import cerr, cout

def includeme( config ):
    """ this configuration must be included as the last order
    """

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

    #config.add_route('rpc', '/rpc')
    #config.add_view('messy.views.rpc.do_rpc', route_name='rpc')
    config.include("pyramid_rpc.jsonrpc")
    config.add_jsonrpc_endpoint('rpc', '/rpc')
    config.add_jsonrpc_method('messy.views.rpc.check_auth', endpoint='rpc', method='check_auth')
    config.add_jsonrpc_method("messy.views.rpc.pipeline_upload", endpoint="rpc", method="pipeline_upload")

    config.add_route('upload', '/upload')
    config.add_view('messy.views.upload.UploadViewer', attr='index', route_name='upload')

    config.add_route('upload-commit', '/upload/commit')
    config.add_view('messy.views.upload.UploadViewer', attr='commit', route_name='upload-commit')

    config.add_route('tools', '/tools')
    config.add_view('messy.views.tools.ToolsViewer', attr='index', route_name='tools')

    add_route_view_class( config, 'messy.views.institution.InstitutionViewer', 'messy.institution',
        '/institution',
        '/institution/@@action',
        '/institution/@@add',
        ('/institution/@@lookup', 'lookup', 'json'),
        '/institution/{id}@@edit',
        '/institution/{id}@@save',
        ('/institution/{id}', 'view')
    )

    add_route_view_class( config, 'messy.views.collection.CollectionViewer', 'messy.collection',
        '/collection',
        '/collection/@@action',
        '/collection/@@add',
        '/collection/{id}@@edit',
        '/collection/{id}@@save',
        ('/collection/{id}', 'view')
    )

    add_route_view_class( config, 'messy.views.sample.SampleViewer', 'messy.sample',
        '/sample',
        '/sample/@@action',
        '/sample/@@add',
        ('/sample/@@lookup', 'lookup', 'json'),
        '/sample/{id}@@edit',
        '/sample/{id}@@save',
        ('/sample/{id}', 'view')
    )

    add_route_view_class( config, 'messy.views.sequence.SequenceViewer', 'messy.sequence',
        '/sequence',
        '/sequence/@@action',
        '/sequence/@@add',
        '/sequence/{id}@@edit',
        '/sequence/{id}@@save',
        ('/sequence/{id}', 'view')
    )

    add_route_view_class( config, 'messy.views.plate.PlateViewer', 'messy.plate',
        '/plate',
        '/plate/@@action',
        '/plate/@@add',
        ('/plate@@lookup', 'lookup', 'json'),
        '/plate/{id}@@edit',
        '/plate/{id}@@save',
        ('/plate/{id}@@position', 'position', 'json'),
        ('/plate/{id}', 'view')
    )

    add_route_view_class( config, 'messy.views.run.RunViewer', 'messy.run',
        '/run',
        '/run/@@action',
        '/run/@@add',
        ('/run/@@lookup', 'lookup', 'json'),
        '/run/{id}@@edit',
        '/run/{id}@@save',
        ('/run/{id}@@attachment/{fieldname}', 'attachment'),
        ('/run/{id}', 'view')
    )

    #config.add_route('post-add', '/add')
    #config.add_view('messy.views.post.PostViewer', attr='add', route_name='post-add')

    #config.add_route('post-edit', '/posts/{id}@@edit')
    #config.add_view('messy.views.post.PostViewer', attr='edit', route_name='post-edit')

    #config.add_route('post-view', '/posts/{id}')
    #config.add_view('messy.views.post.PostViewer', attr='index', route_name='post-view')


    # add additional routes and views here

    # whoosh

    set_index_service( IndexService(config.registry.settings['messy.whoosh.path']))
