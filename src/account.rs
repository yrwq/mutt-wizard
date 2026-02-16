use regex::Regex;
use anyhow::Result;

use crate::config::Config;

pub struct Account {
    email: String,
}

impl Account {
    pub fn add(
        config: &Config,
        email: String
    ) -> Result<()> {
        config.check_pass_initialized()?;

        let email_regex = Regex::new(r"^.+@.+\.[A-Za-z]+$")?;

        if !email_regex.is_match(&email) {
            anyhow::bail!("{} is not a valid email address", email);
        }

        let account = Account {
            email: email.clone()
        };

        println!("adding {}", account.email);
        Ok(())
    }
}
