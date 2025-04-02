from fastapi import FastAPI, File, UploadFile, Form
import os
import psycopg2
from datetime import datetime
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from dotenv import load_dotenv
import json
from urllib.parse import urlparse
# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Database Connection using environment variables
# def get_db_connection():
#     return psycopg2.connect(
#         database=os.getenv("DB_NAME"),
#         user=os.getenv("DB_USER"),
#         password=os.getenv("DB_PASSWORD"),
#         host=os.getenv("DB_HOST"),
#         port=os.getenv("DB_PORT")
#     )
def get_db_connection():
    # Parse DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL is not set in environment variables")

    result = urlparse(db_url)
    
    return psycopg2.connect(
        dbname=result.path[1:],  # Remove leading '/'
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port,
        cursor_factory=RealDictCursor  # Returns results as dictionaries
    )

# Google Drive API Setup using environment variables
service_account_info = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=SCOPES)

drive_service = build("drive", "v3", credentials=creds)

# Root Google Drive Folder ID (Where all month folders will be created)
ROOT_DRIVE_FOLDER_ID = os.getenv("ROOT_DRIVE_FOLDER_ID")

# Function to create folder in Google Drive
def create_drive_folder(folder_name, parent_folder_id):
    """Creates a folder in Google Drive under the specified parent folder."""
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and '{parent_folder_id}' in parents and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id)").execute()
    
    folder_list = results.get("files", [])
    
    if folder_list:
        return folder_list[0]["id"]  # Return existing folder ID

    folder_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_folder_id]
    }
    folder = drive_service.files().create(body=folder_metadata, fields="id").execute()
    
    return folder.get("id")  # Return new folder ID

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), custom_name: str = Form(...)):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_month = datetime.now().strftime("%Y-%m")
    
    # Calculate the first day of the current year
    start_of_year = datetime(datetime.now().year, 1, 1)
    
    # Get the current date and calculate the week number
    delta = datetime.now() - start_of_year
    current_week = f"week_{(delta.days // 7) + 1}"

    # 🛠️ Step 1: Create month folder in Google Drive if it doesn't exist
    drive_month_folder_id = create_drive_folder(current_month, ROOT_DRIVE_FOLDER_ID)

    # 🛠️ Step 2: Create week folder in Google Drive under the month folder
    drive_week_folder_id = create_drive_folder(current_week, drive_month_folder_id)

    # Set custom filename (keep original extension)
    file_extension = os.path.splitext(file.filename)[1]
    custom_filename = f"{custom_name}{file_extension}"

    # 🛠️ Step 3: Upload file directly to Google Drive
    file_metadata = {"name": custom_filename, "parents": [drive_week_folder_id]}
    file_content = BytesIO(await file.read())  # Read file content into memory
    media = MediaIoBaseUpload(file_content, mimetype=file.content_type, resumable=True)
    
    drive_response = drive_service.files().create(body=file_metadata, media_body=media, fields="id, webViewLink").execute()
    drive_file_url = drive_response.get("webViewLink")

    # 🛠️ Step 4: Save metadata in PostgreSQL
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO uploads (filename, timestamp, month, week, drive_url) VALUES (%s, %s, %s, %s, %s)", 
                (custom_filename, timestamp, current_month, current_week, drive_file_url))
    conn.commit()
    cur.close()
    conn.close()

    return {"message": "File uploaded successfully!", "drive_url": drive_file_url}
