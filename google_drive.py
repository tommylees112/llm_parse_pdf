import io
import os
from pathlib import Path
from typing import Optional, Tuple

import PyPDF2  # Needed for type hinting in load_pdf_from_drive
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build
from googleapiclient.http import MediaIoBaseDownload
from loguru import logger

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def get_google_drive_service() -> Resource:
    """Authenticates and returns a Google Drive API service client."""
    creds: Optional[Credentials] = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if Path("token.json").exists():
        logger.debug("Token file found")
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    else:
        logger.debug("Token file not found")

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                # Consider deleting the token file or asking the user
                # For now, forcing re-authentication
                if Path("token.json").exists():
                    try:
                        os.remove("token.json")
                        logger.info("Removed expired token file.")
                    except OSError as rm_err:
                        logger.error(f"Error removing token file: {rm_err}")
                creds = None  # Force re-authentication
        if not creds:  # Either refresh failed or no creds initially
            # Ensure credentials.json exists
            if not Path("credentials.json").exists():
                logger.error(
                    "credentials.json not found. Please download it from Google Cloud Console and place it in the root directory."
                )
                raise FileNotFoundError("credentials.json not found.")
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            except Exception as e:
                logger.error(f"Failed to run OAuth flow: {e}", exc_info=True)
                raise
        # Save the credentials for the next run
        try:
            with open("token.json", "w") as token:
                token.write(creds.to_json())
            logger.info("Saved new credentials to token.json")
        except IOError as e:
            logger.error(f"Failed to save token.json: {e}")
            # Decide if we should proceed without saving or raise an error

    try:
        service = build("drive", "v3", credentials=creds)
        logger.info("Google Drive service built successfully.")
        return service
    except Exception as e:
        logger.error(f"Failed to build Google Drive service: {e}", exc_info=True)
        raise


def download_pdf_from_drive(file_id: str) -> io.BytesIO:
    """Downloads a native PDF file from Google Drive given its file ID.
    Raises ValueError if the file is not a native PDF.
    """
    logger.info(f"Attempting to download native PDF for file_id: {file_id}")
    try:
        service: Resource = get_google_drive_service()

        # 1. Get file metadata to check MIME type
        file_metadata = service.files().get(fileId=file_id, fields="mimeType").execute()
        mime_type = file_metadata.get("mimeType")
        logger.info(f"Detected MIME type: {mime_type}")

        # 2. Check if it's a native PDF
        if mime_type == "application/pdf":
            logger.info("File is native PDF. Proceeding with download using get_media.")
            request = service.files().get_media(fileId=file_id)
        else:
            # Raise error if not a native PDF
            error_msg = f"File is not a native PDF (mimeType: {mime_type}). Only native PDFs are supported."
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 3. Download the file content
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            if status:
                logger.debug(f"Download progress: {int(status.progress() * 100)}%")
        file.seek(0)
        logger.info("PDF download completed successfully")
        return file
    except Exception as e:
        # Use a safer logging format to avoid KeyError with HttpError messages
        logger.error("Error downloading PDF from Drive: {}", e, exc_info=True)
        raise


def load_pdf_from_drive(file_id: str) -> Tuple[io.BytesIO, PyPDF2.PdfReader, int]:
    """Downloads a PDF from Google Drive and returns the stream, a PdfReader object, and total pages."""
    logger.info(f"Loading PDF from Google Drive with file_id: {file_id}")
    try:
        pdf_file_stream: io.BytesIO = download_pdf_from_drive(file_id)
        # Reset stream position in case download_pdf_from_drive moved it (it does)
        pdf_file_stream.seek(0)
        pdf_reader = PyPDF2.PdfReader(pdf_file_stream)
        total_pages: int = len(pdf_reader.pages)
        logger.info(f"Successfully loaded PDF with {total_pages} pages")

        # Return all three needed values
        return pdf_file_stream, pdf_reader, total_pages
    except Exception as e:
        # Use a safer logging format here as well
        logger.error(f"Error loading PDF from Drive: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    file_id = "1rmqc9ZMWB696oUS8N2tMqzRvRbPEavDR"
    output_filename = "downloaded_pdf.pdf"

    logger.info(f"Attempting to load and save file ID: {file_id} to {output_filename}")
    pdf_file_stream, pdf_reader, total_pages = load_pdf_from_drive(file_id)

    # Save the downloaded PDF stream to a local file
    with open(output_filename, "wb") as f:
        f.write(pdf_file_stream.getbuffer())  # Efficiently write the whole buffer
    logger.info(f"Successfully saved PDF to {output_filename}")

    # Log other details
    # logger.info(f"PDF reader object: {pdf_reader}") # Avoid logging large objects
    logger.info(f"Total pages detected: {total_pages}")
