// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract MedicalRecord {
    struct Record {
        uint id;
        string dataHash;
        uint timestamp;
        bool deleted;
        address owner;
    }

    mapping(uint => Record) public records;
    mapping(address => uint[]) public ownerToIds;

    function addRecord(uint id, string memory dataHash) public {
        require(!records[id].deleted, "Record was deleted");
        records[id] = Record(id, dataHash, block.timestamp, false, msg.sender);
        ownerToIds[msg.sender].push(id);
    }

    function getRecord(uint id) public view returns (uint, string memory, uint, bool, address) {
        Record memory r = records[id];
        return (r.id, r.dataHash, r.timestamp, r.deleted, r.owner);
    }

    function updateRecord(uint id, string memory newDataHash) public {
        require(!records[id].deleted, "Cannot update deleted record");
        require(records[id].owner == msg.sender, "Not record owner");
        records[id].dataHash = newDataHash;
        records[id].timestamp = block.timestamp;
    }

    function deleteRecord(uint id) public {
        require(!records[id].deleted, "Already deleted");
        require(records[id].owner == msg.sender, "Not record owner");
        records[id].deleted = true;
    }

    function getRecordsByOwner(address owner) public view returns (uint[] memory) {
        return ownerToIds[owner];
    }
}
