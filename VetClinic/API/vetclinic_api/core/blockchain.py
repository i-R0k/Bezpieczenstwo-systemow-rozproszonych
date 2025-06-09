from web3 import Web3
from solcx import compile_source, install_solc
import os

install_solc('0.8.0')  # tylko raz, można potem usunąć

# Połączenie z lokalnym blockchainem
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
assert w3.is_connected(), "Brak połączenia z Ganache"

accounts = w3.eth.accounts
acct = accounts[0]

# Ścieżka do kontraktu
contract_path = os.path.join(os.path.dirname(__file__), '../contracts/MedicalRecord.sol')

with open(contract_path, 'r') as f:
    source = f.read()

compiled = compile_source(source, output_values=["abi", "bin"])
contract_id, contract_interface = compiled.popitem()

# Deploy
MedicalRecord = w3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])
tx_hash = MedicalRecord.constructor().transact({'from': acct})
tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
contract = w3.eth.contract(address=tx_receipt.contractAddress, abi=contract_interface['abi'])

print("✅ Kontrakt wdrożony na adres:", contract.address)
