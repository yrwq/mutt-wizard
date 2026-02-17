use anyhow::Result;
use std::fs;
use std::io::Write;

use crate::config::Config;
use crate::account::Account;

pub fn generate_configs(
    config: &Config,
    account: &Account,
    mailboxes: &[String],
    idnum: usize,
) -> Result<()> {
    fs::create_dir_all(config.msmtprc.parent().unwrap())?;
    fs::create_dir_all(config.mbsyncrc.parent().unwrap())?;
    fs::create_dir_all(&config.accdir)?;

    generate_msmtprc(config, account)?;
    generate_mbsyncrc(config, account)?;
    generate_muttrc(config, account, mailboxes, idnum)?;

    Ok(())
}


fn generate_msmtprc(config: &Config, account: &Account) -> Result<()> {
    let tls_line = if account.smtp_port == 587 {
        "tls_starttls on"
    } else {
        "tls_starttls off"
    };

    let content = format!(
        r#"
account {}
host {}
port {}
from {}
user {}
passwordeval "pass {}"
auth on
tls on
tls_trust_file {}
{}
logfile {}

"#,
        account.email,
        account.smtp,
        account.smtp_port,
        account.email,
        account.login,
        account.email,
        config.sslcert.display(),
        tls_line,
        config.msmtplog.display(),
    );

    let mut file = fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&config.msmtprc)?;
    
    file.write_all(content.as_bytes())?;

    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&config.msmtprc, fs::Permissions::from_mode(0o600))?;
    }

    Ok(())
}

fn generate_mbsyncrc(config: &Config, account: &Account) -> Result<()> {
    let imapssl = match account.imap_port {
        1143 => "None",
        143 => "STARTTLS",
        _ => "IMAPS",
    };

    // check mbsync version
    let (master, slave) = get_mbsync_terms()?;

    let content = format!(
        r#"
IMAPAccount {}
Host {}
Port {}
User {}
PassCmd "pass {}"
SSLType {}
CertificateFile {}

IMAPStore {}-remote
Account {}

MaildirStore {}-local
Subfolders Verbatim
Path {}/
Inbox {}/INBOX

Channel {}
{} :{}-remote:
{} :{}-local:
Patterns *
Create Both
Expunge Both
SyncState *

# End profile

"#,
        account.email,
        account.imap,
        account.imap_port,
        account.login,
        account.email,
        imapssl,
        config.sslcert.display(),
        account.email,
        account.email,
        account.email,
        account.maildir,
        account.maildir,
        account.email,
        master,
        account.email,
        slave,
        account.email,
    );

    let mut file = fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&config.mbsyncrc)?;
    
    file.write_all(content.as_bytes())?;

    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&config.mbsyncrc, fs::Permissions::from_mode(0o600))?;
    }

    Ok(())
}


fn get_mbsync_terms() -> Result<(&'static str, &'static str)> {
    use std::process::Command;
    
    let output = Command::new("mbsync").arg("-v").output();
    
    if let Ok(output) = output {
        let version = String::from_utf8_lossy(&output.stdout);
        if let Some(ver_str) = version.split_whitespace().nth(1) {
            let ver_parts: Vec<&str> = ver_str.split('.').collect();
            if ver_parts.len() >= 2 {
                if let (Ok(major), Ok(minor)) = (ver_parts[0].parse::<u32>(), ver_parts[1].parse::<u32>()) {
                    let ver_num = major * 10 + minor;
                    if ver_num > 14 {
                        return Ok(("Far", "Near"));
                    }
                }
            }
        }
    }
    
    Ok(("Master", "Slave"))
}


fn generate_muttrc(
    config: &Config,
    account: &Account,
    mailboxes: &[String],
    idnum: usize,
) -> Result<()> {
    let mut content = format!(
        r#"# vim: filetype=neomuttrc
# muttrc file for account {}
set realname = "{}"
set from = "{}"
set sendmail = "msmtp -a {}"
alias me {} <{}>
set folder = "{}"
set header_cache = "{}/{}/headers"
set message_cachedir = "{}/{}/bodies"
set mbox_type = Maildir

"#,
        account.email,
        account.realname,
        account.email,
        account.email,
        account.realname,
        account.email,
        account.maildir,
        config.cachedir.display(),
        account.email.replace('@', "_"),
        config.cachedir.display(),
        account.email.replace('@', "_"),
    );

    // mailbox configuration
    content.push_str("set spoolfile = \"+INBOX\"\n");
    content.push_str("set postponed = \"+Drafts\"\n");
    content.push_str("set trash = \"+Trash\"\n");
    content.push_str("set record = \"+Sent\"\n\n");

    // Add mailboxes list
    content.push_str("mailboxes ");
    for (i, mailbox) in mailboxes.iter().enumerate() {
        if i > 0 {
            content.push(' ');
        }
        content.push_str(&format!("\"={}\"", mailbox.replace('\'', "\\'")));
    }
    content.push('\n');

    // write account muttrc
    let acc_file = config.accdir.join(format!("{}.muttrc", account.email));
    fs::write(&acc_file, content)?;

    // update main muttrc
    if !config.muttrc.exists() {
        fs::write(&config.muttrc, "# vim: filetype=neomuttrc\n")?;
    }

    let mut muttrc_content = fs::read_to_string(&config.muttrc)?;

    // mutt-wizard source if not present
    let wizard_source = format!("source {}/mutt-wizard.muttrc", config.muttshare.display());
    if !muttrc_content.contains(&wizard_source) {
        muttrc_content.push_str(&format!("\n{}\n", wizard_source));
    }

    // account source
    let acc_source = format!("source {}", acc_file.display());
    if !muttrc_content.contains(&acc_source) {
        muttrc_content.push_str(&format!("{}\n", acc_source));
    }

    // macro for switching accounts
    let mutt_macro = format!(
        r#"macro index,pager i{} '<sync-mailbox><enter-command>source {}<enter><change-folder>!<enter>;<check-stats>' "switch to {}"
"#,
        idnum,
        acc_file.display(),
        account.email
    );
    muttrc_content.push_str(&mutt_macro);

    fs::write(&config.muttrc, muttrc_content)?;

    Ok(())
}
