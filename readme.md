# mutt-wizard

rust port of Luke Smith's [mutt-wizard](https://github.com/lukesmithxyz)
Configures neomutt, mbsync, and msmtp for email.

## Installation

```bash
cargo build --release
sudo cp target/release/mutt-wizard /usr/local/bin/mw
```

## Prerequisites

- neomutt or mutt
- isync (mbsync)
- msmtp
- pass (password-store)
- gpg

## Setup

Initialize pass if you haven't:

```bash
gpg --full-generate-key
pass init your@email.com
```

## Usage

Add an account:

```bash
mw add user@gmail.com
```

List accounts:

```bash
mw list
```

Delete an account:

```bash
mw delete user@gmail.com
```

Delete with local mail:

```bash
mw delete user@gmail.com -X
```

Delete every account, local mail

```bash
mw reset
```

## After Setup

Sync mail:

```bash
mbsync -a
```

Open neomutt:

```bash
neomutt
```

## Gmail

You need an app password, not your regular password:

1. Enable 2FA in Google Account
2. Go to Security -> App passwords
3. Generate password
4. Use that password when prompted

## Options

```bash
mw add <email> [OPTIONS]
  -n <name>      real name
  -i <server     IMAP server
  -I <port>      IMAP port
  -s <server>    SMTP server
  -S <port>      SMTP port
  -u <login>     login username
  -x <password>  password
```
