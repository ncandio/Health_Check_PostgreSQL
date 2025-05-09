#!/usr/bin/env python3
"""
Script to check if PostgreSQL is installed and print instructions to install it if needed.
"""

import platform
import shutil
import sys
from typing import Dict, List, Tuple

def get_postgresql_install_instructions() -> Dict[str, List[Tuple[str, str]]]:
    """Get PostgreSQL installation instructions for different operating systems."""
    instructions = {
        "Linux": [
            ("Ubuntu/Debian", "sudo apt update && sudo apt install postgresql postgresql-contrib"),
            ("Fedora/RHEL", "sudo dnf install postgresql postgresql-server"),
            ("Arch Linux", "sudo pacman -S postgresql"),
        ],
        "Darwin": [
            ("Homebrew", "brew install postgresql"),
            ("MacPorts", "sudo port install postgresql14-server"),
        ],
        "Windows": [
            ("Download the installer", "https://www.postgresql.org/download/windows/"),
            ("Using Chocolatey", "choco install postgresql"),
        ],
    }
    return instructions

def print_colored(text: str, color: str = "default"):
    """Print colored text for better readability."""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "default": "\033[0m",
        "bold": "\033[1m",
    }
    
    # Check if stdout is a terminal
    if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
        print(f"{colors.get(color, colors['default'])}{text}{colors['default']}")
    else:
        print(text)

def print_installation_instructions(os_name: str):
    """Print installation instructions for the current operating system."""
    instructions = get_postgresql_install_instructions()
    
    print_colored("PostgreSQL is not installed or not in your PATH.", "red")
    print_colored("\nInstallation instructions for your operating system:", "yellow")
    
    for distro, command in instructions.get(os_name, instructions["Linux"]):
        print_colored(f"\n{distro}:", "bold")
        if command.startswith("http"):
            print_colored(f"Visit: {command}", "blue")
        else:
            print_colored(f"Run: {command}", "green")
    
    print_colored("\nAfter installation, rerun your script.", "yellow")

def check_postgresql_installed() -> bool:
    """Check if PostgreSQL is installed and available in the system PATH."""
    return shutil.which("psql") is not None

def main():
    """Main entry point."""
    print_colored("Checking PostgreSQL installation...", "blue")
    
    os_name = platform.system()
    
    if check_postgresql_installed():
        print_colored("PostgreSQL is installed and available in your PATH.", "green")
        return 0
    else:
        print_installation_instructions(os_name)
        return 1

if __name__ == "__main__":
    sys.exit(main())