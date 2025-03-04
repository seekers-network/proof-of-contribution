import os
import bs4
import jinja2
import redis
import requests
import gnupg
import zipfile
import io
import pandas as pd
import json
import logging
import yaml
from deepdiff import DeepDiff  # Ensure deepdiff is installed

# Initialize Redis connection
def get_redis_client():
    try:
        redis_client = redis.StrictRedis(
            host=os.environ.get('REDIS_HOST', 'localhost'),
            port=int(os.environ.get('REDIS_PORT', 6379)),
            db=0,
            password=os.environ.get('REDIS_PWD', None),
            decode_responses=True,
            socket_timeout=30,
            retry_on_timeout=True
        )
        redis_client.ping()
        return redis_client
    except redis.ConnectionError:
        logging.warning("Redis connection failed. Proceeding without caching.")
        return None

# Fetch file mappings from API
# TODO: Remove comments
def get_file_mappings(wallet_address):
    validator_base_api_url = os.environ.get('VALIDATOR_BASE_API_URL')
    endpoint = "/api/userinfo"
    url = f"{validator_base_api_url.rstrip('/')}{endpoint}"

    payload = {"walletAddress": wallet_address}  # Send walletAddress in the body
    headers = {"Content-Type": "application/json"}  # Set headers for JSON request

    response = requests.post(url, json=payload, headers=headers)  # Make POST request

    if response.status_code == 200:
        return response.json()  # Return JSON response
    else:
        return []  # Return empty list in case of an error
    # return [{"fileId":1615127, "fileUrl":"https://drive.google.com/uc?export=download&id=1DX-e7gzJHQ_j_EJWUeBUdhYgwxmKf2oF"}
    #         ,{"fileId":1615146, "fileUrl":"https://drive.google.com/uc?export=download&id=1qm0gQ3w462qZYdTrDH4bU8wuH8Qs9dVq"}
    #         ]

# Download and decrypt file
def download_and_decrypt(file_url, gpg_signature):
    response = requests.get(file_url)
    if response.status_code == 200:
        gpg = gnupg.GPG()
        decrypted_data = gpg.decrypt(response.content, passphrase=gpg_signature)
        if decrypted_data.ok:
            return decrypted_data.data
        else:
            logging.error("Decryption failed.")
            return None
    else:
        logging.error(f"Failed to download file: {response.status_code}")
        return None

# Extract files from ZIP data
def extract_files_from_zip(zip_data):
    json_data_list = []

    # Check if the data is a zip file by inspecting the header
    if zip_data[:2] == b'PK':  # Check for the "PK" header of ZIP files
        with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zip_ref:
            for file_name in zip_ref.namelist():
                with zip_ref.open(file_name) as file:
                    content = file.read().decode("utf-8")
                    
                    if file_name.endswith('.json'):
                        json_data = json.loads(content)
                        json_data_list.append(json_data)
    else:
        # If it's not a ZIP, assume it's a JSON file directly
        content = zip_data.decode("utf-8")
        json_data = json.loads(content)
        json_data_list.append(json_data)
    
    return json_data_list

def process_json_files(redis_client, file_mappings, gpg_signature, input_dir):
    combined_json_data = []

    if redis_client:
        for file_info in file_mappings:
            file_id = file_info.get("fileId")
            if redis_client.exists(file_id):
                stored_json_data = redis_client.hget(file_id, "submission_data")
                if stored_json_data:
                    json_data = json.loads(stored_json_data)
                    combined_json_data.extend(json_data)
                else:
                    file_url = file_info.get("fileUrl")
                    if not file_url:
                        logging.warning(f"Skipping invalid fileUrl for fileId {file_id}")
                        continue

                    decrypted_data = download_and_decrypt(file_url, gpg_signature)
                    if decrypted_data:
                        json_data_list = extract_files_from_zip(decrypted_data)
                        if json_data_list:
                            combined_json_data.extend(json_data_list)
            else:
                file_url = file_info.get("fileUrl")
                if not file_url:
                    logging.warning(f"Skipping invalid fileUrl for fileId {file_id}")
                    continue
                decrypted_data = download_and_decrypt(file_url, gpg_signature)
                if decrypted_data:
                    json_data_list = extract_files_from_zip(decrypted_data)
                    if json_data_list:
                        combined_json_data.extend(json_data_list)
    else:
        for file_info in file_mappings:
            file_url = file_info.get("fileUrl")
            if not file_url:
                logging.warning(f"Skipping invalid fileUrl for fileId {file_info.get('fileId')}")
                continue
            decrypted_data = download_and_decrypt(file_url, gpg_signature)
            if decrypted_data:
                json_data_list = extract_files_from_zip(decrypted_data)
                if json_data_list:
                    combined_json_data.extend(json_data_list)

    curr_file_json_data = []
    local_json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
    for json_file in local_json_files:
        file_path = os.path.join(input_dir, json_file)
        with open(file_path, 'r') as file:
            json_data = json.load(file)
            curr_file_json_data.append(json_data)
        with open(file_path, 'w') as file:
            json.dump(json_data, file, indent=4)

    print("JSON files processed and formatted successfully.")

    # Flatten the list of tokens for comparison
    curr_file_tokens = [token for entry in curr_file_json_data for token in entry["tokens"]]
    combined_tokens = [token for entry in combined_json_data for token in entry.get("tokens", [])]

    # Calculate uniqueness by comparing current file tokens against combined (old) tokens
    unique_tokens = []
    for token in curr_file_tokens:
        # Check if the token exists in the combined data with the exact same 'reason'
        if not any(
            token["token_metadata"]["chain"] == existing_token["token_metadata"]["chain"] and
            token["token_metadata"]["contract"] == existing_token["token_metadata"]["contract"]
            for existing_token in combined_tokens
        ):
            unique_tokens.append(token)

    # Calculate total and unique entries
    total_json_entries = len(curr_file_tokens)
    unique_json_entries = len(unique_tokens)

    # Uniqueness score calculation
    json_uniqueness_score = unique_json_entries / total_json_entries if total_json_entries > 0 else 0.0

    print(f"Uniqueness Score: {json_uniqueness_score}, {unique_json_entries} unique tokens out of {total_json_entries} total tokens.")
    print(f"Unique Tokens: {unique_tokens}")

    return combined_json_data, curr_file_json_data, json_uniqueness_score, unique_tokens


def uniqueness_details(wallet_address, input_dir):
    wallet_address = wallet_address
    gpg_signature = os.environ.get("SIGNATURE") 
    redis_client = get_redis_client()
    file_mappings = get_file_mappings(wallet_address)
    
    combined_json_data, curr_file_json_data, json_uniqueness_score, unique_json_entries = process_json_files(redis_client, file_mappings, gpg_signature, input_dir)
    
    return {
        "unique_json_data": unique_json_entries,
        "old_files_json_data": combined_json_data,
        "curr_file_json_data": curr_file_json_data,
        "uniqueness_score": json_uniqueness_score
    }

# Execute the script independently for testing the values
if __name__ == "__main__":
    redis_client = get_redis_client()
    file_mappings = get_file_mappings("0x1234567890abcdef")
    gpg_signature = ""
    input_dir = "../demo/input"
    
    combined_json_data, curr_file_json_data, json_uniqueness_score, unique_json_entries = process_json_files(redis_client, file_mappings, gpg_signature, input_dir)
    
    print("Unique JSON Entries:", unique_json_entries)
    print("Combined JSON Data:", combined_json_data)
    print("Current File JSON Data:", curr_file_json_data)
    print("JSON Uniqueness Score:", json_uniqueness_score)