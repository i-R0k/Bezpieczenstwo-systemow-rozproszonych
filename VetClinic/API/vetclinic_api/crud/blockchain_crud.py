from vetclinic_api.core.blockchain import BlockchainProvider

# Provider singleton for blockchain connection and contract
_provider = BlockchainProvider()


def add_record(record_id: int, data_hash: str) -> str:
    """
    Wysyła nowy hash rekordu na blockchain.
    Zwraca hash transakcji.
    """
    contract, account, w3 = _provider.get()
    tx_hash = contract.functions.addRecord(record_id, data_hash).transact({'from': account})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.transactionHash.hex()


def get_record(record_id: int):
    """
    Pobiera rekord z blockchainu.
    Zwraca tuple: (id, dataHash, timestamp, deleted).
    """
    contract, _, _ = _provider.get()
    return contract.functions.getRecord(record_id).call()


def update_record(record_id: int, new_data_hash: str) -> str:
    """
    Aktualizuje hash istniejącego rekordu.
    Zwraca hash transakcji.
    """
    contract, account, w3 = _provider.get()
    tx_hash = contract.functions.updateRecord(record_id, new_data_hash).transact({'from': account})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.transactionHash.hex()


def delete_record(record_id: int) -> str:
    """
    Oznacza rekord jako usunięty na blockchainie.
    Zwraca hash transakcji.
    """
    contract, account, w3 = _provider.get()
    tx_hash = contract.functions.deleteRecord(record_id).transact({'from': account})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.transactionHash.hex()


def get_records_by_owner(owner: str) -> list[int]:
    """
    Zwraca listę ID rekordów zapisanych on‐chain przez owner.
    """
    contract, _, _ = _provider.get()
    return contract.functions.getRecordsByOwner(owner).call()
