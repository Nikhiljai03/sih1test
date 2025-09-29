// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract QualityInspectionRegistry {
    struct Inspection {
        uint productId;
        address inspector;
        uint score; // e.g., scaled by 100 (e.g., 87 for 0.87)
        string grade;
        string certificate;
        string comments;
        uint timestamp;
    }

    uint public inspectionCount = 0;
    mapping(uint => Inspection) public inspections;
    mapping(uint => uint[]) public productToInspections; // productId => array of inspection ids

    event InspectionRecorded(
        uint indexed inspectionId,
        uint indexed productId,
        address indexed inspector,
        uint score,
        string grade,
        string certificate,
        string comments,
        uint timestamp
    );

    function recordInspection(
        uint productId,
        uint score,
        string memory grade,
        string memory certificate,
        string memory comments
    ) public {
        inspectionCount++;
        inspections[inspectionCount] = Inspection(
            productId,
            msg.sender,
            score,
            grade,
            certificate,
            comments,
            block.timestamp
        );
        productToInspections[productId].push(inspectionCount);
        emit InspectionRecorded(
            inspectionCount,
            productId,
            msg.sender,
            score,
            grade,
            certificate,
            comments,
            block.timestamp
        );
    }

    function getInspections(uint productId) public view returns (Inspection[] memory) {
        uint[] memory ids = productToInspections[productId];
        Inspection[] memory result = new Inspection[](ids.length);
        for (uint i = 0; i < ids.length; i++) {
            result[i] = inspections[ids[i]];
        }
        return result;
    }
}
