#!/usr/bin/env python3
import os
import sys
import time
import signal
import logging
import threading

# Prefer RPi.GPIO; fall back to gpiozero if desired (but we'll stick to RPi.GPIO)
try:
    import RPi.GPIO as GPIO
except Exception as e:
    print("ERROR: RPi.GPIO not available. Install it or run on Raspberry Pi OS.\n", e)
    sys.exit(1)

from capture_service import CameraService
from config import (
    GPIO_ENABLED,
    GPIO_TRIGGER_ENABLED,
    GPIO_BOUNCE_TIME,
    GPIO_CAMERA_1_PIN,
    GPIO_CAMERA_2_PIN,
    GPIO_CAMERA_3_PIN,
)

# ----- Logging setup -----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("gpio_daemon")

# ----- Pin→camera map -----
PIN_TO_CAMERA = {}

def _build_pin_map():
    """Build the pin-to-camera map from config pins."""
    return {
        GPIO_CAMERA_1_PIN: "camera_1",
        GPIO_CAMERA_2_PIN: "camera_2",
        GPIO_CAMERA_3_PIN: "camera_3",
    }

# ----- Cooldown guard to avoid repeated triggers -----
_LAST_TRIGGER_TS = {}
COOLDOWN_SEC = 0.8  # short cooldown to avoid multi-captures if bouncing

# ----- Capture worker -----
def _capture_async(service: CameraService, camera_key: str):
    try:
        logger.info(f"Trigger received -> {camera_key}: capturing...")
        result = service.capture_by_key(camera_key)  # queues background S3 upload internally
        if result:
            logger.info(
                f"Captured {result['filename']} at {result['local_path']} (camera={result['camera_name']})"
            )
        else:
            logger.warning(f"Capture failed for {camera_key}")
    except Exception as e:
        logger.exception(f"Unhandled error in capture worker for {camera_key}: {e}")

def _button_callback_factory(service: CameraService, camera_key: str):
    def _inner(channel_pin):
        now = time.time()
        last = _LAST_TRIGGER_TS.get(camera_key, 0)
        if now - last < COOLDOWN_SEC:
            # ignore very fast repeats
            return
        _LAST_TRIGGER_TS[camera_key] = now

        # Run capture in a thread to keep GPIO callback lightweight
        t = threading.Thread(target=_capture_async, args=(service, camera_key), daemon=True)
        t.start()
    return _inner

def _setup_gpio(pin_to_camera: dict):
    """
    Configure GPIO for 3 push buttons using internal pull-ups.
    Wiring: one side of button to the GPIO pin, the other side to GND.
    We trigger on FALLING edge (pressed -> goes to ground).
    """
    GPIO.setmode(GPIO.BCM)  # use BCM numbering so 18,19,20 match config exactly
    for pin, camera_key in pin_to_camera.items():
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # internal pull-up
        GPIO.add_event_detect(
            pin,
            GPIO.FALLING,
            bouncetime=GPIO_BOUNCE_TIME,
            callback=_button_callback_factory(service, camera_key)
        )
        logger.info(f"Configured GPIO pin {pin} for {camera_key}")

def _cleanup():
    try:
        GPIO.cleanup()
    except Exception:
        pass

def _handle_exit(signum, frame):
    logger.info(f"Received signal {signum}. Shutting down...")
    try:
        service.stop_upload_service(wait_for_completion=False)
    except Exception:
        pass
    _cleanup()
    sys.exit(0)

if __name__ == "__main__":
    if not GPIO_ENABLED or not GPIO_TRIGGER_ENABLED:
        logger.error("GPIO triggering is disabled by configuration. Set GPIO_ENABLED=true and GPIO_TRIGGER_ENABLED=true in your .env")
        sys.exit(1)

    # Build pin map and log
    PIN_TO_CAMERA = _build_pin_map()
    logger.info(f"Pin map: {PIN_TO_CAMERA}")

    # Start camera service + background uploader
    service = CameraService()  # handles local save + queue upload
    service.start_upload_service()  # starts background + retry workers

    # Setup GPIO and callbacks
    _setup_gpio(PIN_TO_CAMERA)

    # Signal handling for clean shutdown
    signal.signal(signal.SIGINT, _handle_exit)
    signal.signal(signal.SIGTERM, _handle_exit)

    logger.info("GPIO daemon is running. Press the physical buttons to capture images.")
    try:
        while True:
            time.sleep(1)
    finally:
        _handle_exit(signal.SIGTERM, None)
