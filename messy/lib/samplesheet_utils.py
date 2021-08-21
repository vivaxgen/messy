
import datetime

from messy.lib import adapterindex

complements = dict(a='t', t='a', c='g', g='c', A='T', T='A', C='G', G='C')


def reverse_complemented(sequence):
    return ''.join([complements[x] for x in reversed(sequence)])


def generate_samplesheet(sequencingrun):
    """ generate CSV samplesheet for a particular run """

    # prepare data part for each plate
    instrument = sequencingrun.sequencing_kit
    revcomp = instrument.startswith('novaseq') or instrument.startswith('nextseq')

    data = []
    for runplate in sequencingrun.plates:
        # create (Lane, Sample_Name, Sample_Well, I7_Index_ID, index, I5_Index_ID, index2, Sample_Project) or
        # create (Lane, Sample_Name, Sample_Well, Index_ID, index, index2, Sample_Project)

        index_kit = adapterindex.adapter_indexes[runplate.adapterindex]
        indexes = index_kit['indexes']
        need_revcomp = (revcomp != index_kit['revcomp'])

        lane = runplate.lane

        for platepos, index_item in zip(runplate.plate.positions, indexes):
            if platepos.sample.code in ['-', '*']:
                continue
            if platepos.position != index_item[0]:
                raise ValueError('Position orders for sample and index are not in sync!')
            if need_revcomp:
                index_item = index_item[:-1] + (reverse_complemented(index_item[-1]), )
            data.append((str(lane), platepos.sample.code) + index_item + ('NCOV19-WGS', ))

    if len(data[0]) == 8:
        data.insert(0, ('Lane', 'Sample_Name', 'Sample_Well',
                        'I7_Index_ID', 'index', 'I5_Index_ID', 'index2', 'Sample_Project'))
    else:
        data.insert(0, ('Lane', 'Sample_Name', 'Sample_Well',
                        'Index_ID', 'index', 'index2', 'Sample_Project'))

    lines = [
        ('[Header]', ),
        ('Date', str(datetime.date.today())),
        ('Experiment Name', sequencingrun.code),
        ('Workflow', 'None'),
        ('Application', 'EIMB Sequencing'),
        ('Chemistry', 'Amplicon'),
        (),
        ('[Data]', )
    ] + data

    return '\n'.join([','.join(line) for line in lines])

# EOF
