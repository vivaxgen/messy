
from messy.lib import roles as r
from messy.lib import plate_utils

from dateutil import parser
import uuid


def setup(dbh):

    dbh.Group.bulk_insert(messy_groups, dbsession=dbh.session())

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
            uuid=uuid.uuid4(),
            group=dbh.get_group('CollectionMgr'),
            institutions=[dbh.get_institutions_by_codes('NOT-AVAILABLE', None)[0]],
        )
    )
    dbh.session().flush()

    plates = [
        dbh.Plate(
            code='TEMPLATE-96',
            group=dbh.get_group('PlateMgr'),
            date=parser.parse('1970'),
            specimen_type='water',
            experiment_type='sample-container',
            user=dbh.get_user('system/_SYSTEM_'),
        ),
        dbh.Plate(
            code='TEMPLATE-384',
            group=dbh.get_group('PlateMgr'),
            date=parser.parse('1970'),
            specimen_type='water',
            experiment_type='sample-container',
            user=dbh.get_user('system/_SYSTEM_'),
        )
    ]
    for p in plates:
        dbh.session().add(p)
    dbh.session().flush(plates)

    d_sample = dict(
        collection=dbh.get_collections_by_codes('CONTROL', None, ignore_acl=True)[0],
        received_date=parser.parse('1970'),
        collection_date=parser.parse('1970'),
        passage='original',
        species='no-species',
        host='no-species',
        host_occupation='other',
        host_status='unknown',
        category='Z-CR',
        specimen_type='no-specimen',
        ct_method='no-ct',
        originating_institution=dbh.get_institutions_by_codes('NOT-AVAILABLE', None)[0],
        sampling_institution=dbh.get_institutions_by_codes('NOT-AVAILABLE', None)[0],
    )

    samples = [
        dbh.Sample().update(d_sample | dict(code='-')),
        dbh.Sample().update(d_sample | dict(code='NTC1')),
        dbh.Sample().update(d_sample | dict(code='NTC2')),
        dbh.Sample().update(d_sample | dict(code='NTC3')),
        dbh.Sample().update(d_sample | dict(code='NTC4')),
        dbh.Sample().update(d_sample | dict(code='*')),
    ]
    for s in samples:
        dbh.session().add(s)
    dbh.session().flush(samples)

    plate_utils.create_positions(plates[0], 96)
    plate_utils.create_positions(plates[1], 384)
    dbh.session().flush()


# add additional initial data here

messy_groups = [
    ('InstitutionMgr', [r.INSTITUTION_MANAGE]),
    ('CollectionMgr', [r.COLLECTION_MODIFY, r.COLLECTION_VIEW]),
    ('CollectionViewer', [r.COLLECTION_VIEW]),
    ('SampleMgr', [r.SAMPLE_MANAGE]),
    ('SampleModifier', [r.SAMPLE_MODIFY, r.SAMPLE_VIEW]),
    ('SampleViewer', [r.SAMPLE_VIEW]),
    ('PlateMgr', [r.PLATE_MANAGE]),
    ('PlateModifier', [r.PLATE_MODIFY, r.PLATE_VIEW]),
    ('PlateViewer', [r.PLATE_VIEW]),
    ('SequencingRunMgr', [r.SEQUENCINGRUN_MANAGE]),
    ('SequencingRunModifier', [r.SEQUENCINGRUN_MODIFY, r.SEQUENCINGRUN_VIEW]),
    ('SequencingRunViewer', [r.SEQUENCINGRUN_VIEW]),
    ('SequenceMgr', [r.SEQUENCE_MODIFY, r.SEQUENCE_VIEW]),
    ('SequenceViewer', [r.SEQUENCE_VIEW]),
    ('ProjectMgr', [r.SAMPLE_MODIFY, r.PLATE_MODIFY, r.SEQUENCINGRUN_MODIFY, r.SEQUENCE_MODIFY]),
    ('ProjectViewer', [r.SAMPLE_VIEW, r.PLATE_VIEW, r.SEQUENCINGRUN_VIEW, r.SEQUENCE_VIEW]),
    ('Collaborator', [r.SAMPLE_MODIFY, r.SEQUENCE_VIEW]),
]


ek_initlist = [
    ('@SYSNAME', 'System names',
        [
            ('messy'.upper(), 'messy'),
        ]
     ),
    ('@ROLES', None,
        [
            (r.INSTITUTION_MANAGE, 'manage institution'),
            (r.INSTITUTION_MODIFY, 'modify institution'),
            (r.COLLECTION_MANAGE, 'manage collection'),
            (r.COLLECTION_MODIFY, 'modify collection'),
            (r.COLLECTION_VIEW, 'view collection'),
            (r.SAMPLE_MANAGE, 'manage sample'),
            (r.SAMPLE_MODIFY, 'modify sample'),
            (r.SAMPLE_VIEW, 'view sample'),
            (r.PLATE_MANAGE, 'plate manager'),
            (r.PLATE_MODIFY, 'modify plate'),
            (r.PLATE_VIEW, 'view plate'),
            (r.SEQUENCINGRUN_MANAGE, 'manage sequencing run'),
            (r.SEQUENCINGRUN_MODIFY, 'modify sequencing run'),
            (r.SEQUENCINGRUN_VIEW, 'view sequencing run'),
            (r.SEQUENCE_MANAGE, 'manage sequence'),
            (r.SEQUENCE_MODIFY, 'modify sequence'),
            (r.SEQUENCE_VIEW, 'view sequence'),
        ]
     ),
    ('@SPECIES', "Species",
        [
            ('betacoronavirus', 'betacoronavirus'),
            ('betacoronavirus-ncov19', 'betacoronavirus nCoV-19'),
            ('human', 'human'),
            ('no-species', 'no-species'),
        ]
     ),
    ('@PASSAGE', 'Passage',
        [
            ('original', 'Original'),
            ('vero', 'Vero cell 1st passage'),
            ('vero+2', 'Vero cell 2nd passage'),
            ('hek293', 'HEK293 cell 1st passage'),
            ('hek293+2', 'HEK293 cell 2nd passage')
        ]
     ),
    ('@HOST_STATUS', 'Host status',
        [
            ('unknown', 'Unknown'),
            ('hospitalized', 'Hospitalized'),
            ('live', 'Live'),
            ('deceased', 'Deceased'),
            ('released', 'Released')
        ]
     ),
    ('@HOST_OCCUPATION', 'Host occupation',
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
    ('@CATEGORY', 'Sample category',
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
            ('H-CO', 'H - comorbid case'),
            ('Z-CR', 'Z - Control or reference sample'),
        ]
     ),
    ('@SPECIMEN_TYPE', 'Specimen type',
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
            ('no-specimen', 'no specimen'),
        ]
     ),
    ('@CT_METHOD', 'Ct Methodology',
        [
            ('rtpcr', 'generic realtime RT-PCR'),
            ('cobas', 'Cobas'),
            ('charite-berlin', 'Charite-Berlin method'),
            ('lamp', 'LAMP'),
            ('no-ct', 'No Ct'),
        ]
     ),
    ('@EXPERIMENT_TYPE', 'Laboratory experiment type',
        [
            ('sample-container', 'container for sample storage'),
            ('rna-extraction', 'RNA extraction'),
            ('qc-qubit', 'QC with qubit'),
            ('qc-accuclear', 'QC with AccuClear'),
            ('cdna-ssiv', 'cDNA with Superscript IV'),
            ('cdna-lunascript', 'cDNA with Lunascript'),
            ('pcr-artic-idt', 'PCR with IDT ARTICv3 kit'),
            ('pcr-artic-neb', 'PCR with NEB balanced ARTICv3 kit'),
            ('pcr-artic-covidseq', 'PCR with CovidSeq ARTIC'),
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
    ('@SEQUENCING_KIT', 'Sequencing kit',
        [
            ('merged-data', 'Merged data from more than one run'),
            ('MiSeq-V3-600', 'MiSeq 600-cycle v3'),
            ('MiSeq-V2-500', 'MiSeq 500-cycle v2'),
            ('MiSeq-V2-300', 'MiSeq 300-cycle v2'),
            ('MiSeq-MicroV2-300', 'MiSeq 300-cycle v2 Micro'),
            ('MiSeq-NanoV2-500', 'MiSeq Nano v2 500-cycle'),
            ('MiSeq-NanoV2-300', 'MiSeq Nano v2 300-cycle'),
            ('NextSeq-HiV2.5-300', 'NextSeq 500/550 High Output 300-cycle'),
            ('NextSeq-HiV2.5-150', 'NextSeq 500/550 High Output 150-cycle'),
            ('NextSeq-MidV2.5-300', 'NextSeq 500/550 Mid Output 300-cycle'),
            ('NextSeq-MidV2.5-150', 'NextSeq 500/550 Mid Output 150-cycle'),
            ('NovaSeq-SPv1.5-500', 'NovaSeq 6000 SP v1.5 500-cycle'),
            ('NovaSeq-SPv1.5-300', 'NovaSeq 6000 SP v1.5 300-cycle'),
            ('NovaSeq-SPv1.5-200', 'NovaSeq 6000 SP v1.5 200-cycle'),
            ('NovaSeq-SPv1.5-100', 'NovaSeq 6000 SP v1.5 100-cycle'),
            ('data-container', 'Container for imported data')
        ]
     ),
    ('@METHOD', 'Upstream analysis method',
        [
            ('ncov19-pipeline/artic', 'ncov19-pipeline ARTIC mode'),
            ('ncov19-pipeline/mapping', 'ncov19-pipeline generic mapping (minimap2) mode'),
            ('ncov19-pipeline/assembling', 'ncov19-pipeline generic denovo assembling (SPAdes) mode'),
            ('gisaid', 'direct GISAID import'),
            ('other', 'other analysis method'),
        ]
     ),
    ('@ADAPTERINDEX', 'Adapter-index for sequencing',
        [
            ('covidseq-set-1', 'CovidSeq UDI Set 1 1-96'),
            ('covidseq-set-2', 'CovidSeq UDI Set 2 97-192'),
            ('covidseq-set-3', 'CovidSeq UDI Set 3 193-288'),
            ('covidseq-set-4', 'CovidSeq UDI Set 4 289-384'),
            ('nebnext-udi-set-1', 'NebNext Multiplex Oligo UDI Set 1'),
            ('nebnext-udi-set-2', 'NebNext Multiplex Oligo UDI Set 2'),
            ('nebnext-udi-set-3', 'NebNext Multiplex Oligo UDI Set 3'),
            ('nebnext-udi-set-4', 'NebNext Multiplex Oligo UDI Set 4'),
        ]
     ),
    ('@LINEAGEMETHOD', 'Lineage classification method',
        [
            ('pangolin', 'Pangolin'),
            ('scorpio', 'Scorpio'),
            ('gisaid', 'GISAID'),
            ('nextstrain', 'NextStrain'),
        ]
     ),
]

# EOF
