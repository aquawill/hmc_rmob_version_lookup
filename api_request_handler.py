import os
import threading
import time

import requests
from requests_oauthlib import OAuth1

# Global variables
TOKEN_CACHE = {"token": None, "expires_at": 0}
TOKEN_LOCK = threading.Lock()  # Prevent race conditions when updating Token


def load_credentials(file_path="credential.properties"):
    """
    Load credentials from file or environment variables.
    """
    credentials = {}

    # Check if credential.properties exists
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    credentials[key.strip()] = value.strip()

    # Load from environment variables
    credentials["here.token.endpoint.url"] = credentials.get("here.token.endpoint.url", os.getenv("HERE_TOKEN_URL"))
    credentials["here.access.key.id"] = credentials.get("here.access.key.id", os.getenv("HERE_CLIENT_ID"))
    credentials["here.access.key.secret"] = credentials.get("here.access.key.secret", os.getenv("HERE_CLIENT_SECRET"))

    # Check for missing credentials
    missing_keys = [key for key, value in credentials.items() if not value]

    if missing_keys:
        return {
            "credentials": credentials,
            "status": "error",
            "message": f"Missing required credentials: {', '.join(missing_keys)}"
        }
    else:
        return {
            "credentials": credentials,
            "status": "ok",
            "message": "All credentials are loaded successfully."
        }


# Load credentials once, but do not validate immediately
credentials_result = load_credentials()
CREDENTIALS = credentials_result["credentials"]

OAUTH2_URL = CREDENTIALS.get("here.token.endpoint.url")
CLIENT_ID = CREDENTIALS.get("here.access.key.id")
CLIENT_SECRET = CREDENTIALS.get("here.access.key.secret")


def get_oauth_token():
    """
    Obtain OAuth2 Token, ensuring it is shared within its validity period.
    """
    global TOKEN_CACHE

    # Ensure credentials are valid before attempting token request
    if credentials_result["status"] == "error":
        raise Exception(f"Cannot retrieve Token: {credentials_result['message']}")

    with TOKEN_LOCK:
        # Return cached Token if still valid
        if TOKEN_CACHE["token"] and time.time() < TOKEN_CACHE["expires_at"]:
            return TOKEN_CACHE["token"]

        # Request a new Token
        oauth = OAuth1(client_key=CLIENT_ID, client_secret=CLIENT_SECRET, signature_type='auth_header')
        response = requests.post(OAUTH2_URL, data={"grant_type": "client_credentials"},
                                 auth=oauth, headers={"Content-Type": "application/x-www-form-urlencoded"})

        if response.status_code == 200:
            data = response.json()
            TOKEN_CACHE["token"] = data["access_token"]
            # TOKEN_CACHE["expires_at"] = time.time() + data.get("expires_in", 3600)  # Default 1-hour expiration
            TOKEN_CACHE["expires_at"] = time.time() + 10
            return TOKEN_CACHE["token"]
        elif response.status_code == 401:
            raise Exception("Invalid credentials: Authentication failed (401 Unauthorized). Please check API keys.")
        else:
            raise Exception(f"OAuth2 Token request failed: {response.text}")


def validate_credentials():
    """
    Validate the credentials by attempting to retrieve a Token.
    If authentication fails (401), raise an error and prevent API startup.
    """
    global TOKEN_CACHE
    try:
        # If no valid token is cached, request one and store it in TOKEN_CACHE
        if not TOKEN_CACHE["token"] or time.time() >= TOKEN_CACHE["expires_at"]:
            token = get_oauth_token()
            print("✅ Credentials validated successfully. Token acquired.")
        else:
            print("✅ Credentials validated. Using cached Token.")
        return True
    except Exception as e:
        raise Exception(f"[ERROR] {str(e)}")


def request_with_token_refresh(url, method="GET", retry=True):
    """
    Perform an API request, refreshing Token on 401 Unauthorized.
    """

    def make_request(token):
        headers = {"Authorization": f"Bearer {token}"}
        if method == "GET":
            return requests.get(url, headers=headers)
        elif method == "POST":
            return requests.post(url, headers=headers)
        else:
            raise ValueError("Unsupported HTTP method")

    token = get_oauth_token()
    response = make_request(token)

    # If Token expired (401), refresh it and retry once
    if response.status_code == 401 and retry:
        print("[WARN] Token expired, refreshing and retrying...")
        token = get_oauth_token()  # Obtain new Token
        response = make_request(token)  # Retry request with new Token

    return response


# Do NOT call validate_credentials() here to prevent multiple executions
if __name__ == "__main__":
    validate_credentials()
