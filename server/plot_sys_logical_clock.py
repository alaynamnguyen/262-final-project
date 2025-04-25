import matplotlib.pyplot as plt

MODE = "strong"
SHARD_ID = 2
OUTPUT_PATH = f"server/plot_sys_logical_clock_{MODE}_shard{SHARD_ID}.pdf"
PORT = 5000 + (SHARD_ID == 0) + (not SHARD_ID == 0) * 10 * 2 * SHARD_ID

print(PORT)

leader_file = f"server/run-{MODE}/127.0.0.1:{PORT}_shard_{SHARD_ID}.txt"
replica1_file = f"server/run-{MODE}/127.0.0.1:{PORT + 1}_shard_{SHARD_ID}.txt"
replica2_file = f"server/run-{MODE}/127.0.0.1:{PORT + 2}_shard_{SHARD_ID}.txt"

def load_clock_data(filepath):
    system_times = []
    logical_clocks = []
    with open(filepath, "r") as f:
        next(f)  # Skip header
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                try:
                    system_times.append(float(parts[0]))
                    logical_clocks.append(int(parts[1]))
                except ValueError:
                    continue
    return system_times, logical_clocks

# Load the data
leader_time, leader_clock = load_clock_data(leader_file)
replica1_time, replica1_clock = load_clock_data(replica1_file)
replica2_time, replica2_clock = load_clock_data(replica2_file)

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(leader_time, leader_clock, label="Shard Leader", marker='o', markersize=1, linewidth=1)
plt.plot(replica1_time, replica1_clock, label="Replica 1", marker='x', markersize=1, linewidth=1)
plt.plot(replica2_time, replica2_clock, label="Replica 2", marker='s', markersize=1, linewidth=1)

plt.xlabel("System Time")
plt.ylabel("Logical Clock")
plt.title("Logical Clock vs System Time for Shard Leader and Replicas")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(OUTPUT_PATH)
