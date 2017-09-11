import os
import tempfile
import json
import shutil
import qrcode
import qrcode_terminal

from secretsharing import BitcoinToB58SecretSharer

from blessings import Terminal
from bitmerchant.wallet import Wallet

from .utils import _get_input, _print

term = Terminal()

def generate(number_of_users=None,
             number_of_accounts=None,
             key_threshold=None,
             extra_entropy=None):
    _print(term.clear)

    if number_of_users is None:
        number_of_users = _get_input('Enter number of users participating [1]: ', input_type=int, default=1)

    if number_of_users > 1 and not key_threshold:
        key_threshold = _get_input('Enter key threshold [1, {}]: '.format(number_of_users), input_type=int, default=number_of_users)

    if number_of_accounts is None:
        number_of_accounts = _get_input('Enter number of accounts to be created per user [1]: ', input_type=int, default=1)

    if not extra_entropy:
        extra_entropy = _get_input('Enter additional entropy [None]: ')

    master_wallet = Wallet.new_random_wallet(extra_entropy)
    serialized_wallet = master_wallet.serialize_b58()

    if number_of_users > 1:
        shares = BitcoinToB58SecretSharer.split_secret(serialized_wallet.encode(),
                                                       key_threshold,
                                                       number_of_users)
    else:
        shares = None

    for user_index in range(number_of_users):
        _print(('The following screen is meant for user {index} (of {total})\n'
                'Do not press continue if you are not user {index}').format(index=user_index + 1,
                                                                            total=number_of_users),
               formatters=[term.clear, term.red])

        _get_input('Press enter to continue when ready')
        _print(term.clear)

        if number_of_users > 1:
            data = {'child': '{index} of {total}'.format(index=user_index + 1,
                                                         total=number_of_users),
                    'master_shard': '{}-{}'.format(key_threshold, shares[user_index]),
                    }
        else:
            data = {}
        _generateKeys(master_wallet, user_index, number_of_accounts, extra_data=data)

    _print('All done')

def recover():
    shards = []

    user_index = _get_input("Enter the index of the user who's key should be regenerated: ", input_type=int) - 1
    number_of_accounts = _get_input('Enter number of accounts to be created per user [1]: ',
                                    input_type=int,
                                    default=1)
    _print(term.clear)

    _print('Starting on the next screen, each user will be asked to input their piece of the master key.')
    _get_input('Press enter to continue')

    _print(term.clear)
    _print('Attempting to recover keys for user {}'.format(user_index + 1))
    _print('Key progress: 0')
    _print()
    piece = _get_input('Enter first shard: ')
    initial_threshold, shard = piece.split('-', 1)
    initial_threshold = int(initial_threshold)
    shards.append(shard)

    for i in range(1, initial_threshold):
        _print(term.clear)
        _print('The next screen is for the next user.')
        _get_input('Press enter to continue')

        _print(term.clear)
        _print('Attempting to recover keys for user {}'.format(user_index + 1))
        _print('Key progress: {}'.format(i))
        _print()
        piece = _get_input('Enter shard: ')
        threshold, shard = piece.split('-', 1)
        shards.append(shard)

        if initial_threshold != int(threshold):
            raise Exception('Shard thresholds do not match. An invalid shard has been provided.')

    master_key = BitcoinToB58SecretSharer.recover_secret(shards)
    master_wallet = Wallet.deserialize(master_key)

    _generateKeys(master_wallet, user_index, number_of_accounts)

def _generateKeys(master_wallet, user_index, number_of_accounts, extra_data=None):
    directory = tempfile.mkdtemp()
    user_key = master_wallet.get_child(user_index, is_prime=True)

    data = {'user_key': user_key.export_to_wif(),
            'pub_priv_accounts': [],
            }
    if extra_data:
        data.update(extra_data)

    first = None
    for idx in range(number_of_accounts):
        child = user_key.get_child(idx, is_prime=True)

        if idx == 0:
            first = child

        img = qrcode.make(child.export_to_wif())
        qr_filename = os.path.join(directory, 'child{}.priv.png'.format(idx + 1))
        img.save(qr_filename)

        img = qrcode.make(child.to_address())
        qr_filename = os.path.join(directory, 'child{}.pub.png'.format(idx + 1))
        img.save(qr_filename)

        data['pub_priv_accounts'].append(child.export_to_wif())

    filename = os.path.join(directory, 'child{}.priv.json'.format(user_index + 1))
    json_data = json.dumps(data)
    with open(filename, 'w+b') as f:
        f.write(json_data)

    if 'master_shard' in data:
        shard_img = qrcode.make(data['master_shard'])
        shard_img_filename = os.path.join(directory, 'child{}_shard.png'.format(user_index + 1))
        shard_img.save(shard_img_filename)

    _print(('Key for user {user_index}:\n'
            'Data has been written to {filename}\n'
            'QR codes have been written for {number_of_accounts} account(s)').format(number_of_accounts=number_of_accounts,
                                                                                     filename=filename,
                                                                                     user_index=user_index + 1),
            formatters=[term.clear, term.blue])
    _print()
    _print('Take the time to copy these files before continuing\n'
           'After leaving this screen, the files will be destroyed')
    _print()
    _print('BE EXTREMELY CAREFUL WITH THE ACCOUNT AND SHARD INFORMATION\n'
           'Especially when handling data in the QR form. A picture of the QR code may be enough to steal your entire account\n'
           'and potentially compromise the other linked accounts',
           formatters=[term.red, term.bold])
    _print()

    if first:
        _print('Your first account address is being displayed here for your convenience')
        _print()
        address = first.to_address()
        _print(address)
        _print()
        qrcode_terminal.draw(address)
        _print()
    _get_input('Press enter to continue when ready')

    shutil.rmtree(directory)
    _print(term.clear)

def rekey():
    # TODO: I need to figure out how this functionality should work

    raise NotImplemented
    shards = []

    print(term.clear)

    print('Starting on the next screen, each user will be asked to input their piece of the master key.')
    _get_input('Press enter to continue')

    print(term.clear)
    print('Attempting to recover master wallet')
    print('Key progress: 0')
    print()
    piece = _get_input('Enter first shard: ')
    initial_threshold, shard = piece.split('-', 1)
    initial_threshold = int(initial_threshold)
    shards.append(shard)

    for i in range(1, initial_threshold):
        print(term.clear)
        print('The next screen is for the next user.')
        _get_input('Press enter to continue')

        print(term.clear)
        print('Attempting to recover master wallet')
        print('Key progress: {}'.format(i))
        print()
        piece = _get_input('Enter shard: ')
        threshold, shard = piece.split('-', 1)
        shards.append(shard)

        if initial_threshold != int(threshold):
            raise Exception('Shard thresholds do not match. An invalid shard has been provided.')

    master_key = BitcoinToB58SecretSharer.recover_secret(shards)
    master_wallet = Wallet.deserialize(master_key)
