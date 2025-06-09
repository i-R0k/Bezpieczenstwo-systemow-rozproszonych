import pytest
from web3 import Web3
from solcx import compile_source, install_solc, set_solc_version
import os

# Instalacja i ustawienie wersji kompilatora Solidity
install_solc("0.8.0")
set_solc_version("0.8.0")

@pytest.fixture(scope="module")
def blockchain_contract():
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    assert w3.is_connected()

    acct = w3.eth.accounts[0]

    contract_path = os.path.join(os.path.dirname(__file__), "../vetclinic_api/contracts/MedicalRecord.sol")
    with open(contract_path) as f:
        source = f.read()

    compiled = compile_source(source, output_values=["abi", "bin"])
    contract_id, interface = compiled.popitem()

    Contract = w3.eth.contract(abi=interface["abi"], bytecode=interface["bin"])
    tx_hash = Contract.constructor().transact({"from": acct})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    deployed = w3.eth.contract(address=tx_receipt.contractAddress, abi=interface["abi"])
    return deployed, acct, w3


def test_add_and_get_record(blockchain_contract):
    contract, acct, w3 = blockchain_contract

    record_id = 1
    data_hash = "abc123test"
    tx = contract.functions.addRecord(record_id, data_hash).transact({'from': acct})
    receipt = w3.eth.wait_for_transaction_receipt(tx)

    result = contract.functions.getRecord(record_id).call()
    assert result[0] == record_id
    assert result[1] == data_hash
    assert result[2] > 0  # timestamp
