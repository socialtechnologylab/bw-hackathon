"""Download the bw-hackathon-data release tarball and lay parquets into
tasks/<id>/data/.

Idempotent: skips work if all 3 task parquet triplets are already present.
Pinned to a specific release tag — refreshing requires a code change here.
The tarball contains parquets + per-task READMEs only; it does NOT carry
ground-truth labels (those live on the scoring endpoint).
"""

from __future__ import annotations

import hashlib
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

import httpx


RELEASE_URL = (
    "https://github.com/socialtechnologylab/bw-hackathon-data"
    "/releases/download/v1.3.0/bw-hackathon-data-2026-05-13-participant.tar.gz"
)
EXPECTED_SHA = "86ec432ae0c191882bf33c810699980c0d9c32856cca314f80106b3bd02b48b2"

REPO_ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = REPO_ROOT / "tasks"
EXPECTED_TASKS = (
    "solar-1d-ahead",
    "wind-2h-ahead",
    "demand-1d-ahead-test",
)


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _all_parquets_present() -> bool:
    needed = [
        TASKS_DIR / t / "data" / fname
        for t in EXPECTED_TASKS
        for fname in ("X_train.parquet", "y_train.parquet", "X_test.parquet")
    ]
    return all(p.exists() for p in needed)


def main() -> None:
    if _all_parquets_present():
        print("all 3 task parquets already present — skipping download")
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        tarball = tmp / "release.tar.gz"

        print(f"fetching {RELEASE_URL}")
        with httpx.stream("GET", RELEASE_URL, timeout=120.0, follow_redirects=True) as resp:
            resp.raise_for_status()
            with tarball.open("wb") as out:
                for chunk in resp.iter_bytes(1 << 20):
                    out.write(chunk)

        sha = _sha256_of(tarball)
        if sha != EXPECTED_SHA:
            print(
                f"ERROR: SHA mismatch.\n  got      {sha}\n  expected {EXPECTED_SHA}\n"
                "Refusing to extract. Re-pull or update EXPECTED_SHA after a release refresh.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Extract only participant/<task>/* into tasks/<task>/data/.
        with tarfile.open(tarball, "r:gz") as tar:
            extracted = 0
            for m in tar.getmembers():
                if not m.isfile():
                    continue
                # m.name looks like 'bw-hackathon-data-YYYY-MM-DD/participant/<task>/<file>'
                if "/participant/" not in m.name:
                    continue
                rel = m.name.split("/participant/", 1)[1]
                # rel is '<task>/<file>'
                if "/" not in rel:
                    continue
                task_id, fname = rel.split("/", 1)
                target = TASKS_DIR / task_id / "data" / fname
                target.parent.mkdir(parents=True, exist_ok=True)
                extracted_handle = tar.extractfile(m)
                if extracted_handle is None:
                    continue
                with target.open("wb") as out:
                    shutil.copyfileobj(extracted_handle, out)
                extracted += 1

    print(f"✓ extracted {extracted} files into {TASKS_DIR}/<task>/data/")


if __name__ == "__main__":
    main()
