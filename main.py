import functools
import pickle
import os.path
from typing import List, Dict

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
]

FOLDER_MIMETYPE = 'application/vnd.google-apps.folder'

with open('official.txt', 'r') as f:
    KINSPIRE_OFFICIAL = f.readline()

print(KINSPIRE_OFFICIAL)


def str_cmp(a: str, b: str):
    return 1 if a > b else -1 if a < b else 0


def comparator(a, b):
    if a['mimeType'] == FOLDER_MIMETYPE:
        if b['mimeType'] == FOLDER_MIMETYPE:
            return str_cmp(a['name'], b['name'])
        else:
            return -1
    else:
        if b['mimeType'] == FOLDER_MIMETYPE:
            return 1
        else:
            return str_cmp(a['name'], b['name'])
    pass


class DriveHelper:
    def __init__(self):
        credentials = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                credentials = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                credentials = flow.run_local_server()
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(credentials, token)

        self.service = build('drive', 'v3', credentials=credentials)

    def evaluate_path(self):
        curr_folder = KINSPIRE_OFFICIAL
        path = []

        query = f"'{curr_folder}' in parents"

        items: List[Dict] = sorted(self.service.files().list(q=query).execute().get('files', []),
                                   key=functools.cmp_to_key(comparator))
        print("\n".join([f"[{i}] {item['name']}: {item['mimeType']}" for (i, item) in enumerate(items)]))

    def run(self):
        # Get the user that needs to be added
        email = input("Enter user to be added: ")

        # Figure out which exact folder that needs to be shared and evaluate the path to the Official for this folder
        print("Let's figure out which folder we want to share.")
        self.evaluate_path()

        # Add the user to Kinspire Official, remove from all other folders. Enter the folder,
        #     remove all others. Recurse until we reach the current folder.


if __name__ == '__main__':
    h = DriveHelper()
    h.run()
