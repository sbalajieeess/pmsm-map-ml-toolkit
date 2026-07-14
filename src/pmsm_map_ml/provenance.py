from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_commit(repo_root: str | Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(repo_root),
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() or None


def build_manifest(input_path: str | Path, repo_root: str | Path) -> dict[str, object]:
    source = Path(input_path).resolve()
    return {
        "input": str(source),
        "input_sha256": sha256_file(source),
        "git_commit": git_commit(repo_root),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
    }


def write_json(path: str | Path, payload: object) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output
