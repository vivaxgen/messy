"""Top-level package for MESSy pathogen extension."""

__author__ = """Hidayat Trimarsanto"""
__email__ = 'trimarsanto@gmail.com'
__version__ = '0.1.0'


from rhombus.lib.utils import cerr, set_dbhandler_class, get_dbhandler_class
from rhombus.routes import add_route_view, add_route_view_class

from messy.ext.pathogen.models.handler import generate_handler_class


# generate new dbhandler class, which will generate new Sample class
set_dbhandler_class(generate_handler_class(get_dbhandler_class()))


def includeme(config):

    # add new routes here
    add_route_view_class(
        config, 'messy.ext.pathogen.views.sample.PathogenSampleViewer', 'messy.sample',
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


# EOF
