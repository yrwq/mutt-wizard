use anyhow::{Result};

mod config;
mod account;

use config::Config;

fn main() -> Result<()> {
    println!("Hello, world!");
    let config = Config::load()?;

    config.check_pass_initialized()?;
    
    Ok(())
}
