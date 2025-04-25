import pytest
import grpc
from concurrent import futures
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import kv_store_pb2
import kv_store_pb2_grpc
from server.shard import ShardNodeServicer

TEST_CONFIG = {
    "mode": "strong",
    "leader_leader": {
        "address": "127.0.0.1:5999"
    },
    "shards": {
        "shard_0": {
            "shard_leader": "127.0.0.1:5990",
            "replicas": ["127.0.0.1:5991", "127.0.0.1:5992"]
        }
    }
}

@pytest.fixture(scope="module")
def grpc_shard_server():
    shard_id = "shard_0"
    local_address = "127.0.0.1:5990"
    role = "shard_leader"

    # Patch using the name actually used in shard.py
    with patch("server.shard.utils") as mock_utils:
        mock_utils.write_line_to_txt = MagicMock()
        mock_utils.write_dict_to_json = MagicMock()
        mock_utils.dict_to_store = lambda store: []
        mock_utils.store_to_dict = lambda store: {}

        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        servicer = ShardNodeServicer(role, shard_id, local_address, TEST_CONFIG)
        kv_store_pb2_grpc.add_KeyValueStoreServicer_to_server(servicer, server)
        server.add_insecure_port(local_address)
        server.start()

        yield servicer, f"{local_address}"

        server.stop(None)

def test_basic_set_and_get(grpc_shard_server):
    _, address = grpc_shard_server
    channel = grpc.insecure_channel(address)
    stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)

    set_resp = stub.Set(kv_store_pb2.SetRequest(key="foo", value="bar"))
    assert set_resp.success is True

    get_resp = stub.Get(kv_store_pb2.GetRequest(key="foo"))
    assert get_resp.found is True
    assert get_resp.value == "bar"

def test_delete_existing_key(grpc_shard_server):
    _, address = grpc_shard_server
    channel = grpc.insecure_channel(address)
    stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)

    stub.Set(kv_store_pb2.SetRequest(key="todelete", value="data"))
    del_resp = stub.Delete(kv_store_pb2.DeleteRequest(key="todelete"))
    assert del_resp.success is True

    get_resp = stub.Get(kv_store_pb2.GetRequest(key="todelete"))
    assert get_resp.found is False

def test_register_replica_mocked(grpc_shard_server):
    servicer, address = grpc_shard_server
    channel = grpc.insecure_channel(address)
    stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)

    with patch.object(servicer, "push_replica_list_to_replicas") as mock_push, \
         patch.object(servicer, "forward_to_replica") as mock_forward, \
         patch("server.shard.grpc.insecure_channel") as mock_channel:
        
        mock_push.return_value = None
        mock_forward.return_value = None
        
        # Stub out PushStore response so it doesn't actually connect
        mock_stub = MagicMock()
        mock_stub.PushStore.return_value = kv_store_pb2.StoreResponse(success=True)
        mock_channel.return_value.__enter__.return_value = mock_stub

        req = kv_store_pb2.RegisterReplicaRequest(ip_address="127.0.0.1", port=6999)
        response = stub.RegisterReplica(req)
        assert response.success is True

def test_heartbeat(grpc_shard_server):
    _, address = grpc_shard_server
    channel = grpc.insecure_channel(address)
    stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)

    resp = stub.Heartbeat(kv_store_pb2.HeartbeatRequest(server_id="test_server"))
    assert resp.success is True

def test_push_replica_list(grpc_shard_server):
    servicer, address = grpc_shard_server
    channel = grpc.insecure_channel(address)
    stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)

    new_replicas = ["127.0.0.1:6001", "127.0.0.1:6002"]
    request = kv_store_pb2.ReplicaListRequest(replicas=new_replicas)
    response = stub.PushReplicaList(request)

    assert response.success is True
    assert servicer.replicas == new_replicas

def test_push_store(grpc_shard_server):
    _, address = grpc_shard_server
    channel = grpc.insecure_channel(address)
    stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)

    request = kv_store_pb2.StoreRequest(store=[
        kv_store_pb2.KeyValuePair(key="preload", value="injected")
    ])
    response = stub.PushStore(request)

    assert response.success is True
