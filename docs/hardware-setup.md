# Hardware setup

This document covers the physical setup for a closed-loop LIFU–EEG session and the
installation of the proprietary g.Pipe SDK.

> **Research use only.** This describes a research bench setup, not a clinical procedure.

---

## Bill of materials

| Item | Notes |
|------|-------|
| g.tec EEG amplifier + electrode set | The reference amplifier for this implementation |
| g.Pipe SDK | **User-supplied** — see [Installing the g.Pipe SDK](#installing-the-gpipe-sdk) |
| EEG cap | Sized to the subject |
| Conductive gel | For electrode–scalp impedance |
| OpenLIFU transducer + drive hardware | Per the OpenLIFU platform documentation |
| Acoustic coupling medium | For LIFU–scalp coupling |
| Host computer | Runs acquisition, task, trigger, and LIFU control over LSL |
| 3D Slicer + SlicerOpenLIFU | Only for the default (non-`--hardware-enabled`) run path — see [Installing the vendored Slicer module](#installing-the-vendored-slicer-module) |

---

## Headset + LIFU co-placement

The EEG cap and the LIFU transducer share scalp real estate, so placement has to be
planned so that neither compromises the other:

- Place the EEG cap first and establish acceptable electrode impedances with gel.
- Position the LIFU transducer at the intended target with its coupling medium, taking
  care not to disturb or bridge nearby electrodes.
- Verify that electrodes adjacent to the transducer still read acceptable impedance
  after the transducer and coupling medium are in place — coupling medium contacting an
  electrode is a common source of artefact.
- Confirm the EEG stream is clean (visually and via the artifact-gating flag rate)
  *before* starting calibration.

> [!NOTE]
> Transducer placement is manual and anatomical for this study, however MR-guided targetting is possible. Those are tracked as open enhancement
> items in [`known-issues.md`](known-issues.md) and are design decisions for the
> platform owners, not something this feasibility implementation resolves.

---

## Installing the g.Pipe SDK

The g.Pipe SDK is **proprietary software from g.tec** and **cannot be redistributed or
vendored** in this repository. You must obtain and install it yourself under your own
license from g.tec.

1. Obtain the g.Pipe SDK and license from g.tec.
2. Install it per g.tec's instructions for your platform.
3. Make the SDK importable in the environment where you run this pipeline (e.g. on the
   `PYTHONPATH`, or installed into the same virtual environment).
4. Verify it's importable:

   ```bash
   python -c "import gpype"
   ```

   `src/openlifu_closed_loop/main_pipeline.py` (the migrated pipeline) imports `gpype`
   directly and unconditionally today — there is no separate acquisition adapter module
   to check yet (see [`known-issues.md`](known-issues.md#current-implementation-status)).

If you use a **different amplifier**, you do not need the g.Pipe SDK, but you will need
to adapt `main_pipeline.py`'s g.Pype-specific pipeline construction (`build_pipeline()`)
to your hardware directly — the acquisition-interface extension point described in
[`architecture.md`](architecture.md#module-boundaries) is the intended design, not yet
how the migrated code is structured. Adapter contributions are welcome regardless.

---

## Installing the vendored Slicer module

`main_pipeline.py`'s default run path (without `--hardware-enabled`) triggers and stops
sonication over TCP against a listener running inside 3D Slicer's
`OpenLIFUSonicationControl` module. One file from that module, modified specifically for
this experiment, is vendored in
[`third_party/SlicerOpenLIFU/`](../third_party/SlicerOpenLIFU) — see that directory's
[`README.md`](../third_party/SlicerOpenLIFU/README.md) for exactly what's modified and
the AGPL-3.0 licensing detail (separate from this repository's own Apache-2.0 license;
see [`NOTICE`](../NOTICE)). Everything else — `OpenLIFULib`, the rest of
`OpenLIFUSonicationControl/`, every other module — comes from a normal SlicerOpenLIFU
install; none of it is vendored here.

1. Install 3D Slicer and the upstream
   [SlicerOpenLIFU](https://github.com/OpenwaterHealth/SlicerOpenLIFU) extension per its
   own [releases](https://github.com/OpenwaterHealth/SlicerOpenLIFU/releases).
2. In that installation, replace `OpenLIFUSonicationControl/OpenLIFUSonicationControl.py`
   with the version in `third_party/SlicerOpenLIFU/OpenLIFUSonicationControl/`.
3. Open Slicer with the `OpenLIFUSonicationControl` module loaded, with a device connected
   and a solution sent to hardware, before starting `main_pipeline.py`.

If you only ever run with `--hardware-enabled` (headless, no Slicer GUI), none of this is
needed.

---

## Sanity check before a session

- [ ] EEG stream present on LSL and timestamps advancing
- [ ] Electrode impedances acceptable, including electrodes adjacent to the transducer
- [ ] Artifact-gating flag rate low on resting subject
- [ ] Task (PsychoPy 2-back) launches and publishes markers to LSL
- [ ] LIFU control reachable; run `main_pipeline.py --sham-run` once to confirm the
      trigger→LIFU path logs decisions without issuing sonications (`--sham-run` skips
      hardware init and the Slicer auto-run trigger; note this is `main_pipeline.py`'s
      own flag, not the scaffold's `--dry-run`, which isn't wired to anything yet — see
      [`known-issues.md`](known-issues.md#current-implementation-status))
- [ ] Logging is writing to the intended output location
