import grpc
from concurrent import futures
import json
import os
import sys
import hashlib

# Add project root to sys.path for importing generated proto modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kv_store_pb2
import kv_store_pb2_grpc

CONFIG_PATH = "config.json"

class LeaderLeaderServicer(kv_store_pb2_grpc.KeyValueStoreServicer):
    def __init__(self, shard_map):
        self.shard_map = shard_map
        print("Initialized Leader-Leader with shard map:")
        for shard_id, info in self.shard_map.items():
            print(f"  {shard_id} -> {info['shard_leader']}")

    def hash_key(self, key):
        return int(hashlib.sha1(key.encode()).hexdigest(), 16)

    def get_shard_id(self, key):
        shard_index = self.hash_key(key) % len(self.shard_map)
        return f"shard_{shard_index}"

    def forward_to_shard(self, method, key, request):
        shard_id = self.get_shard_id(key)
        shard_leader_address = self.shard_map[shard_id]["shard_leader"]

        with grpc.insecure_channel(shard_leader_address) as channel:
            stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)
            return getattr(stub, method)(request)

    def Set(self, request, context):
        print(f"Leader-Leader: forwarding Set({request.key})")
        return self.forward_to_shard("Set", request.key, request)

    def Get(self, request, context):
        print(f"Leader-Leader: forwarding Get({request.key})")
        return self.forward_to_shard("Get", request.key, request)

    def Delete(self, request, context):
        print(f"Leader-Leader: forwarding Delete({request.key})")
        return self.forward_to_shard("Delete", request.key, request)
    
    def ShardLeaderChange(self, request, context):
        print("Leader leader heard about a new shard leader", request.shard_id, request.ip_address)
        self.shard_map[request.shard_id] = request.ip_address
        return kv_store_pb2.LeaderChangeResponse(success=True)

def load_config(path):
    with open(path, "r") as f:
        return json.load(f)

def serve():
    config = load_config(CONFIG_PATH)
    leader_address = config["leader_leader"]["address"]
    shard_map = config["shards"]

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    kv_store_pb2_grpc.add_KeyValueStoreServicer_to_server(
        LeaderLeaderServicer(shard_map), server
    )
    server.add_insecure_port(leader_address)
    print(f"Leader-Leader server started on {leader_address}")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
