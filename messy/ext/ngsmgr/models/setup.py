
from messy.ext.ngsmgr.lib import roles as r
from messy.ext.ngsmgr.models.schema import PanelType
from dateutil import parser


def setup(dbh):

    dbh.Group.bulk_insert(group_initlist, dbsession=dbh.session())

    d_ngsrun = dict(
        date=parser.parse('1970'),
        refctrl=True,
        group=dbh.get_group('NGSRunMgr'),
        ngs_provider=dbh.get_institutions_by_codes('IRRELEVANT', None).one(),
        ngs_kit='data-container',
    )

    ngsruns = [
        dbh.NGSRun(** (d_ngsrun | dict(code='ILMN-INDEPENDENT-RUN', serial='SYSTEM-01'))),
        dbh.NGSRun(** (d_ngsrun | dict(code='ONT-INDEPENDENT-RUN', serial='SYSTEM-02'))),
        dbh.NGSRun(** (d_ngsrun | dict(code='PACBIO-INDEPENDENT-RUN', serial='SYSTEM-03'))),
    ]
    for run in ngsruns:
        dbh.session().add(run)
    dbh.session().flush(ngsruns)

    d_panel = dict(
        type=PanelType.SET.value,
        refctrl=True,
        species='no-species',
        group=dbh.get_group('PanelMgr')
    )

    panels = [
        dbh.Panel(** (d_panel | dict(code='WGS-generic'))).update({}),
    ]
    for panel in panels:
        dbh.session().add(panel)
    dbh.session().flush(panels)


group_initlist = [
    ('NGSRunMgr', [r.NGSRUN_MANAGE]),
    ('NGSRunModifier', [r.NGSRUN_MODIFY, r.NGSRUN_VIEW]),
    ('PanelMgr', [r.PANEL_MANAGE]),
    ('PanelModifier', [r.PANEL_MODIFY, r.PANEL_VIEW]),
    ('FastqPairMgr', [r.FASTQPAIR_MANAGE]),
    ('FastqPairModifier', [r.FASTQPAIR_MODIFY, r.FASTQPAIR_VIEW])
]


ek_initlist = [

    ('@ROLES', None,
        [
            (r.NGSRUN_MANAGE, 'manage ngsrun'),
            (r.NGSRUN_MODIFY, 'modify ngsrun'),
            (r.NGSRUN_VIEW, 'view ngsrun'),
            (r.PANEL_MANAGE, 'manage panel'),
            (r.PANEL_MODIFY, 'modify panel'),
            (r.PANEL_VIEW, 'view panel'),
            (r.FASTQPAIR_MANAGE, 'manage fastqpair'),
            (r.FASTQPAIR_MODIFY, 'modify fastqpair'),
            (r.FASTQPAIR_VIEW, 'view fastqpair'),
        ]
     ),
    ('@NGS_KIT', 'NGS kit',
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
    ('@ADAPTERINDEX', 'Adapter-index for sequencing',
        [
            ('custom-index', 'Custom index'),
            ('nebnext-udi-set-1', 'NebNext Multiplex Oligo UDI Set 1'),
            ('nebnext-udi-set-2', 'NebNext Multiplex Oligo UDI Set 2'),
            ('nebnext-udi-set-3', 'NebNext Multiplex Oligo UDI Set 3'),
            ('nebnext-udi-set-4', 'NebNext Multiplex Oligo UDI Set 4'),
        ]
     ),
]

# EOF
