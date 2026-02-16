use std::{fs, path::Path};

use regex::Regex;
use anyhow::Result;

use crate::config::Config;
use crate::pass;

pub struct Account {
    pub email: String,
    pub imap: String,
    pub imap_port: u16,
    pub smtp: String,
    pub smtp_port: u16,
}

impl Account {
    pub fn add(
        config: &Config,
        email: String,
        password: Option<String>,
        imap: Option<String>,
        imap_port: Option<u16>,
        smtp: Option<String>,
        smtp_port: Option<u16>,
    ) -> Result<()> {
        config.check_pass_initialized()?;

        let email_regex = Regex::new(r"^.+@.+\.[A-Za-z]+$")?;

        if !email_regex.is_match(&email) {
            anyhow::bail!("{} is not a valid email address", email);
        }

        // parse domain info from domains.csv
        let (imap, imap_port, smtp, smtp_port) = if imap.is_none() || smtp.is_none() {
            parse_domain_info(config, &email, imap, imap_port, smtp, smtp_port)?
        } else {
            (
                imap.unwrap(),
                imap_port.unwrap_or(993),
                smtp.unwrap(),
                smtp_port.unwrap_or(465),
            )
        };

        let account = Account {
            email: email.clone(),
            imap,
            imap_port,
            smtp,
            smtp_port
        };

        if let Some(pass) = password {
            pass::insert_password(&account.email, &pass)?;
        } else {
            pass::get_password(&account.email)?;
        }

        println!("{}\n\
            {}:{}\n\
            {}:{}",
            account.email,
            account.imap,
            account.imap_port,
            account.smtp,
            account.smtp_port,
            );
        Ok(())
    }
}


fn parse_domain_info(
    config: &Config,
    email: &str,
    imap: Option<String>,
    imap_port: Option<u16>,
    smtp: Option<String>,
    smtp_port: Option<u16>,
) -> Result<(String, u16, String, u16)> {
    let domains_csv = &config.domains;
    
    let domain = email.split('@').nth(1).unwrap_or("");
    
    let patterns = vec![domain.to_string(), format!("*.{}", 
        domain.split('.').last().unwrap_or(""))];
    
    for pattern in patterns {
        if let Some((i, ip, s, sp)) = parse_domains_csv(&domains_csv, &pattern)? {
            return Ok((
                imap.unwrap_or(i),
                imap_port.unwrap_or(ip),
                smtp.unwrap_or(s),
                smtp_port.unwrap_or(sp),
            ));
        }
    }

    Ok((
        imap.unwrap_or_else(|| format!("imap.{}", domain)),
        imap_port.unwrap_or(993),
        smtp.unwrap_or_else(|| format!("smtp.{}", domain)),
        smtp_port.unwrap_or(465),
    ))
}

fn parse_domains_csv(path: &Path, domain: &str) -> Result<Option<(String, u16, String, u16)>> {
    let content = fs::read_to_string(path)?;
    
    for line in content.lines() {
        let parts: Vec<&str> = line.split(',').collect();
        if parts.len() >= 5 && parts[0] == domain {
            return Ok(Some((
                parts[1].to_string(),
                parts[2].parse().unwrap_or(993),
                parts[3].to_string(),
                parts[4].parse().unwrap_or(465),
            )));
        }
    }
    
    Ok(None)
}
