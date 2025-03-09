import logging
import os
import sys
import tempfile
from datetime import datetime


def setup_logging() -> None:
    """Configure logging to output to both file and console with a unique log file per run."""
    # Create a unique log file name using timestamp and UUID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{timestamp}.log"

    # Use the system temp directory
    log_path = os.path.join(
        tempfile.gettempdir(),
        "doc_compiler",
        log_filename
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Log the location of the log file for reference
    logging.info(f"Log file created at: {log_path}")
