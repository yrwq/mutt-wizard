from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from mutt_wizard.config import default_sasl_path, ensure_dirs, get_paths


def _channels_from_mbsync(config_path: Path) -> list[str]:
    if not config_path.exists():
        return []
    channels = []
    for line in config_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Channel "):
            parts = line.split()
            if len(parts) >= 2:
                channels.append(parts[1])
    return channels


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mailsync")
    parser.add_argument("accounts", nargs="*")
    parser.add_argument("--no-notmuch", action="store_true")
    parser.add_argument("--sasl-path", help="Path to SASL plugin directory")
    args = parser.parse_args(argv)

    paths = get_paths()
    ensure_dirs(paths)
    channels = _channels_from_mbsync(paths.mbsync_config)
    if not channels:
        print("No accounts configured.")
        return 1

    env = os.environ.copy()
    if paths.env_file.exists():
        for line in paths.env_file.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.strip().startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()

    sasl_path = args.sasl_path or default_sasl_path()
    if sys.platform == "darwin":
        for candidate in ("/opt/homebrew/lib/sasl2", "/usr/local/lib/sasl2"):
            if Path(candidate).is_dir():
                sasl_path = candidate
                break
    if sasl_path:
        env["SASL_PATH"] = sasl_path
        os.environ["SASL_PATH"] = sasl_path
        try:
            paths.env_file.parent.mkdir(parents=True, exist_ok=True)
            paths.env_file.write_text(f"SASL_PATH={sasl_path}\n", encoding="utf-8")
        except OSError as exc:
            print(
                f"warning: could not write {paths.env_file}: {exc}",
                file=sys.stderr,
            )

    targets = args.accounts or channels
    for account in targets:
        if account not in channels:
            print(f"ERROR: Account {account} not found.")
            continue
        if sasl_path:
            cmd = [
                "/usr/bin/env",
                f"SASL_PATH={sasl_path}",
                "mbsync",
                "-c",
                str(paths.mbsync_config),
                "-q",
                account,
            ]
        else:
            cmd = ["mbsync", "-c", str(paths.mbsync_config), "-q", account]
        subprocess.run(cmd, check=False, env=env)

    notmuch_config = Path(
        os.environ.get("NOTMUCH_CONFIG", "~/.notmuch-config")
    ).expanduser()
    if not args.no_notmuch and shutil.which("notmuch") and notmuch_config.exists():
        subprocess.run(["notmuch", "new", "--quiet"], check=False)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
