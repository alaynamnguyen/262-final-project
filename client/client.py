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
    parser.add_argument('--test', action='store_true', help='Run client in test mode')
    return parser.parse_args()

def test():
    channel = grpc.insecure_channel('localhost:50051')
    stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)

    # Try setting a key
    print("Setting foo=bar...")
    stub.Set(kv_store_pb2.SetRequest(key="foo", value="bar"))

    # Try getting it
    print("Getting foo...")
    response = stub.Get(kv_store_pb2.GetRequest(key="foo"))
    print(f"Found: {response.found}, Value: {response.value}")

    # Try deleting it
    print("Deleting foo...")
    stub.Delete(kv_store_pb2.DeleteRequest(key="foo"))

    # Try getting it again
    print("Getting foo after deletion...")
    response = stub.Get(kv_store_pb2.GetRequest(key="foo"))
    print(f"Found: {response.found}, Value: {response.value}")

def main():
    args = parse_args()

    if args.test:
        test()

if __name__ == '__main__':
    main()
