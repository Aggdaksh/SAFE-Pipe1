"""T0 — 30-minute Dask smoke on the experiment PC, not on the 8 GB coding laptop.

Success: LocalCluster starts, a tiny dataframe sum completes, the process exits.
This is not the main matrix. Use 1 worker and a low memory_limit.
"""

from __future__ import annotations

import time

from safe_pipe.adapters.dask_local import local_client
from safe_pipe.schemas import DaskNativeConfig


def main() -> None:
    config = DaskNativeConfig(n_workers=1, threads_per_worker=1, memory_limit="512MB")
    t0 = time.perf_counter()
    with local_client(config) as client:
        info = client.scheduler_info()
        import dask.dataframe as dd
        import pandas as pd

        pdf = pd.DataFrame({"x": range(10_000)})
        ddf = dd.from_pandas(pdf, npartitions=4)
        total = int(ddf.x.sum().compute())
        workers = list(info["workers"])
        elapsed = time.perf_counter() - t0
        print(
            {
                "ok": True,
                "n_workers_reported": len(workers),
                "sum": total,
                "elapsed_s": round(elapsed, 3),
                "config": config.model_dump(),
            }
        )


if __name__ == "__main__":
    main()
