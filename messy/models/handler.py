
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

        'plate_id': dbschema.Plate.id,
        'plate_code': dbschema.Plate.code,

        'uploadjob_id': dbschema.UploadJob.id,
        'uploadjob_sesskey': dbschema.UploadJob.sesskey,
        'uploaditem_id': dbschema.UploadItem.id,
    }


class DBHandler(rhombus_handler.DBHandler):

    # add additional class references
    FileAttachment = dbschema.FileAttachment
    Institution = dbschema.Institution
    Collection = dbschema.Collection
    Sample = dbschema.Sample
    Plate = dbschema.Plate
    PlatePosition = dbschema.PlatePosition
    UploadJob = dbschema.UploadJob
    UploadItem = dbschema.UploadItem

    query_constructor_class = MessyQueryConstructor

    def initdb(self, create_table=True, init_data=True, rootpasswd=None, ek_initlist=[]):
        """ initialize database """
        from .setup import ek_initlist as messy_ek_initlist
        super().initdb(create_table, init_data, rootpasswd,
                       ek_initlist=messy_ek_initlist + ek_initlist)
        if init_data:
            from .setup import setup
            setup(self)
            cerr('[messy database has been initialized]')

    # add additional methods here

    def fix_result(self, query, fetch, raise_if_empty):
        if not fetch:
            return query

        res = query.all()
        if raise_if_empty and len(res) == 0:
            raise rhombus_handler.exc.NoResultFound()
        return res

    # Institutions

    def get_institutions(self, groups=None, specs=None, user=None, fetch=True,
                         raise_if_empty=False):

        q = self.construct_query(self.Institution, specs)
        if fetch:
            q = q.order_by(self.Institution.code)

        return self.fix_result(q, fetch, raise_if_empty)

    def get_institutions_by_ids(self, ids, groups, user=None, fetch=True, raise_if_empty=False):
        return self.get_institutions(groups, [{'institution_id': ids}], user=user, fetch=fetch,
                                     raise_if_empty=raise_if_empty)

    def get_institutions_by_codes(self, codes, groups, user=None, fetch=True,
                                  raise_if_empty=False):
        return self.get_institutions(groups, [{'institution_code': codes}], user=user,
                                     fetch=fetch, raise_if_empty=raise_if_empty)

    # Collections

    def get_collections(self, groups, specs=None, user=None, fetch=True, raise_if_empty=False,
                        ignore_acl=False):

        q = self.construct_query(self.Collection, specs)

        if user and user.has_roles(r.SYSADM, r.DATAADM, r.COLLECTION_MANAGE):
            ignore_acl = True
            groups = None

        if not ignore_acl and groups is None and user is None:
            raise ValueError(
                'ERR: get_collections() - either groups or user needs to be provided !')

        if not ignore_acl and groups is None:
            groups = user.groups

        if groups is not None:
            # enforce security
            cond = (self.Collection.group_id.in_([x[1] for x in groups]))
            q = q.filter(or_(self.Collection.public, self.Collection.refctrl, cond))

        if fetch:
            q = q.order_by(self.Collection.code)

        return self.fix_result(q, fetch, raise_if_empty)

    def get_collections_by_ids(self, ids, groups, user=None, fetch=True, raise_if_empty=False,
                               ignore_acl=False):
        return self.get_collections(groups, [{'collection_id': ids}], user=user, fetch=fetch,
                                    raise_if_empty=raise_if_empty, ignore_acl=ignore_acl)

    def get_collections_by_codes(self, codes, groups, user=None, fetch=True, raise_if_empty=False,
                                 ignore_acl=False):
        return self.get_collections(groups, [{'collection_code': codes}], user=user, fetch=fetch,
                                    raise_if_empty=raise_if_empty, ignore_acl=ignore_acl)

    #
    # Samples

    def get_samples(self, groups, specs=None, user=None, fetch=True, raise_if_empty=False,
                    ignore_acl=False):

        if user.has_roles(r.SYSADM, r.DATAADM, r.SAMPLE_MANAGE):
            ignore_acl = True
            groups = None

        q = self.construct_query(self.Sample, specs)

        # if groups is not None, we need to join sample with collection to get
        # all samples under collections owned by certain groups to enforce security

        if not ignore_acl and groups is None and user is None:
            raise ValueError('ERR: get_samples() - either groups or user needs to be provided!')

        if not ignore_acl and groups is None:
            if not user.has_roles(r.SYSADM, r.DATAADM, r.SAMPLE_MANAGE):
                groups = user.groups

        if groups is not None:
            q = q.join(self.Collection).filter(
                or_(self.Sample.public, self.Sample.refctrl,
                    self.Collection.group_id.in_([x[1] for x in groups]))
            )

        if fetch:
            q = q.order_by(self.Sample.code.desc())

        return self.fix_result(q, fetch, raise_if_empty)

    def get_samples_by_ids(self, ids, groups, user=None, fetch=True, raise_if_empty=False,
                           ignore_acl=False):
        return self.get_samples(groups, [{'sample_id': ids}], user=user, fetch=fetch,
                                raise_if_empty=raise_if_empty, ignore_acl=ignore_acl)

    def get_samples_by_codes(self, codes, groups, user=None, fetch=True, raise_if_empty=False,
                             ignore_acl=False):
        return self.get_samples(groups, [{'sample_code': codes}], user=user, fetch=fetch,
                                raise_if_empty=raise_if_empty, ignore_acl=ignore_acl)

    # Plates

    def get_plates(self, groups, specs=None, user=None, fetch=True, raise_if_empty=False,
                   ignore_acl=False):

        q = self.construct_query(self.Plate, specs)
        if fetch:
            q = q.order_by(self.Plate.id.desc())

        if groups is not None:
            q = q.filter(self.Plate.group_id.in_([x[1] for x in groups]))

        return self.fix_result(q, fetch, raise_if_empty)

    def get_plates_by_ids(self, ids, groups, user=None, fetch=True, raise_if_empty=False,
                          ignore_acl=False):
        return self.get_plates(groups, [{'plate_id': ids}], user=user, fetch=fetch,
                               raise_if_empty=raise_if_empty, ignore_acl=False)

    def get_plates_by_codes(self, codes, groups, user=None, fetch=True, raise_if_empty=False,
                            ignore_acl=False):
        return self.get_plates(groups, [{'plate_code': codes}], user=user, fetch=fetch,
                               ignore_acl=False, raise_if_empty=raise_if_empty)

    # UploadJob

    def get_uploadjobs(self, groups, specs=None, user=None, fetch=True,
                       raise_if_empty=False, ignore_acl=False, class_=None):

        cls = class_ or self.UploadJob

        q = self.construct_query(cls, specs)

        if groups is None:
            ignore_acl = True

        if not ignore_acl:
            if user:
                q = q.filter(cls.user_id == user.id)
            else:
                raise ValueError('user argument must be assigned')

        if fetch:
            q = q.order_by(cls.start_time.desc())

        return self.fetch_query(q, fetch, raise_if_empty)

    def get_uploadjobs_by_ids(self, ids, groups, user=None, fetch=True, class_=None,
                              spec_tag='uploadjob_id', raise_if_empty=False):
        return self.get_uploadjobs(groups, [{spec_tag: ids}],
                                   user=user, fetch=fetch, class_=class_,
                                   raise_if_empty=raise_if_empty)

    def get_uploadjobs_by_sesskeys(self, sesskeys, groups, user=None, fetch=True,
                                   spec_tag='uploadjob_sesskey', class_=None,
                                   raise_if_empty=False):
        return self.get_uploadjobs(groups, [{spec_tag: sesskeys}],
                                   user=user, fetch=fetch, class_=class_,
                                   raise_if_empty=raise_if_empty)

# EOF
