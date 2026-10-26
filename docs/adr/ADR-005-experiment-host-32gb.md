# ADR-005 — Use the Windows 32 GB PC for physical Dask evidence

- **Date:** 2026-10-26
- **Status:** Accepted by the user in this session

The earlier plan named a 16 GB experiment PC. The user identified the current Windows PC as the machine to use. It has 33,711,480,832 physical bytes (31.4 GiB). T0 passed on it; see [`../../reports/t0.md`](../../reports/t0.md).

Keep the experiment design unchanged: four families, eight configurations, three repeats, one job at a time, and worker `memory_limit` of 1 GB or 2 GB. The extra host RAM is headroom for Windows, scheduler, and data generation, not a reason to raise worker caps or add configurations. Label all physical results with the actual host and OS. The old 16 GB plan remains a conservative sizing reference, not a description of the measured host.
