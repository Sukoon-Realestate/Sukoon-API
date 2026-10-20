"""Locate relocated Aptfile libraries for codec processes, not the web process."""

import os
import shutil
from pathlib import Path


def codec_environment(executable):
    binary = shutil.which(str(executable))
    if binary is None:
        return None
    root = Path(binary).resolve().parent.parent / "lib"
    candidates = [root]
    for architecture in sorted(root.glob("*-linux-gnu")):
        candidates.extend(
            [architecture]
            + [architecture / part for part in ("pulseaudio", "blas", "lapack")]
        )
    paths = [str(path) for path in candidates if path.is_dir()]
    if not paths:
        return None
    env = os.environ.copy()
    inherited = env.get("LD_LIBRARY_PATH", "")
    env["LD_LIBRARY_PATH"] = ":".join(paths + ([inherited] if inherited else []))
    return env
