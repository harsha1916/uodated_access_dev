#!/usr/bin/env python3
"""
GPIO Cleanup Script

Use this script if you get "RuntimeError: Failed to add edge detection" error.
This happens when GPIO pins are still configured from a previous run.

Usage:
    python cleanup_gpio.py
    
Or with sudo:
    sudo python cleanup_gpio.py
"""

import sys

print()
print("=" * 60)
print("GPIO Cleanup Script")
print("=" * 60)
print()

# Try to import GPIO
try:
    import RPi.GPIO as GPIO
    print("✓ RPi.GPIO imported successfully")
except (ImportError, RuntimeError) as e:
    print(f"❌ Failed to import RPi.GPIO: {e}")
    print()
    print("This script only works on Raspberry Pi")
    print("Install with: sudo pip install RPi.GPIO")
    sys.exit(1)

print()
print("🧹 Cleaning up GPIO...")
print()

try:
    # Cleanup GPIO
    GPIO.cleanup()
    print("✓ GPIO cleanup successful!")
    print()
    print("All GPIO pins have been reset to default state.")
    print("You can now run your test scripts or main system.")
    print()
    
except Exception as e:
    print(f"⚠️  Cleanup error: {e}")
    print()
    print("This might be normal if GPIO wasn't initialized.")
    print()

print("=" * 60)
print("Next steps:")
print("=" * 60)
print()
print("1. Run test script:")
print("   python test_gpio_pushbutton.py")
print()
print("2. Or run full system:")
print("   python main.py")
print()
print("The 'failed to add edge detection' error should be fixed!")
print()

