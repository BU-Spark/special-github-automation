from googleapiclient.discovery import build
from google.oauth2 import service_account

SERVICE_ACCOUNT_FILE = 'path/to/your-service-account.json'
SCOPES = ['https://www.googleapis.com/auth/drive']
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

class GoogleDrive:
    
    def __init__(self):
        self.service = build('drive', 'v3', credentials=credentials)

    def share(self, file_id: str, email: str, role: str = 'writer'):
        new_permission = {
            'type': 'user',
            'role': role,
            'emailAddress': email
        }

        try:
            permission = self.service.permissions().create(
                fileId=file_id,
                body=new_permission,
                sendNotificationEmail=True,
                emailMessage='I have shared a file with you!'
            ).execute()
            return permission.get('id')
        except Exception as e:
            return str(e)
