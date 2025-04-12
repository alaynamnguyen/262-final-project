#!/bin/bash

PYTHON_BIN="python3"
SERVER_DIR="server"
LOG_DIR="./logs"
PID_FILE="./pids.txt"
mkdir -p $LOG_DIR

# Clear existing PID file
> $PID_FILE

echo "Starting Leader-Leader..."
$PYTHON_BIN $SERVER_DIR/leader.py --role ll --host 127.0.0.1 --port 5000 > $LOG_DIR/ll.log 2>&1 &
echo $! >> $PID_FILE

echo "Starting Shard 0 Leader..."
$PYTHON_BIN $SERVER_DIR/shard.py --role shard_leader --shard-id 0 --host 127.0.0.1 --port 5001 > $LOG_DIR/shard0_leader.log 2>&1 &
echo $! >> $PID_FILE

# echo "Starting Shard 0 Replicas..."
# $PYTHON_BIN $SERVER_DIR/shard.py --role replica --shard-id 0 --host 127.0.0.1 --port 5002 > $LOG_DIR/shard0_replica1.log 2>&1 &
# $PYTHON_BIN $SERVER_DIR/shard.py --role replica --shard-id 0 --host 127.0.0.1 --port 5003 > $LOG_DIR/shard0_replica2.log 2>&1 &

# # === Shard 1 ===
# echo "Starting Shard 1 Leader..."
# $PYTHON_BIN $SERVER_DIR/shard.py --role leader --shard-id 1 --host 127.0.0.1 --port 5004 > $LOG_DIR/shard1_leader.log 2>&1 &

# echo "Starting Shard 1 Replicas..."
# $PYTHON_BIN $SERVER_DIR/shard.py --role replica --shard-id 1 --host 127.0.0.1 --port 5005 > $LOG_DIR/shard1_replica1.log 2>&1 &
# $PYTHON_BIN $SERVER_DIR/shard.py --role replica --shard-id 1 --host 127.0.0.1 --port 5006 > $LOG_DIR/shard1_replica2.log 2>&1 &

# # === Shard 2 ===
# echo "Starting Shard 2 Leader..."
# $PYTHON_BIN $SERVER_DIR/shard.py --role leader --shard-id 2 --host 127.0.0.1 --port 5007 > $LOG_DIR/shard2_leader.log 2>&1 &

# echo "Starting Shard 2 Replicas..."
# $PYTHON_BIN $SERVER_DIR/shard.py --role replica --shard-id 2 --host 127.0.0.1 --port 5008 > $LOG_DIR/shard2_replica1.log 2>&1 &
# $PYTHON_BIN $SERVER_DIR/shard.py --role replica --shard-id 2 --host 127.0.0.1 --port 5009 > $LOG_DIR/shard2_replica2.log 2>&1 &

# echo "All processes started. Logs are in logs/"