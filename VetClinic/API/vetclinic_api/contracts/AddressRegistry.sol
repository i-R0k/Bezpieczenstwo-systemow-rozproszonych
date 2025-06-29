// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract AddressRegistry {
    // Mapa klucz (bytes32) -> adres kontraktu
    mapping(bytes32 => address) private _addresses;
    
    event AddressSet(bytes32 indexed key, address indexed addr);

    /// @notice Ustawia nowy adres pod danym kluczem
    function setAddress(bytes32 key, address addr) external {
        _addresses[key] = addr;
        emit AddressSet(key, addr);
    }

    /// @notice Zwraca adres dla klucza
    function getAddress(bytes32 key) external view returns (address) {
        return _addresses[key];
    }
}