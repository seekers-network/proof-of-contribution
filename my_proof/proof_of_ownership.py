import logging
import os
import json
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

RPC_URLS = { 
        "vana": os.environ.get("VANA_RPC_URL"),
        "ethereum": os.environ.get("ETH_RPC_URL"),
        "base": os.environ.get("BASE_RPC_URL"),
        "optimistic-ethereum": os.environ.get("OPTIMISM_RPC_URL"),
        "binance-smart-chain": os.environ.get("BSC_RPC_URL"),
        "polygon-pos": os.environ.get("POLYGON_RPC_URL"),
        "opbnb": os.environ.get("OPBNB_RPC_URL"),
        "zksync": os.environ.get("ZK_RPC_URL"),
        "mantle": os.environ.get("MANTLE_RPC_URL"),
        "scroll": os.environ.get("SCROLL_RPC_URL"),
        "arbitrum-one": os.environ.get("ARBITRUM_RPC_URL"),
        "avalanche": os.environ.get("AVALANCHE_RPC_URL"),
        "linea": os.environ.get("LINEA_RPC_URL"),
        "blast": os.environ.get("BLAST_RPC_URL"),
        "solana": os.environ.get("SOLANA_RPC_URL"),
        "xdai": os.environ.get("GNOSIS_RPC_URL"),
        "fantom": os.environ.get("FANTOM_RPC_URL"),
        "zklink-nova": os.environ.get("ZKLINK_RPC_URL"),
        "tron": os.environ.get("TRON_RPC_URL"),
        "kucoin-community-chain": os.environ.get("KCC_RPC_URL"),
        "manta-pacific": os.environ.get("MANTA_RPC_URL"),
        "x-layer": os.environ.get("XLAYER_RPC_URL"),
        "merlin-chain": os.environ.get("MERLIN_RPC_URL"),
        "bitlayer": os.environ.get("BITLAYER_RPC_URL"),
        "cronos": os.environ.get("CRONOS_RPC_URL"),
    }

NON_EVM_CHAINS = {"solana", "tron", "zklink-nova"}

def check_token_ownership(chain: str, token_address: str, wallet_address: str) -> bool:
    """
    Checks if a wallet owns a given ERC-20 token by checking the balance.
    
    :param chain: The blockchain network to check.
    :param token_address: The contract address of the ERC-20 token.
    :param wallet_address: The wallet address to check ownership for.
    :return: True if the wallet owns the token (has a balance > 0), False otherwise. Returns 1 for non-EVM chains.
    """
    if chain in NON_EVM_CHAINS:
        return 1
    
    rpc_url = RPC_URLS.get(chain)
    if not rpc_url:
        raise ValueError(f"RPC URL not found for chain: {chain}")
    
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise ConnectionError("Failed to connect to RPC")
    
    wallet_address = Web3.to_checksum_address(wallet_address)
    token_address = Web3.to_checksum_address(token_address)
    
    erc20_abi = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    contract = w3.eth.contract(address=token_address, abi=erc20_abi)
    balance = contract.functions.balanceOf(wallet_address).call()
    
    return balance > 0
