## mutt-wizard

port of Luke Smith's [mutt-wizard](https://github.com/lukesmithxyz)

configures neomutt, mbsync, and msmtp for email.

### installation

```bash
cargo build --release
sudo cp target/release/mutt-wizard /usr/local/bin/mw
```

### prerequisites

- neomutt or mutt
- isync (mbsync)
- msmtp
- pass (password-store)
- gpg

### setup

initialize pass if you haven't:

```bash
gpg --full-generate-key
pass init your@email.com
```

### usage

add an account:

```bash
mw add user@gmail.com
```

list accounts:

```bash
mw list
```

delete an account:

```bash
mw delete user@gmail.com
```

delete with local mail:

```bash
mw delete user@gmail.com -X
```

delete every account, local mail

```bash
mw reset
```

### after setup

sync mail:

```bash
mbsync -a
```

open neomutt:

```bash
neomutt
```

## gmail

you need an app password, not your regular password:

1. enable 2FA in Google Account
2. go to Security -> App passwords
3. generate password
4. use that password when prompted

## options

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
