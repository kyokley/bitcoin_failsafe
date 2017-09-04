from __future__ import print_function

import os
import tempfile
import json

from secretsharing import BitcoinToB58SecretSharer

from blessings import Terminal
from bitmerchant.wallet import Wallet

term = Terminal()

def generate(number_of_accounts=None,
             key_threshold=None):
    directory = tempfile.mkdtemp()
    print(term.clear)

    if not number_of_accounts:
        number_of_accounts = int(raw_input('Enter how many accounts to create: '))

    if not key_threshold:
        key_threshold = int(raw_input('Enter key threshold: '))
    print()

    master_wallet = Wallet.new_random_wallet()
    serialized_wallet = master_wallet.serialize_b58().encode()
    shares = BitcoinToB58SecretSharer.split_secret(serialized_wallet,
                                                   key_threshold,
                                                   number_of_accounts)
    print('Temp dir at {}'.format(directory))

    for i in range(number_of_accounts):
        print(term.clear)
        print(term.red)
        print('The following screen is meant for user {index} (of {total})'.format(index=i + 1,
                                                                                   total=number_of_accounts))
        print('Do not press continue if you are not user {index}'.format(index=i + 1))
        print(term.normal)
        print()

        raw_input('Press enter to continue when ready')
        print(term.clear)


        child = master_wallet.get_child(i)
        data = {'child': '{index} of {total}'.format(index=i + 1,
                                                     total=number_of_accounts),
                'master_shard': '{}-{}'.format(key_threshold, shares[i]),
                'account': child.serialize_b58(),
                }
        json_data = json.dumps(data)

        filename = os.path.join(directory, 'child{}.txt'.format(i + 1))
        with open(filename, 'w+b') as f:
            f.write(json_data)

        print(term.blue)
        print('Data has been written to {}'.format(filename))
        print()
        print(term.red)
        print('Take the time to copy the file before continuing')
        print('After leaving this screen, the file will be destroyed')
        print(term.normal)
        print()
        raw_input('Press enter to continue when ready')

        os.remove(filename)

    print(term.clear)
    print(term.normal)
    print('All done')

def recover():
    shards = []

    user_index = int(raw_input("Enter the index of the user who's key should be regenerated: ")) - 1
    print(term.clear)

    print('Starting on the next screen, each user will be asked to input their piece of the master key.')
    raw_input('Press enter to continue')

    print(term.clear)
    print('Attempting to recover keys for user #{}'.format(user_index + 1))
    print('Key progress: 0')
    print()
    piece = raw_input('Enter first shard: ')
    initial_threshold, shard = piece.split('-', 1)
    initial_threshold = int(initial_threshold)
    shards.append(shard)

    for i in range(1, initial_threshold):
        print(term.clear)
        print('The next screen is for the next user.')
        raw_input('Press enter to continue')

        print(term.clear)
        print('Attempting to recover keys for user #{}'.format(user_index + 1))
        print('Key progress: {}'.format(i))
        print()
        piece = raw_input('Enter shard: ')
        threshold, shard = piece.split('-', 1)
        shards.append(shard)

        if initial_threshold != int(threshold):
            raise Exception('Shard thresholds do not match. An invalid shard has been provided.')

    master_key = BitcoinToB58SecretSharer.recover_secret(shards)
    master_wallet = Wallet.deserialize(master_key)
    child_wallet = master_wallet.get_child(user_index)

    print(term.clear)
    print('Key for user #{}:'.format(user_index + 1))
    print(child_wallet.serialize_b58())

def rekey():
    # TODO: I need to figure out how this functionality should work

    raise NotImplemented
    shards = []

    print(term.clear)

    print('Starting on the next screen, each user will be asked to input their piece of the master key.')
    raw_input('Press enter to continue')

    print(term.clear)
    print('Attempting to recover master wallet')
    print('Key progress: 0')
    print()
    piece = raw_input('Enter first shard: ')
    initial_threshold, shard = piece.split('-', 1)
    initial_threshold = int(initial_threshold)
    shards.append(shard)

    for i in range(1, initial_threshold):
        print(term.clear)
        print('The next screen is for the next user.')
        raw_input('Press enter to continue')

        print(term.clear)
        print('Attempting to recover master wallet')
        print('Key progress: {}'.format(i))
        print()
        piece = raw_input('Enter shard: ')
        threshold, shard = piece.split('-', 1)
        shards.append(shard)

        if initial_threshold != int(threshold):
            raise Exception('Shard thresholds do not match. An invalid shard has been provided.')

    master_key = BitcoinToB58SecretSharer.recover_secret(shards)
    master_wallet = Wallet.deserialize(master_key)