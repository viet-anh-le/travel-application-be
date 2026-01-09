import os
from pathlib import Path
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

scopes = ["https://www.googleapis.com/auth/calendar"]

env_path = Path(__file__).resolve().parent.parent / '.env'

load_dotenv(dotenv_path=env_path)

client_config = {
    "web": {
        "client_id": os.getenv('CALENDAR_CLIENT_ID'),         
        "client_secret": os.getenv('CALENDAR_CLIENT_SECRET'),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [os.getenv('CALENDAR_REDIRECT_URI')],
    }
}

oauth2_client = Flow.from_client_config(
    client_config=client_config,
    scopes=scopes
)
oauth2_client.redirect_uri = os.environ['CALENDAR_REDIRECT_URI']

def get_oauth_client_from_user(user):
    """
    Hàm này nhận vào object User (từ DB), lấy access/refresh token
    và trả về đối tượng Credentials để gọi Google API.
    """
    
    info = user.google_calendar 
    
    creds = Credentials(
        token=info.access_token,          
        refresh_token=info.refresh_token, 
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ['CALENDAR_CLIENT_ID'],
        client_secret=os.environ['CALENDAR_CLIENT_SECRET'],
        scopes=scopes
    )
    
    return creds

def get_calendar_service(user):
    """
    Hàm này trả về object 'service' để bạn gọi .events().insert(...)
    """
    creds = get_oauth_client_from_user(user)
    service = build('calendar', 'v3', credentials=creds)
    return service

__all__ = ['oauth2_client', 'scopes', 'get_oauth_client_from_user', 'get_calendar_service']