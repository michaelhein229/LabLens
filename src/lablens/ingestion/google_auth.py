import os.path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.lablens.ingestion.google_drive import list_folder_files


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]


def main():
  """Shows basic usage of the Drive v3 API.
  Prints the names and ids of the first 10 files the user has access to.
  """
  load_dotenv()

  folder_id = os.getenv("LABLENS_DRIVE_FOLDER_ID")

  if not folder_id:
    raise ValueError("LABLENS_DRIVE_FOLDER_ID is not configured")
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("secrets/token.json"):
    creds = Credentials.from_authorized_user_file("secrets/token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "secrets/credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("secrets/token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("drive", "v3", credentials=creds)

    # Call the Drive v3 API
    files = list_folder_files(
        service=service,
        folder_id=folder_id,
    )

    if not files:
      print("No files found.")
      return
    print("Files:")
    for item in files:
      print(f"{item.file_name} ({item.file_id})")
  except HttpError as error:
    # TODO(developer) - Handle errors from drive API.
    print(f"An error occurred: {error}")



if __name__ == "__main__":
  main()