import pytest
import grpc
from concurrent import futures
from unittest.mock import patch, MagicMock
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import kv_store_pb2
import kv_store_pb2_grpc
from server.leader import LeaderLeaderServicer

# Set up a test shard map
TEST_SHARD_MAP = {
    "shard_0": {
        "shard_leader": "127.0.0.1:9999"  # dummy address
    }
}

@pytest.fixture(scope="module")
def grpc_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    servicer = LeaderLeaderServicer(TEST_SHARD_MAP)
    kv_store_pb2_grpc.add_KeyValueStoreServicer_to_server(servicer, server)
    port = server.add_insecure_port('[::]:50051')
    server.start()
    yield f'localhost:{port}'
    server.stop(None)

def test_shard_leader_change(grpc_server):
    channel = grpc.insecure_channel(grpc_server)
    stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)

    request = kv_store_pb2.LeaderChangeRequest(
        shard_id="shard_0",
        ip_address="127.0.0.1:5050"
    )
    response = stub.ShardLeaderChange(request)

    assert response.success is True

def test_forwarding_calls_are_made(grpc_server):
    channel = grpc.insecure_channel(grpc_server)
    stub = kv_store_pb2_grpc.KeyValueStoreStub(channel)

    # Patch the method that does the forwarding to avoid real downstream gRPC call
    with patch.object(LeaderLeaderServicer, "forward_to_shard") as mocked_forward:
        mocked_forward.return_value = kv_store_pb2.SetResponse(success=True)

        request = kv_store_pb2.SetRequest(key="foo", value="bar")
        response = stub.Set(request)
        assert response.success is True
        mocked_forward.assert_called_once_with("Set", "foo", request)
