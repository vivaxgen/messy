
from rhombus.scripts import setup_settings, arg_parser
from rhombus.lib.utils import cerr, cout, cexit, get_dbhandler
from rhombus.lib.mgr import yaml_write, yaml_read
from rhombus.models.core import set_func_userid
from messy.lib.whoosh import set_index_service, IndexService

import transaction
import yaml
import os.path


def init_argparser(parser=None):

    if parser is None:
        p = arg_parser('mgr [options]')
    else:
        p = parser

    p.add_argument('--dump', default=False, action='store_true',
                   help='dump data to destination directory')

    p.add_argument('--load', default=False, action='store_true',
                   help='load data source directory')

    p.add_argument('--export_institutions', action='store_true',
                   help='export institutions')

    p.add_argument('--export_runs', action='store_true',
                   help='export sequencing runs')

    p.add_argument('--export_collections', action='store_true',
                   help='export collections (including their samples')

    p.add_argument('--export_plates', action='store_true',
                   help='export runs (including well positions)')

    p.add_argument('--import_institutions', action='store_true',
                   help='import instituions')

    p.add_argument('--import_runs', action='store_true',
                   help='import sequencing runs')

    p.add_argument('--import_collections', action='store_true',
                   help='import collections')

    p.add_argument('--import_plates', action='store_true',
                   help='import plates')

    p.add_argument('--backup', action='store_true',
                   help='backup to YAML files')

    p.add_argument('--restore', action='store_true',
                   help='restore from YAML files')

    p.add_argument('--whoosh_reindex', action='store_true',
                   help='reindex Whoosh search engine')

    p.add_argument('--change_sample_codes', action='store_true',
                   help='change sample code from old_code to new_code in csv/tsv file')

    # options
    p.add_argument('--with_samples', default=False, action='store_true',
                   help='export samples as well when exporting collections')

    p.add_argument('--srcdir')
    p.add_argument('--dstdir')

    p.add_argument('-o', '--outfile')
    p.add_argument('-i', '--infile')

    p.add_argument('--login', default='')
    p.add_argument('--commit', default=False, action='store_true')

    return p


def main(args):

    settings = setup_settings(args)
    set_index_service(IndexService(settings['messy.whoosh.path']))

    if args.commit:
        with transaction.manager:
            do_mgr(args, settings)
            cerr('** COMMIT database **')

    else:
        do_mgr(args, settings)


def do_mgr(args, settings, dbh=None):

    if not dbh:
        dbh = get_dbhandler(settings)

    # perform function here

    if args.export_institutions:
        do_export_institutions(args, dbh)

    elif args.import_institutions:
        do_import_institutions(args, dbh)

    elif args.export_runs:
        do_export_runs(args, dbh)

    elif args.import_runs:
        do_import_runs(args, dbh)

    elif args.export_collections:
        do_export_collections(args, dbh)

    elif args.import_collections:
        do_import_collections(args, dbh)

    elif args.export_plates:
        do_export_plates(args, dbh)

    elif args.import_plates:
        do_import_plates(args, dbh)

    elif args.backup:
        do_backup(args, dbh)

    elif args.restore:
        do_restore(args, dbh)

    elif args.whoosh_reindex:
        do_whoosh_reindex(args, dbh)

    elif args.change_sample_codes:
        do_change_sample_codes(args, dbh)

    else:
        cerr('Please provide correct operation')


def do_export_institutions(args, dbh):
    yaml_write(args, [inst.as_dict() for inst in dbh.Institution.query(dbh.session())],
               'Institution')


def do_import_institutions(args, dbh):
    return yaml_read(args, dbh, dbh.Institution)
    c = 0
    with open(args.infile) as instream:
        for inst_dict in yaml.safe_load_all(instream):
            inst = dbh.Institution.from_dict(inst_dict, dbh)
            cerr(f'[I - uploaded institution: {inst.code}]')
            c += 1
    cerr(f'[I - institution uploaded: {c}]')


def do_export_runs(args, dbh):
    yaml_write(args, [seqrun.as_dict() for seqrun in dbh.SequencingRun.query(dbh.session())],
               'SequencingRun')


def do_import_runs(args, dbh):
    return yaml_read(args, dbh, dbh.SequencingRun)

    c = 0
    with open(args.infile) as instream:
        for run_dict in yaml.safe_load_all(instream):
            run = dbh.SequencingRun.from_dict(run_dict, dbh)
            cerr(f'[I - uploaded sequencing run: {run.code}]')
            c += 1
    cerr(f'[I - sequencing run uploaded: {c}]')


def do_export_collections(args, dbh):
    sess = dbh.session()
    yaml_write(args, [collection.as_dict(export_samples=args.with_samples)
                      for collection in dbh.Collection.query(sess)],
               'Collection')


def do_import_collections(args, dbh):
    return yaml_read(args, dbh, dbh.Collection)

    c = 0
    with open(args.infile) as instream:
        for coll_dict in yaml.safe_load_all(instream):
            coll = dbh.Collection.from_dict(coll_dict, dbh)
            cerr(f'[I - uploaded collection: {coll.code}]')
            c += 1
            dbh.session().flush([coll])
    cerr(f'[I - collection uploaded: {c}]')


def do_export_plates(args, dbh):
    sess = dbh.session()
    yaml_write(args, [plate.as_dict()
                      for plate in dbh.Plate.query(sess)],
               'Plate')


def do_import_plates(args, dbh):
    yaml_read(args, dbh, dbh.Plate)


def do_export_sequences(args, dbh):
    sess = dbh.session()
    yaml_write(args, [sequence.as_dict()
                      for sequence in dbh.Sequence.query(sess)],
               'Sequence')


def do_import_sequences(args, dbh):
    return yaml_read(args, dbh, dbh.Sequence)


def do_backup(args, dbh):

    args.outfile = os.path.join(args.dstdir, 'institutions.yaml')
    do_export_institutions(args, dbh)

    args.with_samples = True
    args.outfile = os.path.join(args.dstdir, 'collections.yaml')
    do_export_collections(args, dbh)

    args.outfile = os.path.join(args.dstdir, 'plates.yaml')
    do_export_plates(args, dbh)

    args.outfile = os.path.join(args.dstdir, 'sequencingruns.yaml')
    do_export_runs(args, dbh)

    args.outfile = os.path.join(args.dstdir, 'sequences.yaml')
    do_export_sequences(args, dbh)


def do_restore(args, dbh):
    # to restore database, do in the following order:
    # restore Institution
    # restore Collection (including samples)
    # restore Plate
    # restore SequencingRun
    # restore Sequence

    args.infile = os.path.join(args.srcdir, 'institutions.yaml')
    do_import_institutions(args, dbh)
    dbh.session().flush()

    args.infile = os.path.join(args.srcdir, 'collections.yaml')
    do_import_collections(args, dbh)
    dbh.session().flush()

    args.infile = os.path.join(args.srcdir, 'plates.yaml')
    do_import_plates(args, dbh)
    dbh.session().flush()

    args.infile = os.path.join(args.srcdir, 'sequencingruns.yaml')
    do_import_runs(args, dbh)
    dbh.session().flush()

    args.infile = os.path.join(args.srcdir, 'sequences.yaml')
    do_import_sequences(args, dbh)


def do_whoosh_reindex(args, dbh):
    from messy.lib import whoosh
    whoosh.reindex()


def do_change_sample_codes(args, dbh):

    import pandas as pd

    # read infile
    sep = '\t' if args.infile.endswith('.tsv') else ','
    translate_table = pd.read_table(args.infile, sep=sep)

    for _, r in translate_table.iterrows():
        #print(r)
        #import IPython; IPython.embed()
        samples = dbh.get_samples_by_codes(r['old_code'], groups=None, ignore_acl=True)
        if len(samples) == 0:
            raise ValueError(f"sample with code [{r['old_code']}] is not found!")
        samples[0].code = r['new_code']


def yaml_write(args, data, msg, printout=False):
    if printout:
        # this is for debugging purpose, obviously
        import pprint
        for d in data:
            pprint.pprint(d)
            pprint.pprint(yaml.dump(d))
    with open(args.outfile, 'w') as outstream:
        yaml.dump_all(data, outstream, default_flow_style=False)
    cerr(f'[Exported {msg} to {args.outfile}]')

# EOF
