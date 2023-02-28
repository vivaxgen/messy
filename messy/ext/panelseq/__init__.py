
# messy-panelseq requires messy-ngsmgr to be initialized

from rhombus.lib.utils import cerr, set_dbhandler_class, get_dbhandler_class
from rhombus.routes import add_route_view, add_route_view_class

from messy.views.menunav import get_menunav

from messy.ext import ngsmgr
from messy.ext.panelseq.models.handler import generate_handler_class


set_dbhandler_class(generate_handler_class(get_dbhandler_class()))

get_menunav().add_menu(
    'Panel', [('Variant', 'url:/variant'), ('Region', 'url:/region')],
    after=True
)


def includeme(config):

    config.include(ngsmgr.includeme)

    # override messy-ngsmgr.panel route
    add_route_view_class(
        config, 'messy.ext.panelseq.views.panel.PanelSeqViewer', 'messy-ngsmgr.panel',
        '/panel',
        '/panel/@@action',
        '/panel/@@regionaction',
        '/panel/@@variantaction',
        '/panel/@@add',
        ('/panel/@@lookup', 'lookup', 'json'),
        '/panel/{id}@@edit',
        '/panel/{id}@@save',
        ('/panel/{id}@@attachment/{fieldname}', 'attachment'),
        ('/panel/{id}', 'view'),
    )

# EOF
