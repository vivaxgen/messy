
from rhombus.models import handler as rhombus_handler
from rhombus.lib.utils import cerr, cout

# from .setup import setup

from messy.models import dbschema
from messy.lib import roles as r
from sqlalchemy import or_, and_


class MessyQueryConstructor(rhombus_handler.QueryConstructor):

    field_specs = rhombus_handler.QueryConstructor.field_specs | {
        'institution_id': dbschema.Institution.id,
        'institution': dbschema.Institution.code,
        'institution_code': dbschema.Institution.code,

        'collection_id': dbschema.Collection.id,
        'collection': dbschema.Collection.code,
        'collection_code': dbschema.Collection.code,

        'sample_id': dbschema.Sample.id,
        'sample_code': dbschema.Sample.code,
        'acc_code': dbschema.Sample.acc_code,
        'nik': dbschema.Sample.host_nik,
        'nar': dbschema.Sample.host_nar,

        'sequence': dbschema.Sample.sequence_name,
        'sequence_id': dbschema.Sequence.id,
        'accid': dbschema.Sequence.accid,

        'plate_id': dbschema.Plate.id,
        'plate_code': dbschema.Plate.code,

        'run_id': dbschema.SequencingRun.id,
        'run_code': dbschema.SequencingRun.code,
        'run_serial': dbschema.SequencingRun.serial,

        'runplate_id': dbschema.SequencingRunPlate.id,
    }


class DBHandler(rhombus_handler.DBHandler):

    # add additional class references
    FileAttachment = dbschema.FileAttachment
    Institution = dbschema.Institution
    Collection = dbschema.Collection
    Sample = dbschema.Sample
    Sequence = dbschema.Sequence
    Plate = dbschema.Plate
    PlatePosition = dbschema.PlatePosition
    SequencingRun = dbschema.SequencingRun
    SequencingRunPlate = dbschema.SequencingRunPlate

    query_constructor_class = MessyQueryConstructor

    def initdb(self, create_table=True, init_data=True, rootpasswd=None):
        """ initialize database """
        super().initdb(create_table, init_data, rootpasswd)
        if init_data:
            from .setup import setup
            setup(self)
            cerr('[messy-rbmgr] Database has been initialized')

    # add additional methods here

    def fix_result(self, query, fetch, raise_if_empty):
        if not fetch:
            return query

        res = query.all()
        if raise_if_empty and len(res) == 0:
            raise rhombus_handler.exc.NoResultFound()
        return res

    # Institutions

    def get_institutions(self, groups=None, specs=None, user=None, fetch=True, raise_if_empty=False):

        q = self.construct_query(self.Institution, specs)
        if fetch:
            q = q.order_by(self.Institution.code)

        return self.fix_result(q, fetch, raise_if_empty)

    def get_institutions_by_ids(self, ids, groups, user=None, fetch=True, raise_if_empty=False):
        return self.get_institutions(groups, [{'institution_id': ids}], user=user, fetch=fetch, raise_if_empty=raise_if_empty)

    def get_institutions_by_codes(self, codes, groups, user=None, fetch=True, raise_if_empty=False):
        return self.get_institutions(groups, [{'institution_code': codes}], user=user, fetch=fetch, raise_if_empty=raise_if_empty)

    # Collections

    def get_collections(self, groups, specs=None, user=None, fetch=True, raise_if_empty=False,
                        ignore_acl=False):

        q = self.construct_query(self.Collection, specs)

        if not ignore_acl and groups is None and user is None:
            raise ValueError('ERR: either groups or user needs to be provided!')

        if not ignore_acl and groups is None:
            if not user.has_roles(r.SYSADM, r.DATAADM, r.COLLECTION_MANAGE):
                groups = user.groups

        if groups is not None:
            # enforce security
            q = q.filter(self.Collection.group_id.in_([x[1] for x in groups]))

        if fetch:
            q = q.order_by(self.Collection.code)

        return self.fix_result(q, fetch, raise_if_empty)

    def get_collections_by_ids(self, ids, groups, user=None, fetch=True, raise_if_empty=False):
        return self.get_collections(groups, [{'collection_id': ids}], user=user, fetch=fetch,
                                    raise_if_empty=raise_if_empty)

    def get_collections_by_codes(self, codes, groups, user=None, fetch=True, raise_if_empty=False):
        return self.get_collections(groups, [{'collection_code': codes}], user=user, fetch=fetch,
                                    raise_if_empty=raise_if_empty)

    #
    # Samples

    def get_samples(self, groups, specs=None, user=None, fetch=True, raise_if_empty=False, override_security=False):

        q = self.construct_query(self.Sample, specs)

        # if groups is not None, we need to join sample with collection to get
        # all samples under collections owned by certain groups to enforce security

        if not override_security and groups is None and user is None:
            raise ValueError('ERR: either groups or user needs to be provided!')

        if not override_security and groups is None:
            if not user.has_roles(r.SYSADM, r.DATAADM, r.SAMPLE_MANAGE):
                groups = user.groups

        if groups is not None:
            q = q.join(self.Collection).filter(self.Collection.group_id.in_([x[1] for x in groups]))

        if fetch:
            q = q.order_by(self.Sample.code.desc())

        return self.fix_result(q, fetch, raise_if_empty)

    def get_samples_by_ids(self, ids, groups, user=None, fetch=True, raise_if_empty=False):
        return self.get_samples(groups, [{'sample_id': ids}], user=user, fetch=fetch, raise_if_empty=raise_if_empty)

    def get_samples_by_codes(self, codes, groups, user=None, fetch=True, raise_if_empty=False, override_security=False):
        return self.get_samples(groups, [{'sample_code': codes}], user=user, fetch=fetch, raise_if_empty=raise_if_empty,
                                override_security=override_security)

    #
    # Sequences

    def get_sequences(self, groups, specs=None, user=None, fetch=True, raise_if_empty=False):

        q = self.construct_query(self.Sequence, specs)
        if fetch:
            q = q.order_by(self.Sequence.id.desc())

        return self.fix_result(q, fetch, raise_if_empty)

    def get_sequences_by_ids(self, ids, groups, user=None, fetch=True, raise_if_empty=False):
        return self.get_sequences(groups, [{'sequence_id': ids}], user=user, fetch=fetch, raise_if_empty=raise_if_empty)

    # Plates

    def get_plates(self, groups, specs=None, user=None, fetch=True, raise_if_empty=False):

        q = self.construct_query(self.Plate, specs)
        if fetch:
            q = q.order_by(self.Plate.id.desc())

        if groups is not None:
            q = q.filter(self.Plate.group_id.in_([x[1] for x in groups]))

        return self.fix_result(q, fetch, raise_if_empty)

    def get_plates_by_ids(self, ids, groups, user=None, fetch=True, raise_if_empty=False):
        return self.get_plates(groups, [{'plate_id': ids}], user=user, fetch=fetch, raise_if_empty=raise_if_empty)

    def get_plates_by_codes(self, codes, groups, user=None, fetch=True, raise_if_empty=False):
        return self.get_plates(groups, [{'plate_code': codes}], user=user, fetch=fetch, raise_if_empty=raise_if_empty)

    # Runs

    def get_sequencingruns(self, groups, specs=None, user=None, fetch=True, raise_if_empty=False):

        q = self.construct_query(self.SequencingRun, specs)
        if fetch:
            q = q.order_by(self.SequencingRun.date.desc())

        return self.fix_result(q, fetch, raise_if_empty)

    def get_sequencingruns_by_ids(self, ids, groups, user=None, fetch=True, raise_if_empty=False):
        return self.get_sequencingruns(groups, [{'run_id': ids}], user=user, fetch=fetch, raise_if_empty=raise_if_empty)

    def get_sequencingruns_by_codes(self, codes, groups, user=None, fetch=True, raise_if_empty=False):
        return self.get_sequencingruns(groups, [{'run_code': codes}], user=user, fetch=fetch, raise_if_empty=raise_if_empty)

    # Run plates

    def get_runplates(self, groups, specs=None, user=None, fetch=True, raise_if_empty=False):

        q = self.construct_query(self.SequencingRunPlate, specs)
        if fetch:
            q = q.order_by(self.SequencingRunPlate.id)

        return self.fix_result(q, fetch, raise_if_empty)

    def get_runplates_by_ids(self, ids, groups, user=None, fetch=True, raise_if_empty=False):
        return self.get_runplates(groups, [{'runplate_id': ids}], user=user,
                                  fetch=fetch, raise_if_empty=raise_if_empty)

# EOF
