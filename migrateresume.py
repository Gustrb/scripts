import os
import requests
import time
import json

BASE_URL = "https://api.hipeople.io/api"
RESUME_ENDPOINT_URL = f"{BASE_URL}/resumes"
SESSIONS_ENDPOINT_URL = f"{BASE_URL}/sessions"
CANDIDATE_ENDPOINT_URL = f"{BASE_URL}/candidates"
OPEN_JOB_ROLE_ENDPOINT_URL = f"{BASE_URL}/open_job_roles"
INTEGRATION_ENDPOINT_URL = f"{BASE_URL}/integrations"
S3BUCKET_NAME = "prod-assessments-media-uploads"

EMAIL=os.getenv("EMAIL")
PASS=os.getenv("PASS")

LIMIT = 500

def get_access_token(email, password):
    body = { "email": email, "password": password }
    response = requests.put(SESSIONS_ENDPOINT_URL, json=body)
    response = response.json()

    return response["result"]["fields"]["token"]

def get_resumes(token, current_page):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.get(f"{RESUME_ENDPOINT_URL}?limit={LIMIT}&skip={current_page * LIMIT}", headers=headers)
    response = response.json()

    return (response["result"], response["list"]["has_more"])

def migrate_resume(resume, token, resumes):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.put(f"{RESUME_ENDPOINT_URL}/{resume['id']}/migrate", headers=headers)
    response = response.json()

    if 'errors' in response:
        print(f"Error migrating resume {resume['id']}: {response['errors']}")

        # lets try to update the resume to have a new id
        candidate = get_candidate(resume, token)
        if candidate is None:
            print(f"Candidate not found for resume {resume['id']}")
            return

        integration_id = get_integration_id(resume, token)
        attachment = get_application_attachments(candidate, token, integration_id)
        if attachment is None:
            print(f"Attachment not found for candidate {candidate['id']}")
            return

        body = {
            "updates": {
                "external_link": attachment
            },
            "updated": ["external_link"]
        }
        response = requests.put(f"{RESUME_ENDPOINT_URL}/{resume['id']}", headers=headers, json=body)
        response = response.json()

        if 'errors' in response:
            print(f"Error updating resume {resume['id']}: {response['errors']}")
            return

        response = requests.put(f"{RESUME_ENDPOINT_URL}/{resume['id']}/migrate", headers=headers)
        response = response.json()

    print(response)
    resumes.append({ "id": resume['id'], "response": response })
    return

def get_candidate(resume, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print(f"Getting candidate {resume['fields']['candidate_id']}")

    response = requests.get(f"{CANDIDATE_ENDPOINT_URL}/{resume['fields']['candidate_id']}", headers=headers)
    if response.status_code != 200:
        return None
    response = response.json()
    return response["result"]

def get_integration_id(resume, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = get_candidate(resume, token)
    if response is None:
        return None

    open_job_role_id = response["fields"]["open_job_role_id"]

    response = requests.get(f"{OPEN_JOB_ROLE_ENDPOINT_URL}/{open_job_role_id}", headers=headers)
    response = response.json()

    organization_id = response["result"]["fields"]["organization_id"]

    response = requests.get(f"{INTEGRATION_ENDPOINT_URL}?organization_id[id]={organization_id}", headers=headers)
    response = response.json()

    for integration in response['result']:
        if integration["fields"]["type"] == "ats" and integration["fields"]["organization_id"] == organization_id:
            return integration["id"]

    return None

def get_application_attachments(candidate, token, integration_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    ats_application_id = candidate["fields"]["ats_candidate_id"]
    response = requests.get(f"{INTEGRATION_ENDPOINT_URL}/{integration_id}/ats_applications/{ats_application_id}/attachments", headers=headers)
    response = response.json()

    if 'result' not in response or len(response["result"]["fields"]) == 0:
        print(f"No attachments found for candidate {candidate['id']}")
        return None

    return response["result"]["fields"][0]["url"]

def should_migrate_resume(resume):
    return resume["fields"]["external_link"] != "" and not(S3BUCKET_NAME in resume["fields"]["external_link"])

def main():
    current_page = 0
    total_migrated = 0

    token = get_access_token(EMAIL, PASS)

    has_more = True

    with open("migrated_resumes.json", "w") as f:
        while has_more:
            (resumes, has_more) = get_resumes(token, current_page)

            print(f"Found {len(resumes)} resumes")
            print(f"Has more: {has_more}")
            print(f"Current page: {current_page}")

            migrated_resumes = []

            for resume in resumes:
                if not should_migrate_resume(resume):
                    print(f"Skipping resume {resume['id']}")
                    continue

                print(f"Migrating resume {resume['id']}")
                migrate_resume(resume, token, migrated_resumes)
                print(f"Migrated resume {resume['id']}")
                time.sleep(1)

            json.dump(migrated_resumes, f)

            current_page += 1
            total_migrated += len(resumes)
            print(f"Total migrated: {total_migrated} - {current_page}")

if __name__ == "__main__":
    main()
