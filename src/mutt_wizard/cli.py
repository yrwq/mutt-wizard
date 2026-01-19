from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from mutt_wizard.config import (
    Account,
    default_sasl_path,
    ensure_dirs,
    get_paths,
    load_accounts,
    save_accounts,
    ssl_cert_path,
)
from mutt_wizard.oauth import access_token, ensure_token
from mutt_wizard.templates import (
    OPENFILE_SH,
    SWITCH_MUTTRC,
    mailboxes_for_account,
    render_account_muttrc,
    render_base_muttrc,
    render_mailcap,
    render_mbsync,
    render_msmtp,
    render_msmtp_defaults,
)


def _write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _ensure_base_files(paths) -> None:
    _write_file(paths.base_muttrc, render_base_muttrc(paths))
    _write_file(paths.switch_muttrc, SWITCH_MUTTRC)
    _write_file(paths.mailcap, render_mailcap(paths))
    _write_file(paths.openfile, OPENFILE_SH)
    paths.openfile.chmod(0o755)
    sasl_path = default_sasl_path()
    if sasl_path is None and sys.platform == "darwin":
        for candidate in ("/opt/homebrew/lib/sasl2", "/usr/local/lib/sasl2"):
            if Path(candidate).is_dir():
                sasl_path = candidate
                break
    if sasl_path:
        _write_file(paths.env_file, f"SASL_PATH={sasl_path}\n")


def _ensure_main_muttrc(paths) -> None:
    muttrc = paths.mutt_config / "muttrc"
    if not muttrc.exists():
        muttrc.write_text("# vim: filetype=neomuttrc\n", encoding="utf-8")

    content = muttrc.read_text(encoding="utf-8")
    source_line = f"source {paths.base_muttrc}"
    if source_line not in content:
        muttrc.write_text(content + source_line + "\n", encoding="utf-8")


def _next_account_id(muttrc_path: Path) -> int:
    if not muttrc_path.exists():
        return 1
    content = muttrc_path.read_text(encoding="utf-8")
    used = set()
    for line in content.splitlines():
        if line.startswith("macro index,pager i"):
            rest = line.split("macro index,pager i", 1)[1]
            number = ""
            for ch in rest:
                if ch.isdigit():
                    number += ch
                else:
                    break
            if number:
                used.add(int(number))
    for candidate in range(1, 10):
        if candidate not in used:
            return candidate
    return max(used or [0]) + 1


def _append_unique(path: Path, marker: str, content: str) -> None:
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if marker in existing:
            return
        path.write_text(existing + "\n" + content, encoding="utf-8")
    else:
        path.write_text(content, encoding="utf-8")


def _ensure_account_muttrc(paths, account: Account, account_id: int) -> None:
    account_path = paths.mutt_accounts / f"{account.email}.muttrc"
    account_path.write_text(render_account_muttrc(account, paths), encoding="utf-8")

    muttrc = paths.mutt_config / "muttrc"
    content = muttrc.read_text(encoding="utf-8")
    source_line = f"source {account_path}"
    if source_line not in content:
        content += source_line + "\n"

    macro_line = (
        "macro index,pager i{idx} "
        "'<sync-mailbox><enter-command>source {path}<enter>"
        "<change-folder>!<enter>;<check-stats>' "
        '"switch to {email}"'
    ).format(idx=account_id, path=account_path, email=account.email)
    if macro_line not in content:
        content += macro_line + "\n"

    muttrc.write_text(content, encoding="utf-8")


def _ensure_maildir(paths, account: Account) -> None:
    for mailbox in mailboxes_for_account(account):
        mailbox_path = paths.maildir_root / account.email / mailbox
        for sub in ["cur", "new", "tmp"]:
            (mailbox_path / sub).mkdir(parents=True, exist_ok=True)


def _ensure_msmtp(paths, account: Account, sslcert: str) -> None:
    config_path = paths.msmtp_config
    if not config_path.exists():
        config_path.write_text(render_msmtp_defaults(paths, sslcert), encoding="utf-8")

    marker = f"account {account.email}"
    _append_unique(config_path, marker, render_msmtp(account, sslcert))


def _ensure_mbsync(paths, account: Account, sslcert: str, max_messages: int) -> None:
    marker = f"IMAPStore {account.email}-remote"
    _append_unique(
        paths.mbsync_config,
        marker,
        render_mbsync(account, paths, sslcert, max_messages),
    )
    isyncrc = paths.config_home / "isyncrc"
    if not isyncrc.exists():
        try:
            isyncrc.symlink_to(paths.mbsync_config)
        except OSError:
            pass


def _store_account(paths, account: Account) -> None:
    accounts = load_accounts(paths)
    accounts[account.email] = {
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
    save_accounts(paths, accounts)


def _copy_client_secret(paths, email: str, client_secret: Path) -> Path:
    dest = paths.clients_dir / f"{email}.json"
    dest.write_text(client_secret.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


def _setup_account(
    account: Account,
    client_secret: Path | None,
    open_browser: bool,
    max_messages: int,
) -> None:
    paths = get_paths()
    ensure_dirs(paths)
    _ensure_base_files(paths)
    _ensure_main_muttrc(paths)
    sslcert = ssl_cert_path()

    if account.is_gmail and account.auth_method == "oauth":
        if not client_secret:
            raise SystemExit("--client-secrets is required for Gmail OAuth")
        stored_secret = _copy_client_secret(paths, account.email, client_secret)
        token_path = paths.tokens_dir / f"{account.email}.json"
        ensure_token(account.email, stored_secret, token_path, open_browser)
        account.client_secret = str(stored_secret)

    account_id = _next_account_id(paths.mutt_config / "muttrc")
    _ensure_account_muttrc(paths, account, account_id)
    _ensure_maildir(paths, account)
    _ensure_msmtp(paths, account, sslcert)
    _ensure_mbsync(paths, account, sslcert, max_messages)
    _store_account(paths, account)

    print(f"Configured {account.email} (account #{account_id}).")


def _cmd_add(args: argparse.Namespace) -> None:
    email = args.email
    login = args.login or email
    realname = args.realname or email.split("@", 1)[0]

    if args.gmail_oauth:
        account = Account(
            email=email,
            login=login,
            realname=realname,
            imap_host=args.imap or "imap.gmail.com",
            imap_port=args.imap_port,
            smtp_host=args.smtp or "smtp.gmail.com",
            smtp_port=args.smtp_port,
            is_gmail=True,
            auth_method="oauth",
        )
        client_secret = (
            Path(args.client_secrets).expanduser() if args.client_secrets else None
        )
        _setup_account(account, client_secret, not args.no_browser, args.max_messages)
        return

    if args.gmail:
        account = Account(
            email=email,
            login=login,
            realname=realname,
            imap_host=args.imap or "imap.gmail.com",
            imap_port=args.imap_port,
            smtp_host=args.smtp or "smtp.gmail.com",
            smtp_port=args.smtp_port,
            is_gmail=True,
            auth_method="pass",
            pass_prefix=args.pass_prefix or "",
        )
        _setup_account(account, None, True, args.max_messages)
        return

    if not args.imap or not args.smtp:
        raise SystemExit("Non-Gmail accounts require --imap and --smtp")

    account = Account(
        email=email,
        login=login,
        realname=realname,
        imap_host=args.imap,
        imap_port=args.imap_port,
        smtp_host=args.smtp,
        smtp_port=args.smtp_port,
        is_gmail=False,
        pass_prefix=args.pass_prefix or "",
    )
    _setup_account(account, None, True, args.max_messages)


def _cmd_list(args: argparse.Namespace) -> None:
    paths = get_paths()
    accounts = load_accounts(paths)
    for idx, email in enumerate(sorted(accounts), start=1):
        print(f"{idx}. {email}")


def _cmd_oauth_login(args: argparse.Namespace) -> None:
    paths = get_paths()
    accounts = load_accounts(paths)
    account = accounts.get(args.email)
    if not account:
        raise SystemExit("Account not found in accounts.json")
    client_secret = account.get("client_secret")
    if not client_secret:
        raise SystemExit("Account does not have a stored client_secret")
    token_path = paths.tokens_dir / f"{args.email}.json"
    ensure_token(args.email, Path(client_secret), token_path, not args.no_browser)
    print("OAuth token refreshed.")


def _cmd_oauth_token(args: argparse.Namespace) -> None:
    paths = get_paths()
    accounts = load_accounts(paths)
    account = accounts.get(args.email)
    if not account:
        raise SystemExit("Account not found in accounts.json")
    client_secret = account.get("client_secret")
    if not client_secret:
        raise SystemExit("Account does not have a stored client_secret")
    token_path = paths.tokens_dir / f"{args.email}.json"
    token = access_token(args.email, Path(client_secret), token_path)
    print(token)


def _filter_muttrc(muttrc_path: Path, paths, emails: set[str]) -> None:
    if not muttrc_path.exists():
        return
    lines = muttrc_path.read_text(encoding="utf-8").splitlines()
    filtered = []
    for line in lines:
        if line.strip() == f"source {paths.base_muttrc}":
            continue
        if str(paths.mutt_accounts) in line and "source" in line:
            continue
        if any(f"switch to {email}" in line for email in emails):
            continue
        filtered.append(line)
    muttrc_path.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def _cmd_reset(args: argparse.Namespace) -> None:
    paths = get_paths()
    if not args.yes:
        confirm = (
            input("Remove all mutt-wizard data (config, tokens, mail)? [y/N] ")
            .strip()
            .lower()
        )
        if confirm != "y":
            print("Aborted.")
            return

    accounts = load_accounts(paths)
    emails = set(accounts.keys())

    for email in emails:
        account_path = paths.mutt_accounts / f"{email}.muttrc"
        if account_path.exists():
            account_path.unlink()

    _filter_muttrc(paths.mutt_config / "muttrc", paths, emails)

    if paths.app_config.exists():
        shutil.rmtree(paths.app_config)

    for email in emails:
        maildir = paths.maildir_root / email
        if maildir.exists():
            shutil.rmtree(maildir)

    if paths.cache_dir.exists():
        shutil.rmtree(paths.cache_dir)

    isyncrc = paths.config_home / "isyncrc"
    if isyncrc.exists() and isyncrc.is_symlink():
        isyncrc.unlink()

    if paths.msmtp_log.exists():
        paths.msmtp_log.unlink()

    print("mutt-wizard configuration cleared.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mw", description="mutt-wizard Python starter"
    )
    sub = parser.add_subparsers(dest="command")

    add = sub.add_parser("add", help="Add an account")
    add.add_argument("--email", required=True)
    add.add_argument("--gmail", action="store_true", help="Use Gmail app password")
    add.add_argument(
        "--gmail-oauth",
        action="store_true",
        help="Use Gmail OAuth (requires client secrets)",
    )
    add.add_argument(
        "--client-secrets", help="Path to Google OAuth client secrets JSON"
    )
    add.add_argument("--login")
    add.add_argument("--realname")
    add.add_argument("--imap")
    add.add_argument("--imap-port", type=int, default=993)
    add.add_argument("--smtp")
    add.add_argument("--smtp-port", type=int, default=587)
    add.add_argument("--pass-prefix", default="")
    add.add_argument("--max-messages", type=int, default=0)
    add.add_argument("--no-browser", action="store_true")
    add.set_defaults(func=_cmd_add)

    list_cmd = sub.add_parser("list", help="List configured accounts")
    list_cmd.set_defaults(func=_cmd_list)

    oauth = sub.add_parser("oauth", help="OAuth helpers")
    oauth_sub = oauth.add_subparsers(dest="oauth_cmd")

    oauth_login = oauth_sub.add_parser("login", help="Refresh OAuth token")
    oauth_login.add_argument("--email", required=True)
    oauth_login.add_argument("--no-browser", action="store_true")
    oauth_login.set_defaults(func=_cmd_oauth_login)

    oauth_token_cmd = oauth_sub.add_parser("token", help="Print access token")
    oauth_token_cmd.add_argument("email")
    oauth_token_cmd.set_defaults(func=_cmd_oauth_token)

    reset = sub.add_parser("reset", help="Remove mutt-wizard config and entries")
    reset.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    reset.set_defaults(func=_cmd_reset)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
