
from rhombus.scripts import setup_settings, arg_parser
from rhombus.lib.utils import cerr, cout, cexit, get_dbhandler
from rhombus.models.core import set_func_userid

import transaction
import yaml


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

    p.add_argument('--import_institutions', action='store_true',
                   help='import instituions')

    p.add_argument('--import_runs', action='store_true',
                   help='import sequencing runs')

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

    else:
        cerr('Please provide correct operation')


def do_export_institutions(args, dbh):
    yaml_write(args, [inst.as_dict() for inst in dbh.Institution.query(dbh.session())],
               'Institution')


def do_import_institutions(args, dbh):
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


def yaml_write(args, data, msg):
    with open(args.outfile, 'w') as outstream:
        yaml.dump_all(data, outstream, default_flow_style=False)
    cerr(f'[Exported {msg} to {args.outfile}]')

# EOF
