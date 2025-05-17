#!/usr/bin/env python3
"""
Authentication script for PhenoML API
"""

import os
import base64
import requests
import argparse
from dotenv import load_dotenv

def phenoml_authenticate(identity=None, password=None):
    """
    Authenticate with PhenoML API and get a token.
    
    Args:
        identity (str, optional): PhenoML identity. Defaults to env var PHENOML_IDENTITY.
        password (str, optional): PhenoML password. Defaults to env var PHENOML_PASSWORD.
        
    Returns:
        dict: Authentication result with status and token or error message.
    """
    # Load from .env file if present
    load_dotenv()
    
    # Use provided credentials or get from environment
    identity = identity or os.environ.get("PHENOML_IDENTITY")
    password = password or os.environ.get("PHENOML_PASSWORD")
    
    if not identity or not password:
        return {
            "status": "error",
            "error_message": "PhenoML credentials not found. Please provide identity/password or set environment variables."
        }
    
    try:
        # Create Basic Auth credentials
        auth_string = f"{identity}:{password}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        # Authenticate with PhenoML
        auth_url = "https://experiment.app.pheno.ml/auth/token"
        headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Accept": "application/json"
        }
        
        auth_response = requests.post(auth_url, headers=headers)
        auth_response.raise_for_status()
        
        # Extract token from response
        auth_data = auth_response.json()
        token = auth_data.get("token")
        
        if not token:
            return {
                "status": "error",
                "error_message": "Failed to retrieve token from authentication response."
            }
        
        return {
            "status": "success",
            "token": token
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Authentication failed: {str(e)}"
        }

def main():
    """
    Command-line interface for PhenoML authentication.
    """
    parser = argparse.ArgumentParser(description="Authenticate with PhenoML API")
    parser.add_argument("--identity", help="PhenoML identity")
    parser.add_argument("--password", help="PhenoML password")
    parser.add_argument("--save", action="store_true", help="Save token to .env file")
    args = parser.parse_args()
    
    # Authenticate with provided credentials or environment variables
    result = phenoml_authenticate(args.identity, args.password)
    
    if result["status"] == "success":
        token = result["token"]
        print(f"Authentication successful!")
        print(f"PhenoML Token: {token}")
        
        # Save token to .env file if requested
        if args.save:
            env_file = ".env"
            
            # Read existing .env file if it exists
            # Store all lines faithfully, unless it is a line for PHENOML_TOKEN.
            # In that case, store a replacement line with the new token value.
            # If none of the lines were for the PHENOML_TOKEN, append it to the
            # end.
            env_file_lines = []
            token_line_set = False
            if os.path.exists(env_file):
                with open(env_file, "r") as f:
                    for line in f:
                        if line.startswith("#") or line.strip() == "":
                            env_file_lines.append(line)
                        elif "=" in line:
                            key, value = line.strip().split("=", 1)
                            if key == "PHENOML_TOKEN":
                                updated_token_line = f"PHENOML_TOKEN={token}\n"
                                env_file_lines.append(updated_token_line)
                                token_line_set = True
                            else:
                                env_file_lines.append(line)
            if not token_line_set:
                env_file_lines.append(f"PHENOML_TOKEN={token}\n")
            
            # Write the updated env file
            with open(env_file, "w") as f:
                for line in env_file_lines:
                    f.write(f"{line}")
            
            print(f"Token saved to {env_file}")
    else:
        print(f"Authentication failed: {result['error_message']}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
