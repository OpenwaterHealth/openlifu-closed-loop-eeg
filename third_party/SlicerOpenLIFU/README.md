# SlicerOpenLIFU (one modified file, vendored)

This directory vendors **exactly one file**,
[`OpenLIFUSonicationControl/OpenLIFUSonicationControl.py`](OpenLIFUSonicationControl/OpenLIFUSonicationControl.py),
modified from Openwater's
[SlicerOpenLIFU](https://github.com/OpenwaterHealth/SlicerOpenLIFU) 3D Slicer extension.
This is **not** a copy of the extension, or even of the rest of that one module — install
SlicerOpenLIFU normally from its own [releases](https://github.com/OpenwaterHealth/SlicerOpenLIFU/releases)
for everything else (`OpenLIFULib`, the module's own `CMakeLists.txt`/`Resources`/`Testing`,
every other module). Diffed against the commit that first added it to the developer's
personal repo, only this one file differs from upstream — everything else in
`OpenLIFUSonicationControl/` and all of `OpenLIFULib` (which this file imports from) is
byte-identical to what a normal SlicerOpenLIFU install already gives you, so vendoring
those here would be pure redundancy with no changes to show for it.

## Why this is here

`src/openlifu_closed_loop/main_pipeline.py`'s default run path (i.e. without
`--hardware-enabled`) does not talk to LIFU hardware directly. Instead it triggers and
stops sonication by sending commands over a TCP socket to a remote-run listener running
inside Slicer's `OpenLIFUSonicationControl` module (see `trigger_slicer_run()` /
`trigger_slicer_stop()` in `main_pipeline.py`). That listener, and the retry/safety
behavior around it, were added to `OpenLIFUSonicationControl.py` specifically for this
closed-loop EEG experiment — they are not part of upstream SlicerOpenLIFU. Running the
pipeline's default mode requires this modified module loaded in a working Slicer +
SlicerOpenLIFU installation.

## How to use this

1. Install 3D Slicer and the upstream SlicerOpenLIFU extension normally, per
   [SlicerOpenLIFU's own instructions](https://github.com/OpenwaterHealth/SlicerOpenLIFU#readme).
2. In that installation, replace `OpenLIFUSonicationControl/OpenLIFUSonicationControl.py`
   with the version in this directory. Nothing else needs to change.

## What's modified vs. upstream

Changes are specific to this experiment (closed-loop EEG-triggered sonication) and are
not intended to be contributed back upstream. Notable additions:

- A TCP remote-run listener (`run`/`stop` commands) that `main_pipeline.py` drives.
- Retries around hardware trigger calls to survive transient UART timeouts.
- An `absolute_theta_value` safety check.

For the exact diff, see the commit history of `OpenLIFUSonicationControl.py` in
[`janetshin8030/OW_closedloop`](https://github.com/janetshin8030/OW_closedloop) (the
developer's personal repository), starting from
`688d68d open slicer + new sonication control lsl`.

## Requirements and limitations

This code runs **inside 3D Slicer only** (`import slicer`, `qt`, `vtk` are Slicer's
embedded runtime, not pip-installable packages) and is not exercised by this
repository's own test suite or CI — it cannot be. There is no automated verification
that this file still matches whatever SlicerOpenLIFU version you install; if upstream's
`OpenLIFUSonicationControl.py` has diverged significantly since this was last synced,
re-applying these changes by hand may be necessary instead of a straight file swap.

## License

**AGPL-3.0**, inherited from upstream SlicerOpenLIFU — see [`LICENSE`](LICENSE) in this
directory. This is separate from and does not change the Apache-2.0 license covering the
rest of this repository (see the top-level [`LICENSE`](../../LICENSE) and
[`NOTICE`](../../NOTICE)). `main_pipeline.py` communicates with this code only over a TCP
socket (a process boundary, not a Python import), which is the relevant fact for
combined-work analysis, but that analysis has not been performed here — see `NOTICE` for
the same caveat already applied to `openlifu-python`.
