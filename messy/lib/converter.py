
import pandas as pd

# all CSV to dict converter

def import_gisaid_csv(filename):
    """ create a list of dictionary suitable for Sample.bulk_load() from GISAID metadata file"""

    df = pd.read_table(filename, sep=',')
    for f in ['fn', 'covv_subm_sample_id', 'covv_add_host_info', 'covv_last_vaccinated', 'covv_outbreak']:
        df[f] = df[f].fillna('').astype('str')

    a_list = []

    for _, r in df.iterrows():
        d = dict(
            code = r['covv_subm_sample_id'],
            lab_code = r['covv_provider_sample_id'] or r['fn'],
            sequence_name = r['covv_virus_name'],
            species = r['covv_type'],
            passage = r['covv_passage'],
            collection_date = r['covv_collection_date'],
            location = r['covv_location'],
            add_location = r['covv_add_location'],

            host = r['covv_host'],
            host_info = r['covv_add_host_info'] or '',
            host_gender = r['covv_gender'],
            host_age = r['covv_patient_age'],
            host_status = r['covv_patient_status'],

            specimen_type = r['covv_specimen'],
            outbreak = r['covv_outbreak'],
            last_vaccinated_info = r['covv_last_vaccinated'],
            treatment = r['covv_treatment'],

            originating_code = r['covv_provider_sample_id'],
            originating_institution = r['covv_orig_lab'],
            sampling_institution = r['covv_orig_lab'],

            ct_method = 'berlin',
        )
        d['category'] = 'S-SU' if not d['last_vaccinated_info'] else 'F-PO'
        d['ct_method'] = 'rtpcr'
        a_list.append( d )

    return a_list


def import_pipeline_tsv(filename):

    df = pd.read_table(filename, sep='\t')
    for f in ['SAMPLE']:
        df[f] = df[f].fillna('').astype('str')

    a_list = []

    for _, r in df.iterrows():
        d = dict(
            lab_code = r['SAMPLE'],
            avg_depth = r['AVGDEPTH'],
            length = r['LENGTH'],
            base_N = r['N_BASE'],
            point_mutations = r['POINTMUT'],
            inframe_gaps = r['INFRAME'],
            outframe_gaps = r['OOFRAME'],
            read_stas = dict( raw = r['RAW'], op_dedup = r['OP_DEDUP'], adapter = r['ADAPTER'],
                            prop_pair = r['PROP_PAIR'], pcr_dedup = r['PCR_DEDUP'],
                            primal = r['PRIMAL'] ),

        )


def import_fasta(filename, label='lab_code'):
    pass

def export_institution(filename):

    pass
