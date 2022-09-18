
from messy.ext.ngsmgr.lib import roles as r


def setup(dbh):

    dbh.Group.bulk_insert(group_initlist, dbsession=dbh.session())


group_initlist = [
    ('NGSRunMgr', [r.NGSRUN_MANAGE]),
    ('NGSRunModifier', [r.NGSRUN_MODIFY, r.NGSRUN_VIEW]),
]


ek_initlist = [

    ('@ROLES', None,
        [
            (r.NGSRUN_MANAGE, 'manage ngsrun'),
            (r.NGSRUN_MODIFY, 'modify ngsrun'),
            (r.NGSRUN_VIEW, 'view ngsrun'),
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
