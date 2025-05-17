#!/usr/bin/env python3
"""
Authentication script for Medplum API
"""

import os
import requests
import argparse
from dotenv import load_dotenv

def medplum_authenticate(client_id=None, client_secret=None):
    """
    Authenticate with Medplum API and get a token.
    
    Args:
        client_id (str, optional): Medplum client ID. Defaults to env var MEDPLUM_CLIENT_ID.
        client_secret (str, optional): Medplum client secret. Defaults to env var MEDPLUM_CLIENT_SECRET.
        
    Returns:
        dict: Authentication result with status and token or error message.
    """
    # Load from .env file if present
    load_dotenv()
    
    # Use provided credentials or get from environment
    client_id = client_id or os.environ.get("MEDPLUM_CLIENT_ID")
    client_secret = client_secret or os.environ.get("MEDPLUM_CLIENT_SECRET")
    medplum_url = os.environ.get("MEDPLUM_BASE_URL")
    
    if not client_id or not client_secret:
        return {
            "status": "error",
            "error_message": "Medplum credentials not found. Please provide client ID/secret or set environment variables."
        }

    if not medplum_url:
        # if no medplum_url is provided, use the default api.medplum.com
        medplum_url = "https://api.medplum.com"

    try:
        # Authenticate with Medplum
        auth_url = f"{medplum_url}/oauth2/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        auth_response = requests.post(auth_url, data=payload, headers=headers)
        auth_response.raise_for_status()
        
        # Extract token from response
        auth_data = auth_response.json()
        token = auth_data.get("access_token")
        
        if not token:
            return {
                "status": "error",
                "error_message": "Failed to retrieve access token from authentication response."
            }
        
        return {
            "status": "success",
            "token": token,
            "expires_in": auth_data.get("expires_in", 3600)
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Authentication failed: {str(e)}"
        }

def main():
    """
    Command-line interface for Medplum authentication.
    """
    parser = argparse.ArgumentParser(description="Authenticate with Medplum API")
    parser.add_argument("--client-id", help="Medplum client ID")
    parser.add_argument("--client-secret", help="Medplum client secret")
    parser.add_argument("--save", action="store_true", help="Save token to .env file")
    args = parser.parse_args()
    
    # Authenticate with provided credentials or environment variables
    result = medplum_authenticate(args.client_id, args.client_secret)
    
    if result["status"] == "success":
        token = result["token"]
        expires_in = result["expires_in"]
        print(f"Authentication successful!")
        print(f"Medplum Token: {token}")
        print(f"Token expires in: {expires_in} seconds")
        
        # Save token to .env file if requested
        if args.save:
            env_file = ".env"
            
            # Read existing .env file if it exists
            # Store all lines faithfully, unless it is a line for MEDPLUM_TOKEN.
            # In that case, store a replacement line with the new token value.
            # If none of the lines were for the MEDPLUM_TOKEN, append it to the
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
                            if key == "MEDPLUM_TOKEN":
                                updated_token_line = f"MEDPLUM_TOKEN={token}\n"
                                env_file_lines.append(updated_token_line)
                                token_line_set = True
                            else:
                                env_file_lines.append(line)
            if not token_line_set:
                env_file_lines.append(f"MEDPLUM_TOKEN={token}\n")
            
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
