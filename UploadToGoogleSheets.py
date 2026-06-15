import csv
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def get_sheets_service():
    """Handles the OAuth2 User Authentication flow and caches tokens locally."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Expects 'credentials.json' to be in the root directory (Downloaded from Google Cloud Console)
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError(
                    "[Error] Missing 'credentials.json' file. Please place your Google Cloud "
                    "OAuth2 Desktop client configuration file in this folder."
                )
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('sheets', 'v4', credentials=creds)


def upload_csv_to_google_sheet(csv_filename: str, spreadsheet_title: str):
    """Creates a fresh Google Sheet and pushes local CSV rows into the remote grid workspace."""
    csv_path = os.path.join(os.getcwd(), csv_filename)
    if not os.path.exists(csv_path):
        print(f"[Error] The targeted source file does not exist: {csv_path}")
        return

    # 1. Parse rows out of your local CSV file artifact
    print(f"[Sheets Engine] Reading rows from local database: {csv_filename}...")
    rows_to_upload = []
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            rows_to_upload.append(row)

    try:
        service = get_sheets_service()

        # 2. Spawn a new spreadsheet instance on your Google Drive workspace
        print(f"[Sheets Engine] Instantiating new remote document titled: '{spreadsheet_title}'...")
        spreadsheet_metadata = {
            'properties': {'title': spreadsheet_title}
        }
        spreadsheet = service.spreadsheets().create(
            body=spreadsheet_metadata,
            fields='spreadsheetId,spreadsheetUrl'
        ).execute()

        spreadsheet_id = spreadsheet.get('spreadsheetId')
        spreadsheet_url = spreadsheet.get('spreadsheetUrl')
        print(f"[Sheets Engine] Document deployed. Remote ID: {spreadsheet_id}")

        # 3. Stream data grid updates sequentially into Sheet1 (Range A1)
        body = {
            'values': rows_to_upload
        }
        print("[Sheets Engine] Pushing array payloads over secure websocket connection...")
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="Sheet1!A1",
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()

        print(f"\n================ GOOGLE SHEETS EXPORT SUCCESS ================")
        print(f"[Success] Updated cells quantity: {result.get('updatedCells')}")
        print(f"https://www.ibm.com/docs/ssw_ibm_i_74/rzasc/accesspath.htm: {spreadsheet_url}")
        print("==============================================================")
        return spreadsheet_url

    except HttpError as api_err:
        print(f"[Google API Error] Server rejected the workspace modification request: {api_err}")
    except Exception as general_err:
        print(f"[System Error] Pipeline unexpected failure: {general_err}")


if __name__ == "__main__":
    # Test execution parameters targeting your generated Zillow csv
    upload_csv_to_google_sheet(
        csv_filename="pasadena_listings.csv",
        spreadsheet_title="Pasadena MD Single-Family Homes Under 500k"
    )