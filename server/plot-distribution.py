import matplotlib.pyplot as plt
from collections import Counter
import os

SHARD_FILES = {
    "shard_0": "server/run-strong/127.0.0.1:5001_shard_0.txt",
    "shard_1": "server/run-strong/127.0.0.1:5020_shard_1.txt",
    "shard_2": "server/run-strong/127.0.0.1:5040_shard_2.txt"
}

OUTPUT_PATH = "server/distribution_all_shards.png"

def parse_log(filepath):
    counts = Counter()
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found.")
        return counts

    with open(filepath, "r") as f:
        lines = f.readlines()[1:]  # skip header
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

colors = {
    "shard_0": "#b99b74",  # soft copper / muted tan (matches your header background)
    "shard_1": "#d4c084",  # light golden beige (matches right column background)
    "shard_2": "#a7bfa6"   # calm sage green (matches left column accent)
}

def plot_distributions(all_counts):
    labels = ["SET", "DELETE", "GET"]
    x = range(len(labels))
    width = 0.25

    plt.figure(figsize=(8, 5))
    
    for idx, (shard, counts) in enumerate(all_counts.items()):
        values = [counts.get(op, 0) for op in labels]
        bar_x = [i + idx * width for i in x]
        plt.bar(bar_x, values, width=width, label=shard, color=colors[shard])

    plt.xticks([i + width for i in x], labels)
    plt.ylabel("Count")
    plt.title("Operation Distribution by Shard")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.legend(title="Shard")
    plt.tight_layout()
    plt.savefig(OUTPUT_PATH)
    print(f"Plot saved to: {OUTPUT_PATH}")

if __name__ == "__main__":
    all_counts = {shard: parse_log(path) for shard, path in SHARD_FILES.items()}
    plot_distributions(all_counts)
