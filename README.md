# 📄✨ PDFWhisperer: Your PDF Text Extraction Wizard

> Ever wished your PDFs could talk? Now they can! PDFWhisperer uses Google's Gemini AI to transform those stubborn PDF documents into beautiful, structured Markdown text. Smart batching, fault-tolerant processing, and Google Drive integration make handling even the largest documents a breeze. No more copy-paste headaches - just magical text extraction!

Alternatives:
- [marker](https://github.com/VikParuchuri/marker)

# PDF Processing Application 📄➡️📝

This application extracts text from PDF documents using Google's Gemini models via LangChain. It supports processing large PDFs by splitting them into batches, processing them concurrently, and tracking progress to allow for restarts without re-processing completed batches.

## Features ✨

- Extracts text from PDFs sourced from local files or Google Drive.
- Uses LangChain with Google Generative AI (Gemini) for text extraction.
- Splits large PDFs into smaller batches for processing.
- Processes batches concurrently to speed up extraction.
- Tracks processed batches using a JSON file (`data/<file_id>_tracker.json`) to:
    - Prevent duplicate processing and LLM calls if the script is stopped and restarted.
    - Allow resuming processing from the last unprocessed batch.
- Configurable batch size and concurrency level.
- Outputs extracted text to Markdown files, preserving formatting where possible.

## Codebase Structure 🏗️

- **`main.py`**: The main entry point of the application. Handles command-line argument parsing, loading the PDF (either locally or from Google Drive), orchestrating the batch processing using `asyncio`, and calling the generation functions.
- **`process_with_genai.py`**: Contains the core logic for interacting with the LLM.
    - `process_pdf_batch()`: Creates a temporary PDF file containing a specific range of pages (a batch) from the source PDF.
    - `process_batch_with_langchain()`: Takes a batch PDF file, uses `PyPDFLoader` to load it, sends the content along with a system prompt to the specified Gemini model via `ChatGoogleGenerativeAI`, streams the response, and returns the extracted text.
    - `write_to_markdown()`: Writes the extracted text content to a specified Markdown file.
- **`batch_tracker.py`**: Implements the `BatchTracker` class. This class manages the state of batch processing by reading and writing to a JSON tracker file (`data/<file_id>_tracker.json`). It keeps track of which page ranges (batches) have been successfully processed, allowing the application to resume efficiently after interruptions.
- **`google_drive.py`**: Contains functions for interacting with the Google Drive API.
    - `authenticate_google_drive()`: Handles OAuth2 authentication.
    - `download_pdf_from_drive()`: Downloads a PDF file from Google Drive given its file ID.
    - `load_pdf_from_drive()`: Authenticates, downloads the PDF, and returns a `PyPDF2.PdfReader` object and the total page count.
- **`pyproject.toml` & `uv.lock`**: Define project dependencies and lock file for environment management with `uv`.
- **`.env`**: Used to store sensitive information like API keys (should be added to `.gitignore`). Requires `GEMINI_API_KEY` and potentially Google Drive credentials setup.
- **`data/`**: Directory created automatically to store batch tracker JSON files and potentially output Markdown files (depending on how `write_to_markdown` is configured, although currently it writes relative to the script location).

## Environment Setup ⚙️

This project uses `uv` for dependency management.

1.  **Install `uv`**: If you don't have it, follow the official installation instructions: [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv)
2.  **Sync Environment**: Create and sync the virtual environment using the lock file:
    ```bash
    uv sync
    ```
3.  **Activate Environment**:
    ```bash
    source .venv/bin/activate
    # Or on Windows: .venv\Scripts\activate
    ```
4.  **Environment Variables**: Create a `.env` file in the root directory and add your Gemini API key:
    ```
    GEMINI_API_KEY="your_gemini_api_key_here"
    ```
5.  **Google Drive Credentials (if using Drive)**:
    - Follow the steps to enable the Google Drive API and obtain `credentials.json` for OAuth. Place this file in the root directory.
    - The first time you run the script with a `--drive-id`, it will prompt you to go through the OAuth flow in your browser. This will create a `token.json` file storing your access tokens.

## Running the Application 🚀

Execute the main script `main.py` with the required arguments:

```bash
python main.py (--file <local_pdf_path> | --drive-id <google_drive_file_id>) [options]
```

**Required Arguments (choose one):**

-   `--file <local_pdf_path>`: Path to the local PDF file to process.
-   `--drive-id <google_drive_file_id>`: The File ID of the PDF stored in Google Drive.

**Optional Arguments:**

-   `--batch-size <number>`: Number of pages per processing batch (default: 10).
-   `--max-concurrent <number>`: Maximum number of batches to process concurrently (default: 3).
-   `--model <model_name>`: The Gemini model to use (default: `gemini-2.5-pro-exp-03-25`). Other options like `gemini-1.5-flash` might be available.

**Example:**

```bash
# Process a local file
python main.py --file my_document.pdf --batch-size 20 --max-concurrent 5

# Process a Google Drive file
python main.py --drive-id 1aBcDeFgHiJkLmNoPqRsTuVwXyZ --model gemini-1.5-flash
```

## System Prompt for Text Extraction 🧠

The following system prompt is used to instruct the Gemini model on how to extract and format the text from the PDF batches:

```
You will extract text from a PDF document while preserving the original formatting, including paragraphs, bullet points, and other text structures.

Ignore any watermarks with the text "Preview" that spans diagonally across pages.

The extracted text must remain true to the original context, without errors or hallucinations. Accuracy is critical.

For each page, categorize the extracted text using semantic tags:
- Use <main> to enclose the main body text.
- Use <footnotes> to enclose any footnotes.
- Use <notes> to enclose any side notes or marginal notes.
- Use <image> to enclose descriptions of images.

Convert any tables to Markdown table format.

Output the cleaned text in plain text format with proper formatting to distinguish between different elements.
```

## Batch Tracking and Resuming 🔄💾

The `BatchTracker` (`batch_tracker.py`) creates a JSON file named `data/<file_id>_tracker.json`