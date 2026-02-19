"""
utils.py

Utility functions for logging, compression, and other helpers.
"""

import sys
import logging
import gzip
import shutil
import os
from pathlib import Path
from . import config

def setup_logging(name: str = "root", log_to_file: bool = True) -> logging.Logger:
    """
    Sets up logging configuration.
    
    Args:
        name: Logger name.
        log_to_file: Whether to write logs to a file.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler
    if log_to_file:
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = config.LOG_DIR / f"execution-{now}.log"
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
    return logger

def compress_sec_payload(original_path: Path, compressed_path: Path) -> None:
    """
    Compresses raw SEC payloads into GZIP format using chunked binary streaming
    to prevent RAM exhaustion during massive batch operations.
    
    Args:
        original_path: Path to the uncompressed file.
        compressed_path: Path to the target .gz file.
    """
    try:
        with open(original_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Immediate deletion of the uncompressed artifact
        os.remove(original_path)
    except Exception as e:
        logging.error(f"Compression failed for {original_path}: {e}")
        # Note: We do not raise here to avoid crashing the whole batch, 
        # but in a strict system we might want to.
