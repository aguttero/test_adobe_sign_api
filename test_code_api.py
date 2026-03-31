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

## ENDPOINTS
GET_URI_ENDPOINT = f"https://api.{SHARD}.adobesign.com/api/rest/v6/baseUris"
REFRESH_ENDPOINT = f"{BASE_URL}/oauth/v2/refresh"
FETCH_USER_LIST_ENDPOINT = f"{BASE_URL}/api/rest/v6/users"
SECRETS_FOLDER = "./client_secret/"
# URI_FILENAME = f"{SECRETS_FOLDER}adbe_sign_uri.json"

# TEST CONFIG
TOKEN_FILENAME = f"{SECRETS_FOLDER}adbe_dev_token.txt"

# test_access_token = ""

def refresh_token (client_id, client_secret, refresh_token):
    endpoint = REFRESH_ENDPOINT
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

def get_uris(token):
    endpoint = GET_URI_ENDPOINT
    print(f"Consultando: {endpoint}")

    headers = {
            'Authorization': f"Bearer {token}"
        }

    try:
        api_response = requests.get(endpoint, headers=headers)
        api_response.raise_for_status()
        
        uris = api_response.json()
        api_base_uri = uris.get("apiAccessPoint")
        print("OK URIs")
        print(f"{uris}")
        return api_base_uri
        
    except requests.exceptions.HTTPError as e:
        print(f"Error: {e.response.status_code} - {e.response.text}")
        return None    

## TODO FETCH USER LIST
def fetch_adobe_users(token):
    all_users = []
    cursor = None

    endpoint = FETCH_USER_LIST_ENDPOINT
    print(f"Consultando: {endpoint}")
    
    headers = {
            'Authorization': f"Bearer {token}"
        }

    try:
        api_response = requests.get(endpoint, headers=headers)
        api_response.raise_for_status()
        
        response_data = api_response.json()
        all_users.extend(response_data['userInfoList'])
        print("OK Users page 1")
        print("- - - - - - ")
        print ("all_users:", all_users)
        return all_users

        #cual es la diferencia en utilizar .extend en lugar de .append en la lista all_users?

        # api_base_uri = uris.get("apiAccessPoint")
        # print(f"{uris}")
        # return api_base_uri
        
    except requests.exceptions.HTTPError as e:
        print(f"Error: {e.response.status_code} - {e.response.text}")
        return None    


##
    # while True:
    #     # Llamada hipotética al SDK o requests
    #     response = api_client.get_users(cursor=cursor)
    #     all_users.extend(response['userlist'])
        
    #     cursor = response.get('page', {}).get('nextCursor')
    #     if not cursor:
    #         break
            
    # return all_users

# TEST CODE
def test_code():
    refreshed_token = refresh_token(CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN)
    # refreshed_token = test_access_token

    # test_api_base_uri = get_uris(refreshed_token)
    #print ("test_api_base_uri:", test_api_base_uri)

    # write token to file
    with open (TOKEN_FILENAME, "w", encoding="utf-8") as file:
        file.write(f"{refreshed_token}")

    result = fetch_adobe_users(refreshed_token)
    return result

test_output = test_code()
print (" L - L - L - L")
print ("test_output:\n", test_output)
print ("*THE END*")