# Import dependencies
import subprocess
import json
import os
from coincurve import keys
from dotenv import load_dotenv
from requests.sessions import dispatch_hook
from web3.middleware import geth_poa_middleware
from eth_account import Account
from bit import PrivateKeyTestnet
from bit.network import NetworkAPI
from web3 import Web3


# Load and set environment variables
load_dotenv()
mnemonic = os.getenv("MNEMONIC")
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Import constants.py and necessary functions from bit and web3
from constants import * 
coins = [ETH, BTCTEST] 

# Create a function called `derive_wallets`
def derive_wallets(mnemonic, coin, numderive):
    command = 'php ./derive -g --mnemonic="{}" --cols=path,address,privkey,pubkey --format=json --coin={} --numderive={}'.format(mnemonic, coin, numderive) 
    
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, err = p.communicate()
    p_status = p.wait()
    
    return json.loads(output)

# Create a dictionary object called coins to store the output from `derive_wallets`.
def display_accounts():
    keys = {}
    numderive = 3

    for coin in coins:
        keys[coin] = derive_wallets(mnemonic,coin,numderive)

    print("Derived Addresses:")
    for coin in coins:
        for i in range(numderive):
            print(coin, i, "address:",keys[coin][i]['address'])
    print("Use send_tx(<Coin>,<From PubAddress>,<To PubAddress>,<Amount>)")

# Get the priv key from the derived addresses
def get_private_key_from_pub_address(pub_address):
    keys = {}
    numderive = 3

    for coin in coins:
        keys[coin] = derive_wallets(mnemonic,coin,numderive)

    for coin in coins:
        for i in range(numderive):
            if (keys[coin][i]['address'] == pub_address):
                print('The account was found in this wallet. The tx will be sent in a sec...')
                return keys[coin][i]['privkey']

    return 'The address you have provided is not handled by this Wallet'

# Create a function called `priv_key_to_account` that converts privkey strings to account objects.
def priv_key_to_account(coin, priv_key):
    if (coin == ETH):
        return Account.from_key(priv_key)
    elif (coin == BTCTEST):
        return PrivateKeyTestnet(wif=priv_key)
    return 0

# Create a function called `create_tx` that creates an unsigned transaction appropriate metadata.
def create_tx(coin, account, to, amount):

    if (coin == ETH):
        gasEstimate = w3.eth.estimateGas(
            {"from": account.address, "to": to, "value": amount}
        )
        return {
            "from": account.address,
            "to": to,
            "value": amount,
            "gasPrice": w3.eth.gasPrice,
            "gas": gasEstimate,
            "nonce": w3.eth.getTransactionCount(account.address),
        }
    elif (coin == BTCTEST):
        return PrivateKeyTestnet.prepare_transaction(account.address, [(to, amount, BTC)])

    return 0

# Create a function called `send_tx` that calls `create_tx`, signs and sends the transaction.
def send_tx(coin, account, to, amount):

    account = priv_key_to_account(coin, get_private_key_from_pub_address(account))

    raw_tx = create_tx(coin, account, to, amount)

    signed_tx = account.sign_transaction(raw_tx)

    if (coin == ETH):
        return w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    elif (coin == BTCTEST):
        return NetworkAPI.broadcast_tx_testnet(signed_tx)


# Shows Wallet's Accounts
display_accounts()

# Example btc-test: 
# send_tx('btc-test', 'n1ccXXdtqS8EPA5LNh2zAu2CTS6eMbikXK', 'mggG1A5aCT6FZVG2HnwQp7akZED2Gbcbt8', 0.000001)

# Example eth: 
# print("TX Hash: ", send_tx('eth', '0x7620C4022Fb50c8965BDC65908Afbe376F0aCac8','0x81bdA73AFfd9d8e4fB8d67D643343b8EEa13d4F7', 100000).hex())