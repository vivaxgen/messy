
from rhombus.lib.utils import cerr, cout, get_dbhandler
from rhombus.models.core import (Base, BaseMixIn, metadata, deferred, relationship,
                                 registered, declared_attr, column_property)
from rhombus.models.ek import EK
from rhombus.models.user import Group, User
from rhombus.models.fileattach import FileAttachment
from rhombus.models.auxtypes import GUID
import messy.lib.roles as r
from messy.lib import nomenclature
import dateutil.parser
import datetime
from sqlalchemy.sql import func, False_
from sqlalchemy.orm import object_session
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy import (exists, Table, Column, types, ForeignKey, UniqueConstraint,
                        Identity, select)


__version__ = '20210817'

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


class Institution(BaseMixIn, Base):

    __tablename__ = 'institutions'

    code = Column(types.String(24), nullable=False, unique=True)
    alt_codes = Column(types.String(47), nullable=True, unique=True)
    name = Column(types.String(128), nullable=False, unique=True)
    address = deferred(Column(types.String(128), nullable=False, server_default=''))
    zipcode = Column(types.String(8), nullable=False, server_default='')
    contact = Column(types.String(64), nullable=False, server_default='')
    remark = deferred(Column(types.Text, nullable=False, server_default=''))
    refctrl = Column(types.Boolean, nullable=False, server_default=False_())

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


class Collection(BaseMixIn, Base):

    __tablename__ = 'collections'

    code = Column(types.String(16), nullable=False, unique=True)
    uuid = Column(GUID(), nullable=False, unique=True)
    description = Column(types.String(256), nullable=False, server_default='')
    remark = deferred(Column(types.Text, nullable=False, server_default=''))
    data = deferred(Column(types.JSON, nullable=False, server_default='null'))

    refctrl = Column(types.Boolean, nullable=False, server_default=False_())
    public = Column(types.Boolean, nullable=False, server_default=False_())

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

    additional_files = relationship(FileAttachment, secondary="collections_files", cascade='all, delete',
                                    collection_class=attribute_mapped_collection('id'),
                                    order_by=FileAttachment.filename)

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

            # check if UUID still  None, then create one
            if self.uuid is None:
                self.uuid = GUID.new()
        else:
            raise RuntimeError('PROG/ERR: can only update from dict object')

        return self

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

    def get_submitting_institution_name(self):
        return '; '.join(inst.name for inst in self.institutions)

    def get_submitting_institution_addr(self):
        return '; '.join(inst.address for inst in self.institutions)

    # JSON data access

    def get_submitter(self):
        return self.data.get('submitter', '') if self.data else ''

    def get_authors(self):
        return self.data.get('authors', {}) if self.data else {}


collection_file_table = Table(
    'collections_files', metadata,
    Column('id', types.Integer, Identity(), primary_key=True),
    Column('collection_id', types.Integer, ForeignKey('collections.id', ondelete='CASCADE'),
           index=True, nullable=False),
    Column('file_id', types.Integer, ForeignKey('fileattachments.id', ondelete='CASCADE'),
           nullable=False),
    UniqueConstraint('collection_id', 'file_id')
)


class Sample(BaseMixIn, Base):

    __tablename__ = 'samples'

    collection_id = Column(types.Integer, ForeignKey('collections.id', ondelete='CASCADE'),
                           nullable=False, index=True)
    collection = relationship('Collection', uselist=False, back_populates='samples')

    type = Column(types.Integer, nullable=False, server_default='0')

    # various code
    code = Column(types.String(16), nullable=False)
    uuid = Column(GUID(), nullable=False, unique=True)
    acc_code = Column(types.String(31), nullable=True, unique=True)

    related_sample_id = Column(types.Integer, ForeignKey('samples.id'), nullable=True)

    species_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    species = EK.proxy('species_id', '@SPECIES', 'no-species')

    passage_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    passage = EK.proxy('passage_id', '@PASSAGE', default='original')

    collection_date = Column(types.Date, index=True, nullable=False)
    location = Column(types.String(64), nullable=False, index=True, server_default='')
    location_info = Column(types.String(128), nullable=False, server_default='')

    latitude = Column(types.Float, nullable=True)
    longitude = Column(types.Float, nullable=True)
    altitude = Column(types.Float, nullable=True)

    day = Column(types.Integer, nullable=False, server_default='0')

    category_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    category = EK.proxy('category_id', '@CATEGORY')

    specimen_type_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    specimen_type = EK.proxy('specimen_type_id', '@SPECIMEN_TYPE')

    # ct_method_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    # ct_method = EK.proxy('ct_method_id', '@CT_METHOD')

    # ct_info = Column(types.String(64), nullable=False, server_default='')

    received_date = Column(types.Date, nullable=True)

    # originating lab, where diagnostic tests were performed or samples were prepared
    originating_code = Column(types.String(32), nullable=True)
    originating_institution_id = Column(types.Integer, ForeignKey('institutions.id'), nullable=False)
    originating_institution = relationship(Institution, uselist=False, foreign_keys=originating_institution_id)

    # sampling institution, where the samples were initially taken, usually hospital
    # or health facility.
    sampling_code = Column(types.String(32), nullable=True)
    sampling_institution_id = Column(types.Integer, ForeignKey('institutions.id'), nullable=False)
    sampling_institution = relationship(Institution, uselist=False, foreign_keys=sampling_institution_id)

    # host related information
    host_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    host = EK.proxy('host_id', '@SPECIES')

    host_info = Column(types.String(64), nullable=False, server_default='')

    host_status_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    host_status = EK.proxy('host_status_id', '@HOST_STATUS')

    host_severity = Column(types.Integer, nullable=False, server_default='-1')

    # space-delimited symptom list
    symptoms = Column(types.String(128), nullable=False, server_default='')

    # space-delimited comorbid list
    comorbids = Column(types.String(128), nullable=False, server_default='')
    treatment = Column(types.String(64), nullable=False, server_default='')

    # the following fields can be used case-by-case depending on collections or studies

    string_1 = Column(types.String(8), nullable=False, server_default='')
    string_2 = Column(types.String(8), nullable=False, server_default='')
    int_1 = Column(types.Integer, nullable=False, server_default='-1')
    int_2 = Column(types.Integer, nullable=False, server_default='-1')

    remark = deferred(Column(types.Text, nullable=False, server_default=''))
    comment = deferred(Column(types.Text, nullable=False, server_default=''))

    attachment_file_id = Column(types.Integer, ForeignKey('fileattachments.id'), nullable=True)
    attachment_file = relationship(FileAttachment, uselist=False, foreign_keys=attachment_file_id,
                                   cascade='all, delete')
    attachment = FileAttachment.proxy('attachment_file')

    flag = Column(types.Integer, nullable=False, server_default='0')
    refctrl = Column(types.Boolean, nullable=False, server_default=False_())
    public = Column(types.Boolean, nullable=False, server_default=False_())

    extdata = deferred(Column(types.JSON, nullable=False, server_default='null'))

    additional_files = relationship(FileAttachment, secondary="samples_files", cascade='all, delete',
                                    collection_class=attribute_mapped_collection('id'),
                                    order_by=FileAttachment.filename)

    platepositions = relationship('PlatePosition', back_populates='sample',
                                  passive_deletes=True)

    __table_args__ = (
        UniqueConstraint('collection_id', 'code'),
        UniqueConstraint('originating_code', 'originating_institution_id'),
        UniqueConstraint('sampling_code', 'sampling_institution_id'),
    )

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": 0,
    }

    #__ek_fields__ = ['species', 'passage', 'host', 'host_status', 'host_occupation',
    #                 'specimen_type', 'category']

    __managing_roles__ = BaseMixIn.__managing_roles__ | {r.SAMPLE_MANAGE}
    __modifying_roles__ = __managing_roles__ | {r.SAMPLE_MODIFY}

    def init_instance(self):
        self.passage = None

    __init_funcs__ = [
        init_instance,
    ]

    def __repr__(self):
        return f"Sample('{self.code}')"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def update(self, obj):

        if isinstance(obj, dict):

            # for any empty string, remove the reference to fields that are nullable

            dbh = get_dbhandler()

            if type(collection := obj.get('collection', None)) == str:
                self.collection_id = dbh.get_collections_by_codes(collection, groups=None,
                                                                  ignore_acl=True)[0].id
                del obj['collection']

            if type(inst := obj.get('originating_institution', None)) == str:
                self.originating_institution_id = dbh.get_institutions_by_codes(
                    inst, None, raise_if_empty=True)[0].id
                del obj['originating_institution']

            if type(inst := obj.get('sampling_institution', None)) == str:
                self.sampling_institution_id = dbh.get_institutions_by_codes(
                    inst, None, raise_if_empty=True)[0].id
                del obj['sampling_institution']

            now = datetime.date.today()
            for f in ['collection_date', 'received_date', 'host_dob']:
                convert_date(obj, f, now)

            self.update_fields_with_dict(obj, additional_fields=['attachment', 'collection',
                                         'originating_institution', 'sampling_institution'])
            self.update_ek_with_dict(obj, dbh=dbh)

            # check if UUID still  None, then create one
            if self.uuid is None:
                self.uuid = GUID.new()

        else:
            raise RuntimeError('PROG/ERR: can only update from dict object')

        return self

    def __str__(self):
        return self.code

    def as_dict(self):
        return super().as_dict(exclude=['sequences', 'additional_files', 'platepositions'])

    @classmethod
    def from_dict(cls, a_dict, dbh):
        sample = super().from_dict(a_dict, dbh)
        if not sample.passage_id:
            sample.passage = 'original'
        if not sample.species_id:
            sample.species = 'no-species'
        return sample

    # access control

    def can_modify(self, user):
        if user.has_roles(* self.__managing_roles__):
            return True
        if user.has_roles(* self.__modifying_roles__) and user.in_group(self.collection.group):
            return True
        return False

    # aux methods

    def get_related_platepositions(self, func=None):
        """return [ (plate, position), ... ] related to plates"""
        dbsess = object_session(self)
        q = (
            select(PlatePosition, Plate).
            join(Plate).
            filter(PlatePosition.sample_id == self.id)
        )
        if func:
            q = func(q)
        return dbsess.execute(q).all()


sample_file_table = Table(
    'samples_files', metadata,
    Column('id', types.Integer, Identity(), primary_key=True),
    Column('sample_id', types.Integer, ForeignKey('samples.id', ondelete='CASCADE'),
           index=True, nullable=False),
    Column('file_id', types.Integer, ForeignKey('fileattachments.id', ondelete='CASCADE'),
           nullable=False),
    UniqueConstraint('sample_id', 'file_id')
)


class PlatePosition(BaseMixIn, Base):

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

    def clone_sample(self):
        return PlatePosition(sample_id=self.sample_id, position=self.position)


class Plate(BaseMixIn, Base):

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

    refctrl = Column(types.Boolean, nullable=False, server_default=False_())

    additional_files = relationship(FileAttachment, secondary="plates_files", cascade='all, delete',
                                    collection_class=attribute_mapped_collection('id'),
                                    order_by=FileAttachment.filename)

    positions = relationship(PlatePosition, order_by='PlatePosition.id', passive_deletes=True,
                             back_populates='plate')

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

    def get_related_samples(self, scalar=False):
        if scalar:
            q = select(func.count(Sample.id))
        else:
            q = select(Sample)
        q = (
            q.
            join(PlatePosition).
            filter(~Sample.code.in_(['-', '*', 'NTC1', 'NTC2', 'NTC3', 'NTC4'])).
            filter(PlatePosition.plate_id == self.id)
        )
        if scalar:
            return object_session(self).scalar(q)
        return object_session(self).execute(q).scalars()

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
        for pp in a_dict.get('positions', []):
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


# EOF
