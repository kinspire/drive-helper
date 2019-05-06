import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
]


class DriveHelper:
    def __init__(self):
        self.creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                self.creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.creds = flow.run_local_server()
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(self.creds, token)

    def run(self, modify=False):
        service = build('drive', 'v3', credentials=self.creds)

        # Get the user that needs to be added
        # Figure out which exact folder that needs to be shared
        # Evaluate the path to the Official for this folder
        # Add the user to Kinspire Official, remove from all other folders. Enter the folder,
        #     remove all others. Recurse until we reach the current folder.

        results = service.files().list(q=query, corpora="drive", driveId=ASA_DRIVE_ID,
                                       includeItemsFromAllDrives=True, supportsAllDrives=True,
                                       fields="files(id,name,parents)").execute()
        items = results.get('files', [])

        if not items:
            print('Nothing found.')
        else:
            print('Items:')
            for item in items:
                # item = items[0]
                print(item)
                if modify:
                    body = {
                        "name": item["name"][8:]
                    }
                    updated_file = service.files().update(fileId=item["id"], supportsAllDrives=True,
                                                          body=body).execute()
                    print(f"Updated {updated_file.get('id')} to name {body['name']}")


if __name__ == '__main__':
    h = DriveHelper()
    h.run(modify=True)
