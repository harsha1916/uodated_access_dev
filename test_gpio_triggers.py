#!/usr/bin/env python3
"""
GPIO Trigger Test Script

This script helps you test GPIO triggering without running the full system.
It will monitor GPIO pins and show when they are triggered (connected to GND).

Usage:
    python test_gpio_triggers.py
    
Then connect GPIO pins to GND and watch for trigger messages!
"""

import sys
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import GPIO
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False
    logger.error("❌ RPi.GPIO not available!")
    logger.error("This script only works on Raspberry Pi with RPi.GPIO installed")
    logger.error("Install with: pip install RPi.GPIO")
    sys.exit(1)

# Import config
try:
    from config import (
        GPIO_ENABLED, GPIO_TRIGGER_ENABLED,
        GPIO_CAMERA_1_PIN, GPIO_CAMERA_2_PIN, GPIO_CAMERA_3_PIN,
        GPIO_BOUNCE_TIME
    )
except ImportError:
    logger.error("❌ Could not import config.py")
    logger.error("Make sure you're in the correct directory")
    sys.exit(1)


class GPIOTester:
    """Test GPIO trigger functionality."""
    
    def __init__(self):
        self.trigger_count = {
            'camera_1': 0,
            'camera_2': 0,
            'camera_3': 0
        }
        
        self.pin_mapping = {
            GPIO_CAMERA_1_PIN: 'camera_1',
            GPIO_CAMERA_2_PIN: 'camera_2',
            GPIO_CAMERA_3_PIN: 'camera_3'
        }
        
        self.running = True
    
    def setup_gpio(self):
        """Initialize GPIO pins."""
        try:
            logger.info("=" * 60)
            logger.info("GPIO Trigger Test Script")
            logger.info("=" * 60)
            logger.info("")
            
            # Check configuration
            logger.info(f"GPIO_ENABLED: {GPIO_ENABLED}")
            logger.info(f"GPIO_TRIGGER_ENABLED: {GPIO_TRIGGER_ENABLED}")
            logger.info(f"GPIO_BOUNCE_TIME: {GPIO_BOUNCE_TIME}ms")
            logger.info("")
            
            if not GPIO_ENABLED:
                logger.warning("⚠️  GPIO_ENABLED is False in config!")
                logger.warning("Set GPIO_ENABLED=true in .env file")
                return False
            
            # Setup GPIO
            logger.info("Setting up GPIO...")
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Configure pins with pull-up resistors
            logger.info("")
            logger.info("Configuring GPIO pins:")
            
            GPIO.setup(GPIO_CAMERA_1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            logger.info(f"✓ GPIO {GPIO_CAMERA_1_PIN} (Pin 12) - Camera 1 (r1/Entry)")
            
            GPIO.setup(GPIO_CAMERA_2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            logger.info(f"✓ GPIO {GPIO_CAMERA_2_PIN} (Pin 35) - Camera 2 (r2/Exit)")
            
            GPIO.setup(GPIO_CAMERA_3_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            logger.info(f"✓ GPIO {GPIO_CAMERA_3_PIN} (Pin 38) - Camera 3 (r3/Auxiliary)")
            
            logger.info("")
            logger.info("✓ GPIO initialized successfully!")
            logger.info("")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize GPIO: {e}")
            return False
    
    def trigger_callback(self, channel):
        """Callback when GPIO pin is triggered."""
        camera_key = self.pin_mapping.get(channel)
        if camera_key:
            self.trigger_count[camera_key] += 1
            count = self.trigger_count[camera_key]
            
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            
            logger.info("")
            logger.info("🔔" * 20)
            logger.info(f"⚡ TRIGGER DETECTED! Pin {channel} → {camera_key.upper()}")
            logger.info(f"⏰ Time: {timestamp}")
            logger.info(f"📊 Count: {count}")
            logger.info("🔔" * 20)
            logger.info("")
    
    def read_pin_states(self):
        """Read and display current pin states."""
        logger.info("Current Pin States:")
        logger.info("-" * 40)
        
        for pin, camera in self.pin_mapping.items():
            state = GPIO.input(pin)
            state_text = "LOW (Triggered!)" if state == GPIO.LOW else "HIGH (Normal)"
            symbol = "●" if state == GPIO.LOW else "○"
            
            logger.info(f"{symbol} Pin {pin} ({camera}): {state_text}")
        
        logger.info("-" * 40)
        logger.info("")
    
    def start_monitoring(self):
        """Start monitoring GPIO pins."""
        logger.info("=" * 60)
        logger.info("Starting GPIO Trigger Monitoring")
        logger.info("=" * 60)
        logger.info("")
        logger.info("📍 Wiring Guide:")
        logger.info(f"   Camera 1 (r1/Entry): Connect GPIO {GPIO_CAMERA_1_PIN} to GND")
        logger.info(f"   Camera 2 (r2/Exit): Connect GPIO {GPIO_CAMERA_2_PIN} to GND")
        logger.info(f"   Camera 3 (r3/Auxiliary): Connect GPIO {GPIO_CAMERA_3_PIN} to GND")
        logger.info("")
        logger.info("⚡ Trigger pins by connecting them to GND")
        logger.info("   GND pins: Physical pins 6, 9, 14, 20, 25, 30, 34, 39")
        logger.info("")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        logger.info("")
        
        # Read initial pin states
        self.read_pin_states()
        
        # Add event detection
        for pin in self.pin_mapping.keys():
            GPIO.add_event_detect(
                pin,
                GPIO.FALLING,  # Trigger on HIGH to LOW transition
                callback=self.trigger_callback,
                bouncetime=GPIO_BOUNCE_TIME
            )
        
        logger.info("✓ Monitoring started - waiting for triggers...")
        logger.info("")
        
        # Keep script running and periodically show status
        try:
            last_status = time.time()
            
            while self.running:
                time.sleep(1)
                
                # Show status every 30 seconds
                if time.time() - last_status > 30:
                    logger.info(f"⏰ Still monitoring... (Triggers: Camera1={self.trigger_count['camera_1']}, Camera2={self.trigger_count['camera_2']}, Camera3={self.trigger_count['camera_3']})")
                    last_status = time.time()
                    
        except KeyboardInterrupt:
            logger.info("")
            logger.info("🛑 Stopping...")
    
    def cleanup(self):
        """Cleanup GPIO resources."""
        logger.info("")
        logger.info("=" * 60)
        logger.info("Test Summary")
        logger.info("=" * 60)
        logger.info(f"Camera 1 (r1/Entry) triggers: {self.trigger_count['camera_1']}")
        logger.info(f"Camera 2 (r2/Exit) triggers: {self.trigger_count['camera_2']}")
        logger.info(f"Camera 3 (r3/Auxiliary) triggers: {self.trigger_count['camera_3']}")
        logger.info(f"Total triggers: {sum(self.trigger_count.values())}")
        logger.info("=" * 60)
        logger.info("")
        
        # Cleanup GPIO
        GPIO.cleanup()
        logger.info("✓ GPIO cleanup completed")


def main():
    """Main test function."""
    tester = GPIOTester()
    
    # Setup GPIO
    if not tester.setup_gpio():
        sys.exit(1)
    
    try:
        # Start monitoring
        tester.start_monitoring()
    except KeyboardInterrupt:
        pass
    finally:
        # Cleanup
        tester.cleanup()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

