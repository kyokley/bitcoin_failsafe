import unittest
import mock

from bitmerchant.wallet import Wallet

from blessings import Terminal
term = Terminal()

from failsafe.failsafe import (generate,
                               _validate_generate_values,
                               recover,
                               )

class TestValidateGenerateValues(unittest.TestCase):
    def test_negative_number_of_users(self):
        self.assertRaises(ValueError,
                          _validate_generate_values,
                          -1,
                          10,
                          2,
                          'asdf')

    def test_negative_accounts(self):
        self.assertRaises(ValueError,
                          _validate_generate_values,
                          1,
                          -10,
                          2,
                          'asdf')

    def test_invalid_key_threshold(self):
        self.assertRaises(ValueError,
                          _validate_generate_values,
                          1,
                          10,
                          2,
                          'asdf')

        self.assertRaises(ValueError,
                          _validate_generate_values,
                          5,
                          10,
                          6,
                          'asdf')

    def test_valid(self):
        expected = None
        actual = _validate_generate_values(6, 10, 5, 'asdf')
        self.assertEqual(expected, actual)

class TestGenerate(unittest.TestCase):
    def setUp(self):
        self._print_patcher = mock.patch('failsafe.failsafe._print')
        self.mock_print = self._print_patcher.start()

        self._get_input_patcher = mock.patch('failsafe.failsafe._get_input')
        self.mock_get_input = self._get_input_patcher.start()

        self.Wallet_patcher = mock.patch('failsafe.failsafe.Wallet')
        self.mock_Wallet = self.Wallet_patcher.start()

        self.BitcoinToB58SecretSharer_patcher = mock.patch('failsafe.failsafe.BitcoinToB58SecretSharer')
        self.mock_BitcoinToB58SecretSharer = self.BitcoinToB58SecretSharer_patcher.start()

        self._validate_generate_values_patcher = mock.patch('failsafe.failsafe._validate_generate_values')
        self.mock_validate_generate_values = self._validate_generate_values_patcher.start()

        self._generateKeys_patcher = mock.patch('failsafe.failsafe._generateKeys')
        self.mock_generateKeys = self._generateKeys_patcher.start()

        self.wallet = mock.MagicMock(Wallet)
        self.wallet.serialize_b58.return_value = 'b58_serialized_wallet'

        self.mock_Wallet.new_random_wallet.return_value = self.wallet

        self.shares = ['shard1', 'shard2', 'shard3']
        self.mock_BitcoinToB58SecretSharer.split_secret.return_value = self.shares

    def tearDown(self):
        self._print_patcher.stop()
        self._get_input_patcher.stop()
        self.Wallet_patcher.stop()
        self.BitcoinToB58SecretSharer_patcher.stop()
        self._validate_generate_values_patcher.stop()
        self._generateKeys_patcher.stop()

    def test_interactive_inputs(self):
        self.mock_get_input.side_effect = [3, 2, 10, 'asdf', '', '', '']

        expected = None
        actual = generate()

        self.assertEqual(expected, actual)
        self.mock_get_input.assert_has_calls(
                [mock.call('Enter number of users participating [1]: ', input_type=int, default=1),
                    mock.call('Enter key threshold [2]: ', input_type=int, default=2),
                 mock.call('Enter number of accounts to be created per user [1]: ', input_type=int, default=1),
                 mock.call('Enter additional entropy [None]: '),
                 mock.call('Press enter to continue when ready'),
                 mock.call('Press enter to continue when ready'),
                 mock.call('Press enter to continue when ready'),
                 ])

        self.mock_validate_generate_values.assert_called_once_with(3, 10, 2, 'asdf')

        self.mock_Wallet.new_random_wallet.assert_called_once_with('asdf')
        self.wallet.serialize_b58.assert_called_once_with()
        self.mock_BitcoinToB58SecretSharer.split_secret.assert_called_once_with('b58_serialized_wallet',
                                                                                2,
                                                                                3)

        self.mock_print.assert_has_calls(
                [mock.call(term.clear),
                 mock.call('The system will now attempt to generate a master key and split it amongst the users\n'
                           'This process may take awhile...'),
                 mock.call('The following screen is meant for user 1 (of 3)\n'
                           'Do not press continue if you are not user 1',
                           formatters=[term.clear, term.red]),
                 mock.call(term.clear),
                 mock.call('The following screen is meant for user 2 (of 3)\n'
                           'Do not press continue if you are not user 2',
                           formatters=[term.clear, term.red]),
                 mock.call(term.clear),
                 mock.call('The following screen is meant for user 3 (of 3)\n'
                           'Do not press continue if you are not user 3',
                           formatters=[term.clear, term.red]),
                 mock.call(term.clear),
                 mock.call('All done'),
              ])

        self.mock_generateKeys.assert_has_calls(
                [mock.call(self.wallet, 0, 10, extra_data={'child': '1 of 3',
                                                           'master_shard': '2-shard1'}),
                 mock.call(self.wallet, 1, 10, extra_data={'child': '2 of 3',
                                                           'master_shard': '2-shard2'}),
                 mock.call(self.wallet, 2, 10, extra_data={'child': '3 of 3',
                                                           'master_shard': '2-shard3'}),
                 ])

    def test_single_user(self):
        expected = None
        actual = generate(number_of_users=1,
                          number_of_accounts=5,
                          key_threshold=1,
                          extra_entropy='asdf')

        self.assertEqual(expected, actual)
        self.mock_get_input.assert_has_calls([
                 mock.call('Press enter to continue when ready'),
                 ])


        self.mock_validate_generate_values.assert_called_once_with(1, 5, 1, 'asdf')

        self.mock_Wallet.new_random_wallet.assert_called_once_with('asdf')
        self.wallet.serialize_b58.assert_called_once_with()
        self.assertFalse(self.mock_BitcoinToB58SecretSharer.called)

        self.mock_print.assert_has_calls(
                [mock.call(term.clear),
                 mock.call('The system will now attempt to generate a master key and split it amongst the users\n'
                           'This process may take awhile...'),
                 mock.call('The following screen is meant for user 1 (of 1)\n'
                           'Do not press continue if you are not user 1',
                           formatters=[term.clear, term.red]),
                 mock.call(term.clear),
                 mock.call('All done'),
              ])

        self.mock_generateKeys.assert_has_calls(
                [mock.call(self.wallet, 0, 5, extra_data={}),
                 ])

class TestRecover(unittest.TestCase):
    def setUp(self):
        self._print_patcher = mock.patch('failsafe.failsafe._print')
        self.mock_print = self._print_patcher.start()

        self._get_input_patcher = mock.patch('failsafe.failsafe._get_input')
        self.mock_get_input = self._get_input_patcher.start()

        self.decrypt_shard_patcher = mock.patch('failsafe.failsafe.decrypt_shard')
        self.mock_decrypt_shard = self.decrypt_shard_patcher.start()

        self.Wallet_patcher = mock.patch('failsafe.failsafe.Wallet')
        self.mock_Wallet = self.Wallet_patcher.start()

        self.BitcoinToB58SecretSharer_patcher = mock.patch('failsafe.failsafe.BitcoinToB58SecretSharer')
        self.mock_BitcoinToB58SecretSharer = self.BitcoinToB58SecretSharer_patcher.start()

        self._generateKeys_patcher = mock.patch('failsafe.failsafe._generateKeys')
        self.mock_generateKeys = self._generateKeys_patcher.start()

        self.mock_BitcoinToB58SecretSharer.recover_secret.return_value = 'master_key'
        self.mock_BitcoinToB58SecretSharer.recover_share.return_value = 'user_share'

        self.mock_decrypt_shard.side_effect = ['2-shard1', '2-shard2']
        self.wallet = mock.MagicMock(Wallet)
        self.mock_Wallet.deserialize.return_value = self.wallet

    def tearDown(self):
        self._print_patcher.stop()
        self._get_input_patcher.stop()
        self.decrypt_shard_patcher.stop()
        self.Wallet_patcher.stop()
        self.BitcoinToB58SecretSharer_patcher.stop()
        self._generateKeys_patcher.stop()

    def test_(self):
        self.mock_get_input.side_effect = [3,
                                           5,
                                           '',
                                           '',
                                           '',
                                           '',
                                           '',
                                           ]

        expected = None
        actual = recover()

        self.assertEqual(expected, actual)
        self.mock_get_input.assert_has_calls([
            mock.call("Enter the index of the user who's key should be regenerated: ", input_type=int),
            mock.call('Enter number of accounts to be created per user [1]: ', input_type=int, default=1),
            mock.call('Press enter to continue'),
            mock.call('Press enter to continue'),
            mock.call('Press enter to continue'),
            mock.call('Press enter to continue'),
            mock.call('Press enter to continue'),
            ])

        self.mock_print.assert_has_calls([
            mock.call(term.clear),
            mock.call(term.clear),
            mock.call('Starting on the next screen, each user will be asked to input their piece of the master key.'),
            mock.call(term.clear),
            mock.call('Attempting to recover keys for user 3'),
            mock.call('Key progress: 0'),
            mock.call(),
            mock.call(),
            mock.call('Shard has been accepted', formatters=term.blue),
            mock.call(term.clear),
            mock.call('The next screen is for the next user.'),
            mock.call(term.clear),
            mock.call('Attempting to recover keys for user 3'),
            mock.call('Key progress: 1'),
            mock.call(),
            mock.call(),
            mock.call('Shard has been accepted', formatters=term.blue),
            mock.call('The next screen is meant for user 3', formatters=term.clear),
            ])

        self.mock_BitcoinToB58SecretSharer.recover_secret.assert_called_once_with(['shard1', 'shard2'])
        self.mock_BitcoinToB58SecretSharer.recover_share.assert_called_once_with(['shard1', 'shard2'], 3)
        self.mock_Wallet.deserialize.assert_called_once_with('master_key')
        self.mock_generateKeys.assert_called_once_with(self.wallet,
                                                       2,
                                                       5,
                                                       extra_data={'master_shard': '2-user_share',
                                                                   'child': 'user 3'})
        self.mock_decrypt_shard.assert_has_calls([mock.call(), mock.call()])


    def test_thresholds_do_not_match(self):
        self.mock_get_input.side_effect = [3,
                                           5,
                                           '',
                                           '',
                                           '',
                                           '',
                                           ]
        self.mock_decrypt_shard.side_effect = ['2-shard1', '3-shard2']

        self.assertRaises(ValueError,
                          recover)

        self.mock_get_input.assert_has_calls([
            mock.call("Enter the index of the user who's key should be regenerated: ", input_type=int),
            mock.call('Enter number of accounts to be created per user [1]: ', input_type=int, default=1),
            mock.call('Press enter to continue'),
            mock.call('Press enter to continue'),
            ])

        self.mock_print.assert_has_calls([
            mock.call(term.clear),
            mock.call(term.clear),
            mock.call('Starting on the next screen, each user will be asked to input their piece of the master key.'),
            mock.call(term.clear),
            mock.call('Attempting to recover keys for user 3'),
            mock.call('Key progress: 0'),
            mock.call(),
            mock.call(),
            mock.call('Shard has been accepted', formatters=term.blue),
            mock.call(term.clear),
            mock.call('The next screen is for the next user.'),
            mock.call(term.clear),
            mock.call('Attempting to recover keys for user 3'),
            mock.call('Key progress: 1'),
            mock.call(),
            ])

        self.assertFalse(self.mock_BitcoinToB58SecretSharer.recover_secret.called)
        self.assertFalse(self.mock_Wallet.deserialize.called)
        self.assertFalse(self.mock_generateKeys.called)
        self.mock_decrypt_shard.assert_has_calls([mock.call(), mock.call()])
