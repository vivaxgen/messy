
from messy.models import *
from messy.lib.roles import *

from dateutil import parser

def setup( dbh ):

    dbh.EK.bulk_update( ek_initlist, dbsession=dbh.session() )
    dbh.Group.bulk_insert( messy_groups, dbsession = dbh.session() )

    # add controls

    dbh.session().add(
        dbh.Institution(
            code='NOT-AVAILABLE',
            name='Not Available'
            )
    )
    dbh.session().flush()

    dbh.session().add(
        dbh.Collection(
            code='CONTROL',
            group=dbh.get_group('CollectionMgr'),
            institutions = [ dbh.get_institutions_by_codes('NOT-AVAILABLE', None)[0] ],
            )
    )
    dbh.session().flush()

    dbh.session().add(
        dbh.Plate(
            code='CONTROL',
            group=dbh.get_group('PlateMgr'),
            specimen_type='water',
            experiment_type='sample-container',
            user=dbh.get_user('system/_SYSTEM_'),
            )
    )
    dbh.session().flush()

    samples = [
        dbh.Sample(
            collection = dbh.get_collections_by_codes('CONTROL', None)[0],
            code='empty',
            received_date=parser.parse('1970'),
            collection_date=parser.parse('1970'),
            species='no-species',
            host='no-host',
            host_occupation='other',
            host_status='unknown',
            category='R-RA',
            specimen_type='water',
            ct_method='rtpcr',
            originating_institution=dbh.get_institutions_by_codes('NOT-AVAILABLE', None)[0],
            sampling_institution=dbh.get_institutions_by_codes('NOT-AVAILABLE', None)[0],
            ),
        dbh.Sample(
            collection = dbh.get_collections_by_codes('CONTROL', None)[0],
            code='NTC1',
            received_date=parser.parse('1970'),
            collection_date=parser.parse('1970'),
            species='no-species',
            host='no-host',
            host_occupation='other',
            host_status='unknown',
            category='R-RA',
            specimen_type='water',
            ct_method='rtpcr',
            originating_institution=dbh.get_institutions_by_codes('NOT-AVAILABLE', None)[0],
            sampling_institution=dbh.get_institutions_by_codes('NOT-AVAILABLE', None)[0],
            ),
        dbh.Sample(
            collection = dbh.get_collections_by_codes('CONTROL', None)[0],
            code='NTC2',
            received_date=parser.parse('1970'),
            collection_date=parser.parse('1970'),
            species='no-species',
            host='no-host',
            host_occupation='other',
            host_status='unknown',
            category='R-RA',
            specimen_type='water',
            ct_method='rtpcr',
            originating_institution=dbh.get_institutions_by_codes('NOT-AVAILABLE', None)[0],
            sampling_institution=dbh.get_institutions_by_codes('NOT-AVAILABLE', None)[0],
            ),
        dbh.Sample(
            collection = dbh.get_collections_by_codes('CONTROL', None)[0],
            code='NTC3',
            received_date=parser.parse('1970'),
            collection_date=parser.parse('1970'),
            species='no-species',
            host='no-host',
            host_occupation='other',
            host_status='unknown',
            category='R-RA',
            specimen_type='water',
            ct_method='rtpcr',
            originating_institution=dbh.get_institutions_by_codes('NOT-AVAILABLE', None)[0],
            sampling_institution=dbh.get_institutions_by_codes('NOT-AVAILABLE', None)[0],
            ),
        dbh.Sample(
            collection = dbh.get_collections_by_codes('CONTROL', None)[0],
            code='NTC4',
            received_date=parser.parse('1970'),
            collection_date=parser.parse('1970'),
            species='no-species',
            host='no-host',
            host_occupation='other',
            host_status='unknown',
            category='R-RA',
            specimen_type='water',
            ct_method='rtpcr',
            originating_institution=dbh.get_institutions_by_codes('NOT-AVAILABLE', None)[0],
            sampling_institution=dbh.get_institutions_by_codes('NOT-AVAILABLE', None)[0],
            ),
    ]
    for s in samples:
        dbh.session().add(s)
    dbh.session().flush()


# add additional initial data here

messy_groups = [
            ( 'InstitutionMgr', [ INSTITUTION_MODIFY ] ),
            ( 'CollectionMgr', [COLLECTION_MODIFY, COLLECTION_VIEW] ),
            ( 'CollectionViewer', [COLLECTION_VIEW]),
            ( 'SampleMgr', [SAMPLE_MANAGE]),
            ( 'SampleModifier', [SAMPLE_MODIFY, SAMPLE_VIEW]),
            ( 'SampleViewer', [SAMPLE_VIEW]),
            ( 'PlateMgr', [PLATE_MANAGE]),
            ( 'PlateModifier', [PLATE_MODIFY, PLATE_VIEW]),
            ( 'PlateViewer', [PLATE_VIEW]),
            ( 'SequencingRunMgr', [SEQUENCINGRUN_MANAGE]),
            ( 'SequencingRunModifier', [SEQUENCINGRUN_MODIFY, SEQUENCINGRUN_VIEW]),
            ( 'SequencingRunViewer', [SEQUENCINGRUN_VIEW]),
            ( 'SequenceMgr', [SEQUENCE_MODIFY, SEQUENCE_VIEW]),
            ( 'SequenceViewer', [SEQUENCE_VIEW]),
            ( 'ProjectMgr', [SAMPLE_MODIFY, PLATE_MODIFY, SEQUENCINGRUN_MODIFY, SEQUENCE_MODIFY]),
            ( 'ProjectViewer', [SAMPLE_VIEW, PLATE_VIEW, SEQUENCINGRUN_VIEW, SEQUENCE_VIEW]),
            ( 'Collaborator', [SAMPLE_MODIFY, SEQUENCE_VIEW]),
]


ek_initlist = [
    (   '@SYSNAME', 'System names',
        [
            ( 'messy'.upper(), 'messy' ),
        ]
    ),
    (   '@ROLES', None,
        [
            (INSTITUTION_MANAGE, 'manage institution'),
            (INSTITUTION_MODIFY, 'modify institution'),
            (COLLECTION_MANAGE, 'manage collection'),
            (COLLECTION_MODIFY, 'modify collection'),
            (COLLECTION_VIEW, 'view collection'),
            (SAMPLE_MANAGE, 'manage sample'),
            (SAMPLE_MODIFY, 'modify sample'),
            (SAMPLE_VIEW, 'view sample'),
            (PLATE_MANAGE, 'plate manager'),
            (PLATE_MODIFY, 'modify plate'),
            (PLATE_VIEW, 'view plate'),
            (SEQUENCINGRUN_MANAGE, 'manage sequencing run'),
            (SEQUENCINGRUN_MODIFY, 'modify sequencing run'),
            (SEQUENCINGRUN_VIEW, 'view sequencing run'),
            (SEQUENCE_MANAGE, 'manage sequence'),
            (SEQUENCE_MODIFY, 'modify sequence'),
            (SEQUENCE_VIEW, 'view sequence'),
        ]
    ),
    (   '@SPECIES', "Species",
        [
            ('betacoronavirus', 'betacoronavirus'),
            ('human', 'human'),
            ('no-species', 'no-species'),
        ]
    ),
    (   '@PASSAGE', 'Passage',
        [
            ('original', 'Original'),
            ('vero', 'Vero cell 1st passage'),
            ('vero+2', 'Vero cell 2nd passage'),
            ('hek293', 'HEK293 cell 1st passage'),
            ('hek293+2', 'HEK293 cell 2nd passage')
        ]
    ),
    (   '@HOST', 'Host',
        [
            ('human', 'Human'),
            ('no-host', 'no-host'),
        ]
    ),
    (   '@HOST_STATUS', 'Host status',
        [
            ('unknown', 'Unknown'),
            ('hospitalized', 'Hospitalized'),
            ('live', 'Live'),
            ('deceased', 'Deceased'),
            ('released', 'Released')
        ]
    ),
    (    '@HOST_OCCUPATION', 'Host occupation',
        [
            ('irrelevant', 'Irrelevant'),
            ('other', 'Other occupation'),
            ('unemployed', 'Unemployed'),
            ('health', 'Health sector'),
            ('government', 'Government sector'),
            ('media', 'Media sector'),
            ('telecommunication', 'Telecommunication sector'),
            ('finance', 'Financial sector'),
            ('it', 'Information Technology sector'),
            ('teacher', 'Teacher'),
            ('lecturer', 'Lecturer'),
            ('education', 'Education sector'),
            ('student', 'Student'),
            ('retail', 'Retail sector'),
            ('domestic', 'Domestic (family) sector'),
            ('transport', 'Transportation sector'),
            ('entertainment', 'Entertainment sector'),
            ('agriculture', 'Agricultural sector'),
            ('fishery', 'Fishery sector'),
            ('mining', 'Mining sector'),
            ('foresty', 'Forestry sector'),
        ]
    ),
    (   '@CATEGORY', 'Sample category',
        [
            ('R-RA', 'R - Random surveillance and tracking'),
            ('S-SE', 'S - Sentinel surveillance'),
            ('A-NE', 'A - COVID19 clinically (-) test'),
            ('B-CL', 'B - COVID19 severe clinically'),
            ('C-TR', 'C - travel history'),
            ('D-LO', 'D - long COVID19'),
            ('E-RE', 'E - reinfection'),
            ('F-PO', 'F - post-vaccination'),
            ('G-CH', 'G - child case'),
            ('H-CO', 'H - comorbid case')
        ]
    ),
    (   '@SPECIMEN_TYPE', 'Specimen type',
        [
            ('np+op', 'Nasopharyngeal and oropharyngeal swab'),
            ('np', 'Nasopharyngeal swab'),
            ('op', 'Oropharyngeal swab swab'),
            ('sputum', 'Sputum'),
            ('blood', 'Blood'),
            ('serum', 'Serum'),
            ('saliva', 'Saliva'),
            ('stool', 'Stool'),
            ('wastewater', 'Wastewater'),
            ('rna', 'RNA'),
            ('cdna', 'cDNA'),
            ('dna', 'double-strand DNA'),
            ('ssdna', 'single-strand DNA'),
            ('water', 'empty sample'),
        ]
    ),
    (   '@CT_METHOD',   'Ct Methodology',
        [
            ('rtpcr', 'generic realtime RT-PCR'),
            ('cobas', 'Cobas'),
            ('charite-berlin', 'Charite-Berlin method')
        ]
    ),
    (   '@EXPERIMENT_TYPE', 'Laboratory experiment type',
        [
            ('sample-container', 'container for sample storage'),
            ('qc-qubit', 'QC with qubit'),
            ('qc-accuclear', 'QC with AccuClear'),
            ('cdna-ssiv', 'cDNA with Superscript IV'),
            ('cdna-lunascript', 'cDNA with Lunascript'),
            ('pcr-idt-artic', 'PCR with IDT ARTICv3 kit'),
            ('pcr-neb-b.artic', 'PCR with NEB balanced ARTICv3 kit'),
            ('pcr-covidseq', 'PCR with CovidSeq ARTIC'),
            ('libprep-truseqstrandedrna', 'library prep with Truseq Stranded RNA'),
            ('libprep-truseqnano', 'library prep with Truseq Nano'),
            ('libprep-nextera', 'library prep with Nextera XT'),
            ('libprep-dnaprep', 'library prep with DNAPrep (NexteraFlex)'),
            ('libprep-covidseq', 'library prep with CovidSeq DNAPrep'),
            ('libprep-ultraii', 'library prep with UltraII'),
            ('libprep-ultraiifs', 'library prep with UltraII FS'),
            ('libprep-artic-ultraii', 'library prep with NEB Artic UltraII kit'),
            ('libprep-artic-ultraiifs', 'library prep with NEB Artic UltraIIFS kit'),
        ]
    ),
    (   '@SEQUENCING_KIT', 'Sequencing kit',
        [
            ('merged-data', 'Merged data from more than one run'),
            ('MiSeqV3-600', 'MiSeq 600-cycle v3'),
            ('MiSeqV2-500', 'MiSeq 500-cycle v2'),
            ('MiSeqV2-300', 'MiSeq 300-cycle v2'),
            ('MiSeqMicroV2-300', 'MiSeq 300-cycle v2 Micro'),
            ('MiSeqNanoV2-500', 'MiSeq Nano v2 500-cycle'),
            ('MiSeqNanoV2-300', 'MiSeq Nano v2 300-cycle'),
            ('NextSeqHiV2.5-300', 'NextSeq 500/550 High Output 300-cycle'),
            ('NextSeqHiV2.5-150', 'NextSeq 500/550 High Output 150-cycle'),
            ('NextSeqMidV2.5-300', 'NextSeq 500/550 Mid Output 300-cycle'),
            ('NextSeqMidV2.5-150', 'NextSeq 500/550 Mid Output 150-cycle'),
            ('NovaSeqSPv1.5-500', 'NovaSeq 6000 SP v1.5 500-cycle'),
            ('NovaSeqSPv1.5-300', 'NovaSeq 6000 SP v1.5 300-cycle'),
            ('NovaSeqSPv1.5-200', 'NovaSeq 6000 SP v1.5 200-cycle'),
            ('NovaSeqSPv1.5-100', 'NovaSeq 6000 SP v1.5 100-cycle'),
            ('data-container', 'Container for imported data')
        ]
    ),
    (   '@METHOD', 'Upstream analysis method',
        [
            ('ncov19-pipeline/artic', 'ncov19-pipeline ARTIC mode'),
            ('ncov19-pipeline/mapping', 'ncov19-pipeline generic mapping (minimap2) mode'),
            ('ncov19-pipeline/assembling', 'ncov19-pipeline generic denovo assembling (SPAdes) mode'),
            ('gisaid', 'direct GISAID import'),
            ('other', 'other analysis method'),
        ]
    ),
]
