import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def get_sheets_service():
    """Handles the OAuth2 User Authentication flow and caches tokens locally."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError(
                    "[Error] Missing 'credentials.json' file. Please place your Google Cloud "
                    "OAuth2 Desktop client configuration file in this project root folder."
                )
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('sheets', 'v4', credentials=creds)


def upload_to_google_sheet_pipeline(listings_data, spreadsheet_title):
    """Creates a new remote Google Sheet spreadsheet and streams data rows to it."""
    if not listings_data:
        print("[Sheets Engine] Skipped upload phase: No property listings available.")
        return

    # Transform structured data dictionaries into raw rectangular grid arrays
    headers = ["address", "price", "beds", "baths", "sqft", "url"]
    rows_to_upload = [headers]
    for item in listings_data:
        rows_to_upload.append([item.get(k, "") for k in headers])

    try:
        service = get_sheets_service()

        print(f"\n[Sheets Engine] Deploying fresh spreadsheet instance: '{spreadsheet_title}'...")
        spreadsheet_metadata = {'properties': {'title': spreadsheet_title}}
        spreadsheet = service.spreadsheets().create(
            body=spreadsheet_metadata,
            fields='spreadsheetId,spreadsheetUrl'
        ).execute()

        spreadsheet_id = spreadsheet.get('spreadsheetId')
        spreadsheet_url = spreadsheet.get('spreadsheetUrl')
        print(f"[Sheets Engine] Remote workspace online. ID: {spreadsheet_id}")

        body = {'values': rows_to_upload}
        print("[Sheets Engine] Streaming row cells over secure socket connection...")
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="Sheet1!A1",
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()

        print(f"\n================ GOOGLE SHEETS EXPORT SUCCESS ================")
        print(f"[Success] Securely structured and updated {result.get('updatedCells')} grid cells.")
        print(f"https://www.ibm.com/docs/ssw_ibm_i_74/rzasc/accesspath.htm: {spreadsheet_url}")
        print("==============================================================")
        return spreadsheet_url

    except HttpError as api_err:
        print(f"[Google API Error] Remote transaction rejected by server: {api_err}")
    except Exception as general_err:
        print(f"[System Error] Unexpected sheet upload breakdown: {general_err}")