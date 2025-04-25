import matplotlib.pyplot as plt
from collections import Counter
import os

LOG_PATH = "server/run-strong/127.0.0.1:5001_shard_0.txt"
OUTPUT_PATH = "server/run-strong/distribution.png"

def parse_log(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Log file not found: {filepath}")

    counts = Counter()
    with open(filepath, "r") as f:
        lines = f.readlines()[1:]  # Skip header
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 3:
                command = parts[2]
                if command.startswith("SET"):
                    counts["SET"] += 1
                elif command.startswith("GET"):
                    counts["GET"] += 1
                elif command.startswith("DEL"):
                    counts["DELETE"] += 1
    return counts

def plot_distribution(counts):
    plt.figure(figsize=(6, 4))
    plt.bar(counts.keys(), counts.values(), color=["skyblue", "orange", "salmon"])
    plt.title("Operation Distribution")
    plt.ylabel("Count")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(OUTPUT_PATH)
    print(f"Plot saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    op_counts = parse_log(LOG_PATH)
    plot_distribution(op_counts)
