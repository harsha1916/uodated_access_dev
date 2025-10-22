#!/usr/bin/env python3
"""
Password Setup Script for Camera Capture System

This script helps you set up or reset the admin password.
Default password: admin123

Usage:
    python setup_password.py              # Set default password (admin123)
    python setup_password.py mypassword   # Set custom password
"""

import sys
import os
import bcrypt
from pathlib import Path


def hash_password(password: str) -> str:
    """Generate bcrypt hash for password."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def update_env_file(password_hash: str):
    """Update or create .env file with password hash."""
    env_file = Path('.env')
    
    # Read existing content
    if env_file.exists():
        with open(env_file, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Check if PASSWORD_HASH exists
    hash_found = False
    for i, line in enumerate(lines):
        if line.startswith('PASSWORD_HASH='):
            lines[i] = f'PASSWORD_HASH={password_hash}\n'
            hash_found = True
            break
    
    # If not found, add it
    if not hash_found:
        # Also add auth enabled if not present
        auth_found = any(line.startswith('WEB_AUTH_ENABLED=') for line in lines)
        secret_found = any(line.startswith('SECRET_KEY=') for line in lines)
        
        if not auth_found:
            lines.append('WEB_AUTH_ENABLED=true\n')
        if not secret_found:
            import secrets
            lines.append(f'SECRET_KEY={secrets.token_hex(32)}\n')
        lines.append(f'PASSWORD_HASH={password_hash}\n')
    
    # Write back
    with open(env_file, 'w') as f:
        f.writelines(lines)
    
    print(f"✓ Password hash written to {env_file}")


def main():
    """Main function."""
    print("=" * 50)
    print("Camera Capture System - Password Setup")
    print("=" * 50)
    print()
    
    # Get password from command line or use default
    if len(sys.argv) > 1:
        password = sys.argv[1]
        print(f"Setting custom password: {'*' * len(password)}")
    else:
        password = "admin123"
        print(f"Setting default password: admin123")
    
    # Validate password
    if len(password) < 6:
        print("❌ Error: Password must be at least 6 characters")
        sys.exit(1)
    
    print()
    print("Generating password hash...")
    
    # Generate hash
    password_hash = hash_password(password)
    
    print("✓ Password hash generated")
    print()
    
    # Update .env file
    try:
        update_env_file(password_hash)
        print()
        print("=" * 50)
        print("✓ Password setup complete!")
        print("=" * 50)
        print()
        print("You can now login with:")
        print(f"  Password: {password}")
        print()
        print("To change password later:")
        print("  1. Login to web interface")
        print("  2. Click 'Change Password'")
        print("  3. Enter current and new password")
        print()
        print("Or run this script again with a new password:")
        print(f"  python setup_password.py newpassword")
        print()
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

