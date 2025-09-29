// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TransporterRegistry {
    struct TransportRecord {
        uint cropId;
        address transporter;
        string location;
        string custody;
        uint timestamp;
    }

    uint public recordCount = 0;
    mapping(uint => TransportRecord) public records;
    mapping(uint => uint[]) public cropToRecords; // cropId => array of record ids

    event TransportUpdated(uint recordId, uint cropId, address transporter, string location, string custody, uint timestamp);

    function updateTransport(uint cropId, string memory location, string memory custody) public {
        recordCount++;
        records[recordCount] = TransportRecord(cropId, msg.sender, location, custody, block.timestamp);
        cropToRecords[cropId].push(recordCount);
        emit TransportUpdated(recordCount, cropId, msg.sender, location, custody, block.timestamp);
    }

    function getTransportRecords(uint cropId) public view returns (TransportRecord[] memory) {
        uint[] memory ids = cropToRecords[cropId];
        TransportRecord[] memory result = new TransportRecord[](ids.length);
        for (uint i = 0; i < ids.length; i++) {
            result[i] = records[ids[i]];
        }
        return result;
    }
}
