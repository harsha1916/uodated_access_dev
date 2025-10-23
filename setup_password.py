#!/usr/bin/env python3
"""
Password Setup Script for CamCap

This script helps you set up a secure password for the web dashboard.
It generates a SHA256 hash that you can put in your .env file.

Usage:
    python setup_password.py
"""

import hashlib
import os
from dotenv import load_dotenv, set_key

def generate_password_hash(password):
    """Generate SHA256 hash of password."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def main():
    print("=" * 60)
    print("🔐 CamCap Password Setup")
    print("=" * 60)
    print()
    
    # Check if .env exists
    env_file = ".env" if os.path.exists(".env") else "config.example.env"
    print(f"Using environment file: {env_file}")
    print()
    
    # Get password from user
    while True:
        password = input("Enter new password: ").strip()
        if len(password) < 4:
            print("❌ Password must be at least 4 characters long")
            continue
        break
    
    # Confirm password
    confirm = input("Confirm password: ").strip()
    if password != confirm:
        print("❌ Passwords don't match!")
        return
    
    # Generate hash
    password_hash = generate_password_hash(password)
    
    print()
    print("✅ Password hash generated successfully!")
    print()
    print("Add this line to your .env file:")
    print(f"WEB_PASSWORD_HASH={password_hash}")
    print()
    
    # Ask if user wants to update .env automatically
    update_env = input("Update .env file automatically? (y/n): ").strip().lower()
    if update_env in ['y', 'yes']:
        try:
            set_key(env_file, 'WEB_PASSWORD_HASH', password_hash)
            print(f"✅ Updated {env_file} with new password hash")
        except Exception as e:
            print(f"❌ Error updating {env_file}: {e}")
            print("Please add the hash manually to your .env file")
    else:
        print("Please add the hash manually to your .env file")
    
    print()
    print("🔒 Your password is now secured with SHA256!")
    print("Restart the application to use the new password.")
    print()

if __name__ == "__main__":
    main()
