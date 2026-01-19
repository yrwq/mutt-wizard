from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


def _xdg_path(env_var: str, default: str) -> Path:
    return Path(os.environ.get(env_var, default)).expanduser()


@dataclass(frozen=True)
class Paths:
    config_home: Path
    data_home: Path
    cache_home: Path
    state_home: Path
    app_config: Path
    mutt_config: Path
    mutt_accounts: Path
    maildir_root: Path
    mbsync_config: Path
    msmtp_config: Path
    msmtp_log: Path
    tokens_dir: Path
    clients_dir: Path
    base_muttrc: Path
    switch_muttrc: Path
    mailcap: Path
    openfile: Path
    cache_dir: Path
    accounts_file: Path
    env_file: Path


@dataclass
class Account:
    email: str
    login: str
    realname: str
    imap_host: str
    imap_port: int
    smtp_host: str
    smtp_port: int
    is_gmail: bool
    auth_method: str = "oauth"
    pass_prefix: str = ""
    client_secret: str | None = None


def get_paths() -> Paths:
    config_home = _xdg_path("XDG_CONFIG_HOME", "~/.config")
    data_home = _xdg_path("XDG_DATA_HOME", "~/.local/share")
    cache_home = _xdg_path("XDG_CACHE_HOME", "~/.cache")
    state_home = _xdg_path("XDG_STATE_HOME", "~/.local/state")

    app_config = config_home / "mutt-wizard"
    mutt_config = config_home / "mutt"
    mutt_accounts = mutt_config / "accounts"
    maildir_root = data_home / "mail"
    mbsync_config = app_config / "mbsyncrc"
    msmtp_config = app_config / "msmtp" / "config"
    msmtp_log = state_home / "msmtp" / "msmtp.log"
    tokens_dir = app_config / "tokens"
    clients_dir = app_config / "clients"
    base_muttrc = app_config / "mutt-wizard.muttrc"
    switch_muttrc = app_config / "switch.muttrc"
    mailcap = app_config / "mailcap"
    openfile = app_config / "openfile"
    cache_dir = cache_home / "mutt-wizard"
    accounts_file = app_config / "accounts.json"
    env_file = app_config / "env"

    return Paths(
        config_home=config_home,
        data_home=data_home,
        cache_home=cache_home,
        state_home=state_home,
        app_config=app_config,
        mutt_config=mutt_config,
        mutt_accounts=mutt_accounts,
        maildir_root=maildir_root,
        mbsync_config=mbsync_config,
        msmtp_config=msmtp_config,
        msmtp_log=msmtp_log,
        tokens_dir=tokens_dir,
        clients_dir=clients_dir,
        base_muttrc=base_muttrc,
        switch_muttrc=switch_muttrc,
        mailcap=mailcap,
        openfile=openfile,
        cache_dir=cache_dir,
        accounts_file=accounts_file,
        env_file=env_file,
    )


def ensure_dirs(paths: Paths) -> None:
    for path in [
        paths.app_config,
        paths.mutt_config,
        paths.mutt_accounts,
        paths.maildir_root,
        paths.mbsync_config.parent,
        paths.msmtp_config.parent,
        paths.tokens_dir,
        paths.clients_dir,
        paths.cache_dir,
        paths.msmtp_log.parent,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def ssl_cert_path() -> str:
    candidates = [
        "/etc/ssl/certs/ca-certificates.crt",
        "/etc/pki/tls/certs/ca-bundle.crt",
        "/etc/ssl/cert.pem",
        "/etc/ssl/ca-bundle.pem",
        "/etc/pki/tls/cacert.pem",
        "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem",
        "/usr/local/share/ca-certificates/",
    ]
    for candidate in candidates:
        candidate_path = Path(candidate)
        if candidate_path.is_file():
            return str(candidate_path)
    raise RuntimeError("CA certificate not found. Please install ca-certificates.")


def default_sasl_path() -> str | None:
    candidates = [
        "/opt/homebrew/lib/sasl2",
        "/usr/local/lib/sasl2",
        "/usr/lib/sasl2",
        "/usr/lib64/sasl2",
    ]
    for candidate in candidates:
        candidate_path = Path(candidate)
        if candidate_path.is_dir():
            if any(candidate_path.glob("libxoauth2*")):
                return str(candidate_path)
            return str(candidate_path)
    return None


def load_accounts(paths: Paths) -> Dict[str, Dict[str, Any]]:
    if not paths.accounts_file.exists():
        return {}
    return json.loads(paths.accounts_file.read_text(encoding="utf-8"))


def save_accounts(paths: Paths, accounts: Dict[str, Dict[str, Any]]) -> None:
    paths.accounts_file.write_text(
        json.dumps(accounts, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def account_to_dict(account: Account) -> Dict[str, Any]:
    return {
        "email": account.email,
        "login": account.login,
        "realname": account.realname,
        "imap_host": account.imap_host,
        "imap_port": account.imap_port,
        "smtp_host": account.smtp_host,
        "smtp_port": account.smtp_port,
        "is_gmail": account.is_gmail,
        "auth_method": account.auth_method,
        "pass_prefix": account.pass_prefix,
        "client_secret": account.client_secret,
    }
