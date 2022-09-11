

from sqlalchemy import (exists, Table, Column, types, ForeignKey, UniqueConstraint,
                        Identity, select)

from rhombus.models.core import (Base, BaseMixIn, metadata, deferred, relationship,
                                 registered, declared_attr, column_property)


class SNAllele(Base, BaseMixIn):
    """ SNAllele - Single Nucleic Allele
    """

    __tablename__ = 'snalleles'

    sample_id = Column(types.Integer, ForeignKey('samples.id'), nullable=False, index=True)
    variant_id = Column(types.Integer, ForeignKey('variants.id'), nullable=False, index=True)
    alignmentmap_id = Column(types.Integer, ForeignKey('alignmentmaps.id', nullable=False, index=True))

    call = Column(types.String(1), nullable=False, server_default='N')

    # read depth based on NGS-type assessment, if using other kind of technology
    # please adjust as necessary

    allele_A = Column(types.Integer, nullable=False, server_default='0')
    allele_C = Column(types.Integer, nullable=False, server_default='0')
    allele_G = Column(types.Integer, nullable=False, server_default='0')
    allele_T = Column(types.Integer, nullable=False, server_default='0')

    # any indels are count here
    allele_undefined = Column(types.Integer, nullable=False, server_default='0')

    __table_args__ = (
        UniqueConstraint('sample_id', 'variant_id', 'alignmentmap_id'),
    )


class SNHandler(object):

    def __init__(self, dbh):
        self.dbh = dbh

    def get_alleles(
        self, *,
        samples=None, sample_ids=None,
        variants=None, variant_ids=None,
    ):
        """ return list of SNAllele based on samples/sample_ids and/or variants/variant_ids
        """
        pass

    def get_allele_df(
        self, *,
        samples=None, sample_ids=None,
        variants=None, variant_ids=None,
        hetratio=-1,
        mindepth=5,
        hetmindepth=2,
        row='sample',
    ):
        """ return a pandas dataframe of actual allele with sample-based rows or variant-based rows
        """
        pass

    def get_nalt_df(
        self, *,
        samples=None, sample_ids=None,
        variants=None, variant_ids=None,
        hetratio=-1,
        mindepth=5,
        hetmindepth=2,
        row='sample',
    ):
        """ return a pandas dataframe of number of alt alleles with sample-based rows or variant-based rows
        """
        pass



# EOF
