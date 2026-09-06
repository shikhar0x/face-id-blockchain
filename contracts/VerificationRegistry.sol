// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title VerificationRegistry
 * @dev Stores tamper-evident SHA-256 fingerprints of matched social media/web content
 * for face identification verification (HH Goa 2026 Task 3).
 */
contract VerificationRegistry {
    
    struct Record {
        bytes32 contentHash;
        string pageUrl;
        string platform;
        uint256 timestamp;
        address recorder;
        bool exists;
    }

    // Mapping from contentHash (bytes32) to Record struct
    mapping(bytes32 => Record) private _records;

    // Array of recorded content hashes for enumeration
    bytes32[] private _allHashes;

    // Events
    event RecordStored(
        bytes32 indexed contentHash,
        string pageUrl,
        string platform,
        uint256 timestamp,
        address indexed recorder
    );

    /**
     * @dev Stores a content hash and metadata on-chain.
     * @param contentHash SHA-256 content fingerprint represented as bytes32
     * @param pageUrl Discovered post/page URL
     * @param platform Social media/web platform name
     */
    function recordMatch(
        bytes32 contentHash,
        string memory pageUrl,
        string memory platform
    ) public returns (bool) {
        require(contentHash != bytes32(0), "Invalid content hash");

        if (!_records[contentHash].exists) {
            _allHashes.push(contentHash);
        }

        _records[contentHash] = Record({
            contentHash: contentHash,
            pageUrl: pageUrl,
            platform: platform,
            timestamp: block.timestamp,
            recorder: msg.sender,
            exists: true
        });

        emit RecordStored(contentHash, pageUrl, platform, block.timestamp, msg.sender);
        return true;
    }

    /**
     * @dev Retrieves a recorded verification record by content hash.
     * @param contentHash SHA-256 content fingerprint
     */
    function getRecord(bytes32 contentHash)
        public
        view
        returns (
            bytes32 hash,
            string memory pageUrl,
            string memory platform,
            uint256 timestamp,
            address recorder,
            bool exists
        )
    {
        Record memory rec = _records[contentHash];
        return (
            rec.contentHash,
            rec.pageUrl,
            rec.platform,
            rec.timestamp,
            rec.recorder,
            rec.exists
        );
    }

    /**
     * @dev Verifies whether a given content hash exists on-chain.
     * @param contentHash SHA-256 content fingerprint
     */
    function verifyMatch(bytes32 contentHash)
        public
        view
        returns (
            bool isVerified,
            uint256 timestamp,
            string memory pageUrl,
            string memory platform
        )
    {
        Record memory rec = _records[contentHash];
        return (rec.exists, rec.timestamp, rec.pageUrl, rec.platform);
    }

    /**
     * @dev Returns total number of registered records.
     */
    function totalRecords() public view returns (uint256) {
        return _allHashes.length;
    }
}
