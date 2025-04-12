# server/utils.py

import hashlib
import random
import string
import logging
import os


def hash_key(key: str, max_range: int = 2**32) -> int:
    """Hash a string key into a consistent integer using SHA-256."""
    hash_bytes = hashlib.sha256(key.encode()).digest()
    return int.from_bytes(hash_bytes[:4], 'big') % max_range


def generate_node_id(length=8):
    """Generate a random node ID."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def setup_logger(db_name, shard_id, ip, port, log_dir="logs"):
    """
    Set up a logger for a shard replica or leader.
    Log file is named using database name, shard ID, IP, and port.
    """

    os.makedirs(log_dir, exist_ok=True)

    replica_id = f"{db_name}_shard{shard_id}_replica{ip.replace('.', '-')}-{port}"
    log_file = os.path.join(log_dir, f"{replica_id}.log")

    logger = logging.getLogger(replica_id)

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

