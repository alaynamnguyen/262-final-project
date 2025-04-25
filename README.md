# 262-final-project

## Generating proto files

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. kv_store.proto
```

## Running LL, RL, replica

```bash
python server/leader.py --config configs/config.json
python server/shard.py --role shard_leader --shard-id shard_0 --port 5001 --config configs/config.json
python server/shard.py --role replica --shard-id shard_0 --port 5002 --config configs/config.json
python client/client.py --file client/experiment.txt
```

## Bash script to spin up from config

```bash
brew install jq

bash spin_up.sh configs/config-10-weak.json
bash spin_down.sh
```

## Plotting

```bash
python server/plot-distribution.py
```
