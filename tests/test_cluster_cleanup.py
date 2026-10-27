import sys
from types import ModuleType, SimpleNamespace

import pytest

from safe_pipe.adapters.dask_local import local_client
from safe_pipe.schemas import DaskNativeConfig


@pytest.fixture
def fake_dask(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    state = SimpleNamespace(events=[], client_init_error=None, client_close_error=None)

    class FakeCluster:
        def __init__(self, **kwargs: object) -> None:
            state.events.append("cluster.init")

        def close(self) -> None:
            state.events.append("cluster.close")

    class FakeClient:
        def __init__(self, cluster: FakeCluster) -> None:
            state.events.append("client.init")
            if state.client_init_error is not None:
                raise state.client_init_error

        def close(self) -> None:
            state.events.append("client.close")
            if state.client_close_error is not None:
                raise state.client_close_error

    dask = ModuleType("dask")
    distributed = ModuleType("dask.distributed")
    distributed.Client = FakeClient
    distributed.LocalCluster = FakeCluster
    dask.distributed = distributed
    monkeypatch.setitem(sys.modules, "dask", dask)
    monkeypatch.setitem(sys.modules, "dask.distributed", distributed)
    return state


def config() -> DaskNativeConfig:
    return DaskNativeConfig(n_workers=1, threads_per_worker=1, memory_limit="1GB")


def test_normal_exit_closes_client_then_cluster(fake_dask: SimpleNamespace) -> None:
    with local_client(config()) as client:
        assert client is not None
        fake_dask.events.append("body")
    assert fake_dask.events == ["cluster.init", "client.init", "body", "client.close", "cluster.close"]


def test_client_initialization_failure_closes_cluster(fake_dask: SimpleNamespace) -> None:
    error = RuntimeError("client failed to connect")
    fake_dask.client_init_error = error
    with pytest.raises(RuntimeError) as caught:
        with local_client(config()):
            pytest.fail("The context must not yield when Client initialization fails")
    assert caught.value is error
    assert fake_dask.events == ["cluster.init", "client.init", "cluster.close"]


def test_client_close_failure_still_closes_cluster(fake_dask: SimpleNamespace) -> None:
    error = RuntimeError("client shutdown failed")
    fake_dask.client_close_error = error
    with pytest.raises(RuntimeError) as caught:
        with local_client(config()):
            pass
    assert caught.value is error
    assert fake_dask.events == ["cluster.init", "client.init", "client.close", "cluster.close"]


def test_workload_failure_closes_client_and_cluster(fake_dask: SimpleNamespace) -> None:
    error = ValueError("workload failed")
    with pytest.raises(ValueError) as caught:
        with local_client(config()):
            raise error
    assert caught.value is error
    assert fake_dask.events == ["cluster.init", "client.init", "client.close", "cluster.close"]
