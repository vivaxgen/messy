
from rhombus.lib.utils import random_string, get_dbhandler
from messy.lib import converter
import json
import yaml
import pandas as pd
import os
import functools


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
            df = pd.read_table(instream, sep='\t', dtype=str, na_filter=False)
        elif ext == '.csv':
            df = pd.read_table(instream, sep=',', dtype=str)
        elif ext == '.jsonl':
            dicts = []
            for line in instream:
                dicts.append(json.loads(line))
        elif ext == '.yaml':
            dicts = list(yaml.safe_load_all(instream))
        else:
            raise RuntimeError('Invalid input file format')

        if dicts is None:
            dicts = df.to_dict(orient='records')

        # clear off empty string or None
        for d in dicts:
            for f, v in list(d.items()):
                if v == '' or v is None:
                    del d[f]

        import pprint; pprint.pprint(dicts)

        return dicts


class InstitutionUploadJob(UploadJob):

    def __init__(self, user_id, filename, instream):
        super().__init__(user_id)
        # save to memory
        self.filename = filename
        self.dicts = self.stream_to_dicts(instream)

    def confirm(self):
        err_msgs = []
        code_list = [d['code'] for d in self.dicts]
        code_set = set(code_list)
        if len(code_set) < len(code_list):
            err_msgs.append(f'Duplicate code(s) found in the file, from {len(code_list)} to {len(code_set)} unique code(s)')
        dbh = get_dbhandler()
        existing = dbh.Institution.query(dbh.session()).filter(dbh.Institution.code.in_(code_list)).count()
        return {'existing': existing, 'new': len(code_set) - existing, 'err_msgs': err_msgs}

    def commit(self, method):

        dbh = get_dbhandler()
        updated = added = 0

        institutions = {}
        for d in self.dicts:
            institutions[d['code']] = d
        code_list = institutions.keys()

        q = dbh.session().query(dbh.Institution.code).filter(dbh.Institution.code.in_(code_list))
        existing_codes = set([t[0] for t in q])

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
                obj = dbh.Institution.query(dbh.session()).filter(dbh.Institution.code == code).one()
                obj.update(institutions[code])
                updated += 1

            return added, updated

        elif method == 'add_update':

            for d in institutions.values():
                if d['code'] in existing_codes:
                    obj = dbh.Institution.query(dbh.session()).filter(dbh.Institution.code == d['code']).one()
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
        self.institution_translation_table = {}
        self.institution_cache = {}
        self.ekey_cache = {}

    def confirm(self):

        dbh = get_dbhandler()
        samples = len(self.dicts)
        err_msgs, existing_codes, existing_acc_codes = self.check_duplicate_codes()

        for d in self.dicts:
            err_msgs.extend(self.fix_fields(d, dbh))

        err_msgs = sorted(list(set(err_msgs)))
        return {'samples': samples, 'existing_codes': existing_codes,
                'existing_acc_codes': existing_acc_codes, 'err_msgs': err_msgs,
                'institutions': self.institution_cache}

    def commit(self, method):

        dbh = get_dbhandler()
        updated = added = 0

        samples = {}
        for d in self.dicts:
            self.fix_fields(d, dbh)
            samples[d['code']] = d
        code_list = samples.keys()

        q = dbh.session().query(dbh.Sample.code).filter(dbh.Sample.code.in_(code_list))
        existing_codes = set([t[0] for t in q])

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
                obj = dbh.Sample.query(dbh.session()).filter(dbh.Sample.code == code).one()
                obj.update(samples[code])
                updated += 1

            return added, updated

        elif method == 'add_update':

            for d in samples.values():
                if d['code'] in existing_codes:
                    obj = dbh.Sample.query(dbh.session()).filter(dbh.Sample.code == d['code']).one()
                    obj.update(d)
                    updated += 1
                    continue
                obj = dbh.Institution.from_dict(d)
                dbh.session().add(obj)
                added += 1

            return added, updated

        raise RuntimeError

    def check_duplicate_codes(self):
        """ check for duplicate sample codes & acc_codes and also existing codes """

        composite_codes = [(r['code'], r.get('acc_code', '')) for r in self.dicts]
        codes = {}
        acc_codes = {}
        err_msgs = []
        for (c, ac) in composite_codes:
            if c in codes:
                err_msgs.append(f'Duplicate code: {c}')
            else:
                codes[c] = True
            if ac and ac in acc_codes:
                err_msgs.append(f'Duplicate acc_code: {ac}')
            else:
                acc_codes[ac] = True

        dbh = get_dbhandler()

        q = dbh.session().query(dbh.Sample.code).filter(dbh.Sample.code.in_(codes.keys()))
        existing_codes = set([t[0] for t in q])

        q = dbh.session().query(dbh.Sample.acc_code).filter(dbh.Sample.acc_code.in_(acc_codes.keys()))
        existing_acc_codes = set([t[0] for t in q])

        return err_msgs, existing_codes, existing_acc_codes

    def get_institution(self, inst_code, dbh):
        if inst_code not in self.institution_cache:
            inst = self.institution_cache[inst_code] = self._get_institution(inst_code, dbh)
        else:
            inst = self.institution_cache[inst_code]

        if inst is None:
            raise KeyError(f'Cannot find institution with code: {inst_code}')
        return inst

    def _get_institution(self, inst_code, dbh):
        if len(inst_code.split()) == 1:
            inst = dbh.get_institutions_by_codes(inst_code, None)
            if len(inst) == 1:
                return inst[0]

        inst = dbh.Institution.search_text(inst_code, dbh.session(), 1)[0]
        return inst

    def get_ekey(self, key, group, dbh):
        t = (key, group)
        if t not in self.ekey_cache:
            ekey = self._get_ekey(key, group, dbh)
        else:
            ekey = self.ekey_cache[t]

        if ekey is None:
            raise KeyError(f'key "{key}" for group "{group}" not found')
        return ekey

    @functools.cache
    def _get_ekey(self, key, group, dbh):
        try:
            ek_id = dbh.EK.getid(key, grp=group, dbsession=dbh.session())
            if ek_id:
                return key

        except KeyError:
            pass

        key = key.replace('-', ' ')
        eks = dbh.EK.search_text(key, dbh.session(), 1)
        if len(eks) == 0:
            return None
        return eks[0].key

    def fix_ekey(self, d, field, dbh):
        key = d[field]
        try:
            ekey = self.get_ekey(key, dbh.Sample.get_ek_metainfo()[field][1], dbh)
            d[field] = ekey
            if ekey.lower() != key.lower():
                return [f'{field}: "{key}" => {ekey}']
        except RuntimeError as err:
            return [f'{field} error: {str(err)}']
        return []

    def fix_fields(self, d, dbh):
        try:
            return self._fix_fields(d, dbh)

        except Exception as err:
            raise RuntimeError(f'Error parsing data: {err}\r\nduring processing {d}') from err

    def _fix_fields(self, d, dbh):

        err_msgs = []

        d['originating_institution'] = d.get('originating_institution', '') or 'NOT-AVAILABLE'
        code = d['originating_institution']
        try:
            inst = self.get_institution(code, dbh)
            if inst.code != code:
                d['originating_institution'] = inst.code
                d['originating_institution_id'] = inst.id
                self.institution_translation_table[code] = (inst.code, inst.id)
                #err_msgs.append(f'WARN: Institution code "{code}" => {inst.code} | {inst.name}')
        except KeyError:
            err_msgs.append(f'ERR: Institution code "{code}" not found!')
            self.institution_translation_table[code] = None

        code = d.get('sampling_institution', None) or d['originating_institution']
        d['sampling_institution'] = code
        try:
            inst = self.get_institution(code, dbh)
            if inst.code != code:
                d['sampling_institution'] = inst.code
                d['sampling_institution_id'] = inst.id
                self.institution_translation_table[code] = (inst.code, inst.id)
                #err_msgs.append(f'WARN: Institution code "{code}" => {inst.code} | {inst.name}')
        except KeyError:
            err_msgs.append(f'ERR: Institution code "{code}" not found!')

        if 'host_gender' in d:
            gender = d['host_gender']
            d['host_gender'] = gender[0] if gender else None

        d['host_status'] = d.get('host_status', '') or 'unknown'

        for f in dbh.Sample.__ek_fields__:
            if f in d:
                err_msgs.extend(self.fix_ekey(d, f, dbh))

        for f, c in sample_converters.items():
            if f in d:
                try:
                    d[f] = c[0](d[f])
                except Exception:
                    d[f] = c[1]

        for f, v in sample_defaults.items():
            if f not in d:
                d[f] = v

        return err_msgs


class SampleGISAIDUploadJob(SampleUploadJob):

    def stream_to_dicts(self, instream):
        return converter.import_gisaid_csv(instream)


# convert values to their proper format
sample_converters = {
    'host_age': (float, -1),
    'host_severity': (int, -1),
    'viral_load': (float, -1),
    'ct_value1': (float, -1),
    'ct_value2': (float, -1),
}


# fill-in default values
sample_defaults = {
    'host': 'no-species',
    'host_occupation': 'other',
    'host_status': 'unknown',
    'category': 'r-ra',
    'specimen_type': 'no-specimen',
    'ct_method': 'no-ct',
}


class CollectionUploadJob(UploadJob):

    def __init__(self, user_id, filename, instream):
        super().__init__(user_id)
        # save to memory
        self.filename = filename
        self.dicts = self.stream_to_dicts(instream)

    def confirm(self):
        pass

    def commit(self):
        pass

# EOF
