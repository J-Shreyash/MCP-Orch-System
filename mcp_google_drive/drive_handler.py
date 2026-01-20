"""
Google Drive Handler - AUTO TOKEN REFRESH FIX
Automatically deletes expired tokens and re-authenticates
Company: Sepia ML | Enhanced Version
"""
import os
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.exceptions import RefreshError
import pickle


class DriveHandler:
    """Handles all Google Drive API operations with auto token refresh"""
    
    # If modifying these scopes, delete the token.pickle file
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    def __init__(self, credentials_file='credentials.json'):
        """
        Initialize Google Drive Handler
        
        Args:
            credentials_file: Path to OAuth credentials JSON file
        """
        self.credentials_file = credentials_file
        self.service = None
        self.token_file = 'token.pickle'
        self.authenticate()
    
    def _delete_token_file(self):
        """Delete the token file if it exists"""
        if os.path.exists(self.token_file):
            try:
                os.remove(self.token_file)
                print(f"🗑️  Deleted expired token file: {self.token_file}")
                return True
            except Exception as e:
                print(f"⚠️  Could not delete token file: {e}")
                return False
        return True
    
    def authenticate(self, retry=True):
        """
        Authenticate with Google Drive API
        AUTO-FIXES: Automatically handles expired/invalid tokens
        """
        print("🔐 Authenticating with Google Drive...")
        
        creds = None
        
        # Check if we have saved credentials
        if os.path.exists(self.token_file):
            print("   Found existing token file")
            try:
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                print(f"   ⚠️  Error loading token: {e}")
                print("   🔄 Will create new token...")
                self._delete_token_file()
                creds = None
        
        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("   Refreshing expired token...")
                try:
                    creds.refresh(Request())
                    print("   ✅ Token refreshed successfully!")
                except RefreshError as e:
                    # AUTO-FIX: Token refresh failed, delete and re-authenticate
                    print(f"   ❌ Token refresh failed: {e}")
                    print("   🔄 AUTO-FIX: Deleting invalid token...")
                    self._delete_token_file()
                    
                    if retry:
                        print("   🔄 Starting fresh authentication...")
                        return self.authenticate(retry=False)  # Try once more
                    else:
                        print("   ❌ Authentication failed after retry")
                        return
                except Exception as e:
                    print(f"   ❌ Unexpected error during refresh: {e}")
                    self._delete_token_file()
                    if retry:
                        return self.authenticate(retry=False)
                    return
            else:
                print("   Starting OAuth flow...")
                print("   ⚠️  Your browser will open for authentication")
                if not os.path.exists(self.credentials_file):
                    print(f"   ❌ ERROR: {self.credentials_file} not found!")
                    print("   Please download OAuth credentials from Google Cloud Console")
                    return
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"   ❌ OAuth flow failed: {e}")
                    return
            
            # Save credentials for next time
            if creds:
                try:
                    print("   Saving credentials...")
                    with open(self.token_file, 'wb') as token:
                        pickle.dump(creds, token)
                except Exception as e:
                    print(f"   ⚠️  Could not save token: {e}")
        
        # Build the Drive service
        try:
            self.service = build('drive', 'v3', credentials=creds)
            print("✅ Google Drive authentication successful!\n")
        except Exception as e:
            print(f"❌ Failed to build Drive service: {e}")
            self.service = None
    
    def _ensure_authenticated(self):
        """Ensure we're authenticated, re-authenticate if needed"""
        if not self.service:
            print("⚠️  Not authenticated, attempting to authenticate...")
            self.authenticate()
        return self.service is not None
    
    def upload_file(self, file_path: str, folder_id: str = None) -> dict:
        """
        Upload a file to Google Drive
        AUTO-RETRY: Automatically re-authenticates on auth errors
        """
        if not self._ensure_authenticated():
            return None
        
        print(f"\n{'='*60}")
        print(f"📤 Uploading file to Google Drive")
        print(f"   File: {file_path}")
        print(f"{'='*60}\n")
        
        try:
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                return None
            
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            # File metadata
            file_metadata = {'name': file_name}
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Determine MIME type
            mime_type = self._get_mime_type(file_path)
            
            print(f"   Name: {file_name}")
            print(f"   Size: {file_size} bytes")
            print(f"   Type: {mime_type}")
            
            # Upload the file
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, size, mimeType, webViewLink'
            ).execute()
            
            print(f"\n✅ File uploaded successfully!")
            print(f"   File ID: {file.get('id')}")
            print(f"   View: {file.get('webViewLink')}\n")
            
            return file
        
        except RefreshError as e:
            # AUTO-FIX: Auth error, delete token and retry
            print(f"❌ Auth error: {e}")
            print("🔄 AUTO-FIX: Re-authenticating...")
            self._delete_token_file()
            self.authenticate()
            # Could retry the upload here if needed
            return None
        
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def list_files(self, max_results: int = 10) -> list:
        """
        List files in Google Drive
        AUTO-RETRY: Automatically re-authenticates on auth errors
        """
        if not self._ensure_authenticated():
            return []
        
        print(f"\n{'='*60}")
        print(f"📋 Listing files from Google Drive")
        print(f"   Max results: {max_results}")
        print(f"{'='*60}\n")
        
        try:
            # Query for files
            results = self.service.files().list(
                pageSize=max_results,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)",
                orderBy="modifiedTime desc"
            ).execute()
            
            files = results.get('files', [])
            
            if not files:
                print("   No files found")
                return []
            
            print(f"✅ Found {len(files)} files:\n")
            for i, file in enumerate(files, 1):
                size = int(file.get('size', 0)) if file.get('size') else 0
                print(f"   {i}. {file.get('name')}")
                print(f"      ID: {file.get('id')}")
                print(f"      Size: {size} bytes")
                print(f"      Type: {file.get('mimeType')}")
                print()
            
            return files
        
        except RefreshError as e:
            # AUTO-FIX: Auth error, delete token and retry
            print(f"❌ Auth error: {e}")
            print("🔄 AUTO-FIX: Re-authenticating...")
            self._delete_token_file()
            self.authenticate()
            return []
        
        except Exception as e:
            print(f"❌ List failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def download_file(self, file_id: str, output_path: str = None) -> str:
        """
        Download a file from Google Drive
        AUTO-RETRY: Automatically re-authenticates on auth errors
        """
        if not self._ensure_authenticated():
            return None
        
        print(f"\n{'='*60}")
        print(f"📥 Downloading file from Google Drive")
        print(f"   File ID: {file_id}")
        print(f"{'='*60}\n")
        
        try:
            # Get file metadata
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields='name, mimeType, size'
            ).execute()
            
            file_name = file_metadata.get('name')
            
            if not output_path:
                output_path = file_name
            
            print(f"   Downloading: {file_name}")
            print(f"   Saving to: {output_path}")
            
            # Download the file
            request = self.service.files().get_media(fileId=file_id)
            fh = io.FileIO(output_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"   Progress: {int(status.progress() * 100)}%")
            
            print(f"\n✅ Download complete!")
            print(f"   Saved to: {output_path}\n")
            
            return output_path
        
        except RefreshError as e:
            # AUTO-FIX: Auth error, delete token and retry
            print(f"❌ Auth error: {e}")
            print("🔄 AUTO-FIX: Re-authenticating...")
            self._delete_token_file()
            self.authenticate()
            return None
        
        except Exception as e:
            print(f"❌ Download failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from Google Drive
        AUTO-RETRY: Automatically re-authenticates on auth errors
        """
        if not self._ensure_authenticated():
            return False
        
        print(f"\n{'='*60}")
        print(f"🗑️  Deleting file from Google Drive")
        print(f"   File ID: {file_id}")
        print(f"{'='*60}\n")
        
        try:
            # Get file name first
            file_metadata = self.service.files().get(
                fileId=file_id,
                fields='name'
            ).execute()
            
            file_name = file_metadata.get('name')
            print(f"   File: {file_name}")
            
            # Delete the file
            self.service.files().delete(fileId=file_id).execute()
            
            print(f"\n✅ File deleted successfully!\n")
            return True
        
        except RefreshError as e:
            # AUTO-FIX: Auth error, delete token and retry
            print(f"❌ Auth error: {e}")
            print("🔄 AUTO-FIX: Re-authenticating...")
            self._delete_token_file()
            self.authenticate()
            return False
        
        except Exception as e:
            print(f"❌ Delete failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_file_info(self, file_id: str) -> dict:
        """
        Get detailed information about a file
        AUTO-RETRY: Automatically re-authenticates on auth errors
        """
        if not self._ensure_authenticated():
            return None
        
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, createdTime, modifiedTime, webViewLink'
            ).execute()
            return file
        except RefreshError as e:
            print(f"❌ Auth error: {e}")
            print("🔄 AUTO-FIX: Re-authenticating...")
            self._delete_token_file()
            self.authenticate()
            return None
        except Exception as e:
            print(f"❌ Failed to get file info: {e}")
            return None
    
    def _get_mime_type(self, file_path: str) -> str:
        """Determine MIME type from file extension"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'
    
    def is_connected(self) -> bool:
        """Check if connected to Google Drive"""
        return self.service is not None