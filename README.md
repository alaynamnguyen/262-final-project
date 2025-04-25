# Consistency in a Sharded Distributed Key-Value Store

This project implements a distributed key-value store that supports both strong and weak consistency across multiple shards and replicas using gRPC.

## Generating gRPC Python Code from `.proto`

This generates the necessary gRPC and message classes from the protobuf definition file:

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. kv_store.proto
```

## Running the System (Manual)

You can manually launch the system components using the following commands:

```bash
# Start the Leader-Leader node (global coordinator)
python server/leader.py --config configs/config.json

# Start a Shard Leader (RL) for shard_0
python server/shard.py --role shard_leader --shard-id shard_0 --port 5001 --config configs/config.json

# Start a replica for shard_0
python server/shard.py --role replica --shard-id shard_0 --port 5002 --config configs/config.json

# Run a client that sends operations (GET, SET, DELETE)
python client/client.py --file client/experiment.txt
```

## Spin Up All Processes via Config (Recommended)

To automatically start all shard leaders and replicas based on your JSON config:

```bash
# Install jq if not already installed
brew install jq

# Start everything based on the given config file
bash spin_up.sh configs/config-10-weak.json

# Kill all running processes (logs stored in ./logs/)
bash spin_down.sh
```

`configs/config-10-weak.json` defines 3 shards, each with 10 replicas under weak consistency.
`configs/config-10-strong.json` defines 3 shards, each with 10 replicas under strong consistency.

## Plotting and Analysis

After running experiments, use these scripts to visualize and analyze results:

```bash
# Bar chart showing total SET / GET / DELETE operations per shard
python server/plot-distribution.py

# Heatmap showing key-value inconsistencies across replicas (only for weak mode)
python server/plot-inconsistency.py

# Logical clock over time per node (leader and two random replicas)
python server/plot_sys_logical_clock.py
```

## Running Unit Tests

Unit tests are written using pytest for both the Leader-Leader and ShardNode gRPC servers. These tests verify core functionality like request forwarding, key-value operations, heartbeat responses, and replica registration logic.

To run all tests:

```bash
pytest server/tests
```
