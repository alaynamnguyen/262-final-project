import pytest
import grpc
from concurrent import futures
from unittest.mock import patch
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

    with patch("server.shard.utils.write_line_to_txt"), \
         patch("server.shard.utils.write_dict_to_json"), \
         patch("server.shard.utils.dict_to_store", lambda store: []), \
         patch("server.shard.utils.store_to_dict", lambda store: {}):
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

def test_logical_clock_increments(grpc_shard_server):
    servicer, address = grpc_shard_server
    prev_clock = servicer.logical_clock
    channel = grpc.insecure_channel(address)
    stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)

    stub.Set(kv_store_pb2.SetRequest(key="clocktest", value="value"))
    assert servicer.logical_clock > prev_clock

def test_register_replica_mocked(grpc_shard_server):
    servicer, address = grpc_shard_server
    channel = grpc.insecure_channel(address)
    stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)

    with patch.object(servicer, "push_replica_list_to_replicas") as mock_push, \
         patch.object(servicer, "forward_to_replica") as mock_forward:
        mock_push.return_value = None
        mock_forward.return_value = None

        req = kv_store_pb2.RegisterReplicaRequest(ip_address="127.0.0.1", port=6999)
        response = stub.RegisterReplica(req)
        assert response.success is True
