# Test suite overview

These tests exercise `main_pipeline.py`'s closed-loop EEG-triggered LIFU
logic — mainly `theta_trigger_loop()`, the function that decides, sample by
sample, whether to fire a sonication (`LIFU_ON`/`LIFU_OFF`) based on a
rolling theta-band signal. Hardware bindings (`openlifu`) aren't required:
every test stubs that package out so `main_pipeline` can be imported and its
decision logic run in isolation, with LSL outlets swapped for simple
in-memory recorders.

Run an individual file directly with `python`, or the pytest-based ones with
`pytest`. Each file's own usage line is in its module docstring.

## `mad_threshold_test.py`

Tests the MAD-based (median absolute deviation) artifact-rejection step in
`theta_trigger_loop`: a sample is compared to the rolling buffer's own
median/MAD, and rejected as an artifact if its z-score exceeds
`mad_threshold`.

Constructs a smooth low-amplitude baseline signal (so the buffer's own
median/MAD stays small and stable) and splices in one large spike at a known
point. Because the spike's z-score against the baseline is known exactly, a
`mad_threshold` set below it must reject the spike, and one set above it must
accept it — checked by comparing the resulting marker stream in each case.
Also confirms a rejected spike is excluded from the rolling buffer entirely
(it doesn't skew later median/MAD calculations), by comparing a run
containing the spike against a spike-free control run and requiring
identical output.

## `num_sonications_test.py`

Tests the sonication counter and cap: `theta_trigger_loop` should increment
its internal count exactly once per `LIFU_ON`, refuse to trigger again once
the count reaches `max_sonications`, and start over at zero on each fresh
call.

Feeds a continuously in-band signal (one that would keep triggering
indefinitely if the cap didn't work) and checks that exactly
`max_sonications` `LIFU_ON` events fire, each paired with a matching
`LIFU_OFF`, and that two independent calls each hit their own cap rather than
accumulating across calls. A separate test checks that once hardware
triggering has started, a downstream failure in publishing telemetry
(pushing the sonication-count marker) doesn't prevent `stop_trigger()` from
being called on the hardware interface.

## `psychopy_stop_marker_test.py`

Tests the start/stop contract between the PsychoPy N-back task
(`N-back_lastrun.py`) and `main_pipeline.py`'s `listen_for_start_stop()`
listener, which gates sonication on whether an experiment is currently
running.

Covers both directions of that contract:
- **Producer side** (source-text check): `N-back_lastrun.py` must push a
  `"STOP_EXPERIMENT"` LSL marker at the same point it marks the PsychoPy
  experiment finished, in both places that can happen (main trial loop and
  thank-you screen) — not just update local PsychoPy state.
- **Consumer side** (live check, real LSL streams): `listen_for_start_stop()`
  must flip `psychopy_running` True on a `"trial_start"` marker and back to
  False on a `"STOP_EXPERIMENT"` marker.

A further end-to-end test drives a live `theta_trigger_loop` alongside the
real listener and confirms a theta crossing that arrives *after*
`STOP_EXPERIMENT` has been received does not sonicate, even though the same
signal is shown (as a positive control, earlier in the same test) to
sonicate normally while the experiment is still running.

## `theta_lifu_validation_test.py`

Tests `theta_trigger_loop`'s trigger-timing behavior, both against a real
recording and against hand-constructed synthetic signals with known correct
output.

- **Recorded-data replay**: feeds the recorded `EEG_gpype` theta channel from
  an `.xdf` session through `theta_trigger_loop` exactly as production would,
  and compares the resulting `LIFU_ON` times ("offline") against the
  `LIFU_ON` times actually logged live in the same session's
  `EEG_LIFU_events` stream ("online"). Includes a timestamp-gap diagnostic
  that flags whether any online/offline mismatch coincides with an
  irregular sample interval in the recording, to distinguish a real decision
  bug from a recording artifact.
- **Constant-above-threshold**: a signal that stays inside the trigger band
  for an entire run should sonicate at exactly the cooldown interval, no more
  and no less often, and never before the experiment-start gate.
- **Oscillating threshold**: a signal that swings in and out of the trigger
  band multiple times per cooldown window should only ever trigger while
  actually in-band, and must still respect the cooldown and start gate.

## `trigger_accuracy_test.py`

Measures and sanity-checks the physical latency between a software `LIFU_ON`
marker and the actual electrical trigger artifact appearing in the recorded
EEG.

For each `LIFU_ON` marker in a session, extracts a window of raw `EEG_gpype`
samples centered on it and looks for the trigger-pickup channel (the last
channel) to cross a MAD-based threshold computed from that window's own
pre-marker baseline. Reports `detected_time - LIFU_ON_time` as the latency.
The `test_recorded_trigger_accuracy` assertion checks that the number of
detected sonications is bounded (≤10) and that every detected latency falls
in a physically sane range (0–500 ms). A `_sweep_all_runs()` helper (run via
`python tests/trigger_accuracy_test.py` directly, not part of the pytest
run) does the same analysis across every participant/run recording and
prints a combined latency summary.

## `list_xdf_streams.py`

Not a test — a small utility script that lists every LSL stream present in
each `.xdf` file under `xdf_data/` (name, type, channel count, sample
count), for inspecting what was actually recorded in a session without
opening it in a notebook.
