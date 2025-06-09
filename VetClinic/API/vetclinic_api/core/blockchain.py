from web3 import Web3
from solcx import compile_source, install_solc, set_solc_version
import os

# Jednorazowa instalacja/ustawienie solc przy załadowaniu modułu
install_solc("0.8.0")
set_solc_version("0.8.0")

class BlockchainProvider:
    def __init__(self, rpc_url: str = "http://127.0.0.1:8545"):
        self.rpc_url = rpc_url
        self.w3 = None
        self.account = None
        self.contract = None
        self._abi = None

        # Wczytujemy ABI/bin kod raz, bez deployu
        contract_path = os.path.join(os.path.dirname(__file__), "../contracts/MedicalRecord.sol")
        with open(contract_path, "r") as f:
            source = f.read()
        compiled = compile_source(source, output_values=["abi", "bin"])
        _, interface = compiled.popitem()
        self._abi = interface["abi"]
        self._bin = interface["bin"]

    def _ensure_initialized(self):
        if self.contract is not None:
            return

        # 1. Połącz z Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError(f"Nie można połączyć się z blockchainem pod {self.rpc_url}")

        # 2. Wybierz konto
        self.account = self.w3.eth.accounts[0]

        # 3. Deploy kontraktu
        contract_cls = self.w3.eth.contract(abi=self._abi, bytecode=self._bin)
        tx_hash = contract_cls.constructor().transact({'from': self.account})
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        # 4. Zapisz instancję
        self.contract = self.w3.eth.contract(address=receipt.contractAddress, abi=self._abi)

    def get(self):
        """
        Zwraca tuplę (contract, account, w3), inicjalizując wszystko przy pierwszym użyciu.
        """
        self._ensure_initialized()
        return self.contract, self.account, self.w3
