from __future__ import print_function

import os
import tempfile
import json

from secretsharing import BitcoinToB58SecretSharer

from blessings import Terminal
from bitmerchant.wallet import Wallet

term = Terminal()

def main():
    directory = tempfile.mkdtemp()
    print(term.clear)
    number_of_accounts = int(raw_input('Enter how many accounts to create: '))
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
                'master_shard': shares[i],
                'account': child.serialize_b58(),
                }
        json_data = json.dumps(data)

        filename = os.path.join(directory, 'child{}.txt'.format(i))
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


if __name__ == '__main__':
    main()
