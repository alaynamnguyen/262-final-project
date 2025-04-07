# server/utils.py

import hashlib
import random
import string
import logging


def hash_key(key: str, max_range: int = 2**32) -> int:
    """Hash a string key into a consistent integer using SHA-256."""
    hash_bytes = hashlib.sha256(key.encode()).digest()
    return int.from_bytes(hash_bytes[:4], 'big') % max_range


def generate_node_id(length=8):
    """Generate a random node ID."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def setup_logger(name="kvstore", level=logging.INFO):
    """Set up a basic logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger
