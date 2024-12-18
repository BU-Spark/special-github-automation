from googleapiclient.discovery import build
from google.oauth2 import service_account

SERVICE_ACCOUNT_FILE = 'path/to/your-service-account.json'
SCOPES = ['https://www.googleapis.com/auth/drive']
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

class Drive:
    
    def __init__(self):
        self.service = build('drive', 'v3', credentials=credentials)

    def share(self, file_url: str, email: str, role: str = 'writer'):
        try:
            permission = self.service.permissions().create(
                fileId=file_url.split('/')[-2],
                body={
                    'type': 'user',
                    'role': role,
                    'emailAddress': email
                },
                sendNotificationEmail=True,
            ).execute()
            return permission.get('id')
        except Exception as e:
            return str(e)
