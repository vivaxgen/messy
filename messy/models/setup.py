
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


    d_collection = dict(
        group=dbh.get_group('CollectionMgr'),
        institutions=[dbh.get_institutions_by_codes('NOT-AVAILABLE', None)[0]],
        refctrl=True,
    )

    collections = [
        dbh.Collection(** (d_collection | dict(code='CONTROL'))).update({}),
        dbh.Collection(** (d_collection | dict(code='REFERENCE'))).update({}),
    ]
    for c in collections:
        dbh.session().add(c)
    dbh.session.flush(collections)

    d_plate = dict(
        group=dbh.get_group('PlateMgr'),
        date=parser.parse('1970'),
        specimen_type='water',
        experiment_type='sample-container',
        user=dbh.get_user('system/_SYSTEM_'),
        refctrl=True,
    )

    plates = [
        dbh.Plate(** (d_plate | dict(code='TEMPLATE-24'))),
        dbh.Plate(** (d_plate | dict(code='TEMPLATE-48'))),
        dbh.Plate(** (d_plate | dict(code='TEMPLATE-96'))),
        dbh.Plate(** (d_plate | dict(code='TEMPLATE-384'))),
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
        category='CR',
        specimen_type='no-specimen',
        ct_method='no-ct',
        originating_institution=dbh.get_institutions_by_codes('NOT-AVAILABLE', None)[0],
        sampling_institution=dbh.get_institutions_by_codes('NOT-AVAILABLE', None)[0],
        refctrl=True,
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
    ('ProjectMgr', [r.SAMPLE_MODIFY, r.PLATE_MODIFY]),
    ('ProjectViewer', [r.SAMPLE_VIEW, r.PLATE_VIEW]),
    ('Collaborator', [r.SAMPLE_MODIFY]),
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
            ('RS', 'Random surveillance and tracking'),
            ('SS', 'Sentinel surveillance'),
            ('TH', 'Sample with travel history'),
            ('CR', 'Control or reference sample'),
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
]

# EOF
