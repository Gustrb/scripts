import sys
import os
import requests

BASE_URL = "https://api.hipeople.io/api"
SESSIONS_ENDPOINT_URL = f"{BASE_URL}/sessions"
CANDIDATE_ENDPOINT_URL = f"{BASE_URL}/candidates"
CANDIDATE_PROFILE_ENDPOINT_URL = f"{BASE_URL}/candidate_profiles"
EMAIL=os.getenv("EMAIL")
PASS=os.getenv("PASS")

def get_access_token(email, password):
    body = { "email": email, "password": password }
    response = requests.put(SESSIONS_ENDPOINT_URL, json=body)
    response = response.json()

    return response["result"]["fields"]["token"]

def get_candidate_by_id(candidate_id, headers):
    response = requests.get(f"{CANDIDATE_ENDPOINT_URL}/{candidate_id}", headers=headers)
    if response.status_code != 200:
        print(f"Error getting candidate {candidate_id}: {response.text}")
        return None

    return response.json()["result"]

def update_candidate_profile_name(candidate, new_name, headers):
    if candidate['candidate_profile_id'] is None or candidate['candidate_profile_id'] == "":
        print(f"Candidate {candidate['id']} has no candidate profile")
        return None

    response = requests.put(f"{CANDIDATE_PROFILE_ENDPOINT_URL}/{candidate['candidate_profile_id']}", headers=headers, json={
        "updates": { "full_name": new_name },
        "updated": ["full_name"]
    })
    if response.status_code != 200:
        print(f"Error updating candidate profile {candidate['candidate_profile_id']}: {response.text}")
        return None

    return response.json()["result"]

def main():
    token = get_access_token(EMAIL, PASS)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    if len(sys.argv) < 3:
        print("Usage: python updatecandidatename.py <candidate_id> <new_name>")
        return

    candidate_id = sys.argv[1]
    new_name = sys.argv[2]

    if new_name is None:
        print("Usage: python updatecandidatename.py <candidate_id> <new_name>")
        return

    candidate = get_candidate_by_id(candidate_id, headers)
    if candidate is None:
        print(f"Candidate not found {candidate_id}")
        return

    updated_candidate = update_candidate_profile_name(candidate, new_name, headers)
    if updated_candidate is None:
        print(f"Failed to update candidate {candidate_id}")
        return
    
    print(f"Updated candidate {candidate_id} to {new_name}")

if __name__ == "__main__":
    main()
