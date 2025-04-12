#!/bin/bash

PID_FILE="./pids.txt"

if [ ! -f $PID_FILE ]; then
  echo "PID file not found. No processes to kill."
  exit 1
fi

while read pid; do
  if kill -0 $pid 2>/dev/null; then
    echo "Killing process $pid"
    kill $pid
  else
    echo "Process $pid not running"
  fi
done < $PID_FILE

# Optionally, remove the PID file after killing processes
rm -f $PID_FILE
