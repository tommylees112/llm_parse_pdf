import io
import os
import tempfile

import PyPDF2
from google import genai
from google.auth.transport.requests import Request
from google.genai import types
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def get_google_drive_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


def download_pdf_from_drive(file_id):
    service = get_google_drive_service()
    request = service.files().get_media(fileId=file_id)
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    file.seek(0)
    return file


def process_pdf_batch(pdf_file, start_page, end_page):
    # Create a temporary file to store the batch
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        # Create a new PDF writer
        writer = PyPDF2.PdfWriter()

        # Add the specified pages to the writer
        for page_num in range(start_page, min(end_page, len(pdf_file.pages))):
            writer.add_page(pdf_file.pages[page_num])

        # Write the batch to the temporary file
        writer.write(temp_file)
        temp_file_path = temp_file.name

    return temp_file_path


def generate(file_id=None, batch_size=10):
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.5-pro-exp-03-25"

    if file_id:
        # Download the PDF from Google Drive
        pdf_file = download_pdf_from_drive(file_id)

        # Open the PDF with PyPDF2
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        total_pages = len(pdf_reader.pages)

        print(f"Total pages in PDF: {total_pages}")

        # Process the PDF in batches
        for start_page in range(0, total_pages, batch_size):
            end_page = min(start_page + batch_size, total_pages)
            print(f"\nProcessing pages {start_page + 1} to {end_page}...")

            # Create a batch of pages
            batch_file_path = process_pdf_batch(pdf_reader, start_page, end_page)

            # Read the batch file
            with open(batch_file_path, "rb") as batch_file:
                pdf_bytes = batch_file.read()

                contents = [
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_data(
                                data=pdf_bytes, mime_type="application/pdf"
                            ),
                        ],
                    ),
                ]

                generate_content_config = types.GenerateContentConfig(
                    response_mime_type="text/plain",
                    system_instruction=[
                        types.Part.from_text(
                            text="""You will extract the text from a PDF document while preserving the original formatting, including paragraphs, bullet points, and other text structures. The PDF contains a consistent watermark with the text \"Preview\" that spans diagonally from the bottom left to the top right across all pages. Exclude this watermark from the extracted text, ensuring that no trace of it remains in the final output. The extracted text must remain true to the original context, without introducing any errors or hallucinations. Accuracy is critical, and the output should be a faithful representation of the source material. While preserving the overall structure, ensure that sentences are kept intact and are not broken across multiple lines, regardless of how line breaks appear in the original PDF.
"""
                        ),
                    ],
                )

                print(f"\nExtracted text from pages {start_page + 1} to {end_page}:")
                print("-" * 80)
                for chunk in client.models.generate_content_stream(
                    model=model,
                    contents=contents,
                    config=generate_content_config,
                ):
                    print(chunk.text, end="")
                print("\n" + "-" * 80)

            # Clean up the temporary file
            os.unlink(batch_file_path)
    else:
        # Fallback to text input if no file_id is provided
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text="""INSERT_INPUT_HERE"""),
                ],
            ),
        ]

        generate_content_config = types.GenerateContentConfig(
            response_mime_type="text/plain",
            system_instruction=[
                types.Part.from_text(
                    text="""You will extract the text from a PDF document while preserving the original formatting, including paragraphs, bullet points, and other text structures. The PDF contains a consistent watermark with the text \"Preview\" that spans diagonally from the bottom left to the top right across all pages. Exclude this watermark from the extracted text, ensuring that no trace of it remains in the final output. The extracted text must remain true to the original context, without introducing any errors or hallucinations. Accuracy is critical, and the output should be a faithful representation of the source material. While preserving the overall structure, ensure that sentences are kept intact and are not broken across multiple lines, regardless of how line breaks appear in the original PDF.
"""
                ),
            ],
        )

        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            print(chunk.text, end="")


if __name__ == "__main__":
    import sys

    file_id = sys.argv[1] if len(sys.argv) > 1 else None
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    generate(file_id, batch_size)
