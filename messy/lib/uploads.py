
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
        updated = added = failed = 0

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

        elif method == 'update':

            for code in existing_codes:
                obj = dbh.Institution.query(dbh.session()).filter(dbh.Institution.code == code).one()
                obj.update(institutions[code])
                updated += 1

        elif method == 'add_update':

            for code in existing_codes:
                obj = dbh.Institution.query(dbh.session()).filter(dbh.Institution.code == code).one()
                obj.update(institutions[code])
                updated += 1

            dbh.session().flush()

            for d in institutions.values():
                if d['code'] in existing_codes:
                    continue
                obj = dbh.Institution.from_dict(d, dbh)
                dbh.session().add(obj)
                added += 1

        else:
            raise RuntimeError('unrecognized method')

        return added, updated, failed


class SampleUploadJob(UploadJob):

    def __init__(self, user_id, filename, instream, collection_id):
        super().__init__(user_id)
        self.collection_id = collection_id
        self.filename = filename
        self.dicts = self.stream_to_dicts(instream)
        self.institution_translation_table = {}
        self.institution_cache = {}
        self.ekey_cache = {}
        self.collection_cache = {}

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

    def commit(self, method, user):

        dbh = get_dbhandler()
        updated = []
        added = []
        not_added = []
        failed = []

        samples = {}
        for d in self.dicts:
            self.fix_fields(d, dbh)
            samples[d['code']] = d
        code_list = samples.keys()

        q = dbh.session().query(dbh.Sample.code).filter(dbh.Sample.code.in_(code_list))
        existing_codes = set([t[0] for t in q])

        if method == 'add':

            added, not_added, failed = self._add_samples(samples, existing_codes, user, dbh)

        elif method == 'update':

            updated, failed = self._update_samples(samples, existing_codes, user, dbh)

        elif method == 'add_update':

            # we perform updates first before addition in case any of the updates fix inconsistency
            # or constraint that addition may cause

            updated, failed = self._update_samples(samples, existing_codes, user, dbh)
            dbh.session().flush()
            added, not_added, failed_2 = self._add_samples(samples, existing_codes, user, dbh)
            if len(not_added) != (len(updated) + len(failed)):
                raise RuntimeError('samples not being added is not in the set of being updated!')
            else:
                not_added = []
            failed += failed_2

        else:
            raise RuntimeError('method is not registered')

        return added, not_added, updated, failed

    def _add_samples(self, samples, existing_codes, user, dbh):
        added = []
        not_added = []
        failed = []
        for d in samples.values():
            try:
                if d['code'] in existing_codes:
                    not_added.append(d['code'])
                    continue
                if ('collection' not in d) or (not d['collection']):
                    if self.collection_id < 0:
                        raise ValueError('Please either set the collection in the file '
                                         'or use correct collection_id')
                    # collection_id has been verified when assigning the number
                    d['collection_id'] = self.collection_id
                else:
                    collection = d['collection']
                    if not self.is_collection_member(collection, user, dbh):
                        failed.append((d['code'], f'either collection {collection} does not exist or '
                                                     f'{user.login} is not a member of {collection}'))
                        continue
                obj = dbh.Sample.from_dict(d, dbh)
                dbh.session().add(obj)
                added.append(obj.code)

            except AssertionError as err:
                raise RuntimeError(
                    f'Error while processing sample code {d["code"]} with message:\n{str(err)}'
                ) from err

        return added, not_added, failed

    def _update_samples(self, samples, existing_codes, user, dbh):
        updated = []
        failed = []
        for code in existing_codes:
            try:
                obj = dbh.Sample.query(dbh.session()).filter(dbh.Sample.code == code).one()

                # ensure that current user can modify the sample
                if not obj.can_modify(user):
                    failed.append((obj.code, f'{user.login} do not have permission to modify'))
                    continue

                # ensure if current user wants to change collection, the user is also a member
                # of the group of the target collection
                sample = samples[code]
                if (collection := sample.get('collection', None)):
                    if not self.is_collection_member(collection, user, dbh):
                        failed.append((obj.code, f'either collection {collection} does not exist or '
                                                 f'{user.login} is not a member of {collection}'))
                        continue
                if (collection_id := sample.get('collection_id', None)):
                    if not self.is_collection_membet(collection_id, user, dbh):
                        failed.append((obj.code, f'either collection_id {collection_id} does not exist or '
                                                 f'{user.login} is not a member the collection'))
                        continue

                obj.update(samples[code])
                updated.append(code)

            except Exception as err:
                raise RuntimeError(
                    f'Error while processing sample code {code} with message:\n{str(err)}'
                ) from err

        return updated, failed

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

    def is_collection_member(self, collection_or_id, user, dbh):
        """return true or false indicating whether the user is member of collection group"""
        if collection_or_id in self.collection_cache:
            return self.collection_cache[collection_or_id]

        if type(collection_or_id) is int:
            if not dbh.get_collections_by_ids(collection_or_id, groups=None, user=user):
                # user cannot get collection (either wrong colletion_id or not a member)
                self.collection_cache[collection_or_id] = False
            else:
                self.collection_cache[collection_or_id] = True
        else:
            if not dbh.get_collections_by_codes(collection_or_id, groups=None, user=user):
                # user cannot get collection (either wrong colletion or not a member)
                self.collection_cache[collection_or_id] = False
            else:
                self.collection_cache[collection_or_id] = True

        return self.collection_cache[collection_or_id]

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
