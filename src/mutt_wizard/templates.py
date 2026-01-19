from __future__ import annotations

from mutt_wizard.config import Account, Paths

SWITCH_MUTTRC = """\
# vim: filetype=neomuttrc
# Unbind per-account settings before switching accounts.
unset hostname
unmy_hdr Organization
unmailboxes *
unalternates *
unset signature
"""

BASE_MUTTRC_TEMPLATE = """\
# vim: filetype=neomuttrc
# Base settings for mutt-wizard Python starter.
set send_charset=\"us-ascii:utf-8\"
set mailcap_path = \"{mailcap_path}\"
set mime_type_query_command = \"file --mime-type -b %s\"
set date_format=\"%y/%m/%d %I:%M%p\"
set index_format=\"%2C %Z %?X?A& ? %D %-15.15F %s (%-4.4c)\"
set sort = \"reverse-date\"
set sleep_time = 0
set markers = no
set wait_key = no
set mail_check=60

bind index i noop
bind pager i noop
"""

MAILCAP_TEMPLATE = """\
text/plain; $EDITOR %s ;
text/html; {openfile} %s ; nametemplate=%s.html
text/html; lynx -assume_charset=%{{charset}} -display_charset=utf-8 -dump -width=1024 %s; nametemplate=%s.html; copiousoutput;
image/*; {openfile} %s ;
video/*; setsid mpv --quiet %s &; copiousoutput
audio/*; mpv %s ;
application/pdf; {openfile} %s ;
application/pgp-encrypted; gpg -d '%s'; copiousoutput;
application/pgp-keys; gpg --import '%s'; copiousoutput;
application/x-subrip; $EDITOR %s ;
"""

OPENFILE_SH = """\
#!/bin/sh

# Opens files via xdg-open/open without mutt side effects.
tempdir=\"${XDG_CACHE_HOME:-$HOME/.cache}/mutt-wizard/files\"
file=\"$tempdir/${1##*/}\"
[ \"$(uname)\" = \"Darwin\" ] && opener=\"open\" || opener=\"setsid -f xdg-open\"
mkdir -p \"$tempdir\"
cp -f \"$1\" \"$file\"
$opener \"$file\" >/dev/null 2>&1
find \"${tempdir:?}\" -mtime +1 -type f -delete
"""


def render_base_muttrc(paths: Paths) -> str:
    mailcap_path = f"{paths.mutt_config / 'mailcap'}:{paths.mailcap}:$mailcap_path"
    return BASE_MUTTRC_TEMPLATE.format(mailcap_path=mailcap_path)


def render_mailcap(paths: Paths) -> str:
    return MAILCAP_TEMPLATE.format(openfile=paths.openfile)


def mailboxes_for_account(account: Account) -> list[str]:
    if account.is_gmail:
        return [
            "INBOX",
            "[Gmail]/Drafts",
            "[Gmail]/Sent Mail",
            "[Gmail]/Trash",
            "[Gmail]/Spam",
            "[Gmail]/All Mail",
        ]
    return ["INBOX", "Drafts", "Sent", "Trash", "Spam", "Archive"]


def render_account_muttrc(account: Account, paths: Paths) -> str:
    safename = account.email.replace("@", "_")
    folder = paths.maildir_root / account.email
    cache_dir = paths.cache_dir / safename
    hostname = account.email.split("@", 1)[-1]

    if account.is_gmail:
        postponed = "+[Gmail]/Drafts"
        trash = "+[Gmail]/Trash"
        record = "+[Gmail]/Sent Mail"
    else:
        postponed = "+Drafts"
        trash = "+Trash"
        record = "+Sent"

    mailboxes = " ".join(f'"={box}"' for box in mailboxes_for_account(account))

    return "\n".join(
        [
            "# vim: filetype=neomuttrc",
            f"# muttrc file for account {account.email}",
            f'set real_name = "{account.realname}"',
            f'set from = "{account.email}"',
            f'set sendmail = "msmtp -C {paths.msmtp_config} -a {account.email}"',
            f"alias me {account.realname} <{account.email}>",
            f'set folder = "{folder}"',
            f'set header_cache = "{cache_dir / "headers"}"',
            f'set message_cachedir = "{cache_dir / "bodies"}"',
            "set mbox_type = Maildir",
            f'set hostname = "{hostname}"',
            f"source {paths.switch_muttrc}",
            'set spool_file = "+INBOX"',
            f'set postponed = "{postponed}"',
            f'set trash = "{trash}"',
            f'set record = "{record}"',
            f"mailboxes {mailboxes}",
            f'macro index o "<shell-escape>mailsync {account.email}<enter>" "sync {account.email}"',
            "",
        ]
    )


def render_mbsync(
    account: Account, paths: Paths, sslcert: str, max_messages: int
) -> str:
    if account.is_gmail and account.auth_method == "oauth":
        auth_mech = "XOAUTH2"
        pass_cmd = f"mw oauth token {account.email}"
    else:
        auth_mech = "LOGIN"
        pass_cmd = f"pass {account.pass_prefix}{account.email}"
    return "\n".join(
        [
            f"IMAPStore {account.email}-remote",
            f"Host {account.imap_host}",
            f"Port {account.imap_port}",
            f"User {account.login}",
            f'PassCmd "{pass_cmd}"',
            f"AuthMechs {auth_mech}",
            "TLSType IMAPS",
            f"CertificateFile {sslcert}",
            "",
            f"MaildirStore {account.email}-local",
            "Subfolders Verbatim",
            f"Path {paths.maildir_root / account.email}/",
            f"Inbox {paths.maildir_root / account.email}/INBOX",
            "",
            f"Channel {account.email}",
            "Expunge Both",
            f"Far :{account.email}-remote:",
            f"Near :{account.email}-local:",
            'Patterns * !"[Gmail]/All Mail" !"*fts-flatcurve*" !"*virtual*"',
            "Create Both",
            "SyncState *",
            f"MaxMessages {max_messages}",
            "ExpireUnread no",
            "# End profile",
            "",
        ]
    )


def render_msmtp_defaults(paths: Paths, sslcert: str) -> str:
    return "\n".join(
        [
            "defaults",
            "auth on",
            "tls on",
            f"tls_trust_file {sslcert}",
            f"logfile {paths.msmtp_log}",
            "",
        ]
    )


def render_msmtp(account: Account, sslcert: str) -> str:
    if account.is_gmail and account.auth_method == "oauth":
        password_eval = f"mw oauth token {account.email}"
        auth_line = "auth xoauth2"
    else:
        password_eval = f"pass {account.pass_prefix}{account.email}"
        auth_line = "auth on"

    return "\n".join(
        [
            f"account {account.email}",
            f"host {account.smtp_host}",
            f"port {account.smtp_port}",
            f"from {account.email}",
            f"user {account.login}",
            f'passwordeval "{password_eval}"',
            auth_line,
            "tls on",
            f"tls_trust_file {sslcert}",
            "",
        ]
    )
