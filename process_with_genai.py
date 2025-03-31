import os
import tempfile
from typing import Optional

import PyPDF2
from dotenv import load_dotenv
from langchain.schema import HumanMessage
from langchain_community.document_loaders import PyPDFLoader

# Import LangChain modules instead of direct Google GenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from loguru import logger

SYSTEM_PROMPT_DEFAULT = """
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
"""


def process_pdf_batch(
    pdf_reader: PyPDF2.PdfReader, start_page: int, end_page: int
) -> str:
    """Creates a temporary PDF file containing a batch of pages and returns its path."""
    logger.info(f"Creating PDF batch from page {start_page + 1} to {end_page}")
    temp_file_path: Optional[str] = None
    try:
        # Create a temporary file to store the batch
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file_path = temp_file.name
            # Create a new PDF writer
            writer = PyPDF2.PdfWriter()

            # Add the specified pages to the writer
            num_pages_in_reader = len(pdf_reader.pages)
            for page_num in range(start_page, min(end_page, num_pages_in_reader)):
                if page_num < num_pages_in_reader:
                    writer.add_page(pdf_reader.pages[page_num])
                else:
                    logger.warning(
                        f"Attempted to access page {page_num + 1} which is out of bounds ({num_pages_in_reader} pages total)."
                    )
                # logger.debug(f"Added page {page_num + 1} to batch") # Reduced verbosity

            # Write the batch to the temporary file
            writer.write(temp_file)
            logger.debug(f"Batch written to temporary file: {temp_file_path}")
        # Ensure temp_file_path is not None before returning
        if temp_file_path is None:
            raise IOError("Temporary file path was not created.")
        return temp_file_path
    except Exception as e:
        logger.error(f"Error processing PDF batch: {str(e)}", exc_info=True)
        # Clean up temp file if created before error
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"Cleaned up temporary file {temp_file_path} after error.")
            except OSError as unlink_error:
                logger.error(
                    f"Error removing temporary file {temp_file_path}: {unlink_error}"
                )
        raise


def process_batch_with_langchain(
    batch_file_path: str, model_name: str, system_prompt: str = SYSTEM_PROMPT_DEFAULT
) -> str:
    """Processes a PDF batch file using LangChain with Gemini and returns the extracted text.

    Args:
        batch_file_path: Path to the temporary PDF file containing the batch
        model_name: Name of the Gemini model to use
        system_prompt: The system prompt to guide the language model

    Returns:
        The extracted text content as a string
    """
    logger.info(
        f"Processing batch file {batch_file_path} with LangChain using {model_name}"
    )

    extracted_text = ""  # Initialize empty string to collect text

    try:
        # Use LangChain's PyPDFLoader to load the PDF
        loader = PyPDFLoader(batch_file_path)
        pages = loader.load()

        # Combine the content from all pages
        content = "\n\n".join([page.page_content for page in pages])

        # Initialize the LangChain Gemini chat model
        chat = ChatGoogleGenerativeAI(model=model_name, temperature=0)

        # Define system instruction - cleaner formatting
        system_instruction = system_prompt

        # Create messages for the chat - For Gemini, combine system and user message
        messages = [
            HumanMessage(
                content=f"{system_instruction}\n\nExtract and format the text from this PDF content:\n\n{content}"
            ),
        ]

        # Stream the response
        logger.info("Starting LangChain text extraction for batch file")
        for chunk in chat.stream(messages):
            if chunk.content:
                # Append to our text variable
                extracted_text += chunk.content
            else:
                logger.debug("Received empty chunk")

        logger.info(f"Finished extracting text ({len(extracted_text)} characters)")
        return extracted_text

    except FileNotFoundError:
        logger.error(f"Batch file not found: {batch_file_path}")
        return ""  # Return empty string on error
    except Exception as e:
        logger.error(f"Error processing batch with LangChain: {str(e)}", exc_info=True)
        raise  # Re-raise after logging
    finally:
        # Clean up the temporary file
        if os.path.exists(batch_file_path):
            try:
                os.unlink(batch_file_path)
                logger.debug(f"Cleaned up temporary file: {batch_file_path}")
            except OSError as e:
                logger.error(f"Error deleting temporary file {batch_file_path}: {e}")


def write_to_markdown(content: str, output_file: str) -> None:
    """Writes text content to a markdown file.

    Args:
        content: The text content to write
        output_file: Path to the output markdown file
    """
    if not content:
        logger.warning("No content to write to markdown file")
        return

    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")

        # Write the content to the markdown file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)

        file_size = os.path.getsize(output_file)
        logger.info(
            f"Successfully wrote {len(content)} characters to {output_file} ({file_size} bytes)"
        )

    except Exception as e:
        logger.error(
            f"Error writing to markdown file {output_file}: {str(e)}", exc_info=True
        )
        raise


if __name__ == "__main__":
    load_dotenv()

    # --- Configuration ---
    source_pdf_path = "downloaded_pdf.pdf"  # Assumes this file exists
    gemini_api_key = os.getenv("GEMINI_API_KEY")  # Use from .env file
    model_name = "gemini-2.5-pro-exp-03-25"  # The model to use
    batch_start_page = 9  # First page is 0
    batch_end_page = 18  # Process pages 0, 1, 2, 3, 4

    # Output file path for extracted text (now markdown)
    output_file = "extracted_text.md"

    if not gemini_api_key:
        logger.error("GEMINI_API_KEY environment variable not set.")
        exit(1)  # Or raise an error

    if not os.path.exists(source_pdf_path):
        logger.error(f"Source PDF file not found: {source_pdf_path}")
        logger.error("Please run google_drive.py first to download the PDF.")
        exit(1)

    # --- Setup ---
    # Set API key as environment variable for LangChain
    os.environ["GOOGLE_API_KEY"] = gemini_api_key
    logger.debug(f"Using model: {model_name}")
    logger.debug(
        f"Environment variable set: GOOGLE_API_KEY={os.environ.get('GOOGLE_API_KEY')[:4] if os.environ.get('GOOGLE_API_KEY') else 'None'}"
    )
    pdf_reader: Optional[PyPDF2.PdfReader] = None
    temp_batch_path: Optional[str] = None

    system_prompt_file = "./system_prompt.txt"
    system_prompt = ""
    with open(system_prompt_file, "r", encoding="utf-8") as f:
        system_prompt = f.read().strip()

    try:
        # --- Step 1: Create PdfReader ---
        logger.info(f"Opening source PDF: {source_pdf_path}")
        with open(source_pdf_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            total_pages = len(pdf_reader.pages)
            logger.info(f"Source PDF has {total_pages} pages.")

            # Adjust end_page if it exceeds total pages
            actual_end_page = min(batch_end_page, total_pages)
            if actual_end_page < batch_start_page:
                logger.warning(
                    f"Start page ({batch_start_page + 1}) is beyond the total pages ({total_pages}). Nothing to process."
                )
                exit(0)

            logger.info(f"Processing pages {batch_start_page + 1} to {actual_end_page}")

            # --- Step 2: Create PDF Batch File ---
            temp_batch_path = process_pdf_batch(
                pdf_reader=pdf_reader,
                start_page=batch_start_page,
                end_page=actual_end_page,
            )

            # --- Step 3: Process Batch with LangChain and get the extracted text ---
            extracted_text = process_batch_with_langchain(
                batch_file_path=temp_batch_path,
                model_name=model_name,
                system_prompt=system_prompt,
            )

            # --- Step 4: Write the extracted text to a markdown file ---
            if extracted_text:
                write_to_markdown(extracted_text, output_file)
            else:
                logger.warning("No text was extracted from the PDF batch")

            logger.info("Finished processing batch.")

    except FileNotFoundError:
        logger.error(f"Error: Source PDF not found at {source_pdf_path}")
    except PyPDF2.errors.PdfReadError as pdf_err:
        logger.error(f"Error reading source PDF {source_pdf_path}: {pdf_err}")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred in the main block: {e}", exc_info=True
        )
