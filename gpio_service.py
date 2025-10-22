import logging
import threading
from typing import Callable, Optional

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    GPIO_AVAILABLE = False
    
from config import (
    GPIO_ENABLED, GPIO_TRIGGER_ENABLED, GPIO_BOUNCE_TIME,
    GPIO_CAMERA_1_PIN, GPIO_CAMERA_2_PIN, GPIO_CAMERA_3_PIN,
    CAMERA_1_ENABLED, CAMERA_2_ENABLED, CAMERA_3_ENABLED
)


class GPIOService:
    """Service to handle GPIO triggers for camera capture."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.initialized = False
        self.callbacks = {}
        
        # Check if GPIO is available and enabled
        if not GPIO_AVAILABLE:
            self.logger.warning("RPi.GPIO not available. GPIO functionality disabled.")
            return
            
        if not GPIO_ENABLED:
            self.logger.info("GPIO functionality is disabled in configuration.")
            return
            
        if not GPIO_TRIGGER_ENABLED:
            self.logger.info("GPIO triggering is disabled in configuration.")
            return
            
        try:
            # Setup GPIO mode
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Configure pins with pull-up resistors (trigger on LOW state)
            self.pin_mapping = {}
            
            if CAMERA_1_ENABLED:
                GPIO.setup(GPIO_CAMERA_1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                self.pin_mapping[GPIO_CAMERA_1_PIN] = "camera_1"
                self.logger.info(f"GPIO pin {GPIO_CAMERA_1_PIN} configured for camera_1 (r1/entry)")
                
            if CAMERA_2_ENABLED:
                GPIO.setup(GPIO_CAMERA_2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                self.pin_mapping[GPIO_CAMERA_2_PIN] = "camera_2"
                self.logger.info(f"GPIO pin {GPIO_CAMERA_2_PIN} configured for camera_2 (r2/exit)")
                
            if CAMERA_3_ENABLED:
                GPIO.setup(GPIO_CAMERA_3_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                self.pin_mapping[GPIO_CAMERA_3_PIN] = "camera_3"
                self.logger.info(f"GPIO pin {GPIO_CAMERA_3_PIN} configured for camera_3 (r3/auxiliary)")
            
            self.initialized = True
            self.logger.info("GPIO service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize GPIO: {e}")
            self.initialized = False
    
    def register_callback(self, camera_key: str, callback: Callable):
        """Register a callback function for a specific camera trigger."""
        if not self.initialized:
            self.logger.warning(f"Cannot register callback for {camera_key}: GPIO not initialized")
            return False
            
        self.callbacks[camera_key] = callback
        self.logger.info(f"Callback registered for {camera_key}")
        return True
    
    def _gpio_callback(self, channel: int):
        """Internal callback handler for GPIO events."""
        try:
            camera_key = self.pin_mapping.get(channel)
            if not camera_key:
                self.logger.warning(f"Unknown GPIO pin triggered: {channel}")
                return
                
            # Get the callback for this camera
            callback = self.callbacks.get(camera_key)
            if not callback:
                self.logger.warning(f"No callback registered for {camera_key}")
                return
                
            # Execute callback in a separate thread to avoid blocking GPIO
            thread = threading.Thread(
                target=self._execute_callback,
                args=(camera_key, callback),
                daemon=True,
                name=f"GPIO-Callback-{camera_key}"
            )
            thread.start()
            
        except Exception as e:
            self.logger.error(f"Error in GPIO callback: {e}", exc_info=True)
    
    def _execute_callback(self, camera_key: str, callback: Callable):
        """Execute the callback in a separate thread."""
        try:
            self.logger.info(f"GPIO trigger detected for {camera_key}")
            callback(camera_key)
        except Exception as e:
            self.logger.error(f"Error executing callback for {camera_key}: {e}", exc_info=True)
    
    def start_monitoring(self):
        """Start monitoring GPIO pins for triggers."""
        if not self.initialized:
            self.logger.warning("Cannot start monitoring: GPIO not initialized")
            return False
            
        try:
            # Add event detection for all configured pins (falling edge = LOW state)
            for pin, camera_key in self.pin_mapping.items():
                GPIO.add_event_detect(
                    pin,
                    GPIO.FALLING,  # Trigger on transition to LOW
                    callback=self._gpio_callback,
                    bouncetime=GPIO_BOUNCE_TIME
                )
                self.logger.info(f"Started monitoring GPIO pin {pin} for {camera_key}")
            
            self.logger.info("GPIO monitoring started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start GPIO monitoring: {e}", exc_info=True)
            return False
    
    def stop_monitoring(self):
        """Stop monitoring GPIO pins."""
        if not self.initialized:
            return
            
        try:
            # Remove event detection
            for pin in self.pin_mapping.keys():
                try:
                    GPIO.remove_event_detect(pin)
                except Exception as e:
                    self.logger.warning(f"Error removing event detect on pin {pin}: {e}")
            
            self.logger.info("GPIO monitoring stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping GPIO monitoring: {e}", exc_info=True)
    
    def cleanup(self):
        """Cleanup GPIO resources."""
        if not self.initialized:
            return
            
        try:
            self.stop_monitoring()
            GPIO.cleanup()
            self.logger.info("GPIO cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during GPIO cleanup: {e}", exc_info=True)
    
    def is_available(self) -> bool:
        """Check if GPIO service is available and initialized."""
        return self.initialized
    
    def get_pin_state(self, camera_key: str) -> Optional[bool]:
        """Get current state of a GPIO pin for a camera."""
        if not self.initialized:
            return None
            
        pin = None
        if camera_key == "camera_1":
            pin = GPIO_CAMERA_1_PIN
        elif camera_key == "camera_2":
            pin = GPIO_CAMERA_2_PIN
        elif camera_key == "camera_3":
            pin = GPIO_CAMERA_3_PIN
        
        if pin and pin in self.pin_mapping:
            try:
                return GPIO.input(pin) == GPIO.LOW
            except Exception as e:
                self.logger.error(f"Error reading GPIO pin {pin}: {e}")
        
        return None

