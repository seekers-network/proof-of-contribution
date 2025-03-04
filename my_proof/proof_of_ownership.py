import logging
import os
import json
from eth_account import Account
from eth_account.messages import encode_defunct

def recover_account(author: str) -> bool:
    try:
        message_text = os.environ.get("FIXED_MESSAGE")
        signature = os.environ.get("SIGNATURE")

        # Encode the message properly
        message_encoded = encode_defunct(text=message_text)

        # Recover the address
        recovered_address = Account.recover_message(message_encoded, signature=signature)
        
        if recovered_address.lower() == author.lower():
            logging.info(f"Ownership verified successfully for address: {recovered_address}")
            return True
        else:
            logging.warning(f"Recovered address {recovered_address} does not match author {author}")
            return False
    except Exception as e:
        logging.error(f"Error during recovery: {e}")
        return False

def verify_ownership(input_dir: str) -> float:
    """Verify ownership by checking the signature in a .txt file."""
    # logging.info(f"Verifying ownership in directory: {input_dir}")
    json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]

    if len(json_files) != 1:
        logging.warning("There should be exactly one .json file for wallet address extraction.")
        return 0.0

    json_file_path = os.path.join(input_dir, json_files[0])
    with open(json_file_path, 'r') as json_file:
        wallet_data = json.load(json_file)
        wallet_address = wallet_data.get("userAddress")

    if not wallet_address:
        logging.warning("Wallet address not found in the .json file.")
        return 0.0

    is_valid = recover_account(wallet_address)
    return 1.0 if is_valid else 0.0


# Execute the script independently for testing
if __name__ == "__main__":
    input_dir = "../demo/input"
    verify_ownership(input_dir)