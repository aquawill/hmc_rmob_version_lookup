import requests
from requests_oauthlib import OAuth1

# HERE API 設定
OAUTH2_URL = "https://account.api.here.com/oauth2/token"
CLIENT_ID = "E0sDiHLpeKp6X71TqSlKXQ"
CLIENT_SECRET = "WTbJVyLiWLiNYm4tsdOhcj-ZK0i5PQiKjCoKz89ztsj9unHeFXTMhWwo_SCD8cTZ1RQPgk0tm1YPn3kKkkWlHA"

oauth = OAuth1(client_key=CLIENT_ID, client_secret=CLIENT_SECRET, signature_type='auth_header')
r = requests.post('https://account.api.here.com/oauth2/token', data=dict(grant_type='client_credentials'), auth=oauth,
                  headers={'Content-Type': 'application/x-www-form-urlencoded'})

access_token = r.json()['access_token']

print(access_token)
