
from rhombus.lib.utils import cerr
from messy.ext.pathogen.models import sample


def generate_handler_class(base_class):
    """ base class should be the handler base class """

    class PathogenDBHandler(base_class):

        Sample = sample.generate_sample_class(base_class.Sample)

        def initdb(self, create_table=True, init_data=True, rootpasswd=None, ek_initlist=[]):
            """ initialize database """
            from .setup import ek_initlist as messy_pathogen_ek_initlist
            super().initdb(create_table, init_data, rootpasswd,
                           ek_initlist=messy_pathogen_ek_initlist + ek_initlist)
            if init_data:
                from .setup import setup
                setup(self)
                cerr('[messy-pathogen database has been initialized]')

    cerr('[PathogenDBHandler class generated.]')
    return PathogenDBHandler

# EOF
