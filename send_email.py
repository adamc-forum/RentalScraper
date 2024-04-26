import os
import certifi
import ssl
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from azure.identity import DefaultAzureCredential, CertificateCredential
from azure.keyvault.secrets import SecretClient
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

def send_email():
    # Configure SSL context to use certifi
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    # Set the environment variable for SSL_CERT_FILE
    os.environ['SSL_CERT_FILE'] = certifi.where()

    # Your SendGrid API Key
    sendgrid_api_key = f'{os.getenv('EMAIL_API')}'  # Ensure you have set this environment variable

    # Initialize SendGrid client with the SSL context (not directly applicable, just demonstrates setup)
    sg = SendGridAPIClient(sendgrid_api_key)

    # Email details
    message = Mail(
        from_email='shivamj@forumam.com',
        to_emails='sjindal1729@gmail.com',
        subject='Email Via Sendgrid',
        html_content='<p>Here are the listings for the month of april!</p> <br>'
    )
    
    file_path = r'C:\Users\adamc\Downloads\RentalScraper\RentalScraperCode\data\cleaned_data\07-04-2024_cleaned_listings.xlsx'
    with open(file_path, 'rb') as f:
        data = f.read()
        f.close()
    encoded_file = base64.b64encode(data).decode()
    
    attachment = Attachment()
    attachment.file_content = FileContent(encoded_file)
    attachment.file_type = FileType('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')  # MIME type for .xlsx
    attachment.file_name = FileName('07-04-2024_cleaned_listings.xlsx')
    attachment.disposition = Disposition('attachment')
    message.attachment = attachment

    # Send the email
    try:
        response = sg.send(message)
        print(f"Email sent! Status code: {response.status_code}")
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(f"An error occurred: {e}")

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

def upload_document_to_sharepoint(file_content: bytes):
    try:
        access_token = get_access_token()
        headers = get_sharepoint_headers(access_token)
        site_id = get_sharepoint_site_id(os.getenv("GRAPH_API_ENDPOINT"), access_token)
        drive_id = get_sharepoint_drive_id(site_id, access_token)
        if drive_id is None or site_id is None:
            raise Exception("Failed to get SharePoint site or drive ID")
        file_path = f"General/Rental_Listings.xlsx"
        upload_api_endpoint = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{file_path}:/content"
        response = requests.put(upload_api_endpoint,
                                headers=headers, data=file_content, timeout=60)
    except Exception as e:
        raise e
    return response.status_code in (200, 201)

file_path = r'C:\Users\adamc\Downloads\RentalScraper\RentalScraperCode\data\cleaned_data\07-04-2024_cleaned_listings.xlsx'
with open(file_path, 'rb') as f:
    data = f.read()

upload_document_to_sharepoint(data)

# send_email()
