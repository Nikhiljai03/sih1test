// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CropRegistry {
    /// @notice Crop struct. Price is stored in wei.
    struct Crop {
        uint id;
        address farmer;
        string name;
        string details;
        uint price; // in wei
        uint quantity;
        string quality;
        string fertilizer;
        string organic;
        string soil;
        string irrigation;
    }

    uint public cropCount = 0;
    mapping(uint => Crop) public crops;
    // Farmer registration removed; anyone can add crops

    event CropAdded(uint id, address farmer, string name, string details, uint price, uint quantity, string quality, string fertilizer, string organic, string soil, string irrigation);

    // Only owner (admin) can assign farmer role
    address public owner;

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not admin");
        _;
    }

    // Only owner logic retained for admin functions

    // Farmer registration removed

    /// @notice Add a crop (no payment required)
    /// @param name Crop name
    /// @param details Crop details
    /// @param price Price in wei
    /// @param quantity Quantity
    /// @param quality Quality
    function addCrop(
        string memory name,
        string memory details,
        uint price,
        uint quantity,
        string memory quality,
        string memory fertilizer,
        string memory organic,
        string memory soil,
        string memory irrigation
    ) public {
        cropCount++;
        crops[cropCount] = Crop(cropCount, msg.sender, name, details, price, quantity, quality, fertilizer, organic, soil, irrigation);
        emit CropAdded(cropCount, msg.sender, name, details, price, quantity, quality, fertilizer, organic, soil, irrigation);
    }

    // Withdraw removed; contract does not hold funds

    function getCrop(uint id) public view returns (Crop memory) {
        return crops[id];
    }

    function getAllCrops() public view returns (Crop[] memory) {
        Crop[] memory result = new Crop[](cropCount);
        for (uint i = 1; i <= cropCount; i++) {
            result[i-1] = crops[i];
        }
        return result;
    }

}