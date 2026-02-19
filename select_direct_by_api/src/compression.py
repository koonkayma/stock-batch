"""
compression.py — GZIP compression utilities.

Compresses raw SEC payloads into .gz files using chunked binary streaming
to prevent RAM exhaustion during massive batch operations.
"""

import gzip
import logging
import os
import shutil

logger = logging.getLogger(__name__)


def compress_sec_payload(original_path: str, compressed_path: str) -> bool:
    """
    Compress *original_path* into *compressed_path* (.gz) using chunked
    binary streaming via ``shutil.copyfileobj``.

    The raw file is **deleted** immediately after successful compression.

    Returns:
        True on success, False on failure.
    """
    try:
        with open(original_path, "rb") as f_in:
            with gzip.open(compressed_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        # Remove the uncompressed artifact
        os.remove(original_path)
        logger.info("Compressed %s → %s", original_path, compressed_path)
        return True
    except Exception:
        logger.exception("Compression failed for %s", original_path)
        return False


def decompress_payload(compressed_path: str, output_path: str) -> bool:
    """Decompress a .gz file back to its original form."""
    try:
        with gzip.open(compressed_path, "rb") as f_in:
            with open(output_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        return True
    except Exception:
        logger.exception("Decompression failed for %s", compressed_path)
        return False
