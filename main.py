import functools
import os.path
import pickle
import sys
from typing import List, Dict

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
]

FOLDER_MIMETYPE = 'application/vnd.google-apps.folder'

with open('official.txt', 'r') as f:
    KINSPIRE_OFFICIAL = {
        'id': f.readline(),
        'name': 'Kinspire Official',
        'mimeType': FOLDER_MIMETYPE
    }


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


def output_format(i, item):
    return f"[{i}] {item['name']}: {item['mimeType']} - [{item['id']}]"


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

    def query_files(self, query: str, fields: str = None) -> List[Dict]:
        return self.service.files().list(q=query, fields=fields).execute().get('files', [])

    def get_path(self):
        """
        Through console interaction, get the full path from the root to the folder/file that we want to share.
        :return: an array that represents the path to the selected folder
        """
        print("Let's figure out which folder we want to share.")

        path = []

        def recursive_fn(curr_folder):
            print()

            query = f"'{curr_folder['id']}' in parents and trashed = false"

            items = sorted(self.query_files(query), key=functools.cmp_to_key(comparator))
            print(output_format("x", curr_folder))
            print(*[output_format(i, item) for (i, item) in enumerate(items)], sep="\n")

            print()
            n = input("Choose a folder: ")
            if n != "x":
                idx = int(n)
                item = items[idx]
                path.append(item)
                if item['mimeType'] == FOLDER_MIMETYPE:
                    recursive_fn(item)

        recursive_fn(KINSPIRE_OFFICIAL)

        print(*[f"-> {path_piece['name']}" for path_piece in path], sep="\n")

        return path

    def get_files_to_unshare(self, path: List[Dict], user: str) -> List[Dict]:
        """
        Get files that need to be unshared after sharing the parent folder, along the given path.
        :param path:
        :param user:
        :return:
        """
        curr_folder: Dict[str, str] = KINSPIRE_OFFICIAL
        to_unshare: List[Dict] = []

        def callback(request_id, response, exception):
            if exception:
                print(exception, file=sys.stderr)
            else:
                files = filter(lambda file: file['id'] != request_id, response.get('files', []))

                # Add to our collection of files we want to eventually unshare
                to_unshare.extend(files)

        batch = self.service.new_batch_http_request(callback=callback)

        for item in path:
            # Get all files under the current folder that are NOT currently shared with user
            query: str = f"'{curr_folder['id']}' in parents and trashed = false and not ('{user}' in readers)"

            # Filter out the soon-to-be-shared subfolder. Pass the current item's id as the request ID, to ensure
            # uniqueness, and be able to access it in the callback
            batch.add(self.service.files().list(q=query), request_id=item['id'])

            curr_folder = item

        batch.execute()

        return to_unshare

    def share_path(self, path, user: str, to_unshare):
        # Share Kinspire Official if not already shared.
        print("Sharing Kinspire Official...", end="")
        self.service.permissions().create(fileId=KINSPIRE_OFFICIAL['id'],
                                          body={'role': 'writer', 'type': 'user', 'emailAddress': user}).execute()
        print("done.")

        # Unshare everything in to_unshare
        permissions_batch = []

        def callback(request_id, response, exception):
            # request_id: file requested
            if exception:
                print(exception, file=sys.stderr)
            else:
                # Find the permission we care about
                perms = response['permissions']
                perm_id = [perm['id'] for perm in perms if ('emailAddress' in perm and perm['emailAddress'] == user)]
                if len(perm_id) > 0:
                    print("Found!")
                # permissions_batch.append({'id': request_id, 'permissionId': perm_id})

        batch = self.service.new_batch_http_request(callback=callback)

        # Get permission ID's for all items in to_unshare
        for item in to_unshare:
            batch.add(self.service.files().get(fileId=item['id'], fields="permissions"), request_id=item['id'])
            break

        batch.execute()

    def run(self):
        # Figure out which exact folder that needs to be shared and evaluate the path to the Official for this folder
        path = self.get_path()

        # Get the user that needs to be added
        user = input("Enter user to be added: ")

        to_unshare = self.get_files_to_unshare(path, user)

        # Add the user to Kinspire Official, remove from all other folders. Enter the folder,
        #     remove all others. Recurse until we reach the current folder.
        self.share_path(path, user, to_unshare)


if __name__ == '__main__':
    h = DriveHelper()
    h.run()
