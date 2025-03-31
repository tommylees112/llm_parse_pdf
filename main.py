import argparse
import asyncio
import os
from pathlib import Path
from typing import Literal, Tuple

import PyPDF2  # Needed for type hint in generate
from dotenv import load_dotenv
from loguru import logger
from tqdm import tqdm  # Import tqdm for progress bar

from aggregator import FileAggregator  # Import the new aggregator class

# Import functions from the new modules
from batch_tracker import BatchTracker  # Import the moved class
from google_drive import load_pdf_from_drive
from process_with_genai import (
    process_batch_with_langchain,
    process_pdf_batch,
    write_to_markdown,
)

# Configure loguru (keep configuration here)
logger.add("app.log", rotation="500 MB", level="INFO")


def load_local_pdf(file_path: str) -> Tuple[None, PyPDF2.PdfReader, int]:
    """Loads a PDF file from the local filesystem."""
    logger.info(f"Loading local PDF file: {file_path}")
    try:
        pdf_reader = PyPDF2.PdfReader(file_path)
        total_pages = len(pdf_reader.pages)
        logger.info(f"Successfully loaded local PDF with {total_pages} pages")
        return None, pdf_reader, total_pages
    except Exception as e:
        logger.error(f"Error loading local PDF file: {str(e)}", exc_info=True)
        raise


async def process_batch(
    pdf_reader: PyPDF2.PdfReader,
    start_page: int,
    end_page: int,
    tracker: BatchTracker,
    system_prompt: str,
    model: Literal[
        "gemini-1.5-flash", "gemini-2.5-pro-exp-03-25"
    ] = "gemini-2.5-pro-exp-03-25",
) -> None:
    """Process a single batch asynchronously."""
    try:
        logger.info(f"Processing batch: pages {start_page + 1} to {end_page}")

        # Check if this batch has already been processed
        if tracker.is_batch_processed(start_page, end_page):
            logger.info(
                f"Batch {start_page + 1}-{end_page} already processed, skipping"
            )
            return

        # Get the output path for this batch
        output_path = tracker.get_output_path(start_page, end_page)

        # Process the batch
        batch_file_path = process_pdf_batch(pdf_reader, start_page, end_page)

        # This is a CPU-bound task, so run it in a thread pool to avoid blocking the event loop
        extracted_text = await asyncio.to_thread(
            process_batch_with_langchain, batch_file_path, model, system_prompt
        )

        # Write the output to a markdown file
        await asyncio.to_thread(write_to_markdown, extracted_text, str(output_path))

        # Mark the batch as processed
        tracker.mark_batch_processed(start_page, end_page)
        logger.info(
            f"Successfully processed batch: pages {start_page + 1} to {end_page}"
        )

    except Exception as e:
        logger.error(
            f"Error processing batch {start_page + 1}-{end_page}: {str(e)}",
            exc_info=True,
        )


async def generate_async(
    pdf_reader: PyPDF2.PdfReader,
    total_pages: int,
    file_id: str,
    system_prompt: str,
    batch_size: int = 10,
    max_concurrent_batches: int = 3,
    model: Literal[
        "gemini-1.5-flash", "gemini-2.5-pro-exp-03-25"
    ] = "gemini-2.5-pro-exp-03-25",
) -> None:
    """Generates text from a PDF with parallel processing.

    Args:
        pdf_reader: PyPDF2.PdfReader instance with the loaded PDF
        total_pages: Total number of pages in the PDF
        file_id: Unique identifier for the PDF file
        system_prompt: The system prompt to guide the language model
        batch_size: Number of pages to process in each batch
        max_concurrent_batches: Maximum number of batches to process concurrently
        model: Optional model name to use with Langchain
    """
    try:
        # Initialize batch tracker
        tracker = BatchTracker(file_id)

        # Get pending batches (not yet processed)
        pending_batches = tracker.get_pending_batches(total_pages, batch_size)
        logger.info(
            f"Found {len(pending_batches)} pending batches out of {(total_pages + batch_size - 1) // batch_size} total"
        )

        # Process batches concurrently with a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent_batches)

        # Create progress bar
        progress_bar = tqdm(total=len(pending_batches), desc="Processing PDF batches")

        async def process_with_semaphore(batch):
            async with semaphore:
                await process_batch(
                    pdf_reader,
                    batch["start_page"],
                    batch["end_page"],
                    tracker,
                    system_prompt,
                    model,
                )
                # Update progress bar after each batch is processed
                progress_bar.update(1)

        # Create tasks for all pending batches
        tasks = [process_with_semaphore(batch) for batch in pending_batches]

        # Execute all tasks and wait for completion
        if tasks:
            logger.info(
                f"Starting {len(tasks)} tasks with max concurrency of {max_concurrent_batches}"
            )
            await asyncio.gather(*tasks)
            progress_bar.close()
            logger.info("All batches have been processed")
        else:
            logger.info("No pending batches to process")

    except Exception as e:
        logger.error(
            f"An error occurred in the generate_async function: {str(e)}", exc_info=True
        )
        raise


def generate(
    pdf_reader: PyPDF2.PdfReader,
    total_pages: int,
    file_id: str,
    system_prompt: str,
    batch_size: int = 10,
    max_concurrent_batches: int = 3,
    model: Literal[
        "gemini-1.5-flash", "gemini-2.5-pro-exp-03-25"
    ] = "gemini-2.5-pro-exp-03-25",
) -> None:
    """Synchronous wrapper for the async generate function."""
    if not pdf_reader or total_pages <= 0 or not file_id:
        logger.error("Invalid PDF reader, page count, or file ID")
        raise ValueError("Valid PDF reader, page count, and file ID must be provided")
    if not system_prompt:
        logger.error("System prompt must be provided")
        raise ValueError("Valid system prompt must be provided")

    # Run the async function
    asyncio.run(
        generate_async(
            pdf_reader,
            total_pages,
            file_id,
            system_prompt,
            batch_size,
            max_concurrent_batches,
            model,
        )
    )


def parse_args() -> argparse.Namespace:
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Extract text from a PDF using LangChain."
    )

    # Source group - mutually exclusive
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--drive-id",
        type=str,
        help="The Google Drive file ID of the PDF to process",
    )
    source_group.add_argument(
        "--file",
        type=str,
        help="Path to a local PDF file to process",
    )

    # Optional argument for batch_size
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="The number of pages to process in each batch (default: 10).",
    )
    # Optional argument for concurrent batches
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=3,
        help="Maximum number of batches to process concurrently (default: 3).",
    )
    # Optional argument for model selection
    parser.add_argument(
        "--model",
        type=str,
        help="The LangChain model to use (optional).",
        default="gemini-2.5-pro-exp-03-25",
    )

    # Parse the arguments
    args = parser.parse_args()

    # Validate batch size
    if args.batch_size <= 0:
        logger.error(
            f"Batch size must be positive. Received: {args.batch_size}. Using default 10."
        )
        args.batch_size = 10

    # Validate max concurrent
    if args.max_concurrent <= 0:
        logger.error(
            f"Max concurrent must be positive. Received: {args.max_concurrent}. Using default 3."
        )
        args.max_concurrent = 3

    return args


if __name__ == "__main__":
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    # for langchain set the api key
    os.environ["GOOGLE_API_KEY"] = gemini_api_key

    # Parse arguments using the dedicated function
    args = parse_args()

    # Read system prompt from file
    system_prompt_file = "system_prompt.txt"
    system_prompt = ""
    try:
        with open(system_prompt_file, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
        if not system_prompt:
            logger.warning(f"{system_prompt_file} is empty. Using default behavior.")
        else:
            logger.info(f"Loaded system prompt from {system_prompt_file}")
            # Log the system prompt content, truncating if it's too long
            prompt_preview = (
                system_prompt[:200] + "..."
                if len(system_prompt) > 200
                else system_prompt
            )
            logger.info(f"System prompt: {prompt_preview}")
    except FileNotFoundError:
        logger.error(f"System prompt file not found: {system_prompt_file}. Exiting.")
        exit(1)
    except Exception as e:
        logger.error(
            f"Error reading system prompt file {system_prompt_file}: {str(e)}. Exiting."
        )
        exit(1)

    # Determine the source and source type
    source = ""
    is_drive_file = True
    if args.drive_id:
        source = args.drive_id
        is_drive_file = True
    else:
        source = args.file
        is_drive_file = False

        # Validate that the local file exists and is readable
        if not os.path.isfile(source):
            logger.error(f"Local file not found: {source}")
            exit(1)

        if not os.access(source, os.R_OK):
            logger.error(f"Local file is not readable: {source}")
            exit(1)

    # Load the PDF file
    pdf_reader: PyPDF2.PdfReader
    total_pages: int
    file_id: str

    # Load the PDF from Google Drive or local file
    if is_drive_file:
        logger.info(f"Loading PDF from Google Drive with file_id: {source}")
        _, pdf_reader, total_pages = load_pdf_from_drive(source)
        file_id = source
    else:
        logger.info(f"Loading PDF from local file: {source}")
        _, pdf_reader, total_pages = load_local_pdf(source)
        file_id = Path(source).stem

    # Call the main function with loaded PDF and parsed arguments
    generate(
        pdf_reader,
        total_pages,
        file_id,
        system_prompt,
        args.batch_size,
        args.max_concurrent,
        args.model,
    )

    # Aggregate the generated markdown files
    logger.info(f"Starting aggregation for file_id: {file_id}")
    aggregator = FileAggregator(file_id)
    aggregator.aggregate_markdown_files()
    logger.info(f"Aggregation complete. Final file: {aggregator.output_file}")
