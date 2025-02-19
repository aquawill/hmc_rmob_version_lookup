import time
import requests
from requests_oauthlib import OAuth1
import threading
import os

# Load credentials
def load_credentials(file_path="credential.properties"):
    credentials = {}

    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    credentials[key.strip()] = value.strip()

    return {
        "here.token.endpoint.url": credentials.get("here.token.endpoint.url", os.getenv("HERE_TOKEN_URL")),
        "here.access.key.id": credentials.get("here.access.key.id", os.getenv("HERE_CLIENT_ID")),
        "here.access.key.secret": credentials.get("here.access.key.secret", os.getenv("HERE_CLIENT_SECRET"))
    }

# Global Token Cache
TOKEN_CACHE = {"token": None, "expires_at": 0}
TOKEN_LOCK = threading.Lock()  # 避免多線程同時更新 Token

# Load credentials
CREDENTIALS = load_credentials()
OAUTH2_URL = CREDENTIALS["here.token.endpoint.url"]
CLIENT_ID = CREDENTIALS["here.access.key.id"]
CLIENT_SECRET = CREDENTIALS["here.access.key.secret"]

def get_oauth_token():
    """取得 OAuth2 Token，並確保在有效期間內共享 Token"""
    global TOKEN_CACHE

    with TOKEN_LOCK:
        # 若 Token 尚未過期，直接回傳
        if TOKEN_CACHE["token"] and time.time() < TOKEN_CACHE["expires_at"]:
            return TOKEN_CACHE["token"]

        # 重新請求 Token
        oauth = OAuth1(client_key=CLIENT_ID, client_secret=CLIENT_SECRET, signature_type='auth_header')
        response = requests.post(OAUTH2_URL, data={"grant_type": "client_credentials"},
                                 auth=oauth, headers={"Content-Type": "application/x-www-form-urlencoded"})

        if response.status_code == 200:
            data = response.json()
            TOKEN_CACHE["token"] = data["access_token"]
            TOKEN_CACHE["expires_at"] = time.time() + data.get("expires_in", 3600)  # 預設 1 小時過期
            return TOKEN_CACHE["token"]
        else:
            raise Exception(f"OAuth2 Token error: {response.text}")
