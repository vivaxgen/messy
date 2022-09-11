

def setup(dbh):

    #dbh.EK.bulk_update(ek_initlist, dbsession=dbh.session())
    pass


ek_initlist = [
    (
        '@SPECIES', None,
        [
            ('Pf', 'P falciparum'),
            ('Pf+Pv', 'Mixed Pf + Pv'),
            ('Pv', 'P vivax')
        ]
    ),
    (
        '@BLOOD-WITHDRAWAL', 'Blood widthdrawal method',
        [
            ('NA', 'Not available'),
            'venous',
            'capillary',
        ]
    ),
    (
        '@BLOOD-STORAGE', 'Blood storage/source method',
        [
            ('NA', 'Not available'),
            'EDTA',
            'blood tube',
            'filter paper',
        ]
    ),
    (
        '@PCR-METHOD', 'PCR identification method',
        [
            ('NA', 'Not available'),
        ]
    ),
    (
        '@EXTFIELD', None,
        [
            'severity',
        ]
    ),
]

# EOF
