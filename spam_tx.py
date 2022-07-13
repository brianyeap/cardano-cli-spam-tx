import os
import subprocess
import random
import threading
import requests
import json

# Path to the cardano-cli binary or use the global one
CARDANO_CLI_PATH = "cardano-cli"

# BLOCK_FROST (Set Permanent virtualenv variable EG: nano ~/.zshrc, source ~/.zshrc)
PROJECT_ID = os.environ.get('BLOCKFROST_PROJECT_ID')

SEND_ADA_AMOUNT = 1
SEND_TX_AMOUNT = 5
ESTIMATED_ADA_FEE = 0.2
VALID_UTXOS_ARRAY = []

# Read wallet address value from payment.addr file
PaymentAddress = open('wallet/payment.addr').read()
ReceiverAddress = open('wallet/receiver.addr').read()


def get_UTXOs(address):
    url = f"https://cardano-mainnet.blockfrost.io/api/v0/addresses/{address}/utxos"
    headers = {
        'project_id': PROJECT_ID
    }
    return requests.request("GET", url, headers=headers).json()


def calculate_min_fee(tx_in_count, tx_out_count, file_raw):
    fee = subprocess.check_output([
        CARDANO_CLI_PATH,
        'transaction', 'calculate-min-fee',
        '--mainnet',
        '--tx-body-file', file_raw,
        '--tx-in-count', str(tx_in_count),
        '--tx-out-count', str(tx_out_count),
        '--witness-count', '2',
        '--byron-witness-count', '0',
        '--protocol-params-file', 'protocol.json'
    ])
    return int(fee.decode().split()[0])


def submit_txn_blockfrost(signed_file):
    with open(signed_file, 'r') as signed_filehandle:
        tx_cbor = json.load(signed_filehandle)['cborHex']
    req = requests.post(f"https://cardano-mainnet.blockfrost.io/api/v0/tx/submit",
                        headers={'project_id': PROJECT_ID, 'Content-Type': 'application/cbor'},
                        data=bytes.fromhex(tx_cbor))
    return req


def submit_tx_from_utxo(_tx_hash, _tx_ix, _receiver):
    # Build tx
    subprocess.check_output([
        CARDANO_CLI_PATH,
        'transaction', 'build',
        '--mainnet',
        '--tx-in', f'{_tx_hash}#{_tx_ix}',
        '--tx-out', f'{_receiver}+{SEND_ADA_AMOUNT * 10 ** 6}',
        '--change-address', f'{PaymentAddress}',
        '--out-file', f'txs/{_tx_hash}-tx.raw'
    ])

    # Sign tx
    subprocess.check_output([
        CARDANO_CLI_PATH,
        'transaction', 'sign',
        '--mainnet',
        '--signing-key-file', 'wallet/payment.skey',
        '--tx-body-file', f'txs/{_tx_hash}-tx.raw',
        '--out-file', f'txs/{_tx_hash}-tx.signed'
    ])

    # print(submit_txn_blockfrost(f'txs/{_tx_hash}-tx.signed').text)

    # Submit tx
    _submit_tx = subprocess.check_output([
        CARDANO_CLI_PATH,
        'transaction', 'submit',
        '--mainnet',
        '--tx-file', f'txs/{_tx_hash}-tx.signed'
    ])

    if 'Transaction successfully submitted.' in _submit_tx.decode():
        os.remove(f'txs/{_tx_hash}-tx.raw')
        os.remove(f'txs/{_tx_hash}-tx.signed')
        print('TX submitted successfully!')


def empty_ada():
    _total_ada = 0
    _assets = []
    total_input = 0
    random_int = round(random.random() * 10 ** 10)

    # TEMP TX for FEES
    build_tx_array = [
        CARDANO_CLI_PATH,
        'transaction', 'build-raw',
        '--invalid-hereafter=99999999',
        '--out-file', f'txs/{random_int}-tx.raw'
    ]
    for _UTXO in get_UTXOs(PaymentAddress):
        _tx_hash = _UTXO["tx_hash"]
        _tx_index = _UTXO['tx_index']

        for amount in _UTXO['amount']:
            if amount['unit'] == 'lovelace':
                _total_ada += int(amount['quantity'])
            else:
                _assets.append([amount['unit'], amount['quantity']])

        build_tx_array.append('--tx-in')
        build_tx_array.append(f'{_tx_hash}#{_tx_index}')
        total_input += 1

    build_tx_array.append('--fee')
    build_tx_array.append('0')

    # Tx out
    _temp_str = ''
    if _assets:
        for asset in _assets:
            _temp_str += f'+{asset[1]} {asset[0][:56]}.{asset[0][56:]}'

    build_tx_array.append('--tx-out')
    build_tx_array.append(f'{ReceiverAddress}+{_total_ada}{_temp_str}')

    # Build tx
    _total_ada = 0
    _assets = []
    total_input = 0
    subprocess.check_output(build_tx_array)

    build_tx_array = [
        CARDANO_CLI_PATH,
        'transaction', 'build-raw',
        '--invalid-hereafter=99999999',
        '--out-file', f'txs/{random_int}-tx.raw'
    ]
    for _UTXO in get_UTXOs(PaymentAddress):
        _tx_hash = _UTXO["tx_hash"]
        _tx_index = _UTXO['tx_index']

        for amount in _UTXO['amount']:
            if amount['unit'] == 'lovelace':
                _total_ada += int(amount['quantity'])
            else:
                _assets.append([amount['unit'], amount['quantity']])

        build_tx_array.append('--tx-in')
        build_tx_array.append(f'{_tx_hash}#{_tx_index}')
        total_input += 1

    fee = calculate_min_fee(total_input, 1, f'txs/{random_int}-tx.raw')
    build_tx_array.append('--fee')
    build_tx_array.append(str(fee))

    # Tx out
    _temp_str = ''
    if _assets:
        for asset in _assets:
            _temp_str += f'+{asset[1]} {asset[0][:56]}.{asset[0][56:]}'

    build_tx_array.append('--tx-out')
    build_tx_array.append(f'{ReceiverAddress}+{_total_ada - fee}{_temp_str}')

    # Build tx
    subprocess.check_output(build_tx_array)

    # Sign tx
    subprocess.check_output([
        CARDANO_CLI_PATH,
        'transaction', 'sign',
        '--mainnet',
        '--signing-key-file', 'wallet/payment.skey',
        '--tx-body-file', f'txs/{random_int}-tx.raw',
        '--out-file', f'txs/{random_int}-tx.signed'
    ])

    # Submit tx
    _submit_tx = subprocess.check_output([
        CARDANO_CLI_PATH,
        'transaction', 'submit',
        '--mainnet',
        '--tx-file', f'txs/{random_int}-tx.signed'
    ])

    if 'Transaction successfully submitted.' in _submit_tx.decode():
        os.remove(f'txs/{random_int}-tx.raw')
        os.remove(f'txs/{random_int}-tx.signed')
        print('Tx submitted!')


total_ada = 0
send_tx_count = 0
for UTXO in get_UTXOs(PaymentAddress):
    tx_hash = UTXO["tx_hash"]
    tx_index = UTXO['tx_index']
    ada_amount = UTXO['amount'][0]['quantity']

    total_ada += round(int(ada_amount) / 10 ** 6, 2)
    if int(ada_amount) > (SEND_ADA_AMOUNT * 10 ** 6) + (ESTIMATED_ADA_FEE * 10 ** 6) and int(ada_amount) - (
            (SEND_ADA_AMOUNT * 10 ** 6) + (
            ESTIMATED_ADA_FEE * 10 ** 6)) > 1 * 10 ** 6 and send_tx_count < SEND_TX_AMOUNT:
        VALID_UTXOS_ARRAY.append([tx_hash, tx_index, ada_amount])
        send_tx_count += 1

print(f'\n')
print('-----------------------------')
print(f'[+] Total ADA: {total_ada} ADA')
print(f'[+] Send amount: {SEND_ADA_AMOUNT} ADA')
print(f'[+] Number of TX: {SEND_TX_AMOUNT}')
print(f'[+] Valid UTXOS: {len(VALID_UTXOS_ARRAY)}')
print('-----------------------------')
print('[-] 1) Spam TX')
print('[-] 2) Empty wallet')
print('-----------------------------')

user_input = input('Press Enter [NUM] to continue: ')

if user_input == '1':
    ReceiverAddress = input('Enter receiver address: ')
    print(f'Starting {len(VALID_UTXOS_ARRAY)} threads!')
    for valid_utxo in VALID_UTXOS_ARRAY:
        t = threading.Thread(target=submit_tx_from_utxo, args=[valid_utxo[0], valid_utxo[1], ReceiverAddress])
        t.start()
elif user_input == '2':
    print('Emptying wallet !')
    empty_ada()
