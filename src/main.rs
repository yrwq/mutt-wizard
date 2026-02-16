use anyhow::{Result};
use clap::{Parser, Subcommand};

mod config;
mod account;

use config::Config;
use account::Account;


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
    },
}


fn main() -> Result<()> {
    let cli = Cli::parse();
    let config = Config::load()?;

    match cli.command {
        Commands::Add {
            email,
        } => {
            Account::add(
                &config,
                email,
            )?;
        }
    }

    Ok(())
}
