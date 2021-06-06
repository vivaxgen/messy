
from rhombus.models import handler as rhombus_handler
from rhombus.lib.utils import cerr, cout

from .setup import setup

from messy.models import dbschema
from sqlalchemy import or_, and_


class MessyQueryConstructor(rhombus_handler.QueryConstructor):

    field_specs = {
        'institution_id': dbschema.Institution.id,
        'institution': dbschema.Institution.code,
        'institution_code': dbschema.Institution.code,

        'collection_id': dbschema.Collection.id,
        'collection':dbschema.Collection.code,
        'collection_code': dbschema.Collection.code,

        'sample_id': dbschema.Sample.id,
        'sample_lab_code': dbschema.Sample.lab_code,
        'lab_code': dbschema.Sample.lab_code,

        'sequence': dbschema.Sample.sequence_name,
        'sequence_id': dbschema.Sequence.id,
        'accid': dbschema.Sequence.accid,

        'plate_id': dbschema.Plate.id,

        'run_id': dbschema.SequencingRun.id,
        'run_code': dbschema.SequencingRun.code,
        'run_serial': dbschema.SequencingRun.serial,
    }


class DBHandler(rhombus_handler.DBHandler):

    # add additional class references
    Institution = dbschema.Institution
    Collection = dbschema.Collection
    Sample = dbschema.Sample
    Sequence = dbschema.Sequence
    Plate = dbschema.Plate
    SequencingRun = dbschema.SequencingRun

    query_constructor_class = MessyQueryConstructor


    def initdb(self, create_table=True, init_data=True, rootpasswd=None):
        """ initialize database """
        super().initdb(create_table, init_data, rootpasswd)
        if init_data:
            from .setup import setup
            setup(self)
            cerr('[messy-rbmgr] Database has been initialized')


    # add additional methods here


    # Institutions

    def get_institutions(self, groups=None, specs=None, fetch=True, raise_if_empty=False):

        q = self.construct_query(self.Institution, specs).order_by( self.Institution.code )

        if not fetch:
            return q

        res = q.all()
        if raise_if_empty and len(res) == 0:
            raise RuntimeError('Institution not found')

        return res


    def get_institutions_by_ids(self, ids, groups, fetch=True, raise_if_empty=False):
        return self.get_institutions(groups, [ {'institution_id': ids} ], fetch=fetch, raise_if_empty=raise_if_empty)


    def get_institutions_by_codes(self, codes, groups, fetch=True, raise_if_empty=False):
        return self.get_institutions(groups, [ {'institution_code': codes} ], fetch=fetch, raise_if_empty=raise_if_empty)


    # Collections

    def get_collections(self, groups, specs=None, fetch=True, raise_if_empty=False):

        q = self.construct_query(self.Collection, specs)
        if groups is not None:
            # enforce security
            q = q.filter( self.Collection.group_id.in_( [ x[1] for x in groups ] ))
        q = q.order_by( self.Collection.code )

        if not fetch:
            return q

        res = q.all()
        if raise_if_empty and len(res) == 0:
            raise RuntimeError('Collection not found')

        return res

    def get_collections_by_ids(self, ids, groups, fetch=True, raise_if_empty=False):
        return self.get_collections(groups, [ {'collection_id': ids} ], fetch=fetch, raise_if_empty=False)

    # Samples

    def get_samples(self, groups, specs=None, fetch=True, raise_if_empty=False):

        q = self.construct_query(self.Sample, specs)

        # if groups is not None, we need to join sample with collection to get 
        # all samples under collections owned by certain groups to enforce security
        if groups is not None:
            q = q.join( dbh.Collection ).filter( self.Collection.group_id.in_( [ x[1] for x in groups ] ))

        q = q.order_by( self.Sample.code.desc() )

        if not fetch:
            return q

        res = q.all()
        if raise_if_empty and len(res) == 0:
            raise RuntimeError('Collection not found')

        return res

    def get_samples_by_ids(self, ids, groups, fetch=True, raise_if_empty=False):
        return self.get_samples(groups, [ {'sample_id': ids} ], fetch=fetch, raise_if_empty=False)


    # Sequences

    def get_sequences(self, groups, specs=None, fetch=True, raise_if_emtpy=False):

        q = self.construct_query(self.Sequence, specs).order_by( self.Sequence.id.desc() )

        if not fetch:
            return q

        res = q.all()
        if raise_if_empty and len(res) == 0:
            raise RuntimeError('Collection not found')

        return res


    def get_sequences_by_ids(self, ids, groups, fetch=True):
        return get_sequences(groups, [ {'sequence_id': ids} ], fetch=fetch, raise_if_empty=False)


    # Plates

    def get_plates(self, groups, specs=None, fetch=True, raise_if_empty=False):

        q = self.construct_query(self.Plate, specs).order_by( self.Plate.id.desc() )

        if groups is not None:
            q = q.filter( self.Plate.group_id.in_ ( [ x[1] for x in groups ] ))

        if not fetch:
            return q

        res = q.all()
        if raise_if_empty and len(res) == 0:
            raise RuntimeError('Plate not found')

        return res

    def get_plates_by_ids(self, ids, groups, fetch=True):
        return self.get_plates(groups, [ {'plate_id': ids} ], fetch = fetch)


    # Runs

    def get_sequencingruns(self, groups, specs=None, fetch=True, raise_if_empty=False):

        q = self.construct_query(self.SequencingRun, specs).order_by( self.SequencingRun.id.desc() )

        if not fetch:
            return q

        res = q.all()
        if raise_if_empty and len(res) == 0:
            raise RuntimeError('Sequencing run not found')

        return res

    def get_sequencingruns_by_ids(self, ids, groups, fetch=True, raise_if_empty=False):
        return self.get_sequencingruns(groups, [ {'run_id': ids} ], fetch=fetch, raise_if_empty=False)


def construct_query_from_list_xxx( a_list ):
    exprs = []
    classes = []
    for spec in a_list:
        spec_exprs, spec_classes = construct_query_from_dict( spec )
        exprs.append( spec_exprs )
        classes.extend( spec_classes )

    classes = set( classes )
    return or_(* exprs), classes

def construct_query_from_dict_xxx( a_dict ):

    exprs = []
    classes = []

    for k, val in a_dict.items():
        f = field_specs[k]
        if f.class_ not in classes:
            classes.append( f.class_ )
        if isinstance(val, list):
            exprs.append( f.in_(val) )
        elif '%' in val:
            exprs.append( f.like(val))
        else:
            exprs.append( f == val )

    return and_( *exprs ), classes
