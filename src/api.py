import requests
from dotenv import dotenv_values

#CONFIG
config = dotenv_values(".env")
CLIENT_ID = config.get("CLIENT_ID")
CLIENT_SECRET = config.get("CLIENT_SECRET")
REFRESH_TOKEN = config.get("REFRESH_TOKEN")
# ACCESS_TOKEN = config.get("ACCESS_TOKEN")
SHARD = "na1"
BASE_URL = f"https://api.{SHARD}.echosign.com"
SECRETS_FOLDER = "./client_secret/"
# URI_FILENAME = f"{SECRETS_FOLDER}adbe_sign_uri.json"

# TEST CONFIG
TOKEN_FILENAME = f"{SECRETS_FOLDER}adbe_dev_token.txt"


def refresh_token (client_id, client_secret, refresh_token):
    endpoint = f"{BASE_URL}/oauth/v2/refresh"
    print(f"Consultando: {endpoint}")

    payload = {
            'grant_type': 'refresh_token',
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token
        }

    headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

    try:
        api_response = requests.post(endpoint, data=payload, headers=headers)
        api_response.raise_for_status()
        
        tokens = api_response.json()
        new_access_token = tokens.get("access_token")
        print("Token renovado exitosamente.")
        return new_access_token
        
    except requests.exceptions.HTTPError as e:
        print(f"Error al refrescar: {e.response.status_code} - {e.response.text}")
        return None

# TEST CODE

refreshed_tkn = refresh_token(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)

# write token to file
with open (TOKEN_FILENAME, "w", encoding="utf-8") as file:
    file.write(refreshed_tkn)
