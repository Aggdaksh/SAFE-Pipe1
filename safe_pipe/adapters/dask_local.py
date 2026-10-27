from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from safe_pipe.schemas import DaskNativeConfig


def cluster_kwargs(config: DaskNativeConfig) -> dict[str, Any]:
    """Arguments for distributed.LocalCluster. Import of dask is deferred so unit tests stay light."""
    return {
        "n_workers": config.n_workers,
        "threads_per_worker": config.threads_per_worker,
        "memory_limit": config.memory_limit,
        "processes": config.processes,
        "dashboard_address": None,
    }


@contextmanager
def local_client(config: DaskNativeConfig) -> Iterator[Any]:
    from dask.distributed import Client, LocalCluster

    cluster = LocalCluster(**cluster_kwargs(config))
    try:
        client = Client(cluster)
        try:
            yield client
        finally:
            client.close()
    finally:
        cluster.close()
