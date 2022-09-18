
from rhombus.lib.utils import cerr, set_dbhandler_class, get_dbhandler_class
from rhombus.routes import add_route_view, add_route_view_class

from messy.ext.ngsmgr.models.handler import generate_handler_class


set_dbhandler_class(generate_handler_class(get_dbhandler_class()))


def includeme(config):

    add_route_view_class(
        config, 'messy.ext.ngsmgr.views.ngsrun.NGSRunViewer', 'messy-ngsmgr.ngsrun',
        '/ngsrun',
        '/ngsrun/@@action',
        '/ngsrun/@@plateaction',
        '/ngsrun/@@add',
        ('/ngsrun/@@lookup', 'lookup', 'json'),
        '/ngsrun/{id}@@edit',
        '/ngsrun/{id}@@save',
        ('/ngsrun/{id}@@attachment/{fieldname}', 'attachment'),
        ('/ngsrun/{id}', 'view')
    )

# EOF
