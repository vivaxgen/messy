

import itertools
from sqlalchemy.orm import object_session

plate_layouts = {
    6: (2, 3),
    12: (3, 4),
    24: (4, 6),
    48: (6, 8),
    96: (8, 12),
    384: (16, 24)
}

row_labels = 'ABCDEFGHIJKLMNOP'


def create_labels(r, c):
    return [f'{i}{j:02d}' for (j, i) in itertools.product(range(1, c + 1), row_labels[:r])]


def create_positions(plate, size):
    r, c = plate_layouts[size]
    labels = create_labels(r, c)

    return plate.add_positions(labels)


def copy_positions(plate, source_plate):
    dbsess = object_session(plate)
    for pp in source_plate.positions:
        new_pp = pp.clone_sample()
        new_pp.plate_id = plate.id
        dbsess.add(new_pp)


def create_indexadapter_list(labels, index_text):

    indexes = [tuple(line.strip().split()) for line in index_text.split('\n') if line.strip()]
    return [(label, ) + index_item for (label, index_item) in zip(labels, indexes)]

# EOF
