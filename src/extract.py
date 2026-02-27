import pandas as pd

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from logs.logger import get_logger

logger = get_logger(__name__)


def extract_data(file_path: str) -> pd.DataFrame:
    """
    Extract: Read the raw CSV file into a DataFrame.

    The source file uses semicolons (;) as delimiters, which is non-standard.

    Args:
        file_path: Absolute or relative path to candidates.csv.

    Returns:
        Raw DataFrame with all 50k rows and original column names.

    Raises:
        FileNotFoundError: If the CSV file does not exist at the given path.
        Exception: For any other I/O errors.
    """
    logger.info("Starting data extraction from: %s", file_path)

    if not os.path.exists(file_path):
        logger.error("Source file not found: %s", file_path)
        raise FileNotFoundError(f"Source file not found: {file_path}")

    try:
        df = pd.read_csv(file_path, sep=';')
        logger.info("Extraction complete. Rows loaded: %d | Columns: %d", df.shape[0], df.shape[1])
        return df

    except Exception as exc:
        logger.exception("Failed to read source file: %s", exc)
        raise
