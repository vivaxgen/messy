from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from rhombus import init_app
from rhombus.lib.utils import cerr, cout, get_dbhandler
from rhombus.models.core import set_func_userid

# set configuration and dbhandler
from messy.scripts import run

# initialize view
# from messy.views import *
from messy.routes import includeme
from messy.lib.uploads import set_temp_directory
from messy.lib.nomenclature import load_location_data


def get_userid_func():
    return get_dbhandler().session().user.id


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    cerr('messy main() is running...')
    set_func_userid(get_userid_func)

    # attach rhombus to /mgr url, include custom configuration
    config = init_app(global_config, settings, prefix='/mgr',
                      include=includeme, include_tags=['messy.includes'])

    set_temp_directory(config.get_settings().get('messy.temp_directory'))
    load_location_data(config.get_settings().get('assets.directory') + '/locations.json')

    return config.make_wsgi_app()

# EOF
