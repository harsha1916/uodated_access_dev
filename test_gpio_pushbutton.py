#!/usr/bin/env python3
"""
GPIO Push Button Test Script

This script is specifically designed to test PUSH BUTTON triggers.
It will show you exactly what's happening when you press a button.

Wiring for Push Buttons:
    Button Pin 1 → GPIO Pin (18, 19, or 20)
    Button Pin 2 → GND

When button is pressed → Connects GPIO to GND → Triggers capture!

Usage:
    python test_gpio_pushbutton.py
"""

import sys
import time
from datetime import datetime

print()
print("=" * 70)
print("🔘 GPIO PUSH BUTTON TEST SCRIPT")
print("=" * 70)
print()

# Import GPIO
try:
    import RPi.GPIO as GPIO
    print("✓ RPi.GPIO imported successfully")
except (ImportError, RuntimeError) as e:
    print("❌ FAILED: RPi.GPIO not available")
    print(f"   Error: {e}")
    print()
    print("🔧 Solutions:")
    print("   1. Install: sudo pip install RPi.GPIO")
    print("   2. Make sure you're on Raspberry Pi (not Windows!)")
    print("   3. Try: sudo python test_gpio_pushbutton.py")
    print()
    sys.exit(1)

print()

# Pin configuration
PIN_CAMERA_1 = 18  # Entry
PIN_CAMERA_2 = 19  # Exit
PIN_CAMERA_3 = 20  # Auxiliary
BOUNCE_TIME = 300   # milliseconds

# Trigger counters
triggers = {
    PIN_CAMERA_1: {'name': 'Camera 1 (r1/Entry)', 'count': 0},
    PIN_CAMERA_2: {'name': 'Camera 2 (r2/Exit)', 'count': 0},
    PIN_CAMERA_3: {'name': 'Camera 3 (r3/Auxiliary)', 'count': 0}
}


def button_pressed(channel):
    """Called when button is pressed (pin goes LOW)."""
    triggers[channel]['count'] += 1
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    
    print()
    print("🔔" * 35)
    print(f"⚡⚡⚡ BUTTON PRESSED! ⚡⚡⚡")
    print(f"📍 Pin: GPIO {channel}")
    print(f"📹 Camera: {triggers[channel]['name']}")
    print(f"⏰ Time: {timestamp}")
    print(f"📊 Total Count: {triggers[channel]['count']}")
    print("🔔" * 35)
    print()
    print("✓ In full system, this would capture an image!")
    print()


def show_wiring_guide():
    """Show push button wiring guide."""
    print("📋 PUSH BUTTON WIRING GUIDE")
    print("=" * 70)
    print()
    print("For Each Camera, Connect Push Button Like This:")
    print()
    print("  Camera 1 (r1/Entry):")
    print("    Button Pin 1 → GPIO 18 (Physical Pin 12)")
    print("    Button Pin 2 → GND (Physical Pin 6, 9, 14, 20, 25, 30, 34, or 39)")
    print()
    print("  Camera 2 (r2/Exit):")
    print("    Button Pin 1 → GPIO 19 (Physical Pin 35)")
    print("    Button Pin 2 → GND (Any GND pin)")
    print()
    print("  Camera 3 (r3/Auxiliary):")
    print("    Button Pin 1 → GPIO 20 (Physical Pin 38)")
    print("    Button Pin 2 → GND (Any GND pin)")
    print()
    print("🔌 Raspberry Pi Pinout Reference:")
    print()
    print("  Pin 1  [3.3V]  [5V   ] Pin 2")
    print("  Pin 3  [GPIO2] [5V   ] Pin 4")
    print("  Pin 5  [GPIO3] [GND  ] Pin 6  ← GND (use this!)")
    print("  Pin 7  [GPIO4] [TX   ] Pin 8")
    print("  Pin 9  [GND  ] [RX   ] Pin 10 ← GND (or this!)")
    print("  Pin 11 [GPIO17][GPIO18] Pin 12 ← CAMERA 1 HERE!")
    print("  Pin 13 [GPIO27][GND  ] Pin 14 ← GND (or this!)")
    print("  ...")
    print("  Pin 33 [GPIO13][GND  ] Pin 34 ← GND (or this!)")
    print("  Pin 35 [GPIO19][GPIO16] Pin 36 ← CAMERA 2 at Pin 35!")
    print("  Pin 37 [GPIO26][GPIO20] Pin 38 ← CAMERA 3 at Pin 38!")
    print("  Pin 39 [GND  ] [GPIO21] Pin 40 ← GND (or this!)")
    print()
    print("=" * 70)
    print()


def main():
    """Main test function."""
    show_wiring_guide()
    
    try:
        # Cleanup any previous GPIO usage
        print("🔧 Cleaning up any previous GPIO state...")
        try:
            GPIO.cleanup()
            print("  ✓ Previous GPIO state cleaned")
        except:
            print("  ✓ No previous GPIO state to clean")
        
        print()
        
        # Setup GPIO
        print("🔧 Initializing GPIO...")
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup each pin with pull-up resistor
        print()
        print("Setting up pins:")
        GPIO.setup(PIN_CAMERA_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        print(f"  ✓ GPIO {PIN_CAMERA_1} configured with PULL-UP resistor")
        
        GPIO.setup(PIN_CAMERA_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        print(f"  ✓ GPIO {PIN_CAMERA_2} configured with PULL-UP resistor")
        
        GPIO.setup(PIN_CAMERA_3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        print(f"  ✓ GPIO {PIN_CAMERA_3} configured with PULL-UP resistor")
        
        print()
        print("✓ GPIO setup complete!")
        print()
        
        # Check initial pin states
        print("📊 Initial Pin States:")
        print("-" * 70)
        for pin, info in triggers.items():
            state = GPIO.input(pin)
            state_text = "LOW (Button PRESSED)" if state == GPIO.LOW else "HIGH (Button NOT pressed)"
            symbol = "●" if state == GPIO.LOW else "○"
            print(f"  {symbol} GPIO {pin} ({info['name']}): {state_text}")
        print("-" * 70)
        print()
        
        # Add event detection (trigger on FALLING edge = button press)
        print("🎯 Adding event detection for button presses...")
        
        try:
            GPIO.add_event_detect(PIN_CAMERA_1, GPIO.FALLING, callback=button_pressed, bouncetime=BOUNCE_TIME)
            print(f"  ✓ Event detection added for GPIO {PIN_CAMERA_1}")
        except RuntimeError as e:
            print(f"  ⚠️  Warning for GPIO {PIN_CAMERA_1}: {e}")
            print(f"     Trying to remove and re-add...")
            try:
                GPIO.remove_event_detect(PIN_CAMERA_1)
            except:
                pass
            GPIO.add_event_detect(PIN_CAMERA_1, GPIO.FALLING, callback=button_pressed, bouncetime=BOUNCE_TIME)
            print(f"  ✓ Event detection added for GPIO {PIN_CAMERA_1}")
        
        try:
            GPIO.add_event_detect(PIN_CAMERA_2, GPIO.FALLING, callback=button_pressed, bouncetime=BOUNCE_TIME)
            print(f"  ✓ Event detection added for GPIO {PIN_CAMERA_2}")
        except RuntimeError as e:
            print(f"  ⚠️  Warning for GPIO {PIN_CAMERA_2}: {e}")
            print(f"     Trying to remove and re-add...")
            try:
                GPIO.remove_event_detect(PIN_CAMERA_2)
            except:
                pass
            GPIO.add_event_detect(PIN_CAMERA_2, GPIO.FALLING, callback=button_pressed, bouncetime=BOUNCE_TIME)
            print(f"  ✓ Event detection added for GPIO {PIN_CAMERA_2}")
        
        try:
            GPIO.add_event_detect(PIN_CAMERA_3, GPIO.FALLING, callback=button_pressed, bouncetime=BOUNCE_TIME)
            print(f"  ✓ Event detection added for GPIO {PIN_CAMERA_3}")
        except RuntimeError as e:
            print(f"  ⚠️  Warning for GPIO {PIN_CAMERA_3}: {e}")
            print(f"     Trying to remove and re-add...")
            try:
                GPIO.remove_event_detect(PIN_CAMERA_3)
            except:
                pass
            GPIO.add_event_detect(PIN_CAMERA_3, GPIO.FALLING, callback=button_pressed, bouncetime=BOUNCE_TIME)
            print(f"  ✓ Event detection added for GPIO {PIN_CAMERA_3}")
        
        print()
        print("✓ Event detection enabled on all pins")
        print()
        
        print("=" * 70)
        print("🟢 MONITORING ACTIVE - Press your buttons NOW!")
        print("=" * 70)
        print()
        print("📌 What to do:")
        print("   1. Press button connected to GPIO 18 → Should trigger Camera 1")
        print("   2. Press button connected to GPIO 19 → Should trigger Camera 2")
        print("   3. Press button connected to GPIO 20 → Should trigger Camera 3")
print()
        print("   You should see 🔔 trigger messages IMMEDIATELY when pressed!")
        print()
        print("Press Ctrl+C to stop the test")
        print("=" * 70)
        print()
        
        # Monitor continuously with live pin state display
        last_state = {PIN_CAMERA_1: None, PIN_CAMERA_2: None, PIN_CAMERA_3: None}
        check_count = 0
        
        print("👀 Watching pins continuously (checking every 0.1 seconds)...")
        print()
        
        while True:
            # Check pins frequently (10 times per second)
            time.sleep(0.1)
            check_count += 1
            
            # Read all pin states
            for pin, info in triggers.items():
                current_state = GPIO.input(pin)
                
                # Detect state changes
                if last_state[pin] is not None and current_state != last_state[pin]:
                    if current_state == GPIO.LOW:
                        # Button just pressed!
                        print(f"⬇️  BUTTON {pin} PRESSED (going LOW)")
                    else:
                        # Button just released!
                        print(f"⬆️  BUTTON {pin} RELEASED (going HIGH)")
                
                last_state[pin] = current_state
            
            # Show heartbeat every 50 checks (5 seconds)
            if check_count % 50 == 0:
                total_triggers = sum(t['count'] for t in triggers.values())
                print(f"💚 Monitoring... (Checked {check_count} times, {total_triggers} triggers detected)")
                
            # Show detailed status every 300 checks (30 seconds)
            if check_count % 300 == 0:
                print()
                print("📊 Current Button States:")
                for pin, info in triggers.items():
                    state = GPIO.input(pin)
                    state_text = "🔴 PRESSED" if state == GPIO.LOW else "⚪ released"
                    print(f"  GPIO {pin} ({info['name']}): {state_text} | Trigger Count: {info['count']}")
                print()
    
    except KeyboardInterrupt:
        print()
        print()
        print("🛑 Test stopped by user")
        
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Show summary
        print()
        print("=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        total = 0
        for pin, info in triggers.items():
            print(f"  {info['name']:30s} GPIO {pin}: {info['count']:3d} button presses")
            total += info['count']
        print("-" * 70)
        print(f"  {'TOTAL':30s}          {total:3d} triggers detected")
        print("=" * 70)
        print()
        
        # Cleanup
        print("🧹 Cleaning up GPIO...")
        GPIO.cleanup()
        print("✓ GPIO cleanup complete")
        print()
        
        if total > 0:
            print("🎉 SUCCESS! GPIO triggers are working!")
            print()
            print("Next steps:")
            print("  1. Your hardware is working correctly")
            print("  2. Run full system: python main.py")
            print("  3. Open web interface and watch ⚡ GPIO Triggers card")
            print("  4. Press buttons to capture images!")
        else:
            print("⚠️  NO TRIGGERS DETECTED")
            print()
            print("Troubleshooting:")
            print("  1. Check button wiring (see guide above)")
            print("  2. Verify button is working (test with multimeter)")
            print("  3. Try connecting GPIO 18 directly to GND with wire")
            print("  4. Check .env has GPIO_ENABLED=true")
            print("  5. Try running with: sudo python test_gpio_pushbutton.py")
        print()


if __name__ == '__main__':
    main()

