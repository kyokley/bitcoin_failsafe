# Bitcoin Failsafe [![Build Status](https://travis-ci.org/kyokley/bitcoin_failsafe.svg?branch=master)](https://travis-ci.org/kyokley/bitcoin_failsafe)
Generate a group of linked HD wallets with a recoverable master wallet in case of emergency

## Purpose
One of the interesting properties of bitcoin is that anyone can see money flowing into an account with just the public key. However, the associated private key is required to actually spend money in the account. Therefore, it is extremely important to keep the private key safe. Depending on your level of paranoia, this may mean keeping the private key on an air-gapped computer and only signing transactions offline or printing the key on paper for cold storage.

These methods make the account more secure but also make it highly unlikely your coins will be accessible if anything were to happen to you, your offline machine, or your paper backup.

My goal is to provide a method of creating a group of linked wallets in such a way that, in case of emergency, any wallet would be accessible by a consensus of the other accounts. Obviously, there is a tradeoff in security but, with the help of the other participants, you gain the ability to recover in case of the unexpected.

## Installation
### Docker
The simplest way to run the application is through Docker. With the Docker service installed and running, execute
```
docker run -it -v /tmp:/tmp -e NEWUSER:$USER kyokley/failsafe
```

### From Source
This package is not currently available on PYPI so, for the time being, it's easiest to just clone the repo and install from there.

Assuming you've created a virtualenv and activated it in one of the usual ways, do the following to install the package.

```
$ git clone https://github.com/kyokley/bitcoin_failsafe.git
$ cd bitcoin_failsafe
$ pip install .
```

## Example
### Generation
Let's say Alice, Bob, and Carol would like to create linked wallets. The following would take place on an air-gapped machine with all 3 parties in attendance. Begin by running failsafe with no arguments which starts account creation in interactive mode.

![Generate](/../screenshots/screenshots/generate.gif?raw=true)

The application will prompt for the number of accounts to create as well as the number of shards required for consensus. A new hierarchical deterministic wallet (HD wallet) will be created. New accounts for Alice, Bob, and Carol will be generated as children on this wallet. Once the child wallets have been created, the master wallet is serialized, split into shards using Shamir's secret sharing algorithm, and finally, the master is destroyed.

Next, Alice, Bob, and Carol take turns at the offline machine receiving their new accounts and pieces of the master key. Failsafe tries to prevent each user from accidentally seeing each other's private information by giving prompts that say when the next user is required. All data is written to the filesystem in a temporary directories in json and png formats and destroyed before the next user is called for. Before the temporary file is destroyed, it is up to the user to copy the information in their directory (e.g. by copying the files to USB, printing them out, writing them down, etc.).

In each user's directory, there are multiple files. These include ".png" files and a ".json" file called "user_info.priv.json". The ".png" files contain QR codes of public and private account information. Any files containing "priv" in the name contain private information and should be protected accordingly. Files with "pub" in the name are suitable to distribute publicly.

"user_info.priv.json" is the most important file generated. It will look similar to below.
```
{
  "child": "1 of 3",
  "wif_accounts": [
    "secretsecretsecret...",
  ],
  "user_key": "xprv...",
  "encrypted_shard": "encryptedsecret...",
  "passphrase": "harvest beyond exchange wink crisp shallow alert release"
}
```

"child" stores the index for this user. This is important for recovery functions.

The "wif_accounts" section contains accounts in Wallet Import Format. Each entry corresponds to two of the ".png" files. The reason for generating multiple accounts is that they should be thought of as piggybanks. In other words, these accounts are designed to accept as many bitcoins as you would like. However, once bitcoins have been spent (by moving the private key to an internet connected computer), that account should not be used again. It is also possible to prepare transactions on the offline machine but that is beyond the scope of this README.

The "user_key" section contains a serialized version of the user's key in base58 format. This key contains the HD wallet for the user. In addition to the "wif_accounts", it is possible to use this HD wallet key to generate additional accounts in the future.

"encrypted_shard" contains the encrypted version of the shard using "passphrase" as the key. Encryption is done using cryptography's Fernet symmetric key encryption. ![Implementation](https://cryptography.io/en/latest/fernet/#implementation)

Since the shard contains sensitive information that could potentially compromise your account and everyone else's it is important to keep it safe. Because it is encrypted, it should be okay to store it on a machine that is connected to the internet. **However, this assumes the passphrase is not stored in the same location.** Because the passphrase consists of 8 english words, it can easily be written down on paper and stored in a safe.

### Recovery
Let's assume Bob has lost his private key. With the help of Alice and Carol, he can get it back. Running failsafe with the -r or --recover flag starts recovery in interactive mode.

```
failsafe -r
```

The first piece of information required is the index of the user who's key should be regenerated. This comes from the "child" section of "user_info.priv.json" generated earlier. (Assuming Bob lost his private key, he probably doesn't have his user index either. Hopefully, he remembers it. Alternatively, Alice and Carol may be able to aid in figuring it out through process of elimination.)

In this case, Bob's user index is 2.

Next, failsafe begins asking for the shards from Alice and Carol. These can be provided in any order. Each user will be prompted for their encrypted shard followed by prompts for each of their words in the passphrase. Because of the sensitive nature of the passphrase, the words are not shown as they are typed. If decryption of the encrypted shard fails, the system will restart prompting for the words again.

Once the key threshold has been achieved, Bob's private key will be regenerated and written to the filesystem. At this point, there is no way to regenerate Bob's piece of the master key but, hopefully, in future versions, this functionality will be added.

## Caveats
Obviously, this creates new security concerns. I came up with this process for my family that I trust. If Bob did not trust Alice and Carol, he should not engage in this linked wallet. I provide no guarantees about the security or validity of these linked wallets. Use at your own risk.
