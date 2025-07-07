import os
import sys
import requests

BASE_URL = "https://api.hipeople.io/api"
SESSIONS_ENDPOINT_URL = f"{BASE_URL}/sessions"
DECODE_ENDPOINT_URL = f"{BASE_URL}/decode_id"
EMAIL=os.getenv("EMAIL")
PASS=os.getenv("PASS")

def get_access_token(email, password):
    body = { "email": email, "password": password }
    response = requests.put(SESSIONS_ENDPOINT_URL, json=body)
    response = response.json()

    return response["result"]["fields"]["token"]

def decode_id(id, headers):
    response = requests.get(f"{DECODE_ENDPOINT_URL}/{id}", headers=headers)
    if response.status_code != 200:
        print(f"Error decoding id {id}: {response.text}")
        return None
    
    return response.json()["internal_id"]

def main():
    token = get_access_token(EMAIL, PASS)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    if len(sys.argv) < 2:
        print("Usage: decodeid <id>")
        return

    id = sys.argv[1]
    internal_id = decode_id(id, headers)
    if internal_id is None:
        return

    print(f"Internal id: {internal_id}")
    print(f"External id: {id}")

if __name__ == "__main__":
    main()
