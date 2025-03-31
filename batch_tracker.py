import json
from pathlib import Path
from typing import Dict, List, Set

from loguru import logger


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
