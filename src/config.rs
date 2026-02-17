use std::{env, path::PathBuf};

use anyhow::{Context, Result};

pub struct Config {
    pub password_store: PathBuf,
    pub cachedir: PathBuf,
    pub domains: PathBuf,
    pub muttrc: PathBuf,
    pub mbsyncrc: PathBuf,
    pub accdir: PathBuf,
    pub msmtprc: PathBuf,
    pub msmtplog: PathBuf,
    pub sslcert: PathBuf,
    pub maildir: PathBuf,
    pub muttshare: PathBuf,
}

impl Config {
    pub fn load() -> Result<Self> {
        let home = env::var("HOME").context("HOME not set")?;

        let xdg_config = env::var("XDG_CONFIG_HOME")
            .unwrap_or_else(|_| format!("{}/.config", home));
        let xdg_data = env::var("XDG_DATA_HOME")
            .unwrap_or_else(|_| format!("{}/.local/share", home));
        let xdg_state = env::var("XDG_STATE_HOME")
            .unwrap_or_else(|_| format!("{}/.local/state", home));
        let xdg_cache = env::var("XDG_CACHE_HOME")
            .unwrap_or_else(|_| format!("{}/.cache", home));

        let muttshare = PathBuf::from(format!("{}/mutt-wizard", xdg_data));

        let maildir = PathBuf::from(format!("{}/mail", xdg_data));
        let muttrc = PathBuf::from(format!("{}/mutt/muttrc", xdg_config));
        let accdir = PathBuf::from(format!("{}/mutt/accounts", xdg_config));

        let msmtprc = PathBuf::from(format!("{}/msmtp/config", xdg_config));
        let msmtplog = PathBuf::from(format!("{}/msmtp/msmtp.log", xdg_state));

        let mbsyncrc = env::var("MBSYNCRC")
            .map(PathBuf::from)
            .unwrap_or_else(|_| PathBuf::from(format!("{}/mbsync/mbsyncrc", xdg_config)));

        let password_store = env::var("PASSWORD_STORE_DIR")
            .map(PathBuf::from)
            .unwrap_or_else(|_| PathBuf::from(format!("{}/.password-store", home)));

        let cachedir = PathBuf::from(format!("{}/mutt-wizard", xdg_cache));
        let domains = PathBuf::from("domains.csv");

        let sslcert = Self::find_ssl_cert()?;

        Ok(Config{
            cachedir,
            password_store,
            muttshare,
            domains,
            maildir,
            muttrc,
            mbsyncrc,
            sslcert,
            msmtprc,
            msmtplog,
            accdir
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

    fn find_ssl_cert() -> Result<PathBuf> {
        let possible_certs = [
            "/etc/ssl/certs/ca-certificates.crt",
            "/etc/pki/tls/certs/ca-bundle.crt",
            "/etc/ssl/cert.pem",
            "/etc/ssl/ca-bundle.pem",
            "/etc/pki/tls/cacert.pem",
            "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem",
            "/usr/local/share/ca-certificates/",
        ];

        for cert in &possible_certs {
            let path = PathBuf::from(cert);
            if path.exists() {
                return Ok(path);
            }
        }

        anyhow::bail!("ca certificate not found.\ninstall one or link it to /etc/ssl/certs/ca-certificates.crt")
    }
}
