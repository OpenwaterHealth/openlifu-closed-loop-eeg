"""Closed-loop LIFU–EEG reference implementation (research use only).

Modules:
    triggers        — the six-condition safety-critical gate
    main_pipeline    — acquisition, artifact gating, task control, LIFU
                        sonication, and logging, migrated in as-is (not yet
                        split into separate modules)
    EEG_calibration  — standalone script to derive the theta Z-score's MU/SIGMA

See docs/architecture.md for the original module boundaries this may still be
split into.
"""

__version__ = "0.1.0"
