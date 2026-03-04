
import os
import datetime
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
BASE_DIR = r"c:\Project\Alex_Diary"
TOKEN_PATH = os.path.join(BASE_DIR, "config", "token.json")

def main():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    service = build('calendar', 'v3', credentials=creds)
    now = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + '+08:00'
    time_max = datetime.datetime.now().replace(hour=23, minute=59, second=59).isoformat() + '+08:00'
    events = service.events().list(calendarId='primary', timeMin=now, timeMax=time_max, singleEvents=True, orderBy='startTime').execute().get('items', [])
    for e in events:
        print(f"Summary: {e.get('summary')}")
        print(f"Location: {e.get('location', 'No Location')}")
        print(f"Start: {e['start'].get('dateTime')}")
        print("-" * 20)

if __name__ == '__main__':
    main()
