from safe_pipe.adapters.dask_local import cluster_kwargs
from safe_pipe.schemas import DaskNativeConfig


def test_cluster_kwargs_pass_memory_limit() -> None:
    cfg = DaskNativeConfig(n_workers=1, threads_per_worker=2, memory_limit="1GB")
    kwargs = cluster_kwargs(cfg)
    assert kwargs["n_workers"] == 1
    assert kwargs["threads_per_worker"] == 2
    assert kwargs["memory_limit"] == "1GB"
    assert kwargs["dashboard_address"] is None
