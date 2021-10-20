# Import dependencies
import os
import subprocess
import json
from dotenv import load_dotenv

# Load and set environment variables
load_dotenv()
mnemonic=os.getenv("mnemonic")

# Import constants.py and necessary functions from bit and web3
from constants import *

from bit import PrivateKeyTestnet
from bit import wif_to_key

from web3 import Web3, middleware, Account
from web3.middleware import geth_poa_middleware

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545")) 
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
from web3.gas_strategies.time_based import medium_gas_price_strategy
w3.eth.setGasPriceStrategy(medium_gas_price_strategy)

from coincurve.keys import PrivateKey

# Create a function called `derive_wallets`
def derive_wallets(coin=BTC, mnemonic=mnemonic, depth=3):
    command = f'php ./derive -g --mnemonic="{mnemonic}" --cols=all --coin={coin} --numderive={depth} --format=json'
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    p_status = p.wait()
    # keys = json.loads(output)
    return json.loads(output)

# Create a dictionary object called coins to store the output from `derive_wallets`.

#coins = {'BTCTEST': derive_wallets(coin=BTC, mnemonic, depth=3), 'ETH': derive_wallets(coin=ETH, mnemonic, depth=3), 'BTCTEST': derive_wallets(coin=BTCTEST, mnemonic, depth=3)}
#print(output)

coins = {
    ETH: derive_wallets(coin=ETH),
    BTCTEST: derive_wallets(coin=BTCTEST),
}
coins

# Create a function called `priv_key_to_account` that converts privkey strings to account objects.
def priv_key_to_account(coin, priv_key):
    if coin == ETH:
        return Account.privateKeyToAccount(priv_key)
    if coin == BTCTEST:
        return PrivateKeyTestnet(priv_key)

acct = priv_key_to_account(ETH, '0xa50211e1c74190d6a344c1e646f8e3bf9bc2591815c196a8bcb0e11730cf12c4')

# Create a function called `create_tx` that creates an unsigned transaction appropriate metadata.
def create_tx(coin, account, to, amount):
    if coin == ETH:
        value = w3.toWei(amount, "ether") # convert 1.2 ETH to 120000000000 wei
        gasEstimate = w3.eth.estimateGas({ "to": to, "from": account, "amount": value })
        return {
            "to": to,
            "from": account,
            "value": value,
            "gas": gasEstimate,
            "gasPrice": w3.eth.generateGasPrice(),
            "nonce": w3.eth.getTransactionCount(account),
            "chainId": w3.eth.chain_id
        }
    if coin == BTCTEST:
        return PrivateKeyTestnet.prepare_transaction(account.address, [(to, amount, BTC)])

# Create a function called `send_tx` that calls `create_tx`, signs and sends the transaction.
def send_tx(coin, account, to, amount):
    if coin == ETH:
        raw_tx = create_tx(coin, account.address, to, amount)
        signed = account.signTransaction(raw_tx)
        return w3.eth.sendRawTransaction(signed.rawTransaction)
    if coin == BTCTEST:
        raw_tx = create_tx(coin, account, to, amount)
        signed = account.sign_transaction(raw_tx)
        return NetworkAPI.broadcast_tx_testnet(signed)
