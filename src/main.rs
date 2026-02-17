use anyhow::{Result};
use clap::{Parser, Subcommand};

mod config;
mod account;
mod pass;
mod mailbox;
mod templates;

use config::Config;

#[derive(Parser)]
#[command(name = "mw")]
#[command(about = "mw: auto-configure email accounts for (neo)mutt", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// add an account
    Add {
        /// email address to add
        email: String,

        /// login username if not full address
        #[arg(short = 'u', long)]
        login: Option<String>,

        /// Password for account
        #[arg(short = 'p', long)]
        password: Option<String>,

        /// imap server address
        #[arg(short = 'i', long)]
        imap: Option<String>,
        
        /// imap server port
        #[arg(short = 'I', long)]
        imap_port: Option<u16>,
        
        /// stmp server address
        #[arg(short = 's', long)]
        smtp: Option<String>,
        
        /// smtp server port
        #[arg(short = 'S', long)]
        smtp_port: Option<u16>,
    },
}


fn main() -> Result<()> {
    let cli = Cli::parse();
    let config = Config::load()?;

    match cli.command {
        Commands::Add {
            email,
            login,
            password,
            imap,
            imap_port,
            smtp,
            smtp_port
        } => {
            account::add(
                &config,
                email,
                login,
                password,
                imap,
                imap_port,
                smtp,
                smtp_port
            )?;
        }
    }

    Ok(())
}
