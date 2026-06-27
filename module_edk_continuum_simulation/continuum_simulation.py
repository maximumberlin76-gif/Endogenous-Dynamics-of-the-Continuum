from __future__ import annotations

import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from module_framework_core.framework_core import ContinuumSimulation
from module_framework_core.framework_core import run_demo


__all__ = [
    "ContinuumSimulation",
    "run_demo",
]


if __name__ == "__main__":
    run_demo()
