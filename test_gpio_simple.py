#!/usr/bin/env python3
"""
Simple GPIO Test Script (Standalone)

This script tests GPIO pins without needing config.py or the full system.
Perfect for quickly checking if GPIO is working at all.

Usage:
    python test_gpio_simple.py
"""

import sys
import time

print("=" * 60)
print("Simple GPIO Test Script")
print("=" * 60)
print()

# Try to import GPIO
try:
    import RPi.GPIO as GPIO
    print("✓ RPi.GPIO imported successfully")
except (ImportError, RuntimeError) as e:
    print("❌ Failed to import RPi.GPIO")
    print(f"Error: {e}")
    print()
    print("Solutions:")
    print("1. Install RPi.GPIO: pip install RPi.GPIO")
    print("2. Make sure you're on Raspberry Pi")
    print("3. Try running with sudo: sudo python test_gpio_simple.py")
    sys.exit(1)

print()

# Pin configuration (default pins)
PIN_1 = 18  # Camera 1 (r1/Entry)
PIN_2 = 19  # Camera 2 (r2/Exit)
PIN_3 = 20  # Camera 3 (r3/Auxiliary)

BOUNCE_TIME = 300  # milliseconds

print("Pin Configuration:")
print(f"  Pin {PIN_1} (GPIO {PIN_1}, Physical Pin 12) - Camera 1 (r1/Entry)")
print(f"  Pin {PIN_2} (GPIO {PIN_2}, Physical Pin 35) - Camera 2 (r2/Exit)")
print(f"  Pin {PIN_3} (GPIO {PIN_3}, Physical Pin 38) - Camera 3 (r3/Auxiliary)")
print()

# Counter
trigger_count = {
    PIN_1: 0,
    PIN_2: 0,
    PIN_3: 0
}

def trigger_callback(channel):
    """Called when pin is triggered (goes to GND)."""
    trigger_count[channel] += 1
    
    pin_name = {
        PIN_1: "Camera 1 (r1/Entry)",
        PIN_2: "Camera 2 (r2/Exit)",
        PIN_3: "Camera 3 (r3/Auxiliary)"
    }.get(channel, f"Pin {channel}")
    
    timestamp = time.strftime('%H:%M:%S')
    
    print()
    print("🔔" * 20)
    print(f"⚡ TRIGGER! Pin {channel} → {pin_name}")
    print(f"⏰ Time: {timestamp}")
    print(f"📊 Count: {trigger_count[channel]}")
    print("🔔" * 20)
    print()


def main():
    """Main test function."""
    try:
        # Setup GPIO
        print("Setting up GPIO...")
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Configure pins with pull-up resistors (trigger on LOW)
        GPIO.setup(PIN_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(PIN_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(PIN_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        print("✓ GPIO pins configured")
        print()
        
        # Read initial states
        print("Initial Pin States:")
        print("-" * 40)
        state_1 = GPIO.input(PIN_1)
        state_2 = GPIO.input(PIN_2)
        state_3 = GPIO.input(PIN_3)
        
        print(f"Pin {PIN_1}: {'LOW (Connected to GND)' if state_1 == GPIO.LOW else 'HIGH (Normal)'}")
        print(f"Pin {PIN_2}: {'LOW (Connected to GND)' if state_2 == GPIO.LOW else 'HIGH (Normal)'}")
        print(f"Pin {PIN_3}: {'LOW (Connected to GND)' if state_3 == GPIO.LOW else 'HIGH (Normal)'}")
        print("-" * 40)
        print()
        
        # Add event detection (trigger on FALLING edge = HIGH to LOW)
        print("Adding event detection...")
        GPIO.add_event_detect(PIN_1, GPIO.FALLING, callback=trigger_callback, bouncetime=BOUNCE_TIME)
        GPIO.add_event_detect(PIN_2, GPIO.FALLING, callback=trigger_callback, bouncetime=BOUNCE_TIME)
        GPIO.add_event_detect(PIN_3, GPIO.FALLING, callback=trigger_callback, bouncetime=BOUNCE_TIME)
        
        print("✓ Event detection enabled")
        print()
        
        print("=" * 60)
        print("🎯 GPIO MONITORING ACTIVE")
        print("=" * 60)
        print()
        print("Waiting for GPIO triggers...")
        print()
        print("📍 How to Trigger:")
        print(f"   Camera 1: Connect GPIO {PIN_1} (Physical Pin 12) to GND")
        print(f"   Camera 2: Connect GPIO {PIN_2} (Physical Pin 35) to GND")
        print(f"   Camera 3: Connect GPIO {PIN_3} (Physical Pin 38) to GND")
        print()
        print("   GND Pins: Physical pins 6, 9, 14, 20, 25, 30, 34, 39")
        print()
        print("Press Ctrl+C to stop")
        print("=" * 60)
        print()
        
        # Keep script running
        last_heartbeat = time.time()
        
        while True:
            time.sleep(1)
            
            # Show heartbeat every 10 seconds
            if time.time() - last_heartbeat > 10:
                print(f"💚 Monitoring... (Triggers: Pin {PIN_1}={trigger_count[PIN_1]}, Pin {PIN_2}={trigger_count[PIN_2]}, Pin {PIN_3}={trigger_count[PIN_3]})")
                last_heartbeat = time.time()
                
    except KeyboardInterrupt:
        print()
        print()
        print("🛑 Stopping test...")
        
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        
    finally:
        # Summary
        print()
        print("=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"Camera 1 (Pin {PIN_1}) triggers: {trigger_count[PIN_1]}")
        print(f"Camera 2 (Pin {PIN_2}) triggers: {trigger_count[PIN_2]}")
        print(f"Camera 3 (Pin {PIN_3}) triggers: {trigger_count[PIN_3]}")
        print(f"Total triggers detected: {sum(trigger_count.values())}")
        print("=" * 60)
        print()
        
        # Cleanup
        print("Cleaning up GPIO...")
        GPIO.cleanup()
        print("✓ GPIO cleanup complete")
        print()


if __name__ == '__main__':
    main()

