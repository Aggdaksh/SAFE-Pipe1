# Regression review after the balanced advisor change

Date: 2026-10-27. Compared advisor commit `c3e328a` with the original Windows checkpoint `c164657`, then repeated compatibility checks after the model-loading fix described below.

## Result

No unintended change was found in the tested legacy recommendations, model predictions, configuration definitions or recorded benchmark evidence. A model-file newline portability problem was found and fixed without retraining or rewriting the model artifact. The final complete suite passed **79 tests in 7.38 seconds** on the coding Mac, including tiny live Dask execution/timeout tests and two new model newline regressions.

## Baseline comparisons

- Extracted `c164657` to a temporary directory and used the same Python environment for both snapshots. Confirmed each process imported its own snapshot's source.
- Compared 18 original CLI scenarios: four profile commands, all four families at their original/tight/relaxed deadlines, the configuration grid, and manual recommendation from the existing example estimates. Outputs matched after excluding the intentional new `guard_pass` field and clarified decision-reason text. All selected configurations and abstention decisions matched.
- The original point predictions, upper estimates, costs and existing candidate fields matched for all 32 family/configuration combinations. This comparison passed again after the newline fix.
- The 12 original tracked files under `artifacts/`, `configs/` and `data/curated/` were byte-identical to the baseline. The new support manifest is an addition. Original model artifacts, the 96-run CSV, split, deadlines and grid remain unchanged.
- Independent review compared 1,000 deterministic generated legacy optimizer cases against the original implementation: decisions matched apart from the clarified reason text. `guard_pass` defaults to true for old serialized inputs.
- Reviewed changes to cleanup and failure classification. Cleanup now runs when client initialization/shutdown fails. Generic worker death or spill mentions no longer establish an OOM/spill-abort; this is an intentional label correction. An explicit failed guard cannot be bypassed with `failure_limit=1`.

## Issue found and repaired

A CRLF-converted copy of the LightGBM text model passed the advisor's newline-normalized artifact checks but caused the native `model_file` loader to abort in the portability probe. The model text contains tree byte lengths, which newline conversion changes. The original loader was also susceptible; the new artifact checks exposed this inconsistency.

`RuntimePredictor` now reads UTF-8 text with Python's universal-newline decoding and passes the restored LF text through LightGBM's `model_str` interface. A model-specific `.gitattributes` rule also keeps model files LF in future Git checkouts. Neither step edits the saved model coefficients or retrains it.

New automated tests establish:

1. Predictions from a CRLF model copy exactly match the original native file loader on a known-LF copy for all 96 recorded rows, including every upper estimate. The copied file remains unchanged. The native-load regression runs in a subprocess so a recurrence cannot terminate the whole test suite.
2. A copied artifact directory and profile index converted to CRLF produce the same complete advisor report as LF files, except the raw-file hashes that correctly reflect different bytes.

## Scope of the assurance

The complete suite was executed with local scheduler socket permission. This verifies tiny Dask behavior and the software/model compatibility above; it does not repeat the 96-job Windows benchmark or prove performance on new workloads. CRLF compatibility was simulated with real converted files on macOS, not a fresh native Windows test run. The new balanced mode can intentionally choose a different configuration from the historical resource-only command; the original command's tested outputs remain preserved.
