# mutt-wizard

Configure neomutt with Gmail app passwords (default) or OAuth (optional), and
generate mbsync/msmtp configuration files.

This repo focuses on a minimal setup for:
- Gmail app passwords (default, simple)
- Gmail OAuth (optional)
- neomutt account configs
- isync/mbsync sync
- msmtp sendmail

## Table of contents

- [Why this project](#why-this-project)
- [What this tool creates](#what-this-tool-creates)
- [Requirements](#requirements)
- [Install](#install)
- [Gmail app password (default, simplest)](#gmail-app-password-default-simplest)
- [Gmail OAuth setup (optional)](#gmail-oauth-setup-optional)
- [Why OAuth needs a plugin](#why-oauth-needs-a-plugin)
- [Non-Gmail account](#non-gmail-account)
- [Sync mail](#sync-mail)
- [Commands](#commands)
- [Reset (wipe everything created by mw)](#reset-wipe-everything-created-by-mw)
- [macOS notes](#macos-notes)
- [Linux notes](#linux-notes)
- [Troubleshooting](#troubleshooting)

## Why this project

[Luke Smith’s](https://lukesmith.xyz/) original [mutt-wizard](https://github.com/lukesmithxyz/mutt-wizard) is effectively unmaintained, and Gmail now
requires OAuth or app passwords. This repo keeps the idea alive with a
readable Python setup that works today.

## What this tool creates

- `~/.config/mutt-wizard/` config root
- `~/.config/mutt-wizard/mbsyncrc`
- `~/.config/mutt-wizard/msmtp/config`
- `~/.config/mutt-wizard/tokens/` Gmail OAuth tokens
- `~/.config/mutt/accounts/*.muttrc`
- `~/.config/mutt/muttrc` (sourced once)
- `~/.local/share/mail/` Maildir storage

## Requirements

Common:
- Python 3.10+
- neomutt
- isync (mbsync)
- msmtp
- ca-certificates
- pass + GPG (only for non-Gmail accounts)

Optional:
- notmuch
- lynx
- abook
- urlview
- mpv

## Install

Use `uv` so the `mw` and `mailsync` entrypoints are consistent across macOS and Linux.

```bash
uv venv --clear && source .venv/bin/activate
uv pip install -e .
```

To install as global executables:

```bash
uv pip install .
```

or:

```bash
uv tool install .
```

## Gmail app password (default, simplest)

This is the default for Gmail because it “just works” on macOS and Linux
without requiring the XOAUTH2 plugin.

Requirements:
- 2FA enabled on your Google account
- an app password created in Google Account security

Add the account:

```bash
mw add --gmail --email you@gmail.com
pass insert you@gmail.com
```

## Gmail OAuth setup (optional)

1) Create OAuth credentials in Google Cloud:
   - https://console.cloud.google.com/apis/credentials
   - Create OAuth client ID (Desktop app)
   - Download the JSON file
2) Ensure the Gmail API is enabled for the project.
3) If the consent screen is in Testing, add your Gmail address as a test user.

Then run:

```bash
mw add --gmail-oauth --email you@gmail.com --client-secrets /path/to/client_secret.json
```

If your browser cannot open, add `--no-browser` and follow the console flow.

## Why OAuth needs a plugin

`mbsync` uses Cyrus SASL for OAuth. On macOS/Homebrew, the XOAUTH2 SASL plugin
is not bundled, so you must install it (or use app passwords).

## Non-Gmail account

```bash
mw add --email you@example.com --imap imap.example.com --smtp smtp.example.com
```

Passwords are read via `pass`. Example:

```bash
pass insert you@example.com
```

## Sync mail

```bash
mailsync
mailsync you@gmail.com
```

`mailsync` runs `mbsync -c ~/.config/mutt-wizard/mbsyncrc` and runs `notmuch new`
only if `~/.notmuch-config` exists.

You can also run mbsync directly:

```bash
mbsync -c ~/.config/mutt-wizard/mbsyncrc -a
```

## Commands

```bash
mw add --gmail --email you@gmail.com
mw add --gmail-oauth --email you@gmail.com --client-secrets /path/to/client_secret.json
mw add --email you@example.com --imap imap.example.com --smtp smtp.example.com
mw list
mw oauth login --email you@gmail.com
mw oauth token you@gmail.com
mw reset
mailsync
```

## Reset (wipe everything created by mw)

```bash
mw reset
```

This removes:
- `~/.config/mutt-wizard`
- account muttrc files under `~/.config/mutt/accounts`
- mw entries in `~/.config/mutt/muttrc`
- maildirs under `~/.local/share/mail/<account>`
- `~/.config/isyncrc` symlink (if created)
- msmtp log created by mw

## macOS notes

### Install dependencies (Homebrew)

```bash
brew install neomutt isync msmtp pass gnupg notmuch lynx
```

### Gmail XOAUTH2 SASL plugin (macOS only)

On macOS, Homebrew’s `cyrus-sasl` does **not** ship the XOAUTH2 plugin, so Gmail
auth will fail unless you install it. This is a macOS/Homebrew limitation, not a
Linux requirement.

If you see:

`Error performing SASL authentication step: SASL(-1)`

Install the plugin with the helper script (builds in a temp dir):

```bash
./scripts/install_xoauth2_macos.sh
```

After that, plain `mailsync` works with no flags because the path is written to
`~/.config/mutt-wizard/env`.

If you prefer not to build a plugin, use Gmail app password mode above.

you can run `mailsync` with the plugin path:

```bash
mailsync --sasl-path /opt/homebrew/lib/sasl2 yrwqid@gmail.com
```

if its still not working, try setting the SASL_PATH environment variable:

```bash
export SASL_PATH=/opt/homebrew/lib/sasl2
```

## Linux notes

### Install dependencies (Debian/Ubuntu)

```bash
sudo apt install neomutt isync msmtp pass gnupg ca-certificates notmuch lynx
```

For Gmail XOAUTH2 support, also install:

```bash
sudo apt install libsasl2-modules
```

### Install dependencies (Arch)

```bash
sudo pacman -S neomutt isync msmtp pass gnupg ca-certificates notmuch lynx
```

For Gmail XOAUTH2 support, install a SASL XOAUTH2 plugin (AUR example):

```bash
paru -S cyrus-sasl-xoauth2
```

## Troubleshooting

### 403 access_denied on OAuth
- Ensure Gmail API is enabled for your Google Cloud project.
- Ensure OAuth consent screen is configured.
- If in Testing, add your Gmail as a test user.

### SASL authentication failure
- macOS: install XOAUTH2 plugin with `./scripts/install_xoauth2_macos.sh`
- Linux: install SASL XOAUTH2 modules (`libsasl2-modules` or distro equivalent)
- Ensure `SASL_PATH` points to the SASL plugin directory if needed.

### notmuch error on mailsync
`mailsync` only runs `notmuch` if `~/.notmuch-config` exists. Run `notmuch setup`
if you want it enabled.
