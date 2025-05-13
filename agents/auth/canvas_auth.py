#!/usr/bin/env python3
"""
Authentication script for Canvas API
"""

import os
import requests
import argparse
from dotenv import load_dotenv

def canvas_authenticate(client_id=None, client_secret=None, canvas_instance_identifier=None):
    """
    Authenticate with Canvas API and get a token.
    
    Args:
        client_id (str, optional): Canvas client ID. Defaults to env var CANVAS_CLIENT_ID.
        client_secret (str, optional): Canvas client secret. Defaults to env var CANVAS_CLIENT_SECRET.
        
    Returns:
        dict: Authentication result with status and token or error message.
    """
    # Load from .env file if present
    load_dotenv()
    
    # Use provided credentials or get from environment
    client_id = client_id or os.environ.get("CANVAS_CLIENT_ID")
    client_secret = client_secret or os.environ.get("CANVAS_CLIENT_SECRET")
    canvas_instance_identifier = canvas_instance_identifier or os.environ.get("CANVAS_INSTANCE_IDENTIFIER")
    
    if not client_id or not client_secret or not canvas_instance_identifier:
        return {
            "status": "error",
            "error_message": "Canvas credentials not found. Please provide client ID/secret or set environment variables."
        }
    
    try:
        # Authenticate with Canvas
        auth_url = f"https://{canvas_instance_identifier}.canvasmedical.com/auth/token/"
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
    Command-line interface for Canvas authentication.
    """
    parser = argparse.ArgumentParser(description="Authenticate with Canvas API")
    parser.add_argument("--client-id", help="Canvas client ID")
    parser.add_argument("--client-secret", help="Canvas client secret")
    parser.add_argument("--instance-identifier", help="Canvas instance identifier")
    parser.add_argument("--save", action="store_true", help="Save token to .env file")
    args = parser.parse_args()
    
    # Authenticate with provided credentials or environment variables
    result = canvas_authenticate(args.client_id, args.client_secret, args.instance_identifier)
    
    if result["status"] == "success":
        token = result["token"]
        expires_in = result["expires_in"]
        print(f"Authentication successful!")
        print(f"Canvas Token: {token}")
        print(f"Token expires in: {expires_in} seconds")
        
        # Save token to .env file if requested
        if args.save:
            env_file = ".env"
            
            # Read existing .env file if it exists
            # Store all lines faithfully, unless it is a line for CANVAS_TOKEN.
            # In that case, store a replacement line with the new token value.
            # If none of the lines were for the CANVAS_TOKEN, append it to the
            # end.
            env_file_lines = []
            canvas_token_line_set = False
            if os.path.exists(env_file):
                with open(env_file, "r") as f:
                    for line in f:
                        if line.startswith("#") or line.strip() == "":
                            env_file_lines.append(line)
                        elif "=" in line:
                            key, value = line.strip().split("=", 1)
                            if key == "CANVAS_TOKEN":
                                updated_token_line = f"CANVAS_TOKEN={token}\n"
                                env_file_lines.append(updated_token_line)
                                canvas_token_line_set = True
                            else:
                                env_file_lines.append(line)
            if not canvas_token_line_set:
                env_file_lines.append(f"CANVAS_TOKEN={token}\n")
            
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
