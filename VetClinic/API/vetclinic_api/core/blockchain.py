from web3 import Web3
from solcx import compile_source, install_solc, set_solc_version
import os

install_solc("0.8.0")
set_solc_version("0.8.0")

class BlockchainProvider:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
        assert self.w3.is_connected()
        self.account = self.w3.eth.accounts[0]

        contract_path = os.path.join(os.path.dirname(__file__), "../contracts/MedicalRecord.sol")
        with open(contract_path) as f:
            source = f.read()

        compiled = compile_source(source, output_values=["abi", "bin"])
        _, interface = compiled.popitem()

        contract_cls = self.w3.eth.contract(abi=interface["abi"], bytecode=interface["bin"])
        tx_hash = contract_cls.constructor().transact({'from': self.account})
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        self.contract = self.w3.eth.contract(
            address=tx_receipt.contractAddress,
            abi=interface["abi"]
        )

    def get(self):
        return self.contract, self.account, self.w3
