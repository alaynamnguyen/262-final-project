import grpc
import sys
import os
import argparse

# Add project root to sys.path for importing generated proto modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kv_store_pb2
import kv_store_pb2_grpc

def parse_args():
    parser = argparse.ArgumentParser(description="Key-Value Store Client")
    parser.add_argument('--file', type=str, help='Path to command file')
    parser.add_argument('--host', type=str, default='localhost')
    parser.add_argument('--port', type=int, default=5000)
    return parser.parse_args()

def run_from_file(filename, stub):
    with open(filename, 'r') as f:
        for line in f:
            tokens = line.strip().split()
            if not tokens:
                continue

            cmd = tokens[0].lower()

            if cmd == "set" and len(tokens) == 3:
                key, value = tokens[1], tokens[2]
                print(f"> set {key} {value}")
                response = stub.Set(kv_store_pb2.SetRequest(key=key, value=value))
                print(f"  -> success: {response.success}")
            elif cmd == "get" and len(tokens) == 2:
                key = tokens[1]
                print(f"> get {key}")
                response = stub.Get(kv_store_pb2.GetRequest(key=key))
                print(f"  -> found: {response.found}, value: {response.value}")
            elif cmd == "delete" and len(tokens) == 2:
                key = tokens[1]
                print(f"> delete {key}")
                response = stub.Delete(kv_store_pb2.DeleteRequest(key=key))
                print(f"  -> success: {response.success}")
            else:
                print(f"Invalid command: {line.strip()}")

def main():
    args = parse_args()
    channel = grpc.insecure_channel(f'{args.host}:{args.port}')
    stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)

    if args.file:
        run_from_file(args.file, stub)
    else:
        print("Please provide a --file path to run commands.")

if __name__ == '__main__':
    main()
