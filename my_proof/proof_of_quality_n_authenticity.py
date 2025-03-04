from base64 import b64decode
import json
import logging

# Check for Quality
def get_risk_status_and_quality(risk_score: float):
            if 8 < risk_score <= 10:
                return 0.75  # Lower quality for high risk

            elif 5 < risk_score <= 8:
                return  0.85
                
            elif 3 < risk_score <= 5:
                return  0.95
            
            else:
                return  1.0  # Highest quality for safest risk
                
        # Test cases
        # print(get_risk_status_and_quality(1))  # Safe Risk, Quality Score: 1.0
        # print(get_risk_status_and_quality(3))  # Safe Risk, Quality Score: 1.0
        # print(get_risk_status_and_quality(6))  # Moderate Risk, Quality Score: 0.85
        # print(get_risk_status_and_quality(8))  # High Safe, Quality Score: 0.75
 

# Check for Authenticity
def validate_token_metrics(metrics):
    """Perform authenticity checks on token metrics."""
    errors = []
    # Logical checks
    if metrics["circulatingSupply"] > 0:
        expected_market_cap = metrics["price"] * metrics["circulatingSupply"]
        if abs(expected_market_cap - metrics["marketCap"]) > 0.05 * expected_market_cap:
            errors.append("Market Cap doesn't match price * circulating supply.")
    
    if metrics["volatility24h"] > 100:
        errors.append("Volatility is unrealistically high (>100%).")
    
    print(f"print the error", errors)

    return 0.0 if errors else 1.0

def calculate_individual_proofs(unique_tokens, combined_tokens):
    results = []
    valid_chains = {
        "ethereum", "optimistic-ethereum", "cronos", "binance-smart-chain", "xdai", 
        "polygon-pos", "manta-pacific", "x-layer", "opbnb", "fantom", 
        "kucoin-community-chain", "zksync", "merlin-chain", "mantle", "base", 
        "arbitrum-one", "avalanche", "linea", "blast", "bitlayer", 
        "scroll", "zklink-nova", "tron", "vana", "solana"
    }
    
    valid_attributes = {
        "momentum-surge", "high-liquidity", "utility-driven", "backed-by-major-investors",
        "community-powered", "verified-contracts", "disruptive-tech", "major-integrations",
        "limited-supply"
    }
    
    valid_categories = {
        "MemeCoins", "Web3Gaming", "BlueChipDeFi", "AIAgent", "Layer1", "Layer2Layer3", 
        "RWA", "DecentralizedAI", "DecentralizedFinance", "DePIN", "LiquidStakingRestaking", 
        "BlockchainServiceInfra"
    }
    
    for token in unique_tokens:
        token_metadata = token.get("token_metadata", {})
        data_chain = token_metadata.get("chain", "").lower()
        data_contract = token_metadata.get("contract", "")
        metrics = token_metadata.get("metrics", {})
        
        if data_chain not in valid_chains:
            print(f"Skipping token {data_contract}: Invalid chain {data_chain}")
            continue
        
        token_category = token.get("tokenCategory", "")
        if token_category not in valid_categories:
            print(f"Skipping token {data_contract}: Invalid category {token_category}")
            continue
        
        suggestion_attributes = set(token.get("suggestionAttributes", []))
        recommendation_attributes = set(token.get("recommendationAttributes", []))
        has_valid_attributes = bool(suggestion_attributes & valid_attributes or recommendation_attributes & valid_attributes)
        
        individual_authenticity = validate_token_metrics(metrics) if has_valid_attributes else 0
        
        risk_score = metrics.get("riskScore", 0)
        individual_quality = get_risk_status_and_quality(risk_score)
        individual_quality *= individual_authenticity  # Ensure quality is zero if authenticity is zero

        # Calculate uniqueness: Check if the token exists in the combined set
        is_unique = not any(
            data_chain == existing_token["token_metadata"]["chain"] and
            data_contract == existing_token["token_metadata"]["contract"]
            for existing_token in combined_tokens
        )
        individual_uniqueness = 1.0 if is_unique else 0.0
        
        results.append({
            "token_submitted": data_contract,
            "chain": data_chain,
            "authenticity": individual_authenticity,
            "quality": individual_quality,
            "uniqueness": individual_uniqueness
        })
    
    return results

def final_scores(unique_tokens, combined_tokens):
    """Calculate the average authenticity and quality scores."""
    results = calculate_individual_proofs(unique_tokens, combined_tokens)
    # unique_token_count = len(unique_tokens)
    
    if not results:
        return 0, 0

    quality_avg = sum(result["quality"] for result in results) / len(results)
    authenticity_avg = sum(result["authenticity"] for result in results) / len(results)
    uniqueness_avg = sum(result["uniqueness"] for result in results) / len(results)
    logging.info(f"authenticity_avg: {authenticity_avg}, quality_avg: {quality_avg}, uniqueness_avg:, {uniqueness_avg},results, {results[0]}")
    return authenticity_avg, quality_avg, uniqueness_avg, results

# Execute the script independently for testing
if __name__ == "__main__":
    # Assuming we have some example unique tokens
    with open("../demo/input/tokenInput.json", "r") as file:
        data = json.load(file)
    
    unique_tokens = data.get("tokens", []) 
    results = calculate_individual_proofs( unique_tokens,[])
    authenticity, quality = final_scores(unique_tokens)
    print(f"authenticity, quality", authenticity, quality)

    # Output the results
    for result in results:
        # print(f"Token: {result['token']}")
        print(f"Individual authenticity: {result['authenticity']}, Individual quality: {result['quality']} , Result: {result}")
