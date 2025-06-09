// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract MedicalRecord {
    struct Record {
        uint id;
        string dataHash;
        uint timestamp;
        bool deleted;
    }

    mapping(uint => Record) public records;

    function addRecord(uint id, string memory dataHash) public {
        require(!records[id].deleted, "Record was deleted");
        records[id] = Record(id, dataHash, block.timestamp, false);
    }

    function getRecord(uint id) public view returns (uint, string memory, uint, bool) {
        Record memory r = records[id];
        return (r.id, r.dataHash, r.timestamp, r.deleted);
    }

    function updateRecord(uint id, string memory newDataHash) public {
        require(!records[id].deleted, "Cannot update deleted record");
        records[id].dataHash = newDataHash;
        records[id].timestamp = block.timestamp;
    }

    function deleteRecord(uint id) public {
        require(!records[id].deleted, "Already deleted");
        records[id].deleted = true;
    }
}
