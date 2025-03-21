from datetime import datetime
from web3 import Web3
import json
import logging
import os
from typing import Dict, Any
import json

from my_proof.proof_of_ownership import RPC_URLS , check_token_ownership
from my_proof.proof_of_uniqueness import uniqueness_details
from my_proof.proof_of_quality_n_authenticity import final_scores
from my_proof.models.proof_response import ProofResponse

class Proof:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.proof_response = ProofResponse(dlp_id=config['dlp_id'])
        self.max_rewards = int(os.environ.get("MAX_TOKEN_REWARD",5))
        self.reward_per_token = int(os.environ.get("REWARD_PER_TOKEN",1))
        self.wallet_address = ""
    
    def read_author_from_file(self, file_path: str):
        """
        Read parameters from a text file.

        :param file_path: Path to the text file
        :return: Tuple containing author, signature, and random_string
        """
        params = {}
        with open(file_path, "r") as file:
            for line in file:
                key, value = line.strip().split(": ", 1)
                params[key] = value
        return params["author"]

    def generate(self) -> ProofResponse:
        """Generate proofs for all input files."""
        logging.info("Starting proof generation")

        json_files = [f for f in os.listdir(self.config['input_dir']) if f.endswith('.json')]

        json_file_path = os.path.join(self.config['input_dir'], json_files[0])
        with open(json_file_path, 'r') as json_file:
            wallet_data = json.load(json_file)
            self.wallet_address = wallet_data.get("userAddress").lower()
        
        print(f"wallet address from proof is",self.wallet_address)

        uniqueness_details_ = uniqueness_details(self.wallet_address, self.config['input_dir'] )
        unique_tokens = uniqueness_details_.get("unique_json_data", [])
        combined_tokens = uniqueness_details_.get("old_files_json_data",[])
        # combined_tokens = unique_tokens + unique_tokens # for testing uniquness

        logging.info(f" Count of Unique tokens from proof.py: {len(unique_tokens)}")

        authenticity_score, quality_score, uniqueness_score, metadata = final_scores(unique_tokens, combined_tokens)
        self.proof_response.quality = quality_score
        self.proof_response.authenticity = authenticity_score
        self.proof_response.uniqueness = uniqueness_score

        self.proof_response.score = self.calculate_final_score(len(unique_tokens))
        self.proof_response.valid = True

        # Additional metadata about the proof, written onchain
        for item in metadata:
            token_address = item["token_submitted"]
            chain = item["chain"]
            item["ownership"] = 1.0 if check_token_ownership(chain, token_address, self.wallet_address) else 0.95
            item["score"] = (item["authenticity"] + item["quality"] + item["uniqueness"] + item["ownership"]) / 4  # Compute avg score

        self.proof_response.ownership = sum(item["ownership"] for item in metadata) / len(metadata) if metadata else 0

        self.proof_response.metadata = {
            'dlp_id': self.config['dlp_id'],
            'submission_time': datetime.now().isoformat(),
            'token_rewarded': len(unique_tokens) * self.reward_per_token,
            'metadata': metadata,
        }

        return self.proof_response
    
    def calculate_final_score(self, unique_token_count) -> float:
        score = (unique_token_count * self.reward_per_token) / (self.max_rewards)
        return score
