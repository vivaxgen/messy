
from rhombus.lib.utils import cerr

from messy.ext.panelseq.models import schema


def generate_handler_class(base_class):
    """ base_class is the handler base class """

    schema.extend_object_classes(base_class)

    class MessyPanelSeqQueryConstructor(base_class.query_constructor_class):

        field_specs = base_class.query_constructor_class.field_specs | {

            'region_id': schema.Region.id,
            'region_code': schema.Region.code,
            'region_chrom': schema.Region.chrom,
            'region_begin': schema.Region.begin,
            'region_end': schema.Region.end,

            'variant_id': schema.Variant.id,
            'variant_code': schema.Variant.code,
            'variant_chrom': schema.Variant.chrom,
            'variant_position': schema.Variant.position,
        }

    class PanelSeqHandler(base_class):

        # add models here

        Variant = schema.Variant
        Region = schema.Region

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

        # Panel accessors are provided by messy-ngsmgr extension

        # this is for Region and Variant accessors

        def get_regions(self, groups, specs=None, user=None, fetch=True, raise_if_empty=False):

            q = self.construct_select(self.Region, specs)
            if fetch:
                q = q.order_by(self.Region.chrom, self.Region.begin)

            return self.fetch_select(q, fetch, raise_if_empty)

        def get_regions_by_ids(self, ids, groups, user=None, fetch=True, raise_if_empty=False):
            return self.get_regions(groups, [{'region_id': ids}], user=user, fetch=fetch,
                                    raise_if_empty=raise_if_empty)

        def get_regions_by_codes(self, codes, groups, user=None, fetch=True, raise_if_empty=False):
            return self.get_regions(groups, [{'region_code': codes}], user=user, fetch=fetch,
                                    raise_if_empty=raise_if_empty)

        def get_regions_by_position(self, chrom=None, begin=None, end=None):
            specs = {}
            if chrom:
                specs['region_chrom'] = chrom
            if begin:
                specs['region_begin'] = str(begin)
            if end:
                specs['region_end'] = str(end)

            return self.get_regions(None, [specs])

        def get_variants(self, groups, specs=None, user=None, fetch=True, raise_if_empty=False):

            q = self.construct_select(self.Variant, specs)
            if fetch:
                q = q.order_by(self.Variant.chrom, self.Variant.position)

            return self.fetch_select(q, fetch, raise_if_empty)

        def get_variants_by_ids(self, ids, groups, user=None, fetch=True, raise_if_empty=False):
            return self.get_variants(groups, [{'variant_id': ids}], user=user, fetch=fetch,
                                     raise_if_empty=raise_if_empty)

        def get_variants_by_codes(self, codes, groups, user=None, fetch=True, raise_if_empty=False):
            return self.get_variants(groups, [{'variant_code': codes}], user=user, fetch=fetch,
                                     raise_if_empty=raise_if_empty)

        def get_variants_by_position(self, chrom=None, position=None):
            specs = {}
            if chrom:
                specs['variant_chrom'] = chrom
            if position:
                specs['variant_position'] = str(position)

            return self.get_variants(None, [specs])

    cerr('[PanelSeqHandler class generated.]')
    return PanelSeqHandler

# EOF
