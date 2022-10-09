from rhombus.lib.utils import cerr
from messy.ext.ngsmgr.models import schema
from messy.ext.ngsmgr.lib import roles as r

__initialized__ = False


def generate_handler_class(base_class):
    """ base_class is the handler base class """

    # safety measure here to avoid double initialization
    global __initialized__
    if __initialized__:
        return base_class
    __initialized__ = True

    schema.extend_object_classes(base_class)

    class MessyNGSMSQueryConstructor(base_class.query_constructor_class):

        field_specs = base_class.query_constructor_class.field_specs | {
            'ngsrun_id': schema.NGSRun.id,
            'ngsrun_code': schema.NGSRun.code,
            'panel_id': schema.Panel.id,
            'panel_code': schema.Panel.code,
            'fastqpair_id': schema.FastqPair.id,
            'fastquploadjob_id': schema.FastqUploadJob.id,
            'fastquploadjob_sesskey': schema.FastqUploadJob.sesskey,
        }

    class NGSMgrHandler(base_class):

        # add models here

        NGSRun = schema.NGSRun
        NGSRunPlate = schema.NGSRunPlate
        Panel = schema.Panel
        FastqPair = schema.FastqPair
        FastqUploadJob = schema.FastqUploadJob


        # set query constructor class

        query_constructor_class = MessyNGSMSQueryConstructor

        # define additional methods here

        def initdb(self, create_table=True, init_data=True, rootpasswd=None, ek_initlist=[]):
            """ initialize database """
            from .setup import ek_initlist as messy_ngsms_ek_initlist
            super().initdb(create_table, init_data, rootpasswd,
                           ek_initlist=messy_ngsms_ek_initlist + ek_initlist)
            if init_data:
                from .setup import setup
                setup(self)
                cerr('[messy-ngsmgr database has been initialized]')

        # accessor for ngsrun

        def get_ngsruns(self, groups, specs=None, user=None, fetch=True, raise_if_empty=False):

            q = self.construct_query(self.NGSRun, specs)
            if fetch:
                q = q.order_by(self.NGSRun.date.desc())

            return self.fetch_query(q, fetch, raise_if_empty)

        def get_ngsruns_by_ids(self, ids, groups, user=None, fetch=True, raise_if_empty=False):
            return self.get_ngsruns(groups, [{'ngsrun_id': ids}], user=user, fetch=fetch,
                                    raise_if_empty=raise_if_empty)

        def get_ngsruns_by_codes(self, codes, groups, user=None, fetch=True, raise_if_empty=False):
            return self.get_ngsruns(groups, [{'ngsrun_code': codes}], user=user, fetch=fetch,
                                    raise_if_empty=raise_if_empty)

        # accessor for Panel
        # Panel does not require strict ACLs

        def get_panels(self, groups=None, specs=None, user=None, fetch=True, raise_if_empty=False):

            q = self.construct_query(self.Panel, specs)
            if fetch:
                q = q.order_by(self.Panel.code)

            return self.fetch_query(q, fetch, raise_if_empty)

        def get_panels_by_ids(self, ids, groups=None, user=None, fetch=True, raise_if_empty=False):
            return self.get_panels(groups, [{'panel_id': ids}], user=user, fetch=fetch,
                                   raise_if_empty=raise_if_empty)

        def get_panels_by_codes(self, codes, groups=None, user=None, fetch=True, raise_if_empty=False):
            return self.get_panels(groups, [{'panel_code': codes}], user=user, fetch=fetch,
                                   raise_if_empty=raise_if_empty)

        # accessor for FastqPair

        def get_fastqpairs(self, groups, specs=None, user=None, fetch=True, raise_if_empty=False):

            q = self.construct_query(self.FastqPair, specs)

            # check permission
            if groups:
                q = q.filter(self.FastqPair.group_id.in_([x[1] for x in groups]))

            return self.fetch_query(q, fetch, raise_if_empty)

        def get_fastqpairs_by_ids(self, ids, groups, user=None, fetch=True, raise_if_empty=False):
            return self.get_fastqpairs(groups, [{'fastqpair_id': ids}], user=user, fetch=fetch,
                                       raise_if_empty=raise_if_empty)

        # accessor for FastqUploadjob and FastqUploadItem

        def get_fastquploadjobs_by_ids(self, * args, ** kwargs):
            return self.get_uploadjobs_by_ids(* args, ** kwargs,
                                              spec_tag='fastquploadjob_id',
                                              class_=self.FastqUploadJob)

        def get_fastquploadjobs_by_sesskeys(self, * args, ** kwargs):
            return self.get_uploadjobs_by_sesskeys(* args, ** kwargs,
                                                   spec_tag='fastquploadjob_sesskey',
                                                   class_=self.FastqUploadJob)


    # End of NGSMgrHandler

    cerr('[NGSMgrHandler class generated.]')
    return NGSMgrHandler

# EOF
