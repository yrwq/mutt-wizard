use anyhow::Result;
use std::fs;
use std::path::Path;

pub fn remove_section_from_file(path: &Path, start_marker: &str, end_marker: &str) -> Result<()> {
    if !path.exists() {
        return Ok(());
    }

    let content = fs::read_to_string(path)?;
    let mut new_content = String::new();
    let mut in_section = false;

    for line in content.lines() {
        if line.contains(start_marker) {
            in_section = true;
            continue;
        }
        
        if in_section && line.contains(end_marker) {
            in_section = false;
            continue;
        }

        if !in_section {
            new_content.push_str(line);
            new_content.push('\n');
        }
    }

    fs::write(path, new_content)?;
    Ok(())
}


pub fn remove_lines_matching(path: &Path, pattern: &str) -> Result<()> {
    if !path.exists() {
        return Ok(());
    }

    let content = fs::read_to_string(path)?;
    let new_content: String = content
        .lines()
        .filter(|line| !line.contains(pattern))
        .map(|line| format!("{}\n", line))
        .collect();

    fs::write(path, new_content)?;
    Ok(())
}
