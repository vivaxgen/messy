
from rhombus.lib.utils import cerr

from messy.ext.panelseq.models import markers


def generate_handler_class(base_class):
    """ base_class is the handler base class """

    class MessyPanelSeqQueryConstructor(base_class.query_constructor_class):

        field_specs = base_class.query_constructor_class.field_specs | {
            'panel_id': markers.Panel.id,
        }

    class PanelSeqHandler(base_class):

        # add models here

        Variant = markers.Variant
        Region = markers.Region
        Panel = markers.Panel

        # set query constructor class

        query_constructor_class = MessyPanelSeqQueryConstructor

        # define additional methods here

        def initdb(self, create_table=True, init_data=True, rootpasswd=None, ek_initlist=[]):
            """ initialize database """
            from .setup import ek_initlist as messy_panelseq_ek_initlist
            super().initdb(create_table, init_data, rootpasswd,
                           ek_initlist=messy_panelseq_ek_initlist + ek_initlist)
            if init_data:
                from .setup import setup
                setup(self)
                cerr('[messy-panelseq database has been initialized]')

        def get_panels(self, groups=None, specs=None, user=None, fetch=True, raise_if_empty=False):

            q = self.construct_query(self.Panel, specs)
            if fetch:
                q = q.order_by(self.Panel.code)

            return self.fetch_query(q, fetch, raise_if_empty)

        def get_panels_by_ids(self, ids, groups, user=None, fetch=True, raise_if_empty=False):
            return self.get_panels(groups, [{'panel_id': ids}], user=user, fetch=fetch, raise_if_empty=raise_if_empty)

    cerr('[PanelSeqHandler class generated.]')
    return PanelSeqHandler

# EOF
