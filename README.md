# Cardano-cli spam tx 

## Cardano node
1) Install daedalus and sync with blockchain \
[Download Daedalus](https://daedaluswallet.io/)

## Export Socket Path
In terminal paste this:\
``export CARDANO_NODE_SOCKET_PATH=$(ps ax | grep -v grep | grep cardano-wallet | grep mainnet | sed -E 's/(.*)node-socket //')
``

## Generating keys

### Wallet
make a directory called wallet and cd into it and create the keys \
``mkdir wallet``

[Create keys](https://developers.cardano.org/docs/stake-pool-course/handbook/keys-addresses/)

## TXS
Create a directory called txs \
``mkdir txs``

## Fund wallet
Send ada to the payment.addr that you generated in multiple transactions to create multiple utxos

## Run file
``python3 spam_tx.py``

## Extra info on how it works
https://www.youtube.com/watch?v=XVHwWEbExOo&t=2776s