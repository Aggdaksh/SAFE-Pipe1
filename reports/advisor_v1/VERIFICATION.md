# Advisor implementation verification

Date: 2026-10-27. Base: Windows checkpoint `c1646578210083604ac8a2349caa53725115043c`. Work branch: `codex/config-selection-policy`.

Follow-up regression review: **79 tests passed** after fixing CRLF model-loading compatibility. Original predictions and legacy CLI decisions still match the Windows checkpoint. See [REGRESSION_REVIEW.md](REGRESSION_REVIEW.md) for the comparisons and testing limits. The 77-test result below records the initial advisor checkpoint.

## Checks executed

- Complete suite: **77 passed in 6.77 seconds** on the coding Mac with `.[dev,dask,ml]` dependencies installed. Command: `python -B -m pytest -p no:cacheprovider -o addopts='' -q --tb=short`.
- The first sandboxed attempt passed 72 tests; five Dask integration cases could not bind a local scheduler socket. Rerunning with local socket permission passed all 77. These tiny integration jobs verify execution/cleanup/timeout behavior; they do not validate the Windows runtime model on Mac hardware.
- Actual fitted-model inference and CLI covered recommendation and deadline-driven abstention. Regression cases cover budgets, unsupported profiles, invalid predictions, preference inputs, SI/IEC accounting, whole-config comparisons, hard-guard bypass prevention, artifact/index/grid binding and cross-platform audited-table freezing.
- Worker-error classification and mocked cleanup tests cover ambiguous worker death, explicit memory-limit termination, incidental spill text, and client initialization/shutdown failures.
- The support manifest was regenerated from the audited CSV in a temporary directory and matched the committed bundle exactly. The original runtime model, metadata, metrics, dataset index and 96-row run table were not changed.
- The replay completed **20 declared scenarios across four profiles**, all accepted under the original SLAs. Its CSV hash is checked before reading outcomes. The scenarios reuse historical rows; there are no new main-matrix benchmark measurements or newly fitted models in this change.

## Example: sort/merge under the 13.1 s engine SLA

| Mode | Selected config | Total threads | Total configured decimal GB | Predicted seconds | Upper seconds | Historical median seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Balanced | `w2_t2_1g` | 4 | 2 | 2.292 | 3.869 | 2.459 |
| Resource | `w1_t2_1g` | 2 | 1 | 3.297 | 5.566 | 5.342 |
| Fastest | `w2_t2_2g` | 4 | 4 | 2.146 | 3.622 | 2.221 |

This demonstrates the requested tradeoff: balanced mode chooses a slightly slower prediction than fastest mode with half its configured memory. The historical medians come from three main-v1 repeats per cell and overlap the model's source data. They are not an independent performance estimate, and three repeats do not establish tail reliability.

See `sensitivity.csv` for the complete mode/weight replay, `balanced_examples.json` for all eight candidates per family, and `summary.json` for provenance. Scores from different preference modes are different objectives and must not be compared as if they were the same metric.

## Remaining evidence

A prospective frozen-host repeatability evaluation has not been run. New workload/hardware generalization, a learned failure probability and measured peak-memory prediction are not established. Follow [the validation plan](../../docs/INDEPENDENT_VALIDATION.md) before making those claims. No retraining is necessary for the current policy changes.
