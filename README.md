# 262-final-project

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. kv_store.proto
```

```bash
python server/leader.py
python server/shard.py --role shard_leader --shard-id shard_0 --port 5001
python server/shard.py --role replica --shard-id shard_0 --port 5002
python client/client.py --file client/commands.txt
```
