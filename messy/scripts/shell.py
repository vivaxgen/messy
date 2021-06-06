

from rhombus.lib.utils import cerr, get_dbhandler
from rhombus.scripts import setup_settings, arg_parser
from messy.scripts import run
from messy.lib.whoosh import set_index_service, IndexService

import sys

def greet():
    cerr('messy-shell - shell for MESSy')


def usage():
    cerr('messy-shell - shell for MESSy')
    cerr('usage:')
    cerr('\t%s scriptname [options]' % sys.argv[0])
    sys.exit(0)


def main():
    greet()

    # preparing everything
    p = arg_parser('messy-shell')
    args = p.parse_args(sys.argv[1:])

    settings = setup_settings( args )
    dbh = get_dbhandler(settings)
    set_index_service( IndexService(settings['messy.whoosh.path']) )

    from IPython import embed
    import transaction
    embed()

