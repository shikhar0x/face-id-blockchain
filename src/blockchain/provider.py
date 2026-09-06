import os
import time
import hashlib
from typing import Any, Dict, Optional, Tuple


class BaseBlockchainProvider:
    """
    Abstract Base Class for Blockchain Providers.
    """
    def record_match(self, bytes32_hash: str, page_url: str, platform: str) -> Dict[str, Any]:
        raise NotImplementedError

    def get_record(self, bytes32_hash: str) -> Dict[str, Any]:
        raise NotImplementedError

    def verify_match(self, bytes32_hash: str) -> Tuple[bool, Dict[str, Any]]:
        raise NotImplementedError


class LocalBlockchainProvider(BaseBlockchainProvider):
    """
    Zero-dependency, deterministic local chain simulator for local testing and offline demos.
    Emulates an EVM smart contract state machine, emitting transaction hashes and block numbers.
    """
    def __init__(self, contract_address: str = "0x1234567890123456789012345678901234567890"):
        self.contract_address = contract_address
        self.chain_id = 1337
        self.block_number = 1000
        self._records: Dict[str, Dict[str, Any]] = {}
        self._transactions: Dict[str, Dict[str, Any]] = {}
        self._deployer_address = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"

    def _normalize_bytes32(self, bytes32_hash: str) -> str:
        h = bytes32_hash.strip().lower()
        if not h.startswith("0x"):
            h = f"0x{h}"
        return h

    def record_match(self, bytes32_hash: str, page_url: str, platform: str) -> Dict[str, Any]:
        norm_hash = self._normalize_bytes32(bytes32_hash)
        self.block_number += 1
        current_time = int(time.time())

        # Generate realistic transaction hash
        tx_data = f"{norm_hash}:{page_url}:{platform}:{self.block_number}:{current_time}".encode("utf-8")
        tx_hash = f"0x{hashlib.sha256(tx_data).hexdigest()}"

        record_entry = {
            "content_hash": norm_hash,
            "page_url": page_url,
            "platform": platform,
            "timestamp": current_time,
            "recorder": self._deployer_address,
            "exists": True,
            "block_number": self.block_number,
            "transaction_hash": tx_hash,
            "contract_address": self.contract_address,
        }

        self._records[norm_hash] = record_entry
        self._transactions[tx_hash] = record_entry

        return {
            "status": "success",
            "transaction_hash": tx_hash,
            "block_number": self.block_number,
            "contract_address": self.contract_address,
            "content_hash": norm_hash,
            "timestamp": current_time,
        }

    def get_record(self, bytes32_hash: str) -> Dict[str, Any]:
        norm_hash = self._normalize_bytes32(bytes32_hash)
        if norm_hash in self._records:
            return dict(self._records[norm_hash])
        return {
            "content_hash": norm_hash,
            "page_url": "",
            "platform": "",
            "timestamp": 0,
            "recorder": "0x0000000000000000000000000000000000000000",
            "exists": False,
            "block_number": 0,
            "transaction_hash": "",
            "contract_address": self.contract_address,
        }

    def verify_match(self, bytes32_hash: str) -> Tuple[bool, Dict[str, Any]]:
        record = self.get_record(bytes32_hash)
        is_verified = record.get("exists", False)
        return is_verified, record


class Web3BlockchainProvider(BaseBlockchainProvider):
    """
    Live Ethereum / EVM testnet provider connecting via web3.py.
    """
    ABI = [
        {
            "inputs": [
                {"name": "contentHash", "type": "bytes32"},
                {"name": "pageUrl", "type": "string"},
                {"name": "platform", "type": "string"}
            ],
            "name": "recordMatch",
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [{"name": "contentHash", "type": "bytes32"}],
            "name": "getRecord",
            "outputs": [
                {"name": "hash", "type": "bytes32"},
                {"name": "pageUrl", "type": "string"},
                {"name": "platform", "type": "string"},
                {"name": "timestamp", "type": "uint256"},
                {"name": "recorder", "type": "address"},
                {"name": "exists", "type": "bool"}
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"name": "contentHash", "type": "bytes32"}],
            "name": "verifyMatch",
            "outputs": [
                {"name": "isVerified", "type": "bool"},
                {"name": "timestamp", "type": "uint256"},
                {"name": "pageUrl", "type": "string"},
                {"name": "platform", "type": "string"}
            ],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    def __init__(self, rpc_url: str, contract_address: str, private_key: Optional[str] = None):
        try:
            from web3 import Web3
        except ImportError:
            raise RuntimeError("web3 package is required for Web3BlockchainProvider but not installed.")

        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to Web3 RPC endpoint: {rpc_url}")

        self.contract_address = self.w3.to_checksum_address(contract_address)
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=self.ABI)
        self.private_key = private_key
        if private_key:
            self.account = self.w3.eth.account.from_key(private_key)
        else:
            self.account = None

    def record_match(self, bytes32_hash: str, page_url: str, platform: str) -> Dict[str, Any]:
        if not self.account:
            raise ValueError("Private key is required to send on-chain record transaction")

        bytes32_bytes = bytes.fromhex(bytes32_hash.replace("0x", ""))
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        
        tx = self.contract.functions.recordMatch(
            bytes32_bytes, page_url, platform
        ).build_transaction({
            "from": self.account.address,
            "nonce": nonce,
            "gas": 200000,
            "gasPrice": self.w3.eth.gas_price,
        })

        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        return {
            "status": "success" if receipt.status == 1 else "failed",
            "transaction_hash": self.w3.to_hex(tx_hash),
            "block_number": receipt.blockNumber,
            "contract_address": self.contract_address,
            "content_hash": bytes32_hash,
        }

    def get_record(self, bytes32_hash: str) -> Dict[str, Any]:
        bytes32_bytes = bytes.fromhex(bytes32_hash.replace("0x", ""))
        rec = self.contract.functions.getRecord(bytes32_bytes).call()
        content_hash_hex = f"0x{rec[0].hex()}"
        return {
            "content_hash": content_hash_hex,
            "page_url": rec[1],
            "platform": rec[2],
            "timestamp": rec[3],
            "recorder": rec[4],
            "exists": rec[5],
            "contract_address": self.contract_address,
        }

    def verify_match(self, bytes32_hash: str) -> Tuple[bool, Dict[str, Any]]:
        record = self.get_record(bytes32_hash)
        return record.get("exists", False), record


def get_blockchain_provider(env_override: Optional[Dict[str, str]] = None) -> BaseBlockchainProvider:
    """
    Factory function to initialize the blockchain provider based on environment variables.
    Defaults to LocalBlockchainProvider if RPC_URL is absent or USE_LOCAL_BLOCKCHAIN is set.
    """
    env = env_override if env_override is not None else os.environ

    use_local = env.get("USE_LOCAL_BLOCKCHAIN", "true").lower() in ("true", "1", "yes")
    rpc_url = env.get("RPC_URL", "").strip()
    contract_address = env.get("CONTRACT_ADDRESS", "").strip()
    private_key = env.get("PRIVATE_KEY", "").strip()

    if not use_local and rpc_url and contract_address:
        try:
            return Web3BlockchainProvider(rpc_url=rpc_url, contract_address=contract_address, private_key=private_key)
        except Exception as err:
            # Fall back safely to LocalBlockchainProvider if RPC fails
            print(f"[Warning] Web3 RPC connection failed ({err}). Falling back to LocalBlockchainProvider.")
            return LocalBlockchainProvider()
    
    return LocalBlockchainProvider()
