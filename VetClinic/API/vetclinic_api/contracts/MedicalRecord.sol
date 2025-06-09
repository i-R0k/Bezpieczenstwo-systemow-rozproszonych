// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract MedicalRecord {
    struct Record {
        uint id;
        string dataHash;
        uint timestamp;
    }

    mapping(uint => Record) public records;

    function addRecord(uint id, string memory dataHash) public {
        records[id] = Record(id, dataHash, block.timestamp);
    }

    function getRecord(uint id) public view returns (uint, string memory, uint) {
        Record memory r = records[id];
        return (r.id, r.dataHash, r.timestamp);
    }
}
