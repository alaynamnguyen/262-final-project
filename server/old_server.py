import grpc
from concurrent import futures
import sys
import os

# Add project root to sys.path for importing generated proto modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kv_store_pb2
import kv_store_pb2_grpc

# In-memory key-value store
class KeyValueStoreServicer(kv_store_pb2_grpc.KeyValueStoreServicer):
    def __init__(self):
        self.store = {}

    def Set(self, request, context):
        self.store[request.key] = request.value
        print(f"SET: {request.key} -> {request.value}")
        return kv_store_pb2.SetResponse(success=True)

    def Get(self, request, context):
        value = self.store.get(request.key, "")
        found = request.key in self.store
        print(f"GET: {request.key} -> {value if found else 'NOT FOUND'}")
        return kv_store_pb2.GetResponse(found=found, value=value)

    def Delete(self, request, context):
        success = self.store.pop(request.key, None) is not None
        print(f"DELETE: {request.key} -> {'Success' if success else 'Not found'}")
        return kv_store_pb2.DeleteResponse(success=success)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kv_store_pb2_grpc.add_KeyValueStoreServicer_to_server(KeyValueStoreServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Server starting on port 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
