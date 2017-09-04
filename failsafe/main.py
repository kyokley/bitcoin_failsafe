"""Bitcoin Failsafe

Usage:
    failsafe [-a ACCOUNTS] [-t THRESHOLD]
    failsafe (-r | --recover)
    failsafe (-h | --help)
    failsafe --version

Options:
    -r --recover    Recover a user account from master shards
    -a --accounts   Total number of accounts to be created
    -t --threshold  Number of master shards required to regenerate a user's key
    -h --help       Show this screen.
    --version       Show version
"""
from __future__ import print_function

from docopt import docopt

from ._version import get_versions

from blessings import Terminal
from .failsafe import generate, recover

VERSION = get_versions()['version']

term = Terminal()

def main():
    try:
        arguments = docopt(__doc__, version=get_versions()['version'])
        if arguments['--version']:
            print(VERSION)
        if not arguments['--recover']:
            generate(number_of_accounts=int(arguments['ACCOUNTS'] or 0),
                     key_threshold=int(arguments['THRESHOLD'] or 0))
        else:
            recover()
    except KeyboardInterrupt:
        print(term.red)
        print('Aborted')
        print(term.normal)


if __name__ == '__main__':
    main()
