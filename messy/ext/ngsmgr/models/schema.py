
from messy.ext.ngsmgr.lib import roles as r
from messy.models.dbschema import Institution, Sample, Plate, PlatePosition, convert_date

from rhombus.lib.utils import cerr, cout, get_dbhandler
from rhombus.models.core import (Base, BaseMixIn, metadata, deferred, relationship,
                                 registered, declared_attr, column_property)
from rhombus.models.ek import EK
from rhombus.models.user import Group, User
from rhombus.models.fileattach import FileAttachment
from rhombus.models.auxtypes import GUID

from sqlalchemy.sql import func, False_
from sqlalchemy.orm import object_session, class_mapper
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy import (exists, Table, Column, types, ForeignKey, UniqueConstraint,
                        Identity, select)

from pathlib import Path


# add additional relationship from object class from handler

def extend_object_classes(dbh):

    dbh.Plate.__mapper__.add_property(
        'ngsruns',
        relationship('NGSRunPlate', order_by='ngsrunplates.c.plate_id',
                     back_populates='plate')
    )

    dbh.Sample.__mapper__.add_property(
        'fastqpairs',
        relationship('FastqPair',
                     back_populates='sample')
    )


class NGSRunFile(object):

    def generate_fullpath(self):
        """ generate a new fullpath composed from self.id and filename """
        hex_id = f'{self.id:05x}'
        return Path(hex_id[-3:], f'{{{hex_id}}}-{self.filename}').as_posix()


class VCFFile(NGSRunFile, FileAttachment):

    __subdir__ = 'vcfs'

    __mapper_args__ = {
        "polymorphic_identity": 8039635474158829413,    # hash('VCFFile') & sys.maxsize
    }


class FastqFile(NGSRunFile, FileAttachment):

    __subdir__ = 'fastqs'

    __mapper_args__ = {
        "polymorphic_identity": 3128321612305521149,    # hash('FastqFile') & sys.maxsize
    }


class AMFile(NGSRunFile, FileAttachment):

    __subdir__ = 'ams'

    __mapper_args__ = {
        "polymorphic_identity": 3997295282219146844,    # hash('AMFile') & sys.maxsize
    }


class NGSRun(BaseMixIn, Base):
    """
    This class represent a libprep + sequencing run
    """

    __tablename__ = 'ngsruns'

    code = Column(types.String(16), nullable=False, unique=True, server_default='')
    serial = Column(types.String(48), nullable=False, unique=True, server_default='')
    date = Column(types.Date, nullable=False, server_default=func.current_date())

    refctrl = Column(types.Boolean, nullable=False, server_default=False_())
    public = Column(types.Boolean, nullable=False, server_default=False_())

    # primary group of user
    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    group = relationship(Group, uselist=False, foreign_keys=group_id)

    ngs_provider_id = Column(types.Integer, ForeignKey('institutions.id'), nullable=False)
    ngs_provider = relationship(Institution, uselist=False, foreign_keys=ngs_provider_id)

    ngs_kit_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    ngs_kit = EK.proxy('ngs_kit_id', '@SEQUENCING_KIT')

    # pdf of depthplots, if available
    depthplots_file_id = Column(types.Integer, ForeignKey('fileattachments.id'), nullable=True)
    depthplots_file = relationship(FileAttachment, uselist=False, foreign_keys=depthplots_file_id,
                                   cascade='all, delete')
    depthplots = FileAttachment.proxy('depthplots_file')

    # gzip html from multiqc, if available
    qcreport_file_id = Column(types.Integer, ForeignKey('fileattachments.id'), nullable=True)
    qcreport_file = relationship(FileAttachment, uselist=False, foreign_keys=qcreport_file_id,
                                 cascade='all, delete')
    qcreport = FileAttachment.proxy('qcreport_file')

    # screenshot from the instrument, if available
    screenshot_file_id = Column(types.Integer, ForeignKey('fileattachments.id'), nullable=True)
    screenshot_file = relationship(FileAttachment, uselist=False, foreign_keys=screenshot_file_id,
                                   cascade='all, delete')
    screenshot = FileAttachment.proxy('screenshot_file')

    # vcf file if available
    vcf_file_id = Column(types.Integer, ForeignKey('fileattachments.id'), nullable=True)
    vcf_file = relationship(VCFFile, uselist=False, foreign_keys=vcf_file_id,
                            cascade='all, delete')
    vcf = VCFFile.proxy("vcf_file")

    remark = deferred(Column(types.Text, nullable=False, server_default=''))

    fastqpairs = relationship("FastqPair", back_populates="ngsrun")

    additional_files = relationship(FileAttachment, secondary="ngsruns_files", cascade='all, delete',
                                    collection_class=attribute_mapped_collection('id'),
                                    order_by=FileAttachment.filename)

    vcf_files = relationship(VCFFile, secondary='ngsruns_vcffiles', cascade='all, delete',
                             collection_class=attribute_mapped_collection('id'),
                             order_by=VCFFile.filename)

    plates = relationship('NGSRunPlate', order_by='ngsrunplates.c.plate_id',
                          back_populates='ngsrun')

    __managing_roles__ = BaseMixIn.__managing_roles__ | {r.NGSRUN_MANAGE}
    __modifying_roles__ = __managing_roles__ | {r.NGSRUN_MODIFY}

    def __str__(self):
        return self.code

    def __repr__(self):
        return f"NGSRun('{self.code}')"

    def get_related_samples(self, scalar=False):
        if scalar:
            q = select(func.count(Sample.id))
        else:
            q = select(Sample)
        q = (
            q.
            join(PlatePosition).
            join(Plate).
            join(NGSRunPlate).
            filter(NGSRunPlate.ngsrun_id == self.id).
            filter(~Sample.code.in_(['-', '*', 'NTC1', 'NTC2', 'NTC3', 'NTC4']))
        )
        if scalar:
            return object_session(self).scalar(q)
        return object_session(self).execute(q).scalars()

    def update(self, obj):

        if isinstance(obj, dict):

            dbh = get_dbhandler()

            if 'group' in obj:
                obj['group_id'] = dbh.get_group(obj['group']).id
                del obj['group']

            if type(inst := obj.get('sequencing_provider', None)) == str:
                self.sequencing_provider_id = dbh.get_institutions_by_codes(
                    obj['sequencing_provider'], None, raise_if_empty=True)[0].id
                del obj['sequencing_provider']

            convert_date(obj, 'date')

            self.update_fields_with_dict(obj, additional_fields=['depthplots', 'qcreport', 'screenshot'])
            self.update_ek_with_dict(obj, dbh=dbh)

        else:
            raise RuntimeError('PROG/ERR: can only update from dict object')

    def as_dict(self, exclude=None):
        d = super().as_dict(exclude={'sequences', 'plates', 'additional_files'})
        d['plates'] = [[p.plate.code, p.adapterindex, p.lane, p.note] for p in self.plates]
        return d

    @classmethod
    def from_dict(cls, a_dict, dbh):
        run = super().from_dict(a_dict, dbh)
        for rp in a_dict.get('plates', []):
            plate = dbh.get_plates_by_codes(rp[0], groups=None, ignore_acl=True)[0]
            d = dict(ngsrun_id=run.id, plate_id=plate.id, adapterindex=rp[1], lane=rp[2], note=rp[3])
            srp = NGSRunPlate.from_dict(d, dbh)

    def can_modify(self, user):
        if user.has_roles(* self.__managing_roles__):
            return True
        if user.has_roles(* self.__modifying_roles__):  # and user.in_group(self.group):
            return True
        return False


ngsrun_file_table = Table(
    'ngsruns_files', metadata,
    Column('id', types.Integer, Identity(), primary_key=True),
    Column('ngsrun_id', types.Integer, ForeignKey('ngsruns.id', ondelete='CASCADE'),
           index=True, nullable=False),
    Column('file_id', types.Integer, ForeignKey('fileattachments.id', ondelete='CASCADE'), nullable=False),
    UniqueConstraint('ngsrun_id', 'file_id')
)

ngsrun_vcffile_table = Table(
    'ngsruns_vcffiles', metadata,
    Column('id', types.Integer, Identity(), primary_key=True),
    Column('ngsrun_id', types.Integer, ForeignKey('ngsruns.id', ondelete='CASCADE'),
           index=True, nullable=False),
    Column('vcffile_id', types.Integer, ForeignKey('fileattachments.id', ondelete='CASCADE'), nullable=False),
    UniqueConstraint('ngsrun_id', 'vcffile_id')
)


class NGSRunPlate(BaseMixIn, Base):

    __tablename__ = 'ngsrunplates'

    ngsrun_id = Column(types.Integer, ForeignKey('ngsruns.id', ondelete='CASCADE'),
                       index=True, nullable=False)
    ngsrun = relationship(NGSRun, uselist=False, foreign_keys=ngsrun_id,
                          back_populates='plates')

    plate_id = Column(types.Integer, ForeignKey('plates.id', ondelete='CASCADE'),
                      index=True, nullable=False)
    plate = relationship(Plate, uselist=False, foreign_keys=plate_id,
                         back_populates='ngsruns')

    adapterindex_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    adapterindex = EK.proxy('adapterindex_id', '@ADAPTERINDEX')

    lane = Column(types.Integer, nullable=False, server_default='1')

    note = Column(types.Text, nullable=True)

    __ek_fields__ = {'adapterindex'}

    __table_args__ = (
        UniqueConstraint('ngsrun_id', 'plate_id'),
        UniqueConstraint('ngsrun_id', 'adapterindex_id', 'lane'),
    )


class FastqPair(BaseMixIn, Base):

    __tablename__ = 'fastqpairs'

    sample_id = Column(types.Integer, ForeignKey('samples.id', ondelete='CASCADE'),
                       index=True, nullable=False)
    sample = relationship('Sample', uselist=False, foreign_keys=sample_id,
                          back_populates='fastqpairs')

    ngsrun_id = Column(types.Integer, ForeignKey('ngsruns.id', ondelete='CASCADE'),
                       index=True, nullable=False)
    ngsrun = relationship(NGSRun, uselist=False, foreign_keys=ngsrun_id,
                          back_populates='fastqpairs')

    # read1 file if available
    read1_file_id = Column(types.Integer, ForeignKey('fileattachments.id'), nullable=True)
    read1_file = relationship(FastqFile, uselist=False, foreign_keys=read1_file_id,
                              cascade='all, delete')
    read1 = FastqFile.proxy("read1_file")

    # read1 file if available
    read2_file_id = Column(types.Integer, ForeignKey('fileattachments.id'), nullable=True)
    read2_file = relationship(FastqFile, uselist=False, foreign_keys=read2_file_id,
                              cascade='all, delete')
    read2 = FastqFile.proxy("read2_file")

# EOF
