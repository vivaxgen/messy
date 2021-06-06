
import sys, os
import argparse

from rhombus.scripts.run import main as rhombus_main, set_config
from rhombus.lib.utils import cout, cerr, cexit

from messy.models.handler import DBHandler

def greet():
    cerr('command line utility for MESSy')


def usage():
    cerr('messy-run - command line utility for MESSy')
    cerr('usage:')
    cerr('\t%s scriptname [options]' % sys.argv[0])
    sys.exit(0)


set_config( environ='RHOMBUS_CONFIG',
            paths = ['messy.scripts.'],
            greet = greet,
            usage = usage,
            dbhandler_class = DBHandler,
            includes = ['messy.includes'],
)

main = rhombus_main



