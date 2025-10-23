#!/usr/bin/env python3
"""
Minimal GPIO test - just button press detection without any other operations.
This will help identify if the issue is with GPIO detection or with the capture/upload process.
"""

import os
import time
from gpiozero import Button

# Load environment
from dotenv import load_dotenv
load_dotenv(".env" if os.path.exists(".env") else "config.example.env")

# GPIO Configuration
BTN1_GPIO = int(os.getenv("BTN1_GPIO", "18"))
BTN2_GPIO = int(os.getenv("BTN2_GPIO", "19"))

# Simple counters
r1_count = 0
r2_count = 0

def btn1_pressed():
    """Handle GPIO button 1 press - minimal processing."""
    global r1_count
    r1_count += 1
    print(f"[GPIO] 🔔 BUTTON 1 PRESSED - Count: {r1_count}")

def btn2_pressed():
    """Handle GPIO button 2 press - minimal processing."""
    global r2_count
    r2_count += 1
    print(f"[GPIO] 🔔 BUTTON 2 PRESSED - Count: {r2_count}")

def main():
    print("=" * 50)
    print("🔧 Minimal GPIO Test")
    print("=" * 50)
    print(f"Button 1 (r1): GPIO {BTN1_GPIO}")
    print(f"Button 2 (r2): GPIO {BTN2_GPIO}")
    print("\n📌 Instructions:")
    print("1. Press buttons rapidly")
    print("2. Check if ALL presses are detected immediately")
    print("3. Press Ctrl+C to exit")
    print("=" * 50)
    
    try:
        # Setup GPIO buttons with minimal settings
        btn1 = Button(BTN1_GPIO, pull_up=True, bounce_time=0.1)
        btn2 = Button(BTN2_GPIO, pull_up=True, bounce_time=0.1)
        btn1.when_pressed = btn1_pressed
        btn2.when_pressed = btn2_pressed
        
        print(f"[GPIO] ✓ Buttons configured")
        print("[GPIO] 🎯 Testing - Press buttons now!")
        
        # Keep the program running
        while True:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n[GPIO] Test stopped by user")
    except Exception as e:
        print(f"[GPIO] Error: {e}")
    finally:
        print(f"\n[GPIO] Final counts:")
        print(f"  r1: {r1_count}")
        print(f"  r2: {r2_count}")

if __name__ == "__main__":
    main()
