
from rhombus.lib.utils import cerr, cout, get_dbhandler
from rhombus.models.core import (Base, BaseMixIn, metadata, deferred, relationship,
                                 registered, declared_attr, column_property)
from rhombus.models.ek import EK
from rhombus.models.user import Group, User
from rhombus.models.fileattach import FileAttachment
import messy.lib.roles as r
from messy.lib import nomenclature
import dateutil.parser
import datetime
from sqlalchemy.sql import func
from sqlalchemy.orm import object_session
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy import (exists, Table, Column, types, ForeignKey, UniqueConstraint,
                        Identity, select)

import io

__version__ = '20210806'

# Design Consideration
# ====================
#
# the schematic model here is designed to emphasize the type of data (or table)
# that can be managed by certain users (or groups), following the workflow of
# the sequencing activities.
#
# Institution: managed by Data Administrator role (eg database manager)
# Collection: managed by Data Administrator role (eg database manager)
# Sample: metadata managed by Sample Manager role (eg surveillance team)
# Plate: managed by Plate Manager role (eg wet-lab team)
# SequencingRun: managed by Sequencing Manager role (eg sequencing lab staff)
# Sequence: managed by Sequence Manager (eg bioinformaticist, sequence analyst)
#


# set default date to middle of month
default_date = datetime.date(1970, 1, 15)


def dict_from_fields(obj, fields, exclude=None):
    d = {}
    for f in fields:
        if exclude and f in exclude:
            continue
        d[f] = str(getattr(obj, f))
    return d


def convert_date(obj, field, now=None):
    if field in obj and isinstance(obj[field], str):
        date_value = dateutil.parser.parse(obj[field], default=default_date)
        if now and date_value > now:
            raise RuntimeError(f'Invalid date in the future: {date_value}')
        obj[field] = date_value


class Institution(Base, BaseMixIn):

    __tablename__ = 'institutions'

    code = Column(types.String(24), nullable=False, unique=True)
    alt_codes = Column(types.String(47), nullable=True, unique=True)
    name = Column(types.String(128), nullable=False, unique=True)
    address = deferred(Column(types.String(128), nullable=False, server_default=''))
    zipcode = Column(types.String(8), nullable=False, server_default='')
    contact = Column(types.String(64), nullable=False, server_default='')
    remark = deferred(Column(types.String(2048), nullable=False, server_default=''))

    __searchable__ = ['code', 'alt_codes', 'name', 'address']

    __managing_roles__ = BaseMixIn.__managing_roles__ | {r.INSTITUTION_MANAGE}
    __modifying_roles__ = __managing_roles__ | {r.INSTITUTION_MODIFY}

    def __repr__(self):
        return f"Institution('{self.code}', '{self.name}')"

    def serialized_code(self):
        return self.code

    def update(self, obj):

        if isinstance(obj, dict):
            self.update_fields_with_dict(obj)

        else:
            raise RuntimeError('PROG/ERR: can only update from dict object')

    @classmethod
    def can_modify(cls, user):
        if user.has_roles(* cls.__managing_roles__):
            return True
        return False

    def as_dict(self):
        d = super().as_dict()
        d.update(self.create_dict_from_fields())
        return d

    def __str__(self):
        return self.code

    def render(self):
        return f'{self.code} | {self.name}'


collection_institution_table = Table(
    'collections_institutions', metadata,
    Column('id', types.Integer, Identity(), primary_key=True),
    Column('collection_id', types.Integer, ForeignKey('collections.id'), nullable=False),
    Column('institution_id', types.Integer, ForeignKey('institutions.id'), nullable=False),
    UniqueConstraint('collection_id', 'institution_id')
)


class Collection(Base, BaseMixIn):

    __tablename__ = 'collections'

    code = Column(types.String(16), nullable=False, unique=True)
    description = Column(types.String(256), nullable=False, server_default='')
    remark = deferred(Column(types.String(2048), nullable=False, server_default=''))
    data = deferred(Column(types.JSON, nullable=False, server_default='null'))

    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    group = relationship(Group, uselist=False, foreign_keys=group_id)

    attachment_file_id = Column(types.Integer, ForeignKey('fileattachments.id'), nullable=True)
    attachment_file = relationship(FileAttachment, uselist=False, foreign_keys=attachment_file_id,
                                   cascade='all, delete')
    attachment = FileAttachment.proxy('attachment_file')

    contact = deferred(Column(types.String(64), nullable=False, server_default=''))

    institutions = relationship(Institution, secondary=collection_institution_table,
                                order_by=collection_institution_table.c.id)

    samples = relationship('Sample', lazy='dynamic', back_populates='collection',
                           passive_deletes=True)

    __managing_roles__ = BaseMixIn.__managing_roles__ | {r.COLLECTION_MANAGE}
    __modifying_roles__ = __managing_roles__ | {r.COLLECTION_MODIFY}

    def __repr__(self):
        return f"Collection('{self.code}')"

    def update(self, obj):

        if isinstance(obj, dict):

            dbh = get_dbhandler()

            if 'group' in obj:
                self.group_id = dbh.get_group(obj['group']).id

            institutions = []
            if 'institution_ids' in obj:
                institutions = dbh.get_institutions_by_ids(obj['institution_ids'], None)
            elif 'institutions' in obj:
                institutions = dbh.get_institutions_by_codes(obj['institutions'], None)
            if self.institutions != institutions:
                self.institutions = institutions

            self.update_fields_with_dict(obj, additional_fields=['attachment'])

        else:
            raise RuntimeError('PROG/ERR: can only update from dict object')

    def can_upload(self, user):
        if user.has_roles(* self.__managing_roles__):
            return True
        if user.in_group(self.group):
            return True
        return False

    def __str__(self):
        return self.code

    def can_modify(self, user):
        if user.has_roles(* self.__managing_roles__):
            return True
        if user.has_roles(* self.__modifying_roles__) and user.in_group(self.group):
            return True
        return False

    def as_dict(self, export_samples=False):
        d = super().as_dict(exclude=['institutions', 'samples'])
        d['institutions'] = [inst.code for inst in self.institutions]
        if export_samples:
            d['samples'] = [samp.as_dict() for samp in self.samples]
        return d

    @classmethod
    def from_dict(cls, a_dict, dbh):
        # import IPython; IPython.embed()
        coll = super().from_dict(a_dict, dbh)
        dbh.session.flush([coll])
        if 'samples' in a_dict:
            samples = a_dict['samples']
            for samp in samples:
                dbh.Sample.from_dict(samp, dbh)
        return coll


class Sample(Base, BaseMixIn):

    __tablename__ = 'samples'

    collection_id = Column(types.Integer, ForeignKey('collections.id', ondelete='CASCADE'),
                           nullable=False, index=True)
    collection = relationship('Collection', uselist=False, back_populates='samples')

    # various code
    code = Column(types.String(16), nullable=False, unique=True, server_default='')
    acc_code = Column(types.String(15), nullable=True, unique=True)
    received_date = Column(types.Date, nullable=False)

    sequence_name = Column(types.String(63), nullable=True, index=True, unique=True)

    species_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    species = EK.proxy('species_id', '@SPECIES')

    passage_id = Column(types.Integer, nullable=False, server_default='0')
    passage = EK.proxy('passage_id', '@PASSAGE')

    collection_date = Column(types.Date, index=True, nullable=False)
    location = Column(types.String(64), nullable=False, index=True, server_default='')
    location_info = Column(types.String(128), nullable=False, server_default='')

    host_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    host = EK.proxy('host_id', '@SPECIES')

    host_info = Column(types.String(64), nullable=False, server_default='')
    host_gender = Column(types.String(1), nullable=False, server_default='X')
    host_age = Column(types.Float, nullable=False, server_default='0')

    host_occupation_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    host_occupation = EK.proxy('host_occupation_id', '@HOST_OCCUPATION')

    host_status_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    host_status = EK.proxy('host_status_id', '@HOST_STATUS')

    host_severity = Column(types.Integer, nullable=False, server_default='-1')

    infection_date = Column(types.Date, nullable=True)
    symptom_date = Column(types.Date, nullable=True)
    symptoms = Column(types.String(128), nullable=False, server_default='')

    category_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    category = EK.proxy('category_id', '@CATEGORY')

    specimen_type_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    specimen_type = EK.proxy('specimen_type_id', '@SPECIMEN_TYPE')

    outbreak = Column(types.String(64), nullable=False, server_default='')
    last_vaccinated_date = Column(types.Date, nullable=True)
    last_vaccinated_info = Column(types.String(64), nullable=False, server_default='')
    treatment = Column(types.String(64), nullable=False, server_default='')

    viral_load = Column(types.Float, nullable=False, server_default='-1')
    ct_target1 = Column(types.Float, nullable=False, server_default='-1')
    ct_target2 = Column(types.Float, nullable=False, server_default='-1')
    ct_target3 = Column(types.Float, nullable=False, server_default='-1')
    ct_target4 = Column(types.Float, nullable=False, server_default='-1')
    ct_host1 = Column(types.Float, nullable=False, server_default='-1')
    ct_host2 = Column(types.Float, nullable=False, server_default='-1')

    ct_method_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    ct_method = EK.proxy('ct_method_id', '@CT_METHOD')

    ct_info = Column(types.String(64), nullable=False, server_default='')

    # originating lab, where diagnostic tests were performed or samples were prepared
    originating_code = Column(types.String(32), nullable=True)

    originating_institution_id = Column(types.Integer, ForeignKey('institutions.id'), nullable=False)
    originating_institution = relationship(Institution, uselist=False, foreign_keys=originating_institution_id)

    # sampling institution, where the samples were initially taken, usually hospital
    # or health facility.
    sampling_code = Column(types.String(32), nullable=True)

    sampling_institution_id = Column(types.Integer, ForeignKey('institutions.id'), nullable=False)
    sampling_institution = relationship(Institution, uselist=False, foreign_keys=sampling_institution_id)

    related_sample_id = Column(types.Integer, ForeignKey('samples.id'), nullable=True)

    # sample identification

    host_dob = Column(types.Date, nullable=True)
    host_nik = Column(types.String(24), nullable=False, server_default='')
    host_nar = Column(types.String(24), nullable=False, server_default='')

    remark = deferred(Column(types.Text, nullable=False, server_default=''))
    comment = deferred(Column(types.Text, nullable=False, server_default=''))

    attachment_file_id = Column(types.Integer, ForeignKey('fileattachments.id'), nullable=True)
    attachment_file = relationship(FileAttachment, uselist=False, foreign_keys=attachment_file_id,
                                   cascade='all, delete')
    attachment = FileAttachment.proxy('attachment_file')

    flag = Column(types.Integer, nullable=False, server_default='0')
    extdata = deferred(Column(types.JSON, nullable=False, server_default='null'))

    additional_files = relationship(FileAttachment, secondary="samples_files", cascade='all, delete',
                                    collection_class=attribute_mapped_collection('id'),
                                    order_by=FileAttachment.filename)

    platepositions = relationship('PlatePosition', back_populates='sample',
                                  passive_deletes=True)

    sequences = relationship('Sequence', lazy='dynamic', back_populates='sample',
                             passive_deletes=True)

    __table_args__ = (
        UniqueConstraint('originating_code', 'originating_institution_id'),
        UniqueConstraint('sampling_code', 'sampling_institution_id'),
    )

    __ek_fields__ = ['species', 'passage', 'host', 'host_status', 'host_occupation',
                     'specimen_type', 'ct_method', 'category']

    __managing_roles__ = BaseMixIn.__managing_roles__ | {r.SAMPLE_MANAGE}
    __modifying_roles__ = __managing_roles__ | {r.SAMPLE_MODIFY}

    def __repr__(self):
        return f"Sample('{self.code}')"

    def update(self, obj):

        if isinstance(obj, dict):

            # for any empty string, remove the reference to fields that are nullable

            dbh = get_dbhandler()

            if 'collection' in obj:
                self.collection_id = dbh.get_collections_by_codes(obj['collection'], groups=None,
                                                                  ignore_acl=True)[0].id

            if 'originating_institution' in obj:
                self.originating_institution_id = dbh.get_institutions_by_codes(
                    obj['originating_institution'], None, raise_if_empty=True)[0].id

            if 'sampling_institution' in obj:
                self.sampling_institution_id = dbh.get_institutions_by_codes(
                    obj['sampling_institution'], None, raise_if_empty=True)[0].id

            now = datetime.date.today()
            for f in ['collection_date', 'received_date', 'host_dob']:
                convert_date(obj, f, now)

            self.update_fields_with_dict(obj, additional_fields=['attachment'])
            self.update_ek_with_dict(obj, dbh=dbh)

        else:
            raise RuntimeError('PROG/ERR: can only update from dict object')

    def __str__(self):
        return self.code

    def as_dict(self):
        return super().as_dict(exclude=['sequences', 'additional_files', 'platepositions'])

    def update_sequence_name(self):
        if self.species and self.host and self.location and self.acc_code and self.collection_date:
            # only update sequence_name if all fields are filled
            if sequence_name := nomenclature.create_name(self.species, self.host, self.location,
                                                         self.acc_code, self.collection_date):
                # # only update if sequence_name is constructed properly
                self.sequence_name = sequence_name
            else:
                self.sequence_name = None
        return self.sequence_name

    # access control

    def can_modify(self, user):
        if user.has_roles(* self.__managing_roles__):
            return True
        if user.has_roles(* self.__modifying_roles__) and user.in_group(self.collection.group):
            return True
        return False

    # aux methods

    def get_related_platepositions(self):
        """return [ (plate, position), ... ] related to plates"""
        dbsess = object_session(self)
        return dbsess.execute(
            select(PlatePosition, Plate).
            join(Plate).
            filter(PlatePosition.sample_id == self.id)).all()

    def get_related_runs(self):
        """return [ (run, plateposition, plate), ...]"""
        dbsess = object_session(self)
        return dbsess.execute(
            select(SequencingRun, SequencingRunPlate, Plate, PlatePosition).
            join(SequencingRunPlate, SequencingRunPlate.sequencingrun_id == SequencingRun.id).
            join(Plate, Plate.id == SequencingRunPlate.plate_id).
            join(PlatePosition, PlatePosition.plate_id == Plate.id).
            filter(PlatePosition.sample_id == self.id)).all()


sample_file_table = Table(
    'samples_files', metadata,
    Column('id', types.Integer, Identity(), primary_key=True),
    Column('sample_id', types.Integer, ForeignKey('samples.id', ondelete='CASCADE'),
           index=True, nullable=False),
    Column('file_id', types.Integer, ForeignKey('fileattachments.id', ondelete='CASCADE'),
           nullable=False),
    UniqueConstraint('sample_id', 'file_id')
)


class PlatePosition(Base, BaseMixIn):

    __tablename__ = 'platepositions'

    plate_id = Column(types.Integer, ForeignKey('plates.id', ondelete='CASCADE'),
                      index=True, nullable=False)
    plate = relationship("Plate", uselist=False, foreign_keys=plate_id, back_populates='positions')

    sample_id = Column(types.Integer, ForeignKey('samples.id'), index=True, nullable=False)
    sample = relationship(Sample, uselist=False, foreign_keys=sample_id, back_populates='platepositions')

    # position will be 384:A01 -> P24, 96: A01 -> H12
    position = Column(types.String(3), nullable=False, server_default='')
    value = Column(types.Float, nullable=False, server_default='-1')
    volume = Column(types.Float, nullable=False, server_default='-1')
    note = Column(types.String(31), nullable=True)

    __table_args__ = (
        UniqueConstraint('plate_id', 'position'),
    )

    def __repr__(self):
        return f"PlatePosition(plate_id={self.plate_id}, sample_id={self.sample_id}, {self.position})"


class Plate(Base, BaseMixIn):

    __tablename__ = 'plates'

    user_id = Column(types.Integer, ForeignKey('users.id'), nullable=False)
    user = relationship(User, uselist=False, foreign_keys=user_id)

    # primary group of user
    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    group = relationship(Group, uselist=False, foreign_keys=group_id)

    code = Column(types.String(32), nullable=False, unique=True, server_default='')
    date = Column(types.Date, nullable=False, server_default=func.current_date())

    specimen_type_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    specimen_type = EK.proxy('specimen_type_id', '@SPECIMEN_TYPE')

    experiment_type_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    experiment_type = EK.proxy('experiment_type_id', '@EXPERIMENT_TYPE')

    storage = deferred(Column(types.String(64), nullable=False, server_default=''))
    remark = deferred(Column(types.Text, nullable=False, server_default=''))

    attachment_file_id = Column(types.Integer, ForeignKey('fileattachments.id'), nullable=True)
    attachment_file = relationship(FileAttachment, uselist=False, foreign_keys=attachment_file_id,
                                   cascade='all, delete')
    attachment = FileAttachment.proxy('attachment_file')

    additional_files = relationship(FileAttachment, secondary="plates_files", cascade='all, delete',
                                    collection_class=attribute_mapped_collection('id'),
                                    order_by=FileAttachment.filename)

    positions = relationship(PlatePosition, order_by='PlatePosition.id', passive_deletes=True,
                             back_populates='plate')

    sequencingruns = relationship('SequencingRunPlate', order_by='sequencingrunplates.c.plate_id',
                                  back_populates='plate')

    __ek_fields__ = ['specimen_type', 'experiment_type']

    __managing_roles__ = BaseMixIn.__managing_roles__ | {r.PLATE_MANAGE}
    __modifying_roles__ = __managing_roles__ | {r.PLATE_MODIFY}

    #
    # using column_property interferes with auto-correlation when using select(Plate, PlatePosition)
    # @declared_attr
    # def has_layout(self):
    #    return column_property(exists().where(PlatePosition.plate_id == self.id))
    #

    def has_layout(self):
        return object_session(self).query(
            exists().where(PlatePosition.plate_id == self.id)
        ).scalar()

    def __repr__(self):
        return f"Plate('{self.code}')"

    def update(self, obj):

        if isinstance(obj, dict):

            dbh = get_dbhandler()

            if 'user' in obj:
                print(obj['user'])
                obj['user_id'] = dbh.get_user(obj['user']).id

            if 'group' in obj:
                obj['group_id'] = dbh.get_group(obj['group']).id

            convert_date(obj, 'date')

            self.update_fields_with_dict(obj, additional_fields=['attachment'])
            self.update_ek_with_dict(obj, dbh=dbh)

        else:
            raise RuntimeError('PROG/ERR: can only update from dict object')

    def __str__(self):
        return self.code

    def can_modify(self, user):
        if user.has_roles(* self.__managing_roles__):
            return True
        if user.has_roles(* self.__modifying_roles__) and user.in_group(self.group):
            return True
        return False

    def add_positions(self, positions):
        session = object_session(self)
        empty = Sample.query(object_session(self)).filter(Sample.code == '-').one()
        platepositions = []
        for pos in positions:
            platepos = PlatePosition(plate_id=self.id, sample_id=empty.id, position=pos)
            session.add(platepos)
            platepositions.append(platepos)
        return platepos

    @classmethod
    def from_dict(cls, a_dict, dbh):
        plate = super().from_dict(a_dict, dbh)
        dbh.session().flush([plate])
        for pp in a_dict['positions']:
            # get sample_id first
            sample = dbh.get_samples_by_codes(pp[0], groups=None, ignore_acl=True)[0]
            d = dict(plate_id=plate.id, sample_id=sample.id, position=pp[1], value=pp[2],
                     volume=pp[3], note=pp[4])
            PlatePosition.from_dict(d, dbh)

    def as_dict(self):
        d = super().as_dict(exclude=['positions', 'sequencingruns', 'additional_files'])
        d['positions'] = [[p.sample.code, p.position, p.value, p.volume, p.note] for p in self.positions]
        d['additional_files'] = [f.as_dict() for f in self.additional_files]
        return d


plate_file_table = Table(
    'plates_files', metadata,
    Column('id', types.Integer, Identity(), primary_key=True),
    Column('plate_id', types.Integer, ForeignKey('plates.id', ondelete='CASCADE'),
           index=True, nullable=False),
    Column('file_id', types.Integer, ForeignKey('fileattachments.id', ondelete='CASCADE'),
           nullable=False),
    UniqueConstraint('plate_id', 'file_id')
)


class SequencingRun(Base, BaseMixIn):
    """
    This class represent a libprep + sequencing run
    """

    __tablename__ = 'sequencingruns'

    code = Column(types.String(16), nullable=False, unique=True, server_default='')
    serial = Column(types.String(48), nullable=False, unique=True, server_default='')
    date = Column(types.Date, nullable=False, server_default=func.current_date())

    # primary group of user
    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    group = relationship(Group, uselist=False, foreign_keys=group_id)

    sequencing_provider_id = Column(types.Integer, ForeignKey('institutions.id'), nullable=False)
    sequencing_provider = relationship(Institution, uselist=False, foreign_keys=sequencing_provider_id)

    sequencing_kit_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    sequencing_kit = EK.proxy('sequencing_kit_id', '@SEQUENCING_KIT')

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

    additional_files = relationship(FileAttachment, secondary="sequencingruns_files", cascade='all, delete',
                                    collection_class=attribute_mapped_collection('id'),
                                    order_by=FileAttachment.filename)

    sequences = relationship('Sequence', lazy='dynamic', back_populates='sequencingrun',
                             passive_deletes=True)

    plates = relationship('SequencingRunPlate', order_by='sequencingrunplates.c.plate_id',
                          back_populates='sequencingrun')

    __ek_fields__ = ['sequencing_kit']

    __managing_roles__ = BaseMixIn.__managing_roles__ | {r.SEQUENCINGRUN_MANAGE}
    __modifying_roles__ = __managing_roles__ | {r.SEQUENCINGRUN_MODIFY}

    def __str__(self):
        return self.code

    def __repr__(self):
        return f"SequencingRun('{self.code}')"

    def update(self, obj):

        if isinstance(obj, dict):

            dbh = get_dbhandler()

            if 'group' in obj:
                obj['group_id'] = dbh.get_group(obj['group']).id

            if 'sequencing_provider' in obj:
                self.sequencing_provider_id = dbh.get_institutions_by_codes(
                    obj['sequencing_provider'], None, raise_if_empty=True)[0].id

            convert_date(obj, 'date')

            self.update_fields_with_dict(obj, additional_fields=['depthplots', 'qcreport', 'screenshot'])
            self.update_ek_with_dict(obj, dbh=dbh)

        else:
            raise RuntimeError('PROG/ERR: can only update from dict object')

    def as_dict(self, exclude=None):
        d = super().as_dict(exclude={'sequences', 'plates', 'additional_files'})
        d['plates'] = [[p.plate.code, p.adapterindex, p.lane, p.note] for p in self.plates]
        return d

    def can_modify(self, user):
        if user.has_roles(* self.__managing_roles__):
            return True
        if user.has_roles(* self.__modifying_roles__):  # and user.in_group(self.group):
            return True
        return False


sequencingrun_file_table = Table(
    'sequencingruns_files', metadata,
    Column('id', types.Integer, Identity(), primary_key=True),
    Column('sequencingrun_id', types.Integer, ForeignKey('sequencingruns.id', ondelete='CASCADE'),
           index=True, nullable=False),
    Column('file_id', types.Integer, ForeignKey('fileattachments.id', ondelete='CASCADE'), nullable=False),
    UniqueConstraint('sequencingrun_id', 'file_id')
)


class SequencingRunPlate(Base, BaseMixIn):

    __tablename__ = 'sequencingrunplates'

    sequencingrun_id = Column(types.Integer, ForeignKey('sequencingruns.id', ondelete='CASCADE'),
                              index=True, nullable=False)
    sequencingrun = relationship(SequencingRun, uselist=False, foreign_keys=sequencingrun_id,
                                 back_populates='plates')

    plate_id = Column(types.Integer, ForeignKey('plates.id', ondelete='CASCADE'),
                      index=True, nullable=False)
    plate = relationship(Plate, uselist=False, foreign_keys=plate_id,
                         back_populates='sequencingruns')

    adapterindex_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    adapterindex = EK.proxy('adapterindex_id', '@ADAPTERINDEX')

    lane = Column(types.Integer, nullable=False, server_default='1')

    note = Column(types.Text, nullable=True)

    __table_args__ = (
        UniqueConstraint('sequencingrun_id', 'plate_id'),
        UniqueConstraint('sequencingrun_id', 'adapterindex_id', 'lane'),
    )


class Sequence(Base, BaseMixIn):
    """
    """

    __tablename__ = 'sequences'

    # referencing

    sequencingrun_id = Column(types.Integer, ForeignKey('sequencingruns.id', ondelete='CASCADE'),
                              index=True, nullable=False)
    sequencingrun = relationship(SequencingRun, uselist=False, back_populates='sequences')

    sample_id = Column(types.Integer, ForeignKey('samples.id', ondelete='CASCADE'),
                       index=True, nullable=False)
    sample = relationship(Sample, uselist=False, back_populates='sequences')

    method_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    method = EK.proxy('method_id', '@METHOD')

    accid = Column(types.String(32), nullable=True, index=True, unique=True)
    submission_date = Column(types.Date, nullable=True)

    sequence = Column(types.Text, nullable=False, server_default='')
    avg_depth = Column(types.Integer, nullable=False, server_default='-1')

    depthplot_file_id = Column(types.Integer, ForeignKey('fileattachments.id'), nullable=True)
    depthplot_file = relationship(FileAttachment, uselist=False, foreign_keys=depthplot_file_id,
                                  cascade='all, delete')
    depthplot = FileAttachment.proxy('depthplot_file')

    length = Column(types.Integer, nullable=False, server_default='-1')
    gaps = Column(types.Integer, nullable=False, server_default='-1')
    base_N = Column(types.Integer, nullable=False, server_default='-1')
    lineage_1 = Column(types.String(24), nullable=False, server_default='')
    prob_1 = Column(types.Float, nullable=False, server_default='-1')
    lineage_2 = Column(types.String(24), nullable=False, server_default='')
    prob_2 = Column(types.Float, nullable=False, server_default='-1')
    lineage_3 = Column(types.String(24), nullable=False, server_default='')
    prob_3 = Column(types.Float, nullable=False, server_default='-1')

    refid = Column(types.String(32), nullable=True)
    point_mutations = Column(types.Integer, nullable=False, server_default='-1')
    aa_mutations = Column(types.Integer, nullable=False, server_default='-1')
    inframe_gaps = Column(types.Integer, nullable=False, server_default='-1')
    outframe_gaps = Column(types.Integer, nullable=False, server_default='-1')
    reads_raw = Column(types.Integer, nullable=False, server_default='-1')
    reads_optical_dedup = Column(types.Integer, nullable=False, server_default='-1')
    reads_trimmed = Column(types.Integer, nullable=False, server_default='-1')
    reads_pp_mapped = Column(types.Integer, nullable=False, server_default='-1')
    reads_pcr_dedup = Column(types.Integer, nullable=False, server_default='-1')
    reads_consensus_mapped = Column(types.Integer, nullable=False, server_default='-1')
    reads_mean_insertsize = Column(types.Integer, nullable=False, server_default='-1')
    reads_med_insertsize = Column(types.Integer, nullable=False, server_default='-1')
    reads_stddev_insertsize = Column(types.Integer, nullable=False, server_default='-1')

    snvs = deferred(Column(types.JSON, nullable=False, server_default='null'))
    aa_change = deferred(Column(types.JSON, nullable=False, server_default='null'))

    authorship = deferred(Column(types.Text, nullable=False, server_default=''))
    remarks = deferred(Column(types.Text, nullable=False, server_default=''))

    __ek_fields__ = ['method']

    def __repr__(self):
        return f"Sequence(sample='{self.code}')"

    def update(self, obj):

        if isinstance(obj, dict):

            dbh = get_dbhandler()

            if 'sequencingrun' in obj:
                self.sample_id = dbh.get_sequencingrun_by_code(obj['sequencingrun']).id

            if 'sample' in obj:
                self.sample_id = dbh.get_samples_by_lab_code(obj['sample']).id

            convert_date(obj, 'submission_date')

            self.update_fields_with_dict(obj)
            self.update_ek_with_dict(obj, dbh=dbh)

        else:
            raise RuntimeError('PROG/ERR: can only update from dict object')

# EOF
