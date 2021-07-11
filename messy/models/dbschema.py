
from rhombus.lib.utils import cerr, cout, get_dbhandler
from rhombus.models.core import (Base, BaseMixIn, metadata, deferred, relationship,
                                 registered, backref, declared_attr, column_property)
from rhombus.models.ek import EK
from rhombus.models.user import Group, User
from rhombus.models.fileattach import FileAttachment
import messy.lib.roles as r
import dateutil.parser
from sqlalchemy.sql import func
from sqlalchemy import (exists, Table, Column, types, ForeignKey, UniqueConstraint,
                        Identity)

import io

__version__ = '20210711'

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


def dict_from_fields(obj, fields, exclude=None):
    d = {}
    for f in fields:
        if exclude and f in exclude:
            continue
        d[f] = str(getattr(obj, f))
    return d


def convert_date(obj, field):
    if field in obj and isinstance(obj[field], str):
        obj[field] = dateutil.parser.parse(obj[field])


class Institution(Base, BaseMixIn):

    __tablename__ = 'institutions'

    code = Column(types.String(24), nullable=False, unique=True)
    name = Column(types.String(128), nullable=False, unique=True)
    address = deferred(Column(types.String(128), nullable=False, server_default=''))
    zipcode = Column(types.String(8), nullable=False, server_default='')
    contact = Column(types.String(64), nullable=False, server_default='')
    remark = deferred(Column(types.String(2048), nullable=False, server_default=''))

    __searchable__ = ['code', 'name', 'address']

    def update(self, obj):

        if isinstance(obj, dict):
            self.update_fields_with_dict(obj)

        else:
            raise RuntimeError('PROG/ERR: can only update from dict object')

    def as_dict(self):
        d = super().as_dict()
        d.update(self.dict_from_fields())
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
    attachment_file = relationship(FileAttachment, uselist=False, foreign_keys=attachment_file_id)
    attachment = FileAttachment.proxy('attachment_file')

    contact = deferred(Column(types.String(64), nullable=False, server_default=''))

    institutions = relationship(Institution, secondary=collection_institution_table,
                                order_by=collection_institution_table.c.id)

    def update(self, obj):

        if isinstance(obj, dict):

            dbh = get_dbhandler()

            if 'group' in obj:
                self.group_id = dbh.get_group_by_code(obj['group']).id

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
        if user.has_roles(r.SYSADM, r.DATAADM, r.COLLECTION_MODIFY):
            return True
        if user.in_group(self.group):
            return True
        return False

    def __str__(self):
        return self.code


class Sample(Base, BaseMixIn):

    __tablename__ = 'samples'

    collection_id = Column(types.Integer, ForeignKey('collections.id', ondelete='CASCADE'),
                           nullable=False, index=True)
    collection = relationship(Collection, uselist=False,
                              backref=backref('samples', lazy='dynamic', passive_deletes=True))

    # various code
    code = Column(types.String(16), nullable=False, unique=True, server_default='')
    acc_code = Column(types.String(15), nullable=True, unique=True)
    received_date = Column(types.Date, nullable=False)

    sequence_name = Column(types.String(63), nullable=True, unique=True)

    species_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    species = EK.proxy('species_id', '@SPECIES')

    passage_id = Column(types.Integer, nullable=False, server_default='0')
    passage = EK.proxy('passage_id', '@PASSAGE')

    collection_date = Column(types.Date, nullable=False)
    location = Column(types.String(64), nullable=False, index=True, server_default='')
    location_info = Column(types.String(128), nullable=False, server_default='')

    host_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    host = EK.proxy('host_id', '@HOST')

    host_info = Column(types.String(64), nullable=False, server_default='')
    host_gender = Column(types.String(1), nullable=False, server_default='X')
    host_age = Column(types.Float, nullable=False, server_default='0')

    host_occupation_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    host_occupation = EK.proxy('host_occupation_id', '@HOST_OCCUPATION')

    host_status_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    host_status = EK.proxy('host_status_id', '@HOST_STATUS')

    host_severity = Column(types.Integer, nullable=False, server_default='-1')

    category_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    category = EK.proxy('category_id', '@CATEGORY')

    specimen_type_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    specimen_type = EK.proxy('specimen_type_id', '@SPECIMEN_TYPE')

    outbreak = Column(types.String, nullable=False, server_default='')
    last_vaccinated_date = Column(types.Date, nullable=True)
    last_vaccinated_info = Column(types.String, nullable=False, server_default='')
    treatment = Column(types.String(64), nullable=False, server_default='')

    viral_load = Column(types.Float, nullable=False, server_default='-1')
    ct_value = Column(types.Float, nullable=False, server_default='-1')

    ct_method_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    ct_method = EK.proxy('ct_method_id', '@CT_METHOD')

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
    attachment_file = relationship(FileAttachment, uselist=False, foreign_keys=attachment_file_id)
    attachment = FileAttachment.proxy('attachment_file')

    flag = Column(types.Integer, nullable=False, server_default='0')
    extdata = deferred(Column(types.JSON, nullable=False, server_default='null'))

    __table_args__ = (
        UniqueConstraint('originating_code', 'originating_institution_id'),
        UniqueConstraint('sampling_code', 'sampling_institution_id'),
    )

    __ek_fields__ = ['species', 'passage', 'host', 'host_status', 'host_occupation',
                     'specimen_type', 'ct_method', 'category']

    def update(self, obj):

        if isinstance(obj, dict):

            # for any empty string, remove the reference to fields that are nullable

            dbh = get_dbhandler()

            if 'collection' in obj:
                self.collection_id = dbh.get_collections_by_code(obj['collection']).id

            if 'originating_institution' in obj:
                self.originating_institution_id = dbh.get_institutions_by_codes(
                    obj['originating_institution'], None, raise_if_empty=True)[0].id

            if 'sampling_institution' in obj:
                self.sampling_institution_id = dbh.get_institutions_by_codes(
                    obj['sampling_institution'], None, raise_if_empty=True)[0].id

            for f in ['collection_date', 'received_data', 'host_dob']:
                convert_date(obj, f)

            self.update_fields_with_dict(obj, additional_fields=['attachment'])
            self.update_ek_with_dict(obj, dbh=dbh)

        else:
            raise RuntimeError('PROG/ERR: can only update from dict object')

    def __str__(self):
        return self.code


sample_file_table = Table(
    'samples_files', metadata,
    Column('id', types.Integer, Identity(), primary_key=True),
    Column('sample_id', types.Integer, ForeignKey('samples.id'), nullable=False),
    Column('file_id', types.Integer, ForeignKey('fileattachments.id'), nullable=False),
    UniqueConstraint('sample_id', 'file_id')
)


class PlatePosition(Base, BaseMixIn):

    __tablename__ = 'platepositions'

    plate_id = Column(types.Integer, ForeignKey('plates.id'), nullable=False)
    sample_id = Column(types.Integer, ForeignKey('samples.id'), nullable=False)

    # position will be 384:A01 -> P24, 96: A01 -> H12
    position = Column(types.String(3), nullable=False, server_default='')
    value = Column(types.Float, nullable=False, server_default='-1')
    volume = Column(types.Float, nullable=False, server_default='-1')

    __table_args__ = (
        UniqueConstraint('plate_id', 'position'),
    )


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
    experiment_type = EK.proxy('experiment_type_id', '@TREATMENT_TYPE')

    remark = deferred(Column(types.Text, nullable=False, server_default=''))

    attachment_file_id = Column(types.Integer, ForeignKey('fileattachments.id'), nullable=True)
    attachment_file = relationship(FileAttachment, uselist=False, foreign_keys=attachment_file_id)
    attachment = FileAttachment.proxy('attachment_file')

    __ek_fields__ = ['specimen_type', 'experiment_type']

    @declared_attr
    def has_layout(cls):
        return column_property(exists().where(PlatePosition.plate_id == cls.id))

    def update(self, obj):

        if isinstance(obj, dict):

            dbh = get_dbhandler()

            if 'user' in obj:
                obj['user_id'] = dbh.get_user(obj['user']).id

            if 'group' in obj:
                obj['group_id'] = dbh.get_group(obj['code']).id

            convert_date(obj, 'date')

            self.update_fields_with_dict(obj, additional_fields=['attachment'])
            self.update_ek_with_dict(obj, dbh=dbh)

        else:
            raise RuntimeError('PROG/ERR: can only update from dict object')

    def __str__(self):
        return self.code


plate_file_table = Table(
    'plates_files', metadata,
    Column('id', types.Integer, Identity(), primary_key=True),
    Column('plate_id', types.Integer, ForeignKey('plates.id'), nullable=False),
    Column('file_id', types.Integer, ForeignKey('fileattachments.id'), nullable=False),
    UniqueConstraint('plate_id', 'file_id')
)


class SequencingRun(Base, BaseMixIn):
    """
    This class represent a libprep + sequencing run
    """

    __tablename__ = 'sequencingruns'

    code = Column(types.String(16), nullable=False, unique=True, server_default='')
    serial = Column(types.String(32), nullable=False, unique=True, server_default='')
    date = Column(types.Date, nullable=False, server_default=func.current_date())

    sequencing_provider_id = Column(types.Integer, ForeignKey('institutions.id'), nullable=False)
    sequencing_provider = relationship(Institution, uselist=False, foreign_keys=sequencing_provider_id)

    sequencing_kit_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    sequencing_kit = EK.proxy('sequencing_kit_id', '@SEQUENCING_KIT')

    # pdf of depthplots, if available
    # depthplots = deferred(Column(types.LargeBinary, nullable=False, server_default=''))
    depthplots_file_id = Column(types.Integer, ForeignKey('fileattachments.id'), nullable=True)
    depthplots_file = relationship(FileAttachment, uselist=False, foreign_keys=depthplots_file_id)
    depthplots = FileAttachment.proxy('depthplots_file')

    # gzip html from multiqc, if available
    qcreport_file_id = Column(types.Integer, ForeignKey('fileattachments.id'), nullable=True)
    qcreport_file = relationship(FileAttachment, uselist=False, foreign_keys=qcreport_file_id)
    qcreport = FileAttachment.proxy('qcreport_file')

    # screenshot from the instrument, if available
    screenshot_file_id = Column(types.Integer, ForeignKey('fileattachments.id'), nullable=True)
    screenshot_file = relationship(FileAttachment, uselist=False, foreign_keys=screenshot_file_id)
    screenshot = FileAttachment.proxy('screenshot_file')

    remark = deferred(Column(types.Text, nullable=False, server_default=''))

    __ek_fields__ = ['sequencing_kit']

    def __str__(self):
        return self.code

    def __repr__(self):
        return f'<SequencingRun: {self.code}>'

    def update(self, obj):

        if isinstance(obj, dict):

            dbh = get_dbhandler()

            if 'sequencing_provider' in obj:
                self.sequencing_provider_id = dbh.get_institutions_by_code(
                    obj['collection'], None, raise_if_empty=True)[0].id

            convert_date(obj, 'date')

            self.update_fields_with_dict(obj, additional_fields=['depthplots', 'qcreport', 'screenshot'])
            self.update_ek_with_dict(obj, dbh=dbh)

        else:
            raise RuntimeError('PROG/ERR: can only update from dict object')


sequencingrun_plate_table = Table(
    'sequencingruns_plates', metadata,
    Column('id', types.Integer, Identity(), primary_key=True),
    Column('sequencingrun_id', types.Integer, ForeignKey('sequencingruns.id'), nullable=False),
    Column('plate_id', types.Integer, ForeignKey('plates.id'), nullable=False),
    UniqueConstraint('sequencingrun_id', 'plate_id')
)


sequencingrun_file_table = Table(
    'sequencingrun_files', metadata,
    Column('id', types.Integer, Identity(), primary_key=True),
    Column('sequencingrun_id', types.Integer, ForeignKey('sequencingruns.id'), nullable=False),
    Column('file_id', types.Integer, ForeignKey('fileattachments.id'), nullable=False),
    UniqueConstraint('sequencingrun_id', 'file_id')
)


class Sequence(Base, BaseMixIn):
    """
    """

    __tablename__ = 'sequences'

    # referencing

    sequencingrun_id = Column(types.Integer, ForeignKey('sequencingruns.id'), nullable=False)
    sequencingrun = relationship(SequencingRun, uselist=False,
                                 backref=backref('sequences', lazy='dynamic', passive_deletes=True))
    sample_id = Column(types.Integer, ForeignKey('samples.id'), nullable=False)
    sample = relationship(Sample, uselist=False,
                          backref=backref('sequence', lazy='dynamic', passive_deletes=True))

    method_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    method = EK.proxy('method_id', '@METHOD')

    accid = Column(types.String(32), nullable=True, unique=True)
    submission_date = Column(types.Date, nullable=True)

    sequence = Column(types.Text, nullable=False, server_default='')
    avg_depth = Column(types.Integer, nullable=False, server_default='-1')

    depthplot_file_id = Column(types.Integer, ForeignKey('fileattachments.id'), nullable=True)
    depthplot_file = relationship(FileAttachment, uselist=False, foreign_keys=depthplot_file_id)
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

    remarks = deferred(Column(types.Text, nullable=False, server_default=''))

    __ek_fields__ = ['method']

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
