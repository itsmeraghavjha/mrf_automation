import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from src.config import CREDENTIALS_FILE, TOKEN_FILE

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

class DriveService:
    def __init__(self):
        self.creds = self._authenticate()
        self.service = build('drive', 'v3', credentials=self.creds)
    
    def _authenticate(self):
        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        return creds

    def _find_folder_id(self, name, parent_id=None):
        query = f"mimeType='application/vnd.google-apps.folder' and name='{name}' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        return files[0]['id'] if files else None

    def _create_folder(self, name, parent_id=None):
        file_metadata = {'name': name, 'mimeType': 'application/vnd.google-apps.folder'}
        if parent_id: file_metadata['parents'] = [parent_id]
        file = self.service.files().create(body=file_metadata, fields='id').execute()
        return file.get('id')

    def get_or_create_path(self, folder_names):
        """Recursively ensures a folder structure exists."""
        current_parent_id = None 
        for folder in folder_names:
            found_id = self._find_folder_id(folder, current_parent_id)
            current_parent_id = found_id if found_id else self._create_folder(folder, current_parent_id)
        return current_parent_id

    def upload_file(self, file_content, file_name, folder_id):
        # Rename if exists to prevent overwrite
        query = f"name = '{file_name}' and '{folder_id}' in parents and trashed=false"
        results = self.service.files().list(q=query).execute()
        if results.get('files', []):
            import time
            name, ext = file_name.rsplit('.', 1)
            file_name = f"{name}_v{int(time.time())}.{ext}"

        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype='application/octet-stream')
        
        file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return file.get('id'), file_name