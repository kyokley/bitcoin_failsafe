import os
import tempfile
import json
import shutil
import qrcode
import qrcode_terminal
import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from secretsharing import BitcoinToB58SecretSharer

from blessings import Terminal
from bitmerchant.wallet import Wallet

from .utils import _get_input, _print, word_generator

PASSPHRASE_WORD_LENGTH = 8
SALT_LENGTH = 32
term = Terminal()
word_gen = word_generator()

def _validate_generate_values(number_of_users,
                              number_of_accounts,
                              key_threshold,
                              extra_entropy):
    if number_of_users < 1:
        raise ValueError('Number of users must be greater than 1')

    if number_of_accounts < 1:
        raise ValueError('Number of accounts must be greater than 1')

    if key_threshold < 1 or key_threshold > number_of_users:
        raise ValueError('Key threshold must be greater than 1 and less than or equal to the number of users participating')

def generate(number_of_users=None,
             number_of_accounts=None,
             key_threshold=None,
             extra_entropy=None):
    _print(term.clear)

    if number_of_users is None:
        number_of_users = _get_input('Enter number of users participating [1]: ', input_type=int, default=1)

    if number_of_users > 1 and not key_threshold:
        key_threshold = _get_input('Enter key threshold [Default: 1 Min: 1 Max: {}]: '.format(number_of_users), input_type=int, default=number_of_users)

    if number_of_accounts is None:
        number_of_accounts = _get_input('Enter number of accounts to be created per user [1]: ', input_type=int, default=1)

    if not extra_entropy:
        extra_entropy = _get_input('Enter additional entropy [None]: ')

    _validate_generate_values(number_of_users,
                              number_of_accounts,
                              key_threshold,
                              extra_entropy)
    _print('The system will now attempt to generate a master key and split it amongst the users\n'
           'This process may take awhile...')

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

    key_progress = 0
    finished = False

    while not finished:
        _print(term.clear)
        if key_progress == 0:
            _print('Starting on the next screen, each user will be asked to input their piece of the master key.')
        else:
            _print('The next screen is for the next user.')
        _get_input('Press enter to continue')

        _print(term.clear)
        _print('Attempting to recover keys for user {}'.format(user_index + 1))
        _print('Key progress: {}'.format(key_progress))
        _print()

        piece = decrypt_shard()

        threshold, shard = piece.split('-', 1)
        shards.append(shard)

        if key_progress == 0:
            initial_threshold = int(threshold)
        else:
            if initial_threshold != int(threshold):
                raise ValueError('Shard thresholds do not match. An invalid shard has been provided.')

        _print()
        _print('Shard has been accepted', formatters=term.blue)
        _get_input('Press enter to continue')

        key_progress += 1

        if key_progress == int(threshold):
            finished = True

    _print('The next screen is meant for user {}'.format(user_index + 1), formatters=term.clear)
    _get_input('Press enter to continue')

    master_key = BitcoinToB58SecretSharer.recover_secret(shards)
    master_wallet = Wallet.deserialize(master_key)

    _generateKeys(master_wallet, user_index, number_of_accounts)

def _generateKeys(master_wallet, user_index, number_of_accounts, extra_data=None):
    directory = tempfile.mkdtemp()
    user_key = master_wallet.get_child(user_index, is_prime=True)

    data = {'user_key': user_key.serialize_b58(),
            'wif_accounts': [],
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

        data['wif_accounts'].append(child.export_to_wif())

    if 'master_shard' in data:
        salt = os.urandom(SALT_LENGTH)
        shard = data.pop('master_shard')
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),
                         length=32,
                         salt=salt,
                         iterations=100000,
                         backend=default_backend())
        words = [word_gen.next() for x in range(PASSPHRASE_WORD_LENGTH)]
        passphrase = ' '.join(words)
        key = base64.urlsafe_b64encode(kdf.derive(passphrase))
        f = Fernet(key)
        token = f.encrypt(shard)

        data['encrypted_shard'] = '{}${}'.format(base64.urlsafe_b64encode(salt),
                                                 base64.urlsafe_b64encode(token))
        data['passphrase'] = passphrase
        shard_img = qrcode.make(data['encrypted_shard'])
        shard_img_filename = os.path.join(directory, 'child{}_shard.png'.format(user_index + 1))
        shard_img.save(shard_img_filename)

    filename = os.path.join(directory, 'user_info.priv.json'.format(user_index + 1))
    json_data = json.dumps(data)
    with open(filename, 'w+b') as f:
        f.write(json_data)

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

def decrypt_shard():
    encoded_salt, encrypted_shard = _get_input('Enter encrypted shard: ').strip().split('$')
    salt = base64.urlsafe_b64decode(encoded_salt)

    _print()
    done = False
    while not done:
        words = []
        for i in range(1, PASSPHRASE_WORD_LENGTH + 1):
            words.append(_get_input('Enter word #{}: '.format(i), secure=True).strip())

        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),
                         length=32,
                         salt=salt,
                         iterations=100000,
                         backend=default_backend())
        passphrase = ' '.join(words)
        key = base64.urlsafe_b64encode(kdf.derive(passphrase))
        f = Fernet(key)
        try:
            decrypted_shard = f.decrypt(base64.urlsafe_b64decode(encrypted_shard))
        except InvalidToken:
            _print('Failed to decrypt shard. Try Again.', formatters=term.red)
            _print()
            continue
        done = True
    return decrypted_shard
