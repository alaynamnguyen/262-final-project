import grpc
import sys
import os

# Add project root to sys.path for importing generated proto modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kv_store_pb2
import kv_store_pb2_grpc

def main():
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

if __name__ == '__main__':
    main()
