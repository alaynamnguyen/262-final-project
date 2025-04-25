#!/bin/bash

PYTHON_BIN="python3"
SERVER_DIR="server"
LOG_DIR="./logs"
PID_FILE="./pids.txt"

# Use first argument as config path, or default to configs/config.json
CONFIG_PATH=${1:-configs/config.json}

mkdir -p $LOG_DIR

# Clear existing PID file
> $PID_FILE

echo "Reading config from $CONFIG_PATH..."
LL_PORT=$(jq -r '.leader_leader.address' $CONFIG_PATH | cut -d':' -f2)
LL_HOST=$(jq -r '.leader_leader.address' $CONFIG_PATH | cut -d':' -f1)

echo "Starting Leader-Leader on $LL_HOST:$LL_PORT..."
$PYTHON_BIN $SERVER_DIR/leader.py --config $CONFIG_PATH > $LOG_DIR/ll.log 2>&1 &
echo $! >> $PID_FILE

SHARDS=$(jq -r '.shards | keys[]' $CONFIG_PATH)

for SHARD_ID in $SHARDS; do
  LEADER_ADDRESS=$(jq -r ".shards[\"$SHARD_ID\"].shard_leader" $CONFIG_PATH)
  LEADER_PORT=$(echo $LEADER_ADDRESS | cut -d':' -f2)

  echo "Starting Shard Leader for $SHARD_ID on port $LEADER_PORT..."
  $PYTHON_BIN $SERVER_DIR/shard.py --role shard_leader --shard-id $SHARD_ID --port $LEADER_PORT --config $CONFIG_PATH > $LOG_DIR/${SHARD_ID}_leader.log 2>&1 &
  echo $! >> $PID_FILE

  REPLICAS=$(jq -r ".shards[\"$SHARD_ID\"].replicas[]" $CONFIG_PATH)
  REPLICA_NUM=1
  for REPLICA_ADDRESS in $REPLICAS; do
    REPLICA_PORT=$(echo $REPLICA_ADDRESS | cut -d':' -f2)
    echo "Starting Replica $REPLICA_NUM for $SHARD_ID on port $REPLICA_PORT..."
    $PYTHON_BIN $SERVER_DIR/shard.py --role replica --shard-id $SHARD_ID --port $REPLICA_PORT --config $CONFIG_PATH > $LOG_DIR/${SHARD_ID}_replica${REPLICA_NUM}.log 2>&1 &
    echo $! >> $PID_FILE
    ((REPLICA_NUM++))
  done
done

echo "All processes started. Logs are in $LOG_DIR/"
