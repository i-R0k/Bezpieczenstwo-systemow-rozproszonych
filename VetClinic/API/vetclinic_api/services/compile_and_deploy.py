#!/usr/bin/env python3
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from solcx import install_solc, compile_standard
from web3 import Web3

# 1) Load environment variables
load_dotenv()
# pobieramy BLOCKCHAIN_URL, a gdy nie jest ustawione — domyślnie Ganache na localhost
RPC_URL = os.getenv("BLOCKCHAIN_URL", "http://127.0.0.1:8545")

def get_w3():
    from web3 import Web3, HTTPProvider
    print(f"Using RPC URL: {RPC_URL}")
    w3 = Web3(HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise ConnectionError(f"Cannot connect to blockchain at {RPC_URL}")
    return w3


# 2) Connect to blockchain via Ganache (accounts are unlocked)
w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    raise ConnectionError(f"Cannot connect to blockchain at {RPC_URL}")
# Use the first unlocked account
accounts = w3.eth.accounts
if not accounts:
    raise RuntimeError("No accounts available on the node.")
deployer = accounts[0]
print(f"Using deployer account: {deployer}")

# 3) Ensure Solidity compiler is available
SOLC_VERSION = "0.8.0"
install_solc(SOLC_VERSION)

# 4) Compile all contracts in 'contracts' directory
contracts_dir = Path(__file__).parent.parent / "contracts"
sources = {}
for sol_file in contracts_dir.glob("*.sol"):
    sources[str(sol_file)] = {"content": sol_file.read_text()}
compiled = compile_standard(
    {
        "language": "Solidity",
        "sources": sources,
        "settings": {"outputSelection": {"*": {"*": ["abi","evm.bytecode.object"]}}}
    },
    solc_version=SOLC_VERSION
)
# 5) Write build artifacts
build_dir = Path(__file__).parent.parent / "build"
build_dir.mkdir(exist_ok=True)
for file_path, contracts in compiled["contracts"].items():
    for contract_name, data in contracts.items():
        artifact = {
            "abi": data["abi"],
            "bytecode": data["evm"]["bytecode"]["object"]
        }
        out_file = build_dir / f"{contract_name}.json"
        out_file.write_text(json.dumps(artifact, indent=2))
        print(f"Compiled {contract_name} → {out_file}")

# 6) Deploy MedicalRecord contract using transact
medical_artifact = json.loads((build_dir / "MedicalRecord.json").read_text())
Medical = w3.eth.contract(abi=medical_artifact["abi"], bytecode=medical_artifact["bytecode"])
print("Deploying MedicalRecord...")
medical_tx = Medical.constructor().transact({'from': deployer})
receipt = w3.eth.wait_for_transaction_receipt(medical_tx)
med_address = receipt.contractAddress
print(f"MedicalRecord deployed at: {med_address}")
# Save frontend artifact for MedicalRecord
frontend_abi_dir = Path(__file__).parent.parent / "vetclinic_gui" / "abi"
frontend_abi_dir.mkdir(parents=True, exist_ok=True)
frontend_artifact = {"address": med_address, "abi": medical_artifact["abi"]}
(frontend_abi_dir / "MedicalRecord.json").write_text(json.dumps(frontend_artifact, indent=2))
print("Frontend MedicalRecord artifact updated.")

# 7) Optionally deploy AddressRegistry if present
if (build_dir / "AddressRegistry.json").exists():
    addr_artifact = json.loads((build_dir / "AddressRegistry.json").read_text())
    Registry = w3.eth.contract(abi=addr_artifact["abi"], bytecode=addr_artifact["bytecode"])
    print("Deploying AddressRegistry...")
    reg_tx = Registry.constructor().transact({'from': deployer})
    reg_receipt = w3.eth.wait_for_transaction_receipt(reg_tx)
    reg_address = reg_receipt.contractAddress
    print(f"AddressRegistry deployed at: {reg_address}")
    # Save frontend artifact for AddressRegistry
    frontend_artifact = {"address": reg_address, "abi": addr_artifact["abi"]}
    (frontend_abi_dir / "AddressRegistry.json").write_text(json.dumps(frontend_artifact, indent=2))
    print("Frontend AddressRegistry artifact updated.")
