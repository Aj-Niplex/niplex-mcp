"""
Deploy a local folder to the HidenCloud server via the SFTP bridge —
this is the piece that ties the hermes-bot work into the SFTP layer:
build and test locally, then push the files to the server.

Safety-first:
  - --dry-run first (default is dry-run unless --go is passed)
  - never uploads .env (real secrets), .git, __pycache__, bot-data
  - every write goes through the bridge's path confinement
  - UTF-8 text files only; anything binary is skipped with a warning

Usage:
  python scripts/deploy_to_hidencloud.py                  # dry-run of hermes-bot/
  python scripts/deploy_to_hidencloud.py --go             # actually push
  python scripts/deploy_to_hidencloud.py --src hermes-bot --target hermes-bot --go

Env (must be set where this script runs):
  HIDENCLOUD_SFTP_HOST / HIDENCLOUD_SFTP_PORT / HIDENCLOUD_SFTP_USER /
  HIDENCLOUD_SFTP_PASSWORD   (optional HIDENCLOUD_SFTP_TIMEOUT)
"""

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from integrations.hidencloud_sftp import HidenCloudSFTPBridge  # noqa: E402

SKIP_DIRS = {"__pycache__", "bot-data", ".git", ".venv", "node_modules"}
SKIP_FILES = {".env", ".env.local", ".env.production"}


def _collect(src: str):
    """Return list of relative paths (posix) to UTF-8 text files under src."""
    files = []
    for root, dirs, names in os.walk(src):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            if name in SKIP_FILES or name.endswith((".pyc", ".pyo")):
                continue
            full = os.path.join(root, name)
            rel = os.path.relpath(full, src).replace(os.sep, "/")
            try:
                with open(full, "rb") as fh:
                    fh.read().decode("utf-8")
            except UnicodeDecodeError:
                print(f"  SKIP {rel} (binary, not UTF-8)")
                continue
            files.append(rel)
    return sorted(files)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default=os.path.join(ROOT, "hermes-bot"))
    ap.add_argument("--target", default="hermes-bot")
    ap.add_argument("--go", action="store_true", help="actually push (default is dry-run)")
    args = ap.parse_args()

    if not os.path.isdir(args.src):
        print(f"ERROR: source folder not found: {args.src}")
        sys.exit(2)

    files = _collect(args.src)
    if not files:
        print(f"No files to deploy from {args.src}")
        sys.exit(1)

    print(f"{len(files)} files from {args.src} -> HidenCloud:/{args.target.rstrip('/')}/")
    for rel in files:
        print(f"  {'[push]' if args.go else '[dry]'}  {args.target.rstrip('/')}/{rel}")

    if not args.go:
        print("\nDry run — nothing written. Re-run with --go to actually push.")
        return

    bridge = HidenCloudSFTPBridge()
    if not all([bridge.host, bridge.user, bridge.password]):
        print("ERROR: HIDENCLOUD_SFTP_HOST/USER/PASSWORD not set (and no --go anyway).")
        sys.exit(2)

    ok, failed = 0, []
    for i, rel in enumerate(files, 1):
        full = os.path.join(args.src, rel)
        with open(full, encoding="utf-8") as fh:
            content = fh.read()
        target = f"{args.target.rstrip('/')}/{rel}"
        result = bridge.write_file(target, content)
        if result.startswith("Successfully wrote"):
            ok += 1
            print(f"[{i}/{len(files)}] OK  {target}")
        else:
            failed.append((target, result))
            print(f"[{i}/{len(files)}] FAIL {target}: {result[:120]}")

    print(f"\n{ok} pushed, {len(failed)} failed")
    for t, err in failed[:10]:
        print(f"  FAILED {t}: {err[:120]}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
