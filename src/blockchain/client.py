from typing import Any, Dict, Optional, Tuple
from src.blockchain.provider import BaseBlockchainProvider, get_blockchain_provider


class BlockchainClient:
    """
    High-level Blockchain Client for recording and querying verification hashes.
    Delegates to the configured BlockchainProvider (local or Web3).
    """

    def __init__(self, provider: Optional[BaseBlockchainProvider] = None):
        if provider is None:
            self.provider = get_blockchain_provider()
        else:
            self.provider = provider

    def record_hash(self, bytes32_hash: str, page_url: str = "", platform: str = "") -> Dict[str, Any]:
        """
        Records a bytes32 content hash on the blockchain.
        """
        if not bytes32_hash:
            raise ValueError("bytes32_hash cannot be empty")
        return self.provider.record_match(bytes32_hash=bytes32_hash, page_url=page_url, platform=platform)

    def get_record(self, bytes32_hash: str) -> Dict[str, Any]:
        """
        Retrieves a recorded verification hash and its metadata from the blockchain.
        """
        if not bytes32_hash:
            raise ValueError("bytes32_hash cannot be empty")
        return self.provider.get_record(bytes32_hash=bytes32_hash)

    def verify_hash(self, bytes32_hash: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Checks whether a given bytes32 content hash is recorded on-chain.
        """
        if not bytes32_hash:
            raise ValueError("bytes32_hash cannot be empty")
        return self.provider.verify_match(bytes32_hash=bytes32_hash)
