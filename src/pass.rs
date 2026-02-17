use anyhow::{Context, Result};
use std::process::{Command, Stdio};
use std::io::Write;

pub fn insert_password(email: &str, password: &str) -> Result<()> {
    let mut child = Command::new("pass")
        .arg("insert")
        .arg("-f")
        .arg("-e")
        .arg(email)
        .stdin(Stdio::piped())
        .spawn()
        .context("Failed to spawn pass insert")?;

    if let Some(mut stdin) = child.stdin.take() {
        stdin.write_all(password.as_bytes())?;
    }

    let status = child.wait()?;
    if !status.success() {
        anyhow::bail!("Failed to insert password");
    }

    Ok(())
}

pub fn get_password(email: &str) -> Result<()> {
    let check = Command::new("pass")
        .arg("show")
        .arg(email)
        .output();
    
    if let Ok(output) = check {
        if output.status.success() {
            use std::io::{self, Write};
            print!("wordpass already exists for {}.\nuse existing password? [Y/n]: ", email);
            io::stdout().flush()?;
            
            let mut response = String::new();
            io::stdin().read_line(&mut response)?;
            let response = response.trim().to_lowercase();
            
            if response.is_empty() || response == "y" || response == "yes" {
                println!("Using existing password.");
                return Ok(());
            }
        }
    }
    
    loop {
        let status = Command::new("pass")
            .arg("insert")
            .arg("-f")
            .arg(email)
            .status()
            .context("Failed to run pass insert")?;

        if status.success() {
            break;
        }
    }

    Ok(())
}

pub fn read_password(email: &str) -> Result<String> {
    let output = Command::new("pass")
        .arg("show")
        .arg(email)
        .output()
        .context("Failed to read password")?;

    if !output.status.success() {
        anyhow::bail!("Password not found for {}", email);
    }

    let password = String::from_utf8(output.stdout)
        .context("Invalid UTF-8 in password")?;
    
    Ok(password.trim().to_string())
}
