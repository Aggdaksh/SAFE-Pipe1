"""T0 — Dask LocalCluster smoke.

Run this on the **16 GB experiment PC only**.
Do not run it on the 8 GB coding Mac: worker caps of 1–2 GB plus processes will swap.
"""

from __future__ import annotations

import os
import sys
import time

from safe_pipe.adapters.dask_local import local_client
from safe_pipe.schemas import DaskNativeConfig


def main() -> None:
    if os.environ.get("SAFE_PIPE_HOST", "").lower() == "8gb" and not os.environ.get(
        "SAFE_PIPE_ALLOW_DASK_ON_8GB"
    ):
        print(
            "Refusing T0 on the coding Mac (SAFE_PIPE_HOST=8gb). "
            "Run this on the 16GB PC.",
            file=sys.stderr,
        )
        raise SystemExit(2)

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
                "host_note": "official T0 is the 16GB experiment PC",
            }
        )


if __name__ == "__main__":
    main()
