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
    // Create directories
    fs::create_dir_all(config.msmtprc.parent().unwrap())?;
    fs::create_dir_all(config.mbsyncrc.parent().unwrap())?;
    fs::create_dir_all(&config.accdir)?;

    generate_msmtprc(config, account)?;

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
