import os
import json
import hashlib
import matplotlib.pyplot as plt
import numpy as np

DATA_WEAK_DIR = "server/data-weak"

replica_data = {}
all_keys = set()

for filename in os.listdir(DATA_WEAK_DIR):
    if filename.endswith(".json"):
        replica = filename.replace(".json", "")
        filepath = os.path.join(DATA_WEAK_DIR, filename)
        with open(filepath, "r") as f:
            data = json.load(f)
        replica_data[replica] = data
        all_keys.update(data.keys())

all_keys = sorted(all_keys)
replicas = sorted(replica_data.keys())

def color_code(value):
    if value is None:
        return 0
    return int(hashlib.sha1(value.encode()).hexdigest(), 16) % 256

matrix = np.zeros((len(replicas), len(all_keys)), dtype=int)

for i, replica in enumerate(replicas):
    for j, key in enumerate(all_keys):
        val = replica_data[replica].get(key)
        matrix[i, j] = color_code(val)

plt.figure(figsize=(10, len(replicas) * 0.3 + 1.5))
plt.imshow(matrix, aspect='auto', cmap='tab20', interpolation='nearest')
plt.colorbar(label="Hashed Value (color code)")

plt.xticks(ticks=np.arange(len(all_keys)), labels=all_keys, rotation=90)
plt.yticks(ticks=np.arange(len(replicas)), labels=replicas)
plt.title("Replica Value Divergence Heatmap (Weak Consistency)")
plt.xlabel("Key")
plt.ylabel("Replica")
plt.tight_layout()
plt.savefig("server/replica_divergence_heatmap.png")
print("Saved heatmap to server/eplica_divergence_heatmap.png")
