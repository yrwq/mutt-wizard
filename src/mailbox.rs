use anyhow::Result;
use std::process::Command;

use crate::account::Account;
use crate::config::Config;
use crate::pass;

pub fn get_mailboxes(account: &Account) -> Result<Vec<String>> {
    let password = pass::read_password(&account.email)?;

    let url = format!(
        "imaps://{}@{}:{}",
        account.login, account.imap, account.imap_port
    );

    let output = Command::new("curl")
        .arg("--location-trusted")
        .arg("-s")
        .arg("-m")
        .arg("5")
        .arg("--user")
        .arg(format!("{}:{}", account.email, password))
        .arg("--url")
        .arg(&url)
        .output()?;

    if !output.status.success() || output.stdout.is_empty() {
        eprintln!("Warning: Could not fetch mailboxes from server.");
        eprintln!("Using default mailbox list.");
        return Ok(vec![
            "INBOX".to_string(),
            "Drafts".to_string(),
            "Junk".to_string(),
            "Trash".to_string(),
            "Sent".to_string(),
            "Archive".to_string(),
        ]);
    }

    let mailboxes = String::from_utf8_lossy(&output.stdout);
    let mailboxes: Vec<String> = mailboxes
        .lines()
        .filter(|line| !line.contains("HasChildren"))
        .filter_map(|line| {
            // Parse IMAP LIST response
            // Format: * LIST (\flags) "delimiter" "mailbox name"
            if let Some(pos) = line.rfind('"') {
                let start = line[..pos].rfind('"')?;
                Some(line[start + 1..pos].trim().replace('\r', ""))
            } else {
                None
            }
        })
        .collect();

    if mailboxes.is_empty() {
        Ok(vec![
            "INBOX".to_string(),
            "Drafts".to_string(),
            "Junk".to_string(),
            "Trash".to_string(),
            "Sent".to_string(),
            "Archive".to_string(),
        ])
    } else {
        Ok(mailboxes)
    }
}

pub fn sync(config: &Config) -> Result<()> {
    Command::new("mbsync")
        .arg("-a")
        .arg("-c")
        .arg(&config.mbsyncrc);
    Ok(())
}
