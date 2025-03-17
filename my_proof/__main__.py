import json
import logging
import os
import sys
import traceback
import zipfile
from typing import Dict, Any
from my_proof.proof import Proof

# Default to 'production' if NODE_ENV is not set
environment = os.environ.get('NODE_ENV', 'production')

# Set the input and output directories based on the environment
INPUT_DIR = './demo/input' if environment == 'development' else '/input'
OUTPUT_DIR = './demo/output' if environment == 'development' else '/output'
SEALED_DIR = './demo/sealed' if environment == 'development' else '/sealed'

logging.basicConfig(level=logging.INFO, format='%(message)s')

def load_config() -> Dict[str, Any]:
    """Load proof configuration from environment variables."""
    config = {
        'input_dir': INPUT_DIR,
        'use_sealing': os.path.isdir(SEALED_DIR),
        'dlp_id': os.environ.get("DLP_ID", 31),  # DLP ID defaults to 31
        'jwt_expiration_time': os.environ.get('JWT_EXPIRATION_TIME', 600),
        'validator_base_api_url': os.environ.get('VALIDATOR_BASE_API_URL', None),
        'jwt_secret_key': os.environ.get('JWT_SECRET_KEY'),
        'file_id': os.environ.get('FILE_ID'),
        'signature': os.environ.get('SIGNATURE'),
        'max_token_reward': os.environ.get("MAX_TOKEN_REWARD",5),
        'reward_per_token': os.environ.get("REWARD_PER_TOKEN",1),
        'fixed_message': os.environ.get('FIXED_MESSAGE'),
        'redis_port': os.environ.get('REDIS_PORT', None),
        'redis_host': os.environ.get('REDIS_HOST', None),
        'redis_pwd': os.environ.get('REDIS_PWD', None),
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
    logging.info(f"Using config: {json.dumps(config, indent=2)}")
    return config


def run() -> None:
    """Generate proofs for all input files."""
    config = load_config()
    input_files_exist = os.path.isdir(INPUT_DIR) and bool(os.listdir(INPUT_DIR))

    if not input_files_exist:
        raise FileNotFoundError(f"No input files found in {INPUT_DIR}")
    extract_input()

    proof = Proof(config)
    proof_response = proof.generate()

    output_path = os.path.join(OUTPUT_DIR, "results.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(proof_response.model_dump(), f, indent=2)
    logging.info(f"Proof generation complete: {proof_response}")


def extract_input() -> None:
    """
    If the input directory contains any zip files, extract them
    :return:
    """
    for input_filename in os.listdir(INPUT_DIR):
        input_file = os.path.join(INPUT_DIR, input_filename)

        if zipfile.is_zipfile(input_file):
            with zipfile.ZipFile(input_file, 'r') as zip_ref:
                zip_ref.extractall(INPUT_DIR)


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logging.error(f"Error during proof generation: {e}")
        traceback.print_exc()
        sys.exit(1)
