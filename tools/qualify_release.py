#!/usr/bin/env python3
"""Qualify a deterministic TokaKV package archive and replay its quickstart."""

from __future__ import annotations

import argparse
import hashlib
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_INPUTS = ("package.tk", "lib", "tests", "README.md", "LICENSE")
EXPECTED_VERSION = "1.0.0-rc.10"
PACKAGE_VERSION = "0.1.2"


class QualificationError(RuntimeError):
    pass


def run(command: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise QualificationError(
            "command failed: %s\nstdout:\n%s\nstderr:\n%s"
            % (" ".join(command), result.stdout, result.stderr)
        )
    return result


def copy_package_inputs(destination: Path) -> None:
    destination.mkdir(parents=True)
    for relative in PACKAGE_INPUTS:
        source = ROOT / relative
        target = destination / relative
        if source.is_dir():
            shutil.copytree(
                source,
                target,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
            )
        else:
            shutil.copy2(source, target)


def verify_readme_source_parity() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    marker = "```toka\n"
    start = readme.find(marker)
    if start < 0:
        raise QualificationError("README has no Toka quickstart source block")
    start += len(marker)
    end = readme.find("\n```", start)
    if end < 0:
        raise QualificationError("README quickstart source block is unterminated")
    documented = readme[start:end].rstrip() + "\n"
    canonical = (ROOT / "examples" / "ten-minute-tour" / "src" / "main.tk").read_text(
        encoding="utf-8"
    )
    if documented != canonical:
        raise QualificationError("README quickstart source differs from the verified example")


def build_archive(toka: Path, sdk: Path, producer: Path) -> Path:
    env = os.environ.copy()
    env["TOKA_LIB"] = str(sdk / "lib")
    env.pop("TOKA_REGISTRY_URL", None)
    env.pop("TOKA_REGISTRY_PUBLISH_TOKEN", None)
    run([str(toka), "publish"], cwd=producer, env=env)
    archive = producer / f"tokakv-{PACKAGE_VERSION}.tar.gz"
    if not archive.is_file():
        raise QualificationError(f"package archive was not created: {archive}")
    return archive


def make_catalog(server_root: Path, archive: Path, digest: str, port: int) -> None:
    shutil.copy2(archive, server_root / archive.name)
    catalog = {
        "schema_version": 1,
        "lastUpdated": "2026-09-01T00:00:00Z",
        "totalPackages": 1,
        "totalDownloads": 0,
        "packages": [
            {
                "name": "tokakv",
                "kind": "library",
                "version": PACKAGE_VERSION,
                "latest_version": PACKAGE_VERSION,
                "installable": True,
                "versions": [
                    {
                        "version": PACKAGE_VERSION,
                        "published_at": "2026-09-01T00:00:00Z",
                        "tarball_url": f"http://127.0.0.1:{port}/{archive.name}",
                        "sha256": digest,
                        "source": {
                            "repository": "https://github.com/tokalang/tokakv",
                            "tag": f"v{PACKAGE_VERSION}",
                        },
                    }
                ],
                "description": "A durable MVCC LSM key-value engine for Toka.",
                "downloads": 0,
                "repository": "github.com/tokalang/tokakv",
                "license": "Apache-2.0",
                "author": "tokalang",
            }
        ],
    }
    (server_root / "catalog.json").write_text(
        json.dumps(catalog, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def replay_archive(toka: Path, server_root: Path, archive: Path, digest: str) -> None:
    handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(  # noqa: E731
        *args, directory=str(server_root), **kwargs
    )
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = int(server.server_address[1])
    make_catalog(server_root, archive, digest, port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        env = os.environ.copy()
        env["TOKA"] = str(toka)
        env["TOKA_REGISTRY_URL"] = f"http://127.0.0.1:{port}"
        result = run([str(ROOT / "tools" / "verify_quickstart.sh")], cwd=ROOT, env=env)
        if "[PASS] RC10 TokaKV quickstart" not in result.stdout:
            raise QualificationError("archive quickstart did not report success")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sdk", type=Path, required=True, help="Extracted Toka RC10 SDK root")
    parser.add_argument("--skip-suite", action="store_true", help="Skip the 53-stage sanitizer and diagnostic suite")
    parser.add_argument("--output", type=Path, help="Copy the qualified deterministic archive here")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sdk = args.sdk.resolve()
    toka = sdk / "bin" / "toka"
    tokac = sdk / "bin" / "tokac"
    if not toka.is_file() or not tokac.is_file():
        raise QualificationError(f"invalid SDK root: {sdk}")

    env = os.environ.copy()
    env["TOKA_LIB"] = str(sdk / "lib")
    version = run([str(toka), "--version"], cwd=ROOT, env=env).stdout.strip()
    if EXPECTED_VERSION not in version:
        raise QualificationError(f"expected {EXPECTED_VERSION}, got: {version}")
    print(f"[PASS] SDK identity: {version}")

    verify_readme_source_parity()
    print("[PASS] README and verified quickstart source are byte-identical")

    if not args.skip_suite:
        suite_env = env.copy()
        suite_env["TOKA_SDK"] = str(sdk)
        suite_env["TOKA_EXPECT_VERSION"] = EXPECTED_VERSION
        run(["python3", "tests/qualify_package.py"], cwd=ROOT, env=suite_env)
        print("[PASS] 53-stage package qualification")

    with tempfile.TemporaryDirectory(prefix="tokakv-release-") as directory:
        work = Path(directory)
        first_root = work / "first"
        second_root = work / "second"
        server_root = work / "registry"
        copy_package_inputs(first_root)
        copy_package_inputs(second_root)
        server_root.mkdir()

        first_archive = build_archive(toka, sdk, first_root)
        second_archive = build_archive(toka, sdk, second_root)
        first_bytes = first_archive.read_bytes()
        second_bytes = second_archive.read_bytes()
        if first_bytes != second_bytes:
            raise QualificationError("two clean package builds produced different archive bytes")
        digest = hashlib.sha256(first_bytes).hexdigest()
        print(f"[PASS] deterministic archive SHA-256: {digest}")

        replay_archive(toka, server_root, first_archive, digest)
        print("[PASS] archive-only registry resolution and two-process recovery replay")

        if args.output:
            output = args.output.resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(first_archive, output)
            print(f"[PASS] qualified archive copied to {output}")


if __name__ == "__main__":
    try:
        main()
    except QualificationError as error:
        raise SystemExit(f"[FAIL] {error}")
