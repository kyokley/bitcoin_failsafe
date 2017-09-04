# Bitcoin Failsafe
Generate a group of linked HD wallets with a recoverable master wallet in case of emergency

## Purpose
One of the interesting properties of bitcoin is that anyone can see money flowing into an account with just the public key. However, the associated private key is required to actually spend money in the account. Therefore, it is extremely important to keep the private key safe. Depending on your level of paranoia, this may mean keeping the private key on an air-gapped computer and only signing transactions offline or printing the key on paper for cold storage.

These methods make the account more secure but also make it highly unlikely your coins will be accessible if anything were to happen to you, your offline machine, or your paper backup.

My goal is to provide a method of creating a group of linked wallets in such a way that, in case of emergency, any wallet would be accessible by a consensus of the other accounts. Obviously, there is a tradeoff in security but, with the help of the other participants, you gain the ability to recover in case of the unexpected.

## Example
### Generation
Let's say Alice, Bob, and Carol would like to create linked wallets. The following would take place on an air-gapped machine with all 3 parties in attendance. Begin by running failsafe with no arguments which starts account creation in interactive mode.

```
failsafe
```

The application will prompt for the number of accounts to create as well as the number of shards required for consensus. A new hierarchical deterministic wallet (HD wallet) will be created. New accounts for Alice, Bob, and Carol will be generated as children on this wallet. Once the child wallets have been created, the master wallet is serialized, split into shards using Shamir's secret sharing algorithm, and finally, the master is destroyed.

Next, Alice, Bob, and Carol take turns at the offline machine receiving their new accounts and pieces of the master key. Failsafe tries to prevent each user from accidentally seeing each other's private information by giving prompts that say when the next user is required. All data is written to the filesystem in a temporary file in json format and destroyed before the next user is called for. Before the temporary file is destroyed, it is up to the user to copy the information in the file (e.g. by copying the file to USB, printing it out, writing it down, etc.).

The resulting files may look similar to below.

Alice:
```
{
  "account": "xprvsecretsecretsecretsecretsecretsecretsecretsecretsecretsecretsecret",
  "master_shard": "2-2-shardshardshardshardshardshardshardshardshardshardshardshardshardshardshardshardshardshardshardshardshardshardshardshardshard",
  "child": "1 of 3"
}
```

Bob:
```
{
	  "account": "xprvsecret...",
	  "master_shard": "2-2-shard...",
	  "child": "2 of 3"
}
```

Carol:
```
{
	  "account": "xprvsecret...",
	  "master_shard": "2-2-shard...",
	  "child": "3 of 3"
}
```

The "account" is a base58 serialized private key that can be used to generate additional accounts if necessary. The "mater_shard" is a piece of the master wallet that can be used to regenerate the master key given a quorum of other shards. "child" shows the index of the master wallet that was used to create the "account".

It is critical that Alice, Bob, and Carol not share any of this information with anyone, including each other. These accounts become the offline storage for each participant.

### Recovery
Let's assume Bob has lost his private key. With the help of Alice and Carol, he can get it back. Running failsafe with the -r or --recover flag starts recovery in interactive mode.

```
failsafe -r
```

The first piece of information required is the index of the user who's key should be regenerated. This comes from the "child" section of the secret files generated earlier. (Assuming Bob lost his private key, he probably doesn't have his user index either. Hopefully, he remembers it. Alternatively, Alice and Carol may be able to aid in figuring it out through process of elimination.)

In this case, Bob's user index is 2.

Next, failsafe begins asking for the shards from Alice and Carol. These can be provided in any order. Once the key threshold has been achieved, Bob's private key will be regenerated and written to the filesystem. At this point, I would recommend regenerating all accounts since Bob's shard of the master is still lost.

## Caveats
Obviously, this creates new security concerns. I came up with this process for my family that I trust. If Bob did not trust Alice and Carol, he should not engage in this linked wallet. I provide no guarantees about the security or validity of these linked wallets. Use at your own risk.
