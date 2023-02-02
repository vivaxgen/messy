
from messy.ext.ngsmgr.lib import roles as r
from messy.models.dbschema import (Institution, Sample, Plate, PlatePosition, UploadJob,
                                   UploadItem, convert_date)

from rhombus.lib.utils import cerr, cout, get_dbhandler
from rhombus.models.core import (Base, BaseMixIn, metadata, deferred, relationship,
                                 registered, declared_attr, column_property)
from rhombus.models.ek import EK
from rhombus.models.user import Group, User
from rhombus.models.fileattach import FileAttachment
from rhombus.models.auxtypes import GUID

from sqlalchemy.sql import func, False_
from sqlalchemy.orm import object_session, reconstructor, class_mapper
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy import (exists, Table, Column, types, ForeignKey, UniqueConstraint,
                        Identity, select)

from pathlib import Path
from enum import Enum


# auxiliary classses

class PanelType(Enum):
    SET = 1
    ANALYSIS = 2
    ASSAY = 3
    MHAP = 4


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
                     back_populates='sample',
                     cascade='all, delete-orphan')
    )


class NGSRunFile(object):
    """ base class for all NGS-related files """

    def __init__(self, **kw):
        super().__init__(**kw)
        self._file_owner = None

    def set_file_owner(self, inst):
        self._file_owner = inst

    def get_file_owner(self):
        if not self._file_owner:
            # fetch from db
            pass
        return self._file_owner

    @reconstructor
    def init_on_load(self):
        self._file_owner = None

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
    """ Fastq file """

    # Fastqfiles are kept under the following path scheme:
    # root_storage/fastqs/{ngsrun_id}/{sample_id}-{fileattach_id}-{filename}

    __subdir__ = 'fastqs'

    __mapper_args__ = {
        "polymorphic_identity": 3128321612305521149,    # hash('FastqFile') & sys.maxsize
    }

    def generate_fullpath(self):
        # this will generate the following path:
        # {ngsrun_id(hex)}/{sample_id(hex)}-{fileattach_id(hex)}-{filename}

        file_owner = self.get_file_owner()

        # check file_owner, if None then there is error in programming flow, possibly
        # set_file_owner() has not been called before calling this function
        assert file_owner

        return Path(f'{file_owner.ngsrun_id:05x}',
                    f'{file_owner.sample_id:05x}-{self.id:05x}-{self.filename}').as_posix()


class AMFile(NGSRunFile, FileAttachment):
    """ alignment map file (BAM/SAM/CRAM)"""

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
    ngs_kit = EK.proxy('ngs_kit_id', '@NGS_KIT')

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

    remark = deferred(Column(types.Text, nullable=False, server_default=''))

    fastqpairs = relationship("FastqPair", back_populates="ngsrun", cascade='all, delete-orphan')

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


class Panel(BaseMixIn, Base):
    """ Panel can be:
        - Set panel, eg. SPOTMAL, VG
        - Assay panel, eg. SPOTMAL/GCRE-1, VG/GEO33
        - Analysis panel, eg. SPOTMAL/DRG, VG/GEO33
        - Microhap panel
        - etc

        Naming convention:
            SPOTMAL/DRG -> SPOTMAL (set), DRG (analysis)
            VG/GEO33
    """

    __tablename__ = 'panels'

    code = Column(types.String(24), nullable=False, unique=True)
    uuid = Column(GUID(), nullable=False, unique=True)
    json = deferred(Column(types.JSON, nullable=False, server_default='null'))
    remark = Column(types.String(128), nullable=False, server_default='')
    type = Column(types.Integer, nullable=False, server_default='0')

    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    group = relationship(Group, uselist=False, foreign_keys=group_id)

    refctrl = Column(types.Boolean, nullable=False, server_default=False_())
    public = Column(types.Boolean, nullable=False, server_default=False_())

    related_panel_id = Column(types.Integer, ForeignKey('panels.id'), nullable=True)
    related_panel = relationship('Panel', uselist=False, remote_side='Panel.id')

    species_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    species = EK.proxy('species_id', '@SPECIES')

    __table_args__ = (
        UniqueConstraint('code', 'type'),
    )

    fastqpairs = relationship('FastqPair', back_populates='panel')

    additional_files = relationship(FileAttachment, secondary="panels_files", cascade='all, delete',
                                    collection_class=attribute_mapped_collection('id'),
                                    order_by=FileAttachment.filename)

    __managing_roles__ = BaseMixIn.__managing_roles__ | {r.PANEL_MANAGE}
    __modifying_roles__ = __managing_roles__ | {r.PANEL_MODIFY}

    def can_modify(self, user):
        if user.has_roles(* self.__managing_roles__):
            return True
        if user.has_roles(* self.__modifying_roles__) and user.in_group(self.group):
            return True
        return False

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

    panel_id = Column(types.Integer, ForeignKey('panels.id'),
                      index=True, nullable=False)
    panel = relationship(Panel, uselist=False, foreign_keys=panel_id,
                         back_populates='fastqpairs')

    # primary group of user
    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    group = relationship(Group, uselist=False, foreign_keys=group_id)

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

    def can_modify(self, user):
        if self.sample.can_modify(user):
            return True
        if self.ngsrun.can_modify(user):
            return True
        return False

    @property
    def filename1(self):
        return self.read1_file.filename

    @property
    def filename2(self):
        if self.read2:
            return self.read2_file.filename
        return None

    def clear(self):
        if self.read1_file:
            self.read1_file.clear()
        if self.read2_file:
            self.read2_file.clear()


class FastqUploadJob(UploadJob):

    __subdir__ = 'tmp-uploads/fastqs/'

    __mapper_args__ = {
        "polymorphic_identity": 10,
    }

    # json: {'ngsrun_id': ?, 'collection_id': ?}
    # uploaditem json: {'sample_id': ?, 'panel_id': ?, 'readno': ?}

    def __init__(self, ngsrun_id=None, collection_id=None, ** kwargs):
        super().__init__(** kwargs)
        self.ngsrun_id = ngsrun_id
        self.collection_id = collection_id

    @reconstructor
    def init_on_load(self):
        if d := self.json:
            self.ngsrun_id = d['ngsrun_id']
            self.collection_id = d.get('collection_id', None)
        else:
            self.ngsrun_id = self.collection_id = None

    def commit(self, user):
        """ arrange all fastq into respective FastqPair instance, then
            add all instances to database
        """

        if ((completed := self.get_uploaded_count())
                != (file_count := self.json['file_count'])):
            raise ValueError(f'The number of uploaded files {completed} '
                             f'does not match the manifest {file_count}')

        # set to proper data

        fastqpair_d = {}
        ngsrun_id = self.json['ngsrun_id']
        session = object_session(self)

        for item in self.uploaditems:
            sample_id = item.json['sample_id']
            panel_id = item.json['panel_id']
            readno = item.json['readno']

            try:
                key = (sample_id, panel_id)
                fastqpair = fastqpair_d[key]
            except KeyError:
                fastqpair_d[key] = fastqpair = FastqPair(sample_id=sample_id,
                                                         ngsrun_id=ngsrun_id,
                                                         panel_id=panel_id,
                                                         group_id=user.primarygroup_id)

            # for safety reason, we are copying the file instead of moving (use_move=False),
            # in case something happen during the process
            # set_file_owner() will be invoked to ensure generate_fullpath() run without error
            fastqfile = FastqFile.create_from_path(item.get_fullpath(),
                                                   item.filename,
                                                   # FASTQ is plain text
                                                   mimetype="text/plain",
                                                   session=session,
                                                   use_move=False,
                                                   func=lambda x: x.set_file_owner(fastqpair))
            match readno:
                case 1:
                    fastqpair.read1_file = fastqfile
                case 2:
                    fastqpair.read2_file = fastqfile
                case _:
                    raise ValueError('readno has to be either 1 or 2')

        for fastqpair in fastqpair_d.values():
            session.add(fastqpair)

        self.completed = True

    def validate_manifest(self, df, user, dbh=None):
        # 1) check all fields are filled properly
        # 2) check filenames are not duplicated
        # 3) check that both sample and panel exist

        dbh = dbh or get_dbhandler()

        df['sample_id'] = -1
        df['panel_id'] = -1

        fastq_filenames = set()
        panel_cache = {}
        sample_panel_set = set()

        errors = []

        for idx in range(len(df)):
            row = df.loc[idx]

            # check colletion and sample
            if self.collection_id:
                collection_id = self.collection_id
            else:
                results = dbh.get_collections_by_codes([row.COLLECTION.strip()],
                                                       user=user,
                                                       groups=user.groups)
                if len(results) == 0:
                    errors.append(f'line: {idx + 1} - either collection {row.COLLECTION} '
                                  f'does not exist or it is not accessible by current user!')
                    continue

                collection_id = results[0].id

            results = dbh.get_samples(
                user=user,
                groups=user.groups,
                specs=[dict(sample_code=[row.SAMPLE.strip()],
                            collection_id=[collection_id])],
            )
            if len(results) == 0:
                errors.append(f'line: {idx + 1} - either sample {row.SAMPLE} '
                              f'does not exist or it is not accessible by current user!')
                continue

            df.loc[idx, 'sample_id'] = sample_id = results[0].id

            # check panel
            if not (panel_id := panel_cache.get(row.PANEL, None)):
                results = dbh.get_panels_by_codes([row.PANEL])
                if len(results) == 0:
                    errors.append(f'line: {idx + 1} - panel {row.PANEL} '
                                  f'does not exist!')
                    continue
                panel_id = results[0].id

            df.loc[idx, 'panel_id'] = panel_id

            # check filename
            read1 = df.loc[idx, 'READ1'] = row.READ1.strip()
            read2 = df.loc[idx, 'READ2'] = row.READ2.strip() if row.READ2 else None
            if read1 not in fastq_filenames:
                if (sample_id, panel_id, 1) in sample_panel_set:
                    errors.append(
                        f'line: {idx + 1} - duplicate sample/panel/read combination')
                else:
                    sample_panel_set.add((sample_id, panel_id, 1))
                fastq_filenames.add(read1)
            else:
                errors.append(f'line {idx + 1} - duplicated fastq filename: {read1}')
            if read2:
                if read2 not in fastq_filenames:
                    if (sample_id, panel_id, 2) in sample_panel_set:
                        errors.append(
                            f'line: {idx + 1} - duplicate sample/panel/read combination')
                    else:
                        sample_panel_set.add((sample_id, panel_id, 2))
                    fastq_filenames.add(read2)
                else:
                    errors.append(f'line {idx + 1} - duplicated fastq filename: {read2}')

        if len(errors) > 0:
            raise ValueError(errors)

        # if there are no errors, process the file list

        filecount = 0

        for idx in range(len(df)):

            row = df.loc[idx]

            item_1 = UploadItem(uploadjob=self,
                                filename=row.READ1,
                                json=dict(sample_id=int(row.sample_id),
                                          panel_id=int(row.panel_id),
                                          readno=1))
            filecount += 1

            if row.READ2:
                UploadItem(uploadjob=self,
                           filename=row.READ2,
                           json=dict(sample_id=int(row.sample_id),
                                     panel_id=int(row.panel_id),
                                     readno=2))
                filecount += 1

        self.json = dict(collection_id=self.collection_id,
                         ngsrun_id=self.ngsrun_id,
                         file_count=filecount)

        return filecount, df

# EOF
