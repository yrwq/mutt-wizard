use std::{env, path::PathBuf};

use anyhow::{Context, Result};

pub struct Config {
    pub password_store: PathBuf,
    pub domains: PathBuf,
}

impl Config {
    pub fn load() -> Result<Self> {
        let home = env::var("HOME").context("HOME not set")?;

        let password_store = env::var("PASSWORD_STORE_DIR")
            .map(PathBuf::from)
            .unwrap_or_else(|_| PathBuf::from(format!("{}/.password-store", home)));

        let domains = PathBuf::from("domains.csv");

        Ok(Config{
            password_store,
            domains,
        })
    }

    pub fn check_pass_initialized(&self) -> Result<()> {
        let gpg_id = self.password_store.join(".gpg-id");
        if !gpg_id.exists() {
            anyhow::bail!(
                "run `pass init <yourgpgemail>` to set up a password archive.\n\
                if you don't already have a GPG key pair, first run `gpg --full-generate-key`."
            );
        }
        Ok(())
    }
}
