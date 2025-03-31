import re
from pathlib import Path
from typing import List

from loguru import logger
from tqdm import tqdm


class FileAggregator:
    """Aggregates markdown files from a specific directory into a single file."""

    def __init__(self, file_id: str, base_dir: str = "./data"):
        """Initializes the FileAggregator.

        Args:
            file_id (str): The unique identifier for the PDF file (used for directory naming).
            base_dir (str): The base directory where operations will occur. Defaults to current dir.
        """
        self.file_id = file_id
        self.base_path = Path(base_dir)
        self.input_dir = self.base_path / self.file_id / "markdown"
        self.output_file = self.base_path / self.file_id / f"{self.file_id}.md"
        logger.info(f"Aggregator initialized for file_id: {self.file_id}")
        logger.info(f"Input directory set to: {self.input_dir}")
        logger.info(f"Output file set to: {self.output_file}")

    def _get_batch_files(self) -> List[Path]:
        """Finds and returns all .md files in the input directory."""
        if not self.input_dir.is_dir():
            logger.warning(f"Input directory not found: {self.input_dir}")
            return []

        markdown_files = list(self.input_dir.glob("*.md"))
        logger.info(f"Found {len(markdown_files)} markdown files in {self.input_dir}")
        return markdown_files

    def _sort_files(self, files: List[Path]) -> List[Path]:
        """Sorts markdown files based on the starting page number in their filename."""

        def extract_start_page(filename: Path) -> int:
            # Extracts the first number sequence (start page) from the filename
            match = re.search(r"pages_(\d+)-", filename.name)
            if match:
                return int(match.group(1))
            # Fallback if pattern doesn't match - treat as 0 or raise error?
            # Using -1 to ensure these appear first if not matched, or handle appropriately
            logger.warning(
                f"Could not extract start page from {filename.name}. Assigning -1."
            )
            return -1  # Or perhaps raise ValueError("Invalid filename format")

        try:
            # Sort files based on the extracted starting page number
            sorted_files = sorted(files, key=extract_start_page)
            logger.debug(f"Sorted files: {[f.name for f in sorted_files]}")
            return sorted_files
        except Exception as e:
            logger.error(f"Error sorting files: {e}", exc_info=True)
            # Return unsorted list or raise? Returning unsorted for now.
            return files

    def aggregate_markdown_files(self) -> None:
        """Aggregates markdown files into a single output file."""
        batch_files = self._get_batch_files()
        if not batch_files:
            logger.warning("No batch files found to aggregate.")
            return

        sorted_files = self._sort_files(batch_files)

        logger.info(f"Aggregating {len(sorted_files)} files into {self.output_file}")

        try:
            # Ensure the output directory exists (though it's the base path here)
            self.output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.output_file, "w", encoding="utf-8") as outfile:
                for file_path in tqdm(sorted_files, desc="Aggregating Files"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as infile:
                            content = infile.read()
                            outfile.write(content)
                            # Optionally add a separator between files
                            # outfile.write("\\n\\n---\\n\\n")
                        logger.debug(f"Appended content from {file_path.name}")
                    except Exception as e:
                        logger.error(
                            f"Error reading file {file_path}: {e}", exc_info=True
                        )
                        # Decide whether to continue or stop aggregation on error
                        outfile.write(
                            f"\\n\\n[Error reading file: {file_path.name}]\\n\\n"
                        )

            logger.success(f"Successfully aggregated files into {self.output_file}")

        except IOError as e:
            logger.error(
                f"Error writing to output file {self.output_file}: {e}", exc_info=True
            )
            raise  # Re-raise exception after logging
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during aggregation: {e}", exc_info=True
            )
            raise  # Re-raise exception after logging


if __name__ == "__main__":
    aggregator = FileAggregator("downloaded_pdf")
    aggregator.aggregate_markdown_files()
