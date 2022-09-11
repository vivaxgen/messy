
from sqlalchemy import (exists, Table, Column, types, ForeignKey, UniqueConstraint,
                        Identity, select)

from rhombus.models.core import (Base, BaseMixIn, metadata, deferred, relationship,
                                 registered, declared_attr, column_property)


class FastqPair(BaseMixIn, Base):

    __tablename__ = 'fastqpairs'

    sample_id = Column(types.Integer, ForeignKey('samples.id'), nullable=False)



class AlignmentMap(BaseMixIn, Base):

    __tablename__ = 'alignmentmaps'


# EOF