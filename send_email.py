from constants import (
    SHAREPOINT_ROOT_FOLDER
)

from azure.identity import DefaultAzureCredential, CertificateCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv
from datetime import datetime
import os
import base64
import requests

load_dotenv()

APP_TENANT_ID = os.getenv("APP_TENANT_ID")
APP_CLIENT_ID = os.getenv("APP_CLIENT_ID")
KEY_VAULT_URL = os.getenv("KEY_VAULT_URL")        

def get_access_token() -> str:
    default_credential = DefaultAzureCredential()
    vault_url = KEY_VAULT_URL
    secret_client = SecretClient(vault_url=vault_url, credential=default_credential)

    secret_name = [secret.name for secret in secret_client.list_properties_of_secrets()][0]
    secret = secret_client.get_secret(secret_name)  

    # The value of the secret is the base64-encoded bytes of the .pfx certificate
    certificate_bytes = base64.b64decode(secret.value)

    tenant_id = APP_TENANT_ID
    client_id = APP_CLIENT_ID

    credential = CertificateCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        certificate_data=certificate_bytes,
    )

    token = credential.get_token("https://graph.microsoft.com/.default")

    return token.token 

def get_sharepoint_headers(access_token: str) -> dict:
    access_token = get_access_token()
    return {"Authorization": f"Bearer {access_token}"}


def get_sharepoint_site_id(graph_api_endpoint: str, access_token: str):
    headers = get_sharepoint_headers(access_token)
    response = requests.get(graph_api_endpoint, headers=headers)
    return response.json().get('id')

def get_sharepoint_drive_id(site_id: str, access_token: str) -> str:
    headers = get_sharepoint_headers(access_token)
    drives_api_endpoint = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives"
    response = requests.get(drives_api_endpoint, headers=headers)
    drives = response.json().get('value')
    for drive in drives:
        if drive.get('name') == "Documents":
            drive_id = drive.get('id')
            return drive_id
    return ""

def upload_document_to_sharepoint(file_content: bytes, file_path: str):
    try:
        access_token = get_access_token()
        headers = get_sharepoint_headers(access_token)
        site_id = get_sharepoint_site_id(os.getenv("GRAPH_API_ENDPOINT"), access_token)
        drive_id = get_sharepoint_drive_id(site_id, access_token)
        if drive_id is None or site_id is None:
            raise Exception("Failed to get SharePoint site or drive ID")
        upload_api_endpoint = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{file_path}:/content"
        response = requests.put(upload_api_endpoint,
                                headers=headers, data=file_content, timeout=60)
    except Exception as e:
        raise e
    return response.status_code in (200, 201)

current_timestamp = datetime.now().strftime("%m-%Y")
cleaned_data_files = os.listdir(os.path.join('data', 'cleaned_data'))

for directory in [
    r'C:\Users\adamc\Downloads\RentalScraper\RentalScraperCode\data\cleaned_data', r'C:\Users\adamc\Downloads\RentalScraper\RentalScraperCode\data\raw_data', r'C:\Users\adamc\Downloads\RentalScraper\RentalScraperCode\logs'
]:
    files = [os.path.join(directory, f) for f in os.listdir(directory)]
    files.sort(key=os.path.getmtime, reverse=True)
    target_files =  [file_path for file_path in files if current_timestamp in file_path]
    target_file = target_files[0] if target_files else None
    with open(target_file, 'rb') as f:
        data = f.read()
    file_date, file_name = target_file.split('\\')[-1].split('_')[0], target_file.split('\\')[-1].replace(current_timestamp, "")[1:]
    upload_document_to_sharepoint(data, f'{SHAREPOINT_ROOT_FOLDER}/{file_date}/{file_name}')