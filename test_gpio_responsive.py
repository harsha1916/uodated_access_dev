#!/usr/bin/env python3
"""
Test GPIO responsiveness to ensure button presses are detected immediately.
This test focuses on the button press detection without any blocking operations.
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
MIN_TRIGGER_INTERVAL = 0.5  # Reduced to 0.5 seconds for testing

def btn1_pressed():
    """Handle GPIO button 1 press - completely non-blocking."""
    current_time = time.time()
    
    # Quick debounce check with minimal lock time
    with gpio_trigger_lock:
        if current_time - last_trigger_time['r1'] < MIN_TRIGGER_INTERVAL:
            print(f"[GPIO] ⚠ r1 trigger ignored (debounce protection)")
            return
        last_trigger_time['r1'] = current_time
        gpio_triggers['r1'] += 1
    
    # Print immediately - don't block on this
    print(f"[GPIO] 🔔 BUTTON 1 PRESSED - GPIO {BTN1_GPIO} (Count: {gpio_triggers['r1']})")
    print(f"[GPIO] ⏰ Time: {time.strftime('%H:%M:%S.%f')[:-3]}")

def btn2_pressed():
    """Handle GPIO button 2 press - completely non-blocking."""
    current_time = time.time()
    
    # Quick debounce check with minimal lock time
    with gpio_trigger_lock:
        if current_time - last_trigger_time['r2'] < MIN_TRIGGER_INTERVAL:
            print(f"[GPIO] ⚠ r2 trigger ignored (debounce protection)")
            return
        last_trigger_time['r2'] = current_time
        gpio_triggers['r2'] += 1
    
    # Print immediately - don't block on this
    print(f"[GPIO] 🔔 BUTTON 2 PRESSED - GPIO {BTN2_GPIO} (Count: {gpio_triggers['r2']})")
    print(f"[GPIO] ⏰ Time: {time.strftime('%H:%M:%S.%f')[:-3]}")

def main():
    print("=" * 60)
    print("🔧 GPIO Responsiveness Test")
    print("=" * 60)
    print(f"Button 1 (r1): GPIO {BTN1_GPIO}")
    print(f"Button 2 (r2): GPIO {BTN2_GPIO}")
    print(f"Debounce interval: {MIN_TRIGGER_INTERVAL}s")
    print("\n📌 Instructions:")
    print("1. Press buttons rapidly to test responsiveness")
    print("2. Check if button presses are detected immediately")
    print("3. Press Ctrl+C to exit")
    print("=" * 60)
    
    try:
        # Setup GPIO buttons with minimal bounce time
        btn1 = Button(BTN1_GPIO, pull_up=True, bounce_time=0.05)  # Very short bounce time
        btn2 = Button(BTN2_GPIO, pull_up=True, bounce_time=0.05)  # Very short bounce time
        btn1.when_pressed = btn1_pressed
        btn2.when_pressed = btn2_pressed
        
        print(f"[GPIO] ✓ Buttons configured: GPIO {BTN1_GPIO} (r1), GPIO {BTN2_GPIO} (r2)")
        print(f"[GPIO] ✓ Bounce time: 0.05s, Debounce interval: {MIN_TRIGGER_INTERVAL}s")
        print("[GPIO] 🎯 Testing responsiveness...")
        print("[GPIO] Press buttons now!")
        
        # Keep the program running
        while True:
            time.sleep(0.1)  # Short sleep to avoid high CPU usage
            
    except KeyboardInterrupt:
        print("\n[GPIO] Test stopped by user")
    except Exception as e:
        print(f"[GPIO] Error: {e}")
    finally:
        print(f"\n[GPIO] Final trigger counts:")
        print(f"  r1: {gpio_triggers['r1']}")
        print(f"  r2: {gpio_triggers['r2']}")
        print("[GPIO] Test completed!")

if __name__ == "__main__":
    main()
