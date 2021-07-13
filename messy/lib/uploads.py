
from rhombus.lib.utils import random_string, get_dbhandler
from messy.lib import converter
import pandas as pd
import os


_temp_directory_ = None

def set_temp_directory(full_path):
    global _temp_directory_
    _temp_directory_ = full_path

def get_temp_directory():
    global _temp_directory_
    return _temp_directory_

def create_temp_file(prefix, username, extension, randkey):
    return f"{get_temp_directory()}/{prefix}-{username}-{randkey}.{extension}"

def create_temp_directory(prefix, username, randkey):
    return f"{get_temp_directory()}/{prefix}-{username}-{randkey}/"


class UploadJob(object):

    def __init__(self, user_id):
        self.randkey = random_string(16)
        self.user_id = user_id

    def check_user(self, user_id):
        return self.user_id == user_id

    def confirm(self):
        pass

    def commit(self):
        pass

    def stream_to_dicts(self, instream):
        df = dicts = None
        name, ext = os.path.splitext(self.filename)
        if ext == '.tsv':
            df = pd.read_table(instream, sep='\t')
        elif ext == '.csv':
            df = pd.read_table(instream, sep=',')
        elif ext == '.json':
            pass
        elif ext == '.yaml':
            pass
        else:
            raise

        if dicts == None:
            dicts = df.to_dict(orient='records')

        return dicts


class InstitutionUploadJob(UploadJob):

    def __init__(self, user_id, filename, instream):
        super().__init__(user_id)
        # save to memory
        self.filename = filename
        self.dicts = self.stream_to_dicts(instream)

    def confirm(self):
        err_msgs = []
        code_list = [ d['code'] for d in self.dicts ]
        code_set = set(code_list)
        if len(code_set) < len(code_list):
            err_msgs.append(f'Duplicate code(s) found in the file, from {len(code_list)} to {len(code_set)} unique code(s)')
        dbh = get_dbhandler()
        existing = dbh.Institution.query(dbh.session()).filter( dbh.Institution.code.in_( code_list) ).count()
        return { 'existing': existing, 'new': len(code_set) - existing, 'err_msgs': err_msgs }

    def commit(self, method):

        dbh = get_dbhandler()
        updated = added = 0

        institutions = {}
        for d in self.dicts:
            institutions[ d['code'] ] = d
        code_list = institutions.keys()

        q = dbh.session().query(dbh.Institution.code).filter( dbh.Institution.code.in_( code_list ) )
        existing_codes = set( [ t[0] for t in q])

        if method == 'add':

            for d in institutions.values():
                if d['code'] in existing_codes:
                    continue
                obj = dbh.Institution.from_dict(d, dbh)
                dbh.session().add(obj)
                added += 1

            return added, updated

        elif method == 'update':

            for code in existing_codes:
                obj = dbh.Institution.query(dbh.session()).filter( dbh.Institution.code == code ).one()
                obj.update( institutions[ code ])
                updated += 1

            return added, updated

        elif method == 'add_update':

            for d in institutions.values():
                if d['code'] in existing_codes:
                    obj = dbh.Institution.query(dbh.session()).filter( dbh.Institution.code == d['code'] ).one()
                    obj.update(d)
                    updated += 1
                    continue
                obj = dbh.Institution.from_dict(d, dbh)
                dbh.session().add(obj)
                added += 1

            return added, updated

        raise RuntimeError



class SampleUploadJob(UploadJob):

    def __init__(self, user_id, filename, instream, collection_id):
        super().__init__(user_id)
        self.collection_id = collection_id
        self.filename = filename
        self.dicts = self.stream_to_dicts(instream)


    def confirm(self):

        dbh  = get_dbhandler()
        samples = len(self.dicts)
        err_msgs = self.check_duplicate_codes()

        for d in self.dicts:
            err_msgs.extend( self.fix_fields(d, dbh) )

        err_msgs = sorted( list( set(err_msgs) ) )
        return { 'samples': samples, 'err_msgs': err_msgs }


    def commit(self, method):

        dbh = get_dbhandler()
        updated = added = 0

        samples = {}
        for d in self.dicts:
            self.fix_fields(d, dbh)
            samples[ d['code'] ] = d
        code_list = samples.keys()

        q = dbh.session().query(dbh.Sample.code).filter( dbh.Sample.code.in_( code_list ) )
        existing_codes = set( [ t[0] for t in q])

        if method == 'add':

            for d in samples.values():
                if d['code'] in existing_codes:
                    continue
                d['collection_id'] = self.collection_id
                obj = dbh.Sample.from_dict(d, dbh)
                dbh.session().add(obj)
                added += 1

            return added, updated

        elif method == 'update':

            for code in existing_codes:
                obj = dbh.Institution.query(dbh.session()).filter( dbh.Institution.code == code ).one()
                obj.update( institutions[ code ])
                updated += 1

            return added, updated

        elif method == 'add_update':

            for d in institutions.values():
                if d['code'] in existing_codes:
                    obj = dbh.Institution.query(dbh.session()).filter( dbh.Institution.code == d['code'] ).one()
                    obj.update(d)
                    updated += 1
                    continue
                obj = dbh.Institution.from_dict(d)
                dbh.session().add(obj)
                added += 1

            return added, updated

        raise RuntimeError


    def check_duplicate_codes(self):
        """ check for duplicate sample codes & acc_codes """

        composite_codes = [ (r['code'], r['acc_code']) for r in self.dicts ]
        codes = {}
        acc_codes = {}
        err_msgs = []
        for (c, ac) in composite_codes:
            if c in codes:
                err_msgs.append( f'Duplicate code: {c}' )
            else:
                codes[c] = True
            if ac in acc_codes:
                err_msgs.append( f'Duplicate acccode: {ac}' )
            else:
                acc_codes[ac] = True
        return err_msgs


    def check_institution_codes(self):
        """ check for institution codes """
        institution_codes = [ r.get('originating_institution', '') for r in self.dicts ]
        institution_codes += [ r.get('sampling_institution', '') for r in self.dicts ]
        institution_codes = set(institution_codes)
        institution_codes.discard('')

        dbh = get_dbhandler()
        session = dbh.session()
        err_msgs = []
        for code in institution_codes:
            insts = dbh.Institution.search_text(code, session, 1)
            if len(insts) > 0:
                inst = insts[0]
                err_msgs.append(f'WARN: Institution code "{code}" => {inst.code} | {inst.name}')
            else:
                err_msgs.append(f'ERR: Institution code "{code}" not found!')

        return err_msgs

        q = dbh.session().query(dbh.Institution.code).filter( dbh.Institution.code.in_( institution_codes ) )
        existing_codes = set( [ t[0] for t in q])
        non_existing_codes = institution_codes - existing_codes
        return [ f'Non-existing institution: {code}' for code in sorted(list(non_existing_codes)) ]


    def get_institution(self, inst_code, dbh):
        if len(inst_code.split()) == 1:
            inst = dbh.get_institutions_by_codes(inst_code, None)
            if len(inst) == 1:
                return inst[0]

        inst = dbh.Institution.search_text(inst_code, dbh.session(), 1)[0]
        return inst

    def get_ekey(self, key, dbh):
        try:
            ek_id = dbh.EK.getid(key, dbh.session())
            if ek_id:
                return key

        except KeyError:
            pass

        key = key.replace('-', ' ')
        eks = dbh.EK.search_text(key, dbh.session(), 1)
        if len(eks) == 0:
            raise KeyError(f'key "{key}"" not found')
        return eks[0].key

    def fix_ekey(self, d, field, dbh):
        key = d[field]
        print(f'>>> fix_ekey(): {key} >>>')
        try:
            ekey = self.get_ekey(key, dbh)
            d[field] = ekey
            if ekey.lower() != key.lower():
                return [ f'{field}: "{key}" => {ekey}' ]
        except KeyError as err:
            return [ f'{field} error: {str(err)}']
        return []


    def fix_fields(self, d, dbh):

        err_msgs = []
        
        code = d['originating_institution']
        try:
            inst = self.get_institution(code, dbh)
            if inst.code != code:
                del d['originating_institution']
                d['originating_institution_id'] = inst.id
                err_msgs.append( f'WARN: Institution code "{code}" => {inst.code} | {inst.name}' )
        except IndexError:
            err_msgs.append(f'ERR: Institution code "{code}" not found!')

        code = d['sampling_institution']
        try:
            inst = self.get_institution(code, dbh)
            if inst.code != code:
                del d['sampling_institution']
                d['sampling_institution_id'] = inst.id
                err_msgs.append( f'WARN: Institution code "{code}" => {inst.code} | {inst.name}' )
        except IndexError:
            err_msgs.append(f'ERR: Institution code "{code}" not found!')

        for f in dbh.Sample.__ek_fields__:
            err_msgs.extend( self.fix_ekey(d, f, dbh) )

        return err_msgs


class SampleGISAIDUploadJob(SampleUploadJob):

    def stream_to_dicts(self, instream):
        return converter.import_gisaid_csv(instream)
