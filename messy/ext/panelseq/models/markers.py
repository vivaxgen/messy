
from enum import Enum

from sqlalchemy import (exists, Table, Column, types, ForeignKey, UniqueConstraint,
                        Identity, select)
from sqlalchemy.orm.collections import attribute_mapped_collection

from rhombus.models.ek import EK
from rhombus.models.auxtypes import GUID
from rhombus.models.fileattach import FileAttachment
from rhombus.models.core import (Base, BaseMixIn, metadata, deferred, relationship,
                                 registered, declared_attr, column_property)
from rhombus.models.auxtypes import GUID



class PanelType(Enum):
    SET = 1
    ANALYSIS = 2
    ASSAY = 3
    MHAP = 4


class Variant(BaseMixIn, Base):
    """ Variant is a 1-base SNP position to be analyzed
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


class Region(BaseMixIn, Base):
    """ Region is either Assay region or Analysis region
    """

    __tablename__ = 'regions'

    code = Column(types.String(24), nullable=False, unique=True)
    type = Column(types.Integer, nullable=False, server_default='0')
    chrom = Column(types.String(16), nullable=False, server_default='')
    begin = Column(types.Integer, nullable=False, server_default='-1')
    end = Column(types.Integer, nullable=False, server_default='-1')

    species_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    species = EK.proxy('species_id', '@SPECIES')

    __table_args__ = (
        UniqueConstraint('code', 'type'),
    )

    def __repr__(self):
        return f"Region('{self.code}')"


class Panel(BaseMixIn, Base):
    """ Panel can be:
        - Set panel, eg. SPOTMAL, VG
        - Assay panel, eg. SPOTMAL/GCRE-1, VG/GEO33
        - Analysis panel, eg. SPOTMAL/DRG, VG/GEO33
        - Microhap panel

        Naming convention:
            SPOTMAL/DRG -> SPOTMAL (set), DRG (analysis)
            VG/GEO33
    """

    __tablename__ = 'panels'

    code = Column(types.String(24), nullable=False, unique=True)
    type = Column(types.Integer, nullable=False, server_default='0')
    uuid = Column(GUID(), nullable=False, unique=True)

    remark = Column(types.String(128), nullable=False, server_default='')

    related_panel_id = Column(types.Integer, ForeignKey('panels.id'), nullable=True)

    species_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    species = EK.proxy('species_id', '@SPECIES')

    __table_args__ = (
        UniqueConstraint('code', 'type'),
    )

    additional_files = relationship(FileAttachment, secondary="panels_files", cascade='all, delete',
                                    collection_class=attribute_mapped_collection('id'),
                                    order_by=FileAttachment.filename)

    def __repr__(self):
        return f"Panel('{self.code}')"

    def update(self, obj):

        super().update(obj)

        if self.uuid is None:
            self.uuid = GUID.new()

        return self


panel_file_table = Table(
    'panels_files', metadata,
    Column('id', types.Integer, Identity(), primary_key=True),
    Column('panel_id', types.Integer, ForeignKey('panels.id', ondelete='CASCADE'),
           index=True, nullable=False),
    Column('file_id', types.Integer, ForeignKey('fileattachments.id', ondelete='CASCADE'),
           nullable=False),
    UniqueConstraint('panel_id', 'file_id')
)


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

# EOF
