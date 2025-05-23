import grpc
import json
import argparse
import sys
import os
from concurrent import futures
import threading
import time
import utils
import random
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kv_store_pb2
import kv_store_pb2_grpc

CONFIG_PATH = "config.json"

class ShardNodeServicer(kv_store_pb2_grpc.KeyValueStoreServicer):
    def __init__(self, role, shard_id, local_address, config):
        self.role = role
        self.shard_id = shard_id
        self.local_address = local_address
        self.config = config
        self.leader_leader_address = config["leader_leader"]["address"]
        self.store = {}
        self.replicas = [] # Does not include the leader address
        self.shard_id = shard_id
        self.logical_clock = 0
        self.mode = config["mode"]
        self.command_file = f'server/run-{self.mode}/{self.local_address}_{self.shard_id}.txt'
        self.filepath = f'server/data-{self.mode}/{self.local_address}_{self.shard_id}.json'

        header_line = f"system_time logical_clock command status\n"
        utils.write_line_to_txt(self.command_file, header_line, "w")

    def on_server_start(self):
        if self.role == "shard_leader":
            print(f"Shard Leader for {self.shard_id} initialized at {self.local_address}")
            print(f"  -> Replicas: {self.replicas}")
            print("Starting replica leader heartbeat loop...")
            self.start_leader_heartbeat_loop()
        elif self.role == "replica":
            self.leader_address = self.config["shards"][self.shard_id]["shard_leader"]
            # TODO get the leader address from the LEADER LEADER instead of from config
            # may need to add to proto something for this
            print(f"Replica for {self.shard_id} initialized at {self.local_address}")
            print(f"  -> Leader: {self.leader_address}")
            print("Starting replica heartbeat loop...")
            self.start_heartbeat_loop()

            # Register with the shard leader
            ip, port = self.local_address.split(":")
            with grpc.insecure_channel(self.leader_address) as channel:
                stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)
                request = kv_store_pb2.RegisterReplicaRequest(ip_address=ip, port=int(port))
                response = stub.RegisterReplica(request)
                if response.success:
                    print(f"Successfully registered replica with shard leader at {self.leader_address}")
                else:
                    print(f"Failed to register replica with shard leader at {self.leader_address}")

    def start_leader_heartbeat_loop(self):
        """Start sending heartbeat pings from replica leader to all replicas on a background thread."""
        def loop():
            while True:
                for replica in self.replicas:
                    try:
                        with grpc.insecure_channel(replica) as channel:
                            stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)
                            request = kv_store_pb2.HeartbeatRequest(server_id=self.local_address)
                            response = stub.Heartbeat(request)
                            if not response.success:
                                print(f"[{self.local_address}] Replica {replica} failed to respond to heartbeat.")
                    except Exception as e:
                        print(f"[{self.local_address}] Error pinging replica {replica}: replica is down")
                        # Replica is down so remove it from the list and push the new list out to other replicas
                        self.replicas.remove(replica)
                        self.push_replica_list_to_replicas()
                time.sleep(3)  # every 3 seconds

        threading.Thread(target=loop, daemon=True).start()

    def start_heartbeat_loop(self):
        """Start sending heartbeat pings from replica to the replica leader on a background thread."""
        def loop():
            while True:
                try:
                    with grpc.insecure_channel(self.leader_address) as channel:
                        stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)
                        request = kv_store_pb2.HeartbeatRequest(server_id=self.local_address)
                        response = stub.Heartbeat(request)
                        if not response.success:
                            print(f"[{self.local_address}] Leader responded with failure!")
                except Exception as e:
                    print(f"[{self.local_address}] Failed to reach leader {self.leader_address}: time to leader elect")
                    # Trigger leader election
                    self.leader_election()
                time.sleep(3)  # every 3 seconds

        threading.Thread(target=loop, daemon=True).start()

    def leader_election(self):
        """Elects a new leader from the replica list."""
        # Elect new leader (min ip/port combo from replica list)
        new_leader_address = min(self.replicas)
        
        if self.local_address == new_leader_address:
            self.role = "shard_leader"
            self.start_leader_heartbeat_loop()
            # Remove newly elected leader from replica list
        self.replicas.remove(new_leader_address)
        print("REPLICA LIST:", self.replicas)

        # Update everyone's params to new leader
        self.leader_address = new_leader_address

        # Tell the leader leader the new leader address        
        with grpc.insecure_channel(self.leader_leader_address) as channel:
            stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)
            request = kv_store_pb2.LeaderChangeRequest(shard_id=self.shard_id, ip_address=self.local_address)
            _ = stub.ShardLeaderChange(request)
        
        print("    New leader elected:", self.leader_address)

    def RegisterReplica(self, request, context):
        if self.role != "shard_leader":
            print("RegisterReplica called on non-leader — rejecting")
            return kv_store_pb2.RegisterReplicaResponse(success=False)

        replica_address = f"{request.ip_address}:{request.port}"
        if replica_address not in self.replicas:
            self.replicas.append(replica_address)
            print(f"[{self.shard_id}] Registered new replica: {replica_address}")
        else:
            print(f"[{self.shard_id}] Replica {replica_address} already registered")
        
        print(f"  -> Replicas: {self.replicas}")

        # Push replica list to all replicas from replica leader
        self.push_replica_list_to_replicas()
        # Send the new replica the current data store
        with grpc.insecure_channel(replica_address) as channel:
            stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)
            request = kv_store_pb2.StoreRequest(store=utils.dict_to_store(self.store))
            response = stub.PushStore(request)
            assert response.success
        return kv_store_pb2.RegisterReplicaResponse(success=True)
    
    def push_replica_list_to_replicas(self):
        for replica in self.replicas:
            with grpc.insecure_channel(replica) as channel:
                stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)
                request = kv_store_pb2.ReplicaListRequest(replicas=self.replicas)
                response = stub.PushReplicaList(request)
                assert response.success
        
    def PushStore(self, request, context):
        # Update this replica's store from what the leader has
        self.store = utils.store_to_dict(request.store)
        print(f"[{self.shard_id}] Received data store from leader: {self.store}")
        utils.write_dict_to_json(self.store, self.filepath)
        return kv_store_pb2.StoreResponse(success=True)
    
    def Heartbeat(self, request, context):
        # Uncomment for heartbeat logs
        # print(f"[{self.role.upper()} {self.local_address}] Received heartbeat from {request.server_id}")
        return kv_store_pb2.HeartbeatResponse(success=True)
    
    def PushReplicaList(self, request, context):
        self.replicas = request.replicas
        print(f"  -> Updated replica list: {self.replicas}")
        return kv_store_pb2.ReplicaListResponse(success=True)

    def forward_to_replica(self, method, key, request, replica_address):
        with grpc.insecure_channel(replica_address) as channel:
            stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)
            return getattr(stub, method)(request)

    def forward_to_replica_async(self, method, key, request, replica_address):
        def _forward():
            try:
                with grpc.insecure_channel(replica_address) as channel:
                    stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)
                    getattr(stub, method)(request)
            except Exception as e:
                print(f"[{self.local_address}] Gossip to {replica_address} failed: {e}")
        threading.Thread(target=_forward, daemon=True).start()
        
    def handle_logical_clock(self, method, request):
        """method: Get"""
        # Update internal clock by 1 (since you're a replica leader)
        self.logical_clock += 1
        
    def handle_logical_clock_and_push(self, method, request):
        """method: Set or Delete"""
        # Push update to replicas if you're the replica leader
        if self.role == "shard_leader":
            # TODO maybe update clock for having received command
            if self.mode == "strong": # Send to all replicas!
                for replica in self.replicas:
                    self.logical_clock += 1 # leader increments logical clock for each replica it sends to
                    request.logical_clock = self.logical_clock
                    self.forward_to_replica(method, request.key, request, replica)
            elif len(self.replicas) > 0: # Send to one replica randomly
                self.logical_clock += 1 # leader increments logical clock for each replica it sends to
                request.logical_clock = self.logical_clock
                choice = random.choice(self.replicas)
                del request.told_replicas[:]
                request.told_replicas.append(choice)
                self.forward_to_replica_async(method, request.key, request, choice)
        else:
            # replica should update its logical clock based on the leader's
            self.logical_clock = max(self.logical_clock, request.logical_clock) + 1
            if self.mode == "weak": # Pass along to another random replica
                request.logical_clock = self.logical_clock
                remaining = list(set(self.replicas) - set(request.told_replicas))
                if remaining:
                    choice = random.choice(remaining)
                    request.told_replicas.append(choice)
                    self.forward_to_replica_async(method, request.key, request, choice)
                else:
                    print(f"[{self.local_address}] No more replicas left to gossip to for key {request.key}")
            # if strong, do nothing, shard leader informs everyone
        
    def Set(self, request, context):
        print(f"[{self.shard_id}] SET {request.key} -> {request.value}")
        self.store[request.key] = request.value
        
        # Write to persistent storage
        utils.write_dict_to_json(self.store, self.filepath)
        self.handle_logical_clock_and_push("Set", request)
        command = f"SET-{request.key}->{request.value}-{request.logical_clock}"
        utils.write_line_to_txt(self.command_file, f"{time.time()} {self.logical_clock} {command} {True}", "a")
        return kv_store_pb2.SetResponse(success=True)

    def Get(self, request, context): # only the replica leader responds
        value = self.store.get(request.key, "")
        found = request.key in self.store
        print(f"[{self.shard_id}] GET {request.key} -> {value if found else 'NOT FOUND'}")
        self.handle_logical_clock("Get", request)
        command = f"GET-{request.key}-{request.logical_clock}"
        utils.write_line_to_txt(self.command_file, f"{time.time()} {self.logical_clock} {command} {found}", "a")
        return kv_store_pb2.GetResponse(found=found, value=value)

    def Delete(self, request, context):
        success = self.store.pop(request.key, None) is not None
        print(f"[{self.shard_id}] DEL {request.key} -> {'Success' if success else 'Not found'}")

        # Write to persistent storage
        utils.write_dict_to_json(self.store, self.filepath)
        self.handle_logical_clock_and_push("Delete", request)
        command = f"DEL-{request.key}-{request.logical_clock}"
        utils.write_line_to_txt(self.command_file, f"{time.time()} {self.logical_clock} {command} {success}", "a")
        return kv_store_pb2.DeleteResponse(success=success)

def load_config(path):
    with open(path, "r") as f:
        return json.load(f)

def serve(role, shard_id, port, config_path):
    config = load_config(config_path)
    local_address = f"127.0.0.1:{port}"

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = ShardNodeServicer(role, shard_id, local_address, config)
    kv_store_pb2_grpc.add_KeyValueStoreServicer_to_server(servicer, server)

    server.add_insecure_port(local_address)
    print(f"{role.upper()} for {shard_id} listening on {local_address}")
    server.start()
    servicer.on_server_start()
    server.wait_for_termination()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start a shard node.")
    parser.add_argument("--role", choices=["shard_leader", "replica"], required=True)
    parser.add_argument("--shard-id", required=True, help="shard_0 / shard_1 / shard_2")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--config", type=str, default="configs/config.json")

    args = parser.parse_args()
    serve(args.role, args.shard_id, args.port, args.config)
