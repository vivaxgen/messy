
from enum import Enum

from sqlalchemy import (exists, Table, Column, types, ForeignKey, UniqueConstraint,
                        Identity, select)
from sqlalchemy.orm.collections import attribute_mapped_collection

from rhombus.lib.utils import get_dbhandler
from rhombus.models.ek import EK
from rhombus.models.auxtypes import GUID
from rhombus.models.fileattach import FileAttachment
from rhombus.models.core import (Base, BaseMixIn, metadata, deferred, relationship,
                                 registered, declared_attr, column_property)
from rhombus.models.auxtypes import GUID

from messy.ext.ngsmgr.models.schema import Panel


class PanelType(Enum):
    SET = 1
    ANALYSIS = 2
    ASSAY = 3
    MHAP = 4


class Variant(BaseMixIn, Base):
    """ Variant is a 1-base SNP position to be analyzed
        TODO: currently only able for biallelic SNPs, need to think for
        non-biallelic SNPs (possibly uses alt_1, alt_2, alt_3?)
    """

    __tablename__ = 'variants'

    code = Column(types.String(24), nullable=False, unique=True, server_default='')
    chrom = Column(types.String(16), nullable=False, server_default='')
    position = Column(types.Integer, nullable=False, server_default='-1')
    ref = Column(types.String(1), nullable=False, server_default='')
    alt = Column(types.String(1), nullable=False, server_default='')
    gene = Column(types.String(16), nullable=False, server_default='')
    aachange = Column(types.String(8), nullable=False, server_default='')

    __table_args__ = (
        UniqueConstraint('chrom', 'position'),
    )

    def __repr__(self):
        return f"Variant('{self.code}')"

    def __init__(self, code=None, chrom=None, position=None, ref=None, alt=None,
                 gene=None, aachange=None):
        # just perform sanity check and recode empty code
        if not chrom or not position:
            raise ValueError('chrom and position must be provided')
        if code is None:
            code = f"{chrom}:{position}"
        super().__init__(code=code, chrom=chrom, position=position, ref=ref, alt=alt,
                         gene=gene, aachange=aachange)


class Region(BaseMixIn, Base):
    """ Region is either Assay region or Analysis region (set by type)
    """

    __tablename__ = 'regions'

    code = Column(types.String(24), nullable=False, unique=True)
    type = Column(types.Integer, nullable=False, server_default='0')
    chrom = Column(types.String(16), nullable=False, server_default='')
    begin = Column(types.Integer, nullable=False, server_default='-1')
    end = Column(types.Integer, nullable=False, server_default='-1')

    species_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    species = EK.proxy('species_id', '@SPECIES')

    panels = relationship(Panel,
                          secondary='panels_regions',
                          cascade='all, delete',
                          collection_class=attribute_mapped_collection('id'),
                          order_by=Panel.code
                          )

    __table_args__ = (
        UniqueConstraint('code', 'type'),
    )

    def __repr__(self):
        return f"Region('{self.code}')"

    def __init__(self, code=None, type=None, chrom=None, begin=None, end=None, species_id=None):
        if not (chrom and begin and end and type):
            raise ValueError('chrom, begin and end must be provided!')
        if code is None:
            code = f"{chrom}:{begin}:{end-begin}"
        super().__init__(code=code, type=type,
                         chrom=chrom, begin=begin, end=end,
                         species_id=species_id)

    @classmethod
    def get_or_create(cls, chrom, begin, end, type, species_id):
        """ return an already region in database or create a new one """

        dbh = get_dbhandler()
        regions = dbh.get_regions_by_position(chrom=chrom, begin=begin, end=end)
        if not any(regions):
            # empty list, create a new region
            region = cls(type=type, chrom=chrom, begin=begin, end=end, species_id=species_id)
            dbh.session().add(region)
            dbh.session().flush([region])
            return region

        return regions[0]


panel_region_table = Table(
    'panels_regions', metadata,
    Column('id', types.Integer, Identity(), primary_key=True),
    Column('panel_id', types.Integer, ForeignKey('panels.id', ondelete='CASCADE'),
           index=True, nullable=False),
    Column('region_id', types.Integer, ForeignKey('regions.id', ondelete='CASCADE'),
           index=True, nullable=False),
    UniqueConstraint('panel_id', 'region_id'),
)


panel_variant_table = Table(
    'panels_variants', metadata,
    Column('id', types.Integer, Identity(), primary_key=True),
    Column('panel_id', types.Integer, ForeignKey('panels.id', ondelete='CASCADE'),
           index=True, nullable=False),
    Column('variant_id', types.Integer, ForeignKey('variants.id', ondelete='CASCADE'),
           index=True, nullable=False),
    UniqueConstraint('panel_id', 'variant_id'),
)


def extend_object_classes(dbh):

    # the following code might not work properly yet

    dbh.Panel.__mapper__.add_property(
        'regions',
        relationship(Region,
                     secondary=panel_region_table,
                     cascade='all, delete',
                     collection_class=attribute_mapped_collection('id'),
                     order_by=[Region.chrom, Region.begin],
                     )
    )

    dbh.Panel.__mapper__.add_property(
        'variants',
        relationship(Variant,
                     secondary=panel_variant_table,
                     cascade='all, delete',
                     collection_class=attribute_mapped_collection('id'),
                     order_by=[Variant.chrom, Variant.position],
                     )
    )


# EOF
