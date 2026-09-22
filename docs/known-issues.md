# Known issues

This project ships as a **working, documented, imperfect reference implementation.** The
imperfections are listed here honestly and completely — a researcher is better served by
an accurate limitations list than by a polished artifact that hides its edges, and these
items are exactly what generate the first outside contributions.

Items below are mirrored as GitHub issues where an actionable unit of work exists. Labels
in parentheses indicate issue triage intent.

---

## Current implementation status

The developer's real pipeline code has been migrated in, but **not yet split** into the
module boundaries described in [`architecture.md`](architecture.md). Concretely:

- `src/openlifu_closed_loop/main_pipeline.py` and `EEG_calibration.py` are the original
  scripts — acquisition, artifact gating, task control, LIFU sonication, and logging all
  still live together in `main_pipeline.py` rather than in separate `acquisition/` /
  `artifact_gating/` / `task/` / `lifu/` / `logging/` modules.
- `triggers/` is the one module that *is* split out and wired up as designed — a
  separate, tested implementation of the six-condition gate. `main_pipeline.py`'s own
  inline trigger check has been **reconciled with it**: the same threshold values
  (imported from `triggers/conditions.py` as defaults), the same comparison semantics,
  and condition 1 ("baseline complete") now means the same thing in both places —
  `BASELINE_SECONDS` of real elapsed time, not a sample count. The two checks remain two
  separate pieces of code, not one shared function call, because `main_pipeline.py`'s
  test suite relies on overriding individual thresholds per-call (e.g. `cooldown_time=0.0`
  to run fast), which `triggers/conditions.py`'s fixed module constants don't support.
- `theta_z` itself is computed against a **fixed, hardcoded `MU`/`SIGMA`** in
  `main_pipeline.py` (baked into the g.Pype pipeline's `theta_z_eq`), not the fresh
  per-session `baseline_mean`/`baseline_std` that [`calibration.md`](calibration.md)
  describes computing from each session's own 100 s baseline. `EEG_calibration.py` is how
  those two numbers were originally derived (presumably once, offline) and manually
  substituted in — the per-session computation `calibration.md` describes is not
  implemented yet.
- `python -m openlifu_closed_loop --source synthetic --dry-run` (the scaffold's CLI
  entrypoint) does not yet call into `main_pipeline.py` — it still raises
  `NotImplementedError` by design. Run `main_pipeline.py` directly instead (its own CLI
  is `--hardware-enabled` / `--sham-run`, not `--source`/`--dry-run` — the two entrypoints
  have different flags).
- **`main_pipeline.py` has no synthetic-source mode.** `build_pipeline()` unconditionally
  constructs `gp.BCICore8()` (the real g.tec amplifier source) — there is no branch that
  points it at `fixtures/synthetic_theta.py` instead. So even once the CLI above is wired
  up, running the real pipeline end-to-end will still require `gpype` and a connected
  amplifier; the synthetic fixture and the trigger-condition tests
  (`pytest tests/test_trigger_conditions.py`) are the only currently-standalone,
  no-hardware ways to exercise any part of this system.

Splitting the code into the designed module boundaries, implementing per-session
baseline calibration in place of the fixed `MU`/`SIGMA`, and giving `main_pipeline.py` a
synthetic-source mode, are tracked as future work.

---

## Documented technical findings

### Slicer vs. direct-Python trigger latency (~250 ms delta)
The end-to-end trigger latency measured through the 3D Slicer GUI path is **~422 ms**,
versus **~170 ms** running the same logic directly in Python — a reproducible ~250 ms
delta attributable to the Slicer–Python bridge, not to the trigger logic itself.

- This is a real, reproducible measurement and arguably the most interesting technical
  output of the study.
- It is a **Slicer–Python-bridge** characteristic, not an Openwater defect. It is worth
  reporting to the Slicer community as a standalone technical observation, separate from
  this repository.
- See [`../notebooks/latency_analysis.ipynb`](../notebooks/latency_analysis.ipynb) for
  the measurement method.
- Tracked as [#1](https://github.com/OpenwaterHealth/openlifu-closed-loop-eeg/issues/1)
  (`needs-triage`, `area: slicer`, `help wanted`).

---

## Scope limitations (by design)

These are not bugs — they are things this feasibility implementation deliberately does
**not** do. Whether to add them is a design decision for the platform owners.

- **No MRI-guided targeting.** Transducer placement is manual/anatomical. Tracked as
  [#3](https://github.com/OpenwaterHealth/openlifu-closed-loop-eeg/issues/3)
  (`needs-design`) — scope to be ruled on before it is labeled beginner-friendly.
- **No acoustic skull correction** in this pipeline. Tracked as
  [#4](https://github.com/OpenwaterHealth/openlifu-closed-loop-eeg/issues/4)
  (`needs-design`).
- **Software guardrails against a mid-session shutdown.** Hardening the pipeline against
  an abrupt host/process shutdown mid-session is not yet implemented. Tracked as
  [#5](https://github.com/OpenwaterHealth/openlifu-closed-loop-eeg/issues/5) (`help wanted`).

---

## Requested features

- **`build_pipeline()` needs to become a swappable acquisition interface before a
  non-g.tec amplifier adapter (#7) is actually possible.** Right now the g.Pype-specific
  signal graph — `BCICore8` source, notch/bandpass filters, power, moving average, the
  `theta_z_eq` Z-score equation, decimation, and the `LSLSender` that publishes the
  `EEG_gpype` stream — is all built inline in `main_pipeline.py`'s `build_pipeline()`.
  The *downstream* logic is actually already device-agnostic: `theta_trigger_loop()`
  takes any `sample_source` generator of `(theta_val, ts)` pairs (it defaults to
  `theta_sample_source()`, which just reads the `EEG_gpype` LSL stream by name), and the
  MAD gate and trigger conditions never touch `gpype` directly. So a hot-swappable
  acquisition layer doesn't require touching the trigger/artifact-gating logic at
  all — it means extracting `build_pipeline()`'s g.Pype-specific graph behind an
  interface (raw samples in, an LSL stream with the same channel layout as
  `ROUTER_INPUT_CHANNELS` and a theta-Z channel out), so a different amplifier's adapter
  can be swapped in without `theta_trigger_loop()` or anything downstream changing.
  This is a more concrete, currently-accurate version of what `acquisition/`
  (removed from `src/` during this migration — see git history) was meant to be.
  Prerequisite for **Non-g.tec amplifier adapter**, tracked as
  [#7](https://github.com/OpenwaterHealth/openlifu-closed-loop-eeg/issues/7) (`help wanted`).
- **Video-stream marker synchronization.** Synchronizing a video stream's markers with
  the LSL clock, to align behavioral video with EEG/sonication events. Tracked as
  [#6](https://github.com/OpenwaterHealth/openlifu-closed-loop-eeg/issues/6)
  (`good first issue`).

---

## Bug list

> [!NOTE]
> **This section is authored by the original developer (Janet).** The entries below are
> drafted from bugs already found and described (in some cases already fixed) during
> development, plus direct verification against the migrated code — not reconstructed
> from memory. Review before filing: each should become its own GitHub issue (`bug`) on
> this repo, attributed to Janet.

- [ ] **The N-back trial-conditions file must be changed by hand before each run, and
  is easy to silently overwrite back to the wrong one.**
  `n-back-task-with-visual-stimuli/N-back_lastrun.py` loads its trial order from a
  hardcoded filename:
  ```python
  trialList=data.importConditions('trial_4.xlsx'),
  ```
  `N-back_lastrun.py` is a PsychoPy Builder **"last run" export** — it's regenerated from
  `N-back.psyexp` every time the task is launched from the Builder GUI, and the Builder's
  own saved `conditionsFile` setting is also `trial_4.xlsx`. So editing
  `N-back_lastrun.py` by hand to point at a different `trial_N.xlsx` for a new
  participant/run only sticks until the next time someone opens and runs the task from
  Builder — that regenerates the file and silently reverts the trial file back to
  whatever `N-back.psyexp` has saved, overwriting the manual change with no warning.
  Expected: the trial-conditions file should be selected per-run (e.g. via
  `expInfo`/a run parameter) rather than hardcoded in a generated file that gets
  clobbered by the Builder's own export step.

- [ ] **`trigger_slicer_run()` trusts Slicer's TCP acknowledgment at face value.** In
  `main_pipeline.py`, `trigger_slicer_run()` treats a `"ok"` reply from Slicer's
  remote-run listener as confirmation the sonication run actually started:
  ```python
  if reply == "ok":
      logger.info("Triggered Slicer's Run button over the remote-run listener.")
      return True
  ```
  If the listener acknowledges receipt of the command before Slicer has actually
  validated the solution and started the run (asynchronous on Slicer's Qt thread), a
  caller here can report success on a run that was rejected or never started. The
  listener itself lives in `OpenLIFUSonicationControl.py`, vendored in
  [`third_party/SlicerOpenLIFU/`](../third_party/SlicerOpenLIFU) but running inside a
  separate Slicer process, not imported by this pipeline — the ack-then-validate
  ordering would need to change on that side (`_RemoteRunServer`/`remote_run()` in that
  file) for a full fix, but `trigger_slicer_run()`'s trust of the premature ack is worth
  tracking here regardless.

- [ ] **Upstream `openlifu` bug: intermittent hardware timeouts on longer sessions.**
  `openlifu`'s `LIFUUart._read_data()` assumes one `serial.read()` call contains exactly
  one packet and unconditionally clears its buffer after parsing the first one. When two
  packets land in the same read (more likely the longer a session runs, as async TX
  status traffic accumulates), the second is silently dropped — surfacing as
  `"Timeout waiting for response to packet ID N"` on calls this pipeline makes directly
  (`start_trigger()`, `stop_trigger()`, `turn_hv_on()`, hardware status queries in
  `init_hardware()`). Not fixable in this repository (the bug is in the `openlifu`
  package, version 0.20.0 at time of observation) — documented here as an operational
  risk: expect occasional trigger timeouts in longer sessions, not necessarily a bug in
  this pipeline's own logic. Consider wrapping the affected calls in this pipeline with a
  try/except that logs and degrades gracefully rather than propagating, until the
  upstream fix lands.

---

## A note on triage

Design-dependent items (`needs-design`) should **not** be labeled `good first issue`
until scope has been ruled on by the platform owners — otherwise a new contributor can
sink effort into a direction that has not been decided.
