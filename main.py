import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple

import PyPDF2  # Needed for type hint in generate
from loguru import logger

# Import functions from the new modules
from google_drive import load_pdf_from_drive
from process_with_genai import (
    process_batch_with_langchain,
    process_pdf_batch,
    write_to_markdown,
)

# Configure loguru (keep configuration here)
logger.add("app.log", rotation="500 MB", level="INFO")


class BatchTracker:
    """Tracks which batches have been processed for a specific file."""

    def __init__(self, file_id: str):
        self.file_id = file_id
        self.data_dir = Path(f"data/{file_id}")
        self.markdown_dir = self.data_dir / "markdown"
        self.tracker_file = self.data_dir / "processed_batches.json"
        self.processed_batches: Set[str] = set()

        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.markdown_dir.mkdir(parents=True, exist_ok=True)

        # Load previously processed batches if the tracker file exists
        self._load_processed_batches()

    def _load_processed_batches(self) -> None:
        """Load the set of processed batches from the tracker file."""
        if self.tracker_file.exists():
            try:
                with open(self.tracker_file, "r") as f:
                    data = json.load(f)
                    self.processed_batches = set(data.get("processed_batches", []))
                    logger.info(
                        f"Loaded {len(self.processed_batches)} processed batches"
                    )
            except json.JSONDecodeError:
                logger.error(f"Error parsing tracker file: {self.tracker_file}")
                # Initialize with empty set if the file is corrupted
                self.processed_batches = set()

    def save_processed_batches(self) -> None:
        """Save the set of processed batches to the tracker file."""
        try:
            with open(self.tracker_file, "w") as f:
                json.dump({"processed_batches": list(self.processed_batches)}, f)
            logger.info(
                f"Saved {len(self.processed_batches)} processed batches to tracker file"
            )
        except Exception as e:
            logger.error(f"Error saving tracker file: {str(e)}")

    def is_batch_processed(self, start_page: int, end_page: int) -> bool:
        """Check if a specific batch has been processed."""
        batch_id = f"{start_page}-{end_page}"
        return batch_id in self.processed_batches

    def mark_batch_processed(self, start_page: int, end_page: int) -> None:
        """Mark a batch as processed."""
        batch_id = f"{start_page}-{end_page}"
        self.processed_batches.add(batch_id)
        # Save after each successful batch to ensure we don't reprocess
        self.save_processed_batches()

    def get_pending_batches(
        self, total_pages: int, batch_size: int
    ) -> List[Dict[str, int]]:
        """Get a list of batches that have not been processed yet."""
        pending_batches = []
        for start_page in range(0, total_pages, batch_size):
            end_page = min(start_page + batch_size, total_pages)
            if not self.is_batch_processed(start_page, end_page):
                pending_batches.append({"start_page": start_page, "end_page": end_page})
        return pending_batches

    def get_output_path(self, start_page: int, end_page: int) -> Path:
        """Get the output path for a batch's markdown file."""
        return self.markdown_dir / f"pages_{start_page + 1}-{end_page}.md"


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
            process_batch_with_langchain, batch_file_path, model
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
    source: str,
    is_drive_file: bool = True,
    batch_size: int = 10,
    max_concurrent_batches: int = 3,
    model: Literal[
        "gemini-1.5-flash", "gemini-2.5-pro-exp-03-25"
    ] = "gemini-2.5-pro-exp-03-25",
) -> None:
    """Generates text from a PDF with parallel processing.

    Args:
        source: Either a Google Drive file ID or a local file path
        is_drive_file: If True, source is a Google Drive file ID, otherwise it's a local file path
        batch_size: Number of pages to process in each batch
        max_concurrent_batches: Maximum number of batches to process concurrently
        model: Optional model name to use with Langchain
    """
    try:
        # Generate a unique ID for the local file if not a drive file
        file_id = source if is_drive_file else Path(source).stem

        # Initialize batch tracker
        tracker = BatchTracker(file_id)

        pdf_reader: PyPDF2.PdfReader
        total_pages: int

        # Load the PDF from Google Drive or local file
        if is_drive_file:
            logger.info(f"Loading PDF from Google Drive with file_id: {source}")
            _, pdf_reader, total_pages = load_pdf_from_drive(source)
        else:
            logger.info(f"Loading PDF from local file: {source}")
            _, pdf_reader, total_pages = load_local_pdf(source)

        # Get pending batches (not yet processed)
        pending_batches = tracker.get_pending_batches(total_pages, batch_size)
        logger.info(
            f"Found {len(pending_batches)} pending batches out of {(total_pages + batch_size - 1) // batch_size} total"
        )

        # Process batches concurrently with a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent_batches)

        async def process_with_semaphore(batch):
            async with semaphore:
                await process_batch(
                    pdf_reader,
                    batch["start_page"],
                    batch["end_page"],
                    tracker,
                    model,
                )

        # Create tasks for all pending batches
        tasks = [process_with_semaphore(batch) for batch in pending_batches]

        # Execute all tasks and wait for completion
        if tasks:
            logger.info(
                f"Starting {len(tasks)} tasks with max concurrency of {max_concurrent_batches}"
            )
            await asyncio.gather(*tasks)
            logger.info("All batches have been processed")
        else:
            logger.info("No pending batches to process")

    except Exception as e:
        logger.error(
            f"An error occurred in the generate_async function: {str(e)}", exc_info=True
        )
        raise


def generate(
    source: str,
    is_drive_file: bool = True,
    batch_size: int = 10,
    max_concurrent_batches: int = 3,
    model: Literal[
        "gemini-1.5-flash", "gemini-2.5-pro-exp-03-25"
    ] = "gemini-2.5-pro-exp-03-25",
) -> None:
    """Synchronous wrapper for the async generate function."""
    if not source:
        logger.error("No source provided")
        raise ValueError(
            "Source must be provided (either a Google Drive file ID or a local file path)"
        )

    # Run the async function
    asyncio.run(
        generate_async(source, is_drive_file, batch_size, max_concurrent_batches, model)
    )


if __name__ == "__main__":
    # Create the parser
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

    # Determine the source and source type
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

    # Call the main function with parsed arguments
    generate(source, is_drive_file, args.batch_size, args.max_concurrent, args.model)
