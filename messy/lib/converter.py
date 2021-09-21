
import pandas as pd
from collections import deque
from rhombus.lib.utils import get_dbhandler

# all CSV to dict converter


def import_gisaid_csv(filename):
    """ create a list of dictionary suitable for Sample.bulk_load() from GISAID metadata file"""

    df = pd.read_table(filename, sep=',', keep_default_na=False)
    for f in ['fn', 'covv_subm_sample_id', 'covv_add_host_info', 'covv_last_vaccinated', 'covv_outbreak']:
        df[f] = df[f].fillna('').astype('str')

    a_list = []

    for _, r in df.iterrows():
        d = dict(
            collection=r.get('collection', ''),
            code=r['covv_provider_sample_id'] or r['fn'],
            acc_code=r['covv_subm_sample_id'],
            sequence_name=r['covv_virus_name'],
            species=r['covv_type'],
            passage=r['covv_passage'],
            collection_date=r['covv_collection_date'],
            location=r['covv_location'],
            add_location=r['covv_add_location'],
            received_date='1970-01-01',    # add Unix epoch time to indicate NA

            host=r['covv_host'],
            host_info=r['covv_add_host_info'] or '',
            host_gender=r['covv_gender'][0] if r['covv_gender'] else '',
            host_age=r['covv_patient_age'],
            host_status=r['covv_patient_status'],
            host_occupation='other',

            specimen_type=r['covv_specimen'],
            outbreak=r['covv_outbreak'],
            last_vaccinated_info=r['covv_last_vaccinated'],
            treatment=r['covv_treatment'],

            # originating_code = r['covv_provider_sample_id'] or r['fn'],
            originating_institution=r['covv_orig_lab'],
            sampling_institution=r['covv_orig_lab'],

            ct_method='rtpcr',
        )
        d['category'] = 'r-ra' if not d['last_vaccinated_info'] else 'F-PO'
        if type(d['host_age']) == str:
            if 'month' in d['host_age'].lower():
                d['host_age'] = int(d['host_age'].split()[0]) / 12
            elif ('unknown' in d['host_age'].lower()) or (d['host_age'] == ''):
                d['host_age'] = -1
            else:
                d['host_age'] = float(d['host_age'])
        a_list.append(d)

    return a_list


def import_pipeline_tsv(filename):

    df = pd.read_table(filename, sep='\t')
    for f in ['SAMPLE']:
        df[f] = df[f].fillna('').astype('str')

    a_list = []

    for _, r in df.iterrows():
        d = dict(
            lab_code=r['SAMPLE'],
            avg_depth=r['AVGDEPTH'],
            length=r['LENGTH'],
            base_N=r['N_BASE'],
            point_mutations=r['POINTMUT'],
            inframe_gaps=r['INFRAME'],
            outframe_gaps=r['OOFRAME'],
            read_stas = dict( raw = r['RAW'], op_dedup = r['OP_DEDUP'], adapter = r['ADAPTER'],
                            prop_pair = r['PROP_PAIR'], pcr_dedup = r['PCR_DEDUP'],
                            primal = r['PRIMAL'] ),

        )


def import_fasta(filename, label='lab_code'):
    pass


def export_institution(filename):

    pass


def export_gisaid(samples):
    """ return a dict with sample code as key with gisaid fields """

    dbh = get_dbhandler()
    sess = dbh.session()

    # gender
    gender = {'F': 'Female', 'M': 'Male', 'U': 'Unknown'}

    # set for rotating authors
    authors = AuthorHelper()

    gisaid_dict = {}

    # to create consistent and predictable data set, we ordered the samples by code
    sample_collection = {}
    for s in samples:
        sample_collection[s.code] = s

    for k in sorted(sample_collection.keys()):
        s = sample_collection[k]
        d = {
            'submitter': s.collection.data['submitter'],
            'fn': s.code,
            'covv_virus_name': s.sequence_name,
            'covv_type': s.species.split('-')[0],
            'covv_passage': s.passage,
            'covv_collection_date': str(s.collection_date),
            'covv_location': s.location,
            'covv_add_location': s.location_info,
            'covv_host': s.host,
            'covv_add_host_info': s.host_info,
            'covv_gender': gender[s.host_gender],
            'covv_patient_age': s.host_age,
            'covv_patient_status': s.host_status,
            'covv_specimen': dbh.EK.get(s.specimen_type_id, sess).desc,
            'covv_outbreak': s.outbreak,
            'covv_last_vaccinated': '',
            'covv_treatment': '',
            'covv_seq_technology': '',
            'covv_assembly_method': '',
            'covv_coverage': '',
            'covv_orig_lab': s.sampling_institution.name,
            'covv_orig_lab_addr': s.sampling_institution.address,
            'covv_provider_sample_id': '',
            'covv_subm_lab': s.collection.get_submitting_institution_name(),
            'covv_subm_lab_addr': s.collection.get_submitting_institution_addr(),
            'covv_subm_sample_id': s.acc_code,
            'covv_authors': authors.create_authors(s),
            'covv_comment': '',
            'comment_type': '',
        }

        gisaid_dict[s.code] = d

    return gisaid_dict


class AuthorHelper(object):

    def __init__(self):
        self.rotating_authors = {}
        self.last_authors = {}

    def create_authors(self, sample):
        coll_code = sample.collection.code
        if coll_code not in self.last_authors:
            self.prepare_authorship(sample.collection)
        authors = list(self.rotating_authors[coll_code]) + self.last_authors[coll_code]
        self.rotating_authors[coll_code].rotate(-1)
        return ', '.join(authors)

    def prepare_authorship(self, collection):
        authorship = collection.get_authors()
        self.last_authors[collection.code] = authorship.get('fixed', [])
        self.rotating_authors[collection.code] = deque(authorship.get('rotating', []))


# EOF
