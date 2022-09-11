
from messy.ext.panelseq.lib import roles as r


def setup(dbh):
    pass


ek_initlist = [

    ('@ROLES', None,
        [
            (r.PANEL_MANAGE, 'manage panel'),
            (r.PANEL_MODIFY, 'modify panel'),
            (r.PANEL_VIEW, 'view panel'),
        ]
     ),
]

# EOF
