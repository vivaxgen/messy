#
# this module extend sample class for pathogen-related database fields
#

from sqlalchemy import Column, types, ForeignKey
from sqlalchemy.sql import False_

from rhombus.lib.utils import cerr
from rhombus.models.ek import EK


def generate_sample_class(base_class):

    _bs = base_class

    _bs.passive_case_detection = Column(types.Boolean, nullable=False, server_default=False_())

    _bs.imported_case = Column(types.Boolean, nullable=False, server_default=False_())

    _bs.nationality_status = Column(types.Boolean, nullable=False, server_default=False_())

    _bs.storage_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    _bs.storage = EK.proxy('storage_id', '@BLOOD-STORAGE', default='NA')
    """ sample storage method """

    _bs.method_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    _bs.method = EK.proxy('method_id', '@BLOOD-WITHDRAWAL', default='NA')
    """ blood withdrawal method """

    _bs.pcr_method_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    _bs.pcr_method = EK.proxy('pcr_method_id', '@PCR-METHOD', default='NA')
    """ PCR method for detection """

    _bs.pcr_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    _bs.pcr = EK.proxy('pcr_id', '@SPECIES', default='no-species')
    """ species identification based on PCR """

    _bs.microscopy_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    _bs.microscopy = EK.proxy('microscopy_id', '@SPECIES', default='no-species')
    """ species identification based on microscopy """

    _bs.parasitemia = Column(types.Float, nullable=False, server_default='-1')

    _bs.recurrent = Column(types.Boolean, nullable=False, server_default=False_())
    """ if this a recurrent case """

    def init_instance(self):
        self.storage = None
        self.method = None
        self.pcr_method = None
        self.pcr = None
        self.microscopy = None

    _bs.add_init_funcs(init_instance)

    return _bs

    # end of PathogenSample definition

    #cerr('[PathogenSample class generated]')
    #return PathogenSample


# EOF
