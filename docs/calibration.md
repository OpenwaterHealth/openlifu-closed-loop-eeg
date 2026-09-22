# Calibration

> [!NOTE]
> This document describes the **intended** per-session calibration design. As migrated,
> `main_pipeline.py` computes `theta_z` against a **fixed, hardcoded `MU`/`SIGMA`**
> (derived once, offline, via `EEG_calibration.py`, then hand-substituted into
> `main_pipeline.py`'s constants) rather than the fresh `baseline_mean`/`baseline_std`
> this document describes computing each session. See
> [`known-issues.md`](known-issues.md#current-implementation-status).

The trigger gate acts on a **theta-band Z-score** — how far the subject's current theta
power is from *their own* resting baseline, in standard-deviation units. This document
describes how that baseline is collected and how the Z-score is computed online.

Using a per-subject Z-score (rather than an absolute power threshold) is what makes the
trigger threshold (`theta_z > 1.5`) meaningful across subjects with different baseline
theta amplitudes.

---

## 1. Baseline collection (100 s)

At the start of every session, the subject sits at rest while the pipeline collects a
**100-second baseline** of theta-band power. During this window:

- EEG is passed through a real time processing (notch, bandpass, power, moving average, z-score)
- Samples still pass through the artifact-gating stage, so contaminated segments do not
  corrupt the baseline statistics.

From the collected baseline the pipeline computes the two statistics the Z-score needs:

- `baseline_mean` — mean theta-band power over the clean baseline window
- `baseline_std` — standard deviation of theta-band power over the same window

---

## 2. Online Z-score

During the closed-loop task, theta-band power is estimated on the incoming (gated) EEG
and converted to a Z-score against the baseline:

```
theta_z = (theta_power_now - baseline_mean) / baseline_std
```

This `theta_z` is the value the trigger gate tests:

- **Condition 3** — trigger: `theta_z > 1.5`
- **Condition 4** — safety ceiling: `theta_z < 10`

A Z-score at or above the ceiling (10) is treated as an implausible or artefactual
excursion, and the gate refuses to sonicate rather than acting on it. See
[`protocol.md`](protocol.md) for the full six-condition table.

---

## 3. Practical notes

- **Baseline quality gates everything downstream.** If the artifact-gating flag rate is
  high during the 100 s window, the baseline is untrustworthy — re-check electrode
  impedance and coupling (see [`hardware-setup.md`](hardware-setup.md)) and recalibrate.
- **The synthetic fixture does not currently exercise this path end-to-end.**
  [`../fixtures/synthetic_theta.py`](../fixtures/synthetic_theta.py) streams a synthetic
  theta-band signal onto LSL, but `main_pipeline.py`'s acquisition step is hardwired to
  a real g.tec amplifier (`gp.BCICore8()`) — nothing in this repository currently
  consumes the synthetic stream through the baseline → Z-score → trigger path. See
  [`known-issues.md`](known-issues.md#current-implementation-status).
