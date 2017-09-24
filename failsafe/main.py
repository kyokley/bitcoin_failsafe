"""Bitcoin Failsafe

Usage:
    failsafe [-u USERS] [-a ACCOUNTS] [-t THRESHOLD] [-e ENTROPY]
    failsafe (-r | --recover)
    failsafe (-h | --help)
    failsafe --version

Options:
    -u --users      Number of users participating
    -a --accounts   Number of accounts to be created per user
    -t --threshold  Number of master shards required to regenerate a user's key
    -r --recover    Recover a user account from master shards
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
            generate(number_of_accounts=int(arguments['ACCOUNTS']) if arguments['ACCOUNTS'] else None,
                     key_threshold=int(arguments['THRESHOLD']) if arguments['THRESHOLD'] else None,
                     number_of_users=int(arguments['USERS']) if arguments['USERS'] else None)
        else:
            recover()
    except KeyboardInterrupt:
        print(term.red)
        print('Aborted')
        print(term.normal)


if __name__ == '__main__':
    main()
