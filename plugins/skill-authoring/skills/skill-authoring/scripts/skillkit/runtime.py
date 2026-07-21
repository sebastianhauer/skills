"""Runtime environment checks; importing this module enforces them."""

import sys

# Policy floor: oldest interpreter on supported platforms (macOS CLT
# and RHEL 9 ship 3.9); the code itself only needs 3.6. Interpreters
# below 3.6 die at parse time on f-strings in the entry scripts, which
# no runtime guard can intercept.
MIN_PYTHON = (3, 9)

if sys.version_info < MIN_PYTHON:
    sys.exit(
        "skill-authoring scripts require Python %d.%d+ (running %d.%d)"
        % (MIN_PYTHON + sys.version_info[:2])
    )
