# 262-final-project

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. kv_store.proto
```

```bash
python server/leader.py --config configs/config.json
python server/shard.py --role shard_leader --shard-id shard_0 --port 5001 --config configs/config.json
python server/shard.py --role replica --shard-id shard_0 --port 5002 --config configs/config.json
python client/client.py --file client/commands.txt
```

```bash
brew install jq

bash spin_up.sh configs/config-10-weak.json
bash spin_down.sh
```
