#!/usr/bin/env python3
"""
Simple GPIO test to verify button triggering works.
This tests the GPIO setup without requiring RTSP cameras.
"""

import os
import time
import threading
from gpiozero import Button

# Load environment
from dotenv import load_dotenv
load_dotenv(".env" if os.path.exists(".env") else "config.example.env")

# GPIO Configuration
BTN1_GPIO = int(os.getenv("BTN1_GPIO", "18"))
BTN2_GPIO = int(os.getenv("BTN2_GPIO", "19"))

# GPIO state tracking
gpio_triggers = {'r1': 0, 'r2': 0}
gpio_trigger_lock = threading.Lock()
last_trigger_time = {'r1': 0, 'r2': 0}
MIN_TRIGGER_INTERVAL = 1.0  # Minimum 1 second between triggers

def btn1_pressed():
    """Handle GPIO button 1 press."""
    current_time = time.time()
    
    with gpio_trigger_lock:
        # Check debounce - ignore if triggered too recently
        if current_time - last_trigger_time['r1'] < MIN_TRIGGER_INTERVAL:
            print(f"[GPIO] ⚠ r1 trigger ignored (debounce protection)")
            return
        
        # Update trigger time and count
        last_trigger_time['r1'] = current_time
        gpio_triggers['r1'] += 1
    
    print(f"[GPIO] 🔔 BUTTON 1 PRESSED - GPIO {BTN1_GPIO}")
    print(f"[GPIO] r1 trigger count: {gpio_triggers['r1']}")

def btn2_pressed():
    """Handle GPIO button 2 press."""
    current_time = time.time()
    
    with gpio_trigger_lock:
        # Check debounce - ignore if triggered too recently
        if current_time - last_trigger_time['r2'] < MIN_TRIGGER_INTERVAL:
            print(f"[GPIO] ⚠ r2 trigger ignored (debounce protection)")
            return
        
        # Update trigger time and count
        last_trigger_time['r2'] = current_time
        gpio_triggers['r2'] += 1
    
    print(f"[GPIO] 🔔 BUTTON 2 PRESSED - GPIO {BTN2_GPIO}")
    print(f"[GPIO] r2 trigger count: {gpio_triggers['r2']}")

def main():
    print("=" * 50)
    print("🔧 GPIO Button Test")
    print("=" * 50)
    print(f"Button 1 (r1): GPIO {BTN1_GPIO}")
    print(f"Button 2 (r2): GPIO {BTN2_GPIO}")
    print("\n📌 Instructions:")
    print("1. Connect a push button between GPIO pin and GND")
    print("2. Press the button to test triggering")
    print("3. Press Ctrl+C to exit")
    print("=" * 50)
    
    try:
        # Setup GPIO buttons
        btn1 = Button(BTN1_GPIO, pull_up=True, bounce_time=0.3)
        btn2 = Button(BTN2_GPIO, pull_up=True, bounce_time=0.3)
        btn1.when_pressed = btn1_pressed
        btn2.when_pressed = btn2_pressed
        
        print(f"[GPIO] ✓ Buttons configured: GPIO {BTN1_GPIO} (r1), GPIO {BTN2_GPIO} (r2)")
        print("[GPIO] Waiting for button presses...")
        
        # Keep the program running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[GPIO] Test stopped by user")
    except Exception as e:
        print(f"[GPIO] Error: {e}")
    finally:
        print(f"[GPIO] Final trigger counts:")
        print(f"  r1: {gpio_triggers['r1']}")
        print(f"  r2: {gpio_triggers['r2']}")

if __name__ == "__main__":
    main()
