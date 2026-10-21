#!/usr/bin/env python3
"""Build-time, checksum-pinned Node runtime for the existing Python service."""
import hashlib
import os
from pathlib import Path
import platform
import subprocess
import tarfile
import tempfile
from urllib.request import urlopen

BASE = Path(__file__).resolve().parents[1]
VERSION = "22.23.4"
SHA256 = "1805bcd35e6815559bd2eb97db438d3fdb0eb3a5e6a977b7c1badca76337e9ce"


def main():
    if platform.system() != "Linux" or platform.machine() not in {"x86_64", "amd64"}:
        raise SystemExit("This build installer targets the existing Linux x64 service.")
    runtime = BASE / ".runtime"
    runtime.mkdir(exist_ok=True)
    node = runtime / f"node-v{VERSION}-linux-x64"
    if not (node / "bin/node").is_file():
        with tempfile.TemporaryDirectory(dir=runtime) as temporary:
            archive = Path(temporary) / "node.tar.xz"
            with urlopen(
                f"https://nodejs.org/dist/v{VERSION}/node-v{VERSION}-linux-x64.tar.xz",
                timeout=120,
            ) as response:
                archive.write_bytes(response.read(64 * 1024**2 + 1))
            if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
                raise SystemExit("Node runtime checksum mismatch.")
            with tarfile.open(archive) as package:
                package.extractall(runtime, filter="data")
    link = runtime / "node"
    if link.is_symlink():
        link.unlink()
    link.symlink_to(node.name, target_is_directory=True)
    env = {**os.environ, "PATH": str(node / "bin") + os.pathsep + os.environ["PATH"]}
    subprocess.run(
        [
            str(node / "bin/npm"),
            "ci",
            "--omit=dev",
            "--ignore-scripts",
            "--no-audit",
            "--no-fund",
        ],
        cwd=BASE / "tools/virtual_tours",
        env=env,
        check=True,
    )
    subprocess.run([str(node / "bin/node"), "--version"], check=True)


if __name__ == "__main__":
    main()
