#!/usr/bin/env python3
"""
DaVinci Micro Panel Device Interface
Handles USB communication with the panel including illumination control
"""

import usb.core
import usb.util
import time
import threading
import atexit
import signal
import sys
from typing import Optional, Callable, Dict, Any

class DaVinciMicroPanel:
    """Interface for DaVinci Micro Color Panel"""

    # USB Device IDs
    VENDOR_ID = 0x1edb
    PRODUCT_ID = 0xda0f

    # USB Interface
    HID_INTERFACE = 2

    def __init__(self):
        self.device: Optional[usb.core.Device] = None
        self.is_connected = False
        self.is_illuminated = False
        self.input_thread: Optional[threading.Thread] = None
        self.running = False

        # Callbacks for input events
        self.button_callbacks: Dict[int, Callable] = {}
        self.encoder_callbacks: Dict[int, Callable] = {}
        self.trackball_callbacks: Dict[int, Callable] = {}

        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🔌 Received signal {signum}, shutting down panel...")
        self.cleanup()
        sys.exit(0)

    def connect(self) -> bool:
        """Connect to the DaVinci panel"""
        try:
            # Find the device
            self.device = usb.core.find(idVendor=self.VENDOR_ID, idProduct=self.PRODUCT_ID)
            if self.device is None:
                print("❌ DaVinci Micro Panel not found!")
                return False

            print(f"✅ Found DaVinci Micro Panel: {self.device}")

            # Detach kernel driver if necessary
            if self.device.is_kernel_driver_active(self.HID_INTERFACE):
                print(f"🔓 Detaching kernel driver from interface {self.HID_INTERFACE}")
                self.device.detach_kernel_driver(self.HID_INTERFACE)

            # Claim the HID interface
            usb.util.claim_interface(self.device, self.HID_INTERFACE)
            print(f"✅ Claimed HID interface {self.HID_INTERFACE}")

            self.is_connected = True

            # Turn on illumination when connected
            self.set_illumination(True)

            return True

        except usb.core.USBError as e:
            print(f"❌ USB Error during connection: {e}")
            return False

    def disconnect(self):
        """Disconnect from the panel"""
        if not self.is_connected:
            return

        try:
            # Turn off illumination before disconnecting
            self.set_illumination(False)

            # Stop input monitoring
            self.stop_input_monitoring()

            # Release the interface
            if self.device:
                usb.util.release_interface(self.device, self.HID_INTERFACE)
                print(f"🔓 Released interface {self.HID_INTERFACE}")

            self.is_connected = False
            self.device = None
            print("📱 Panel disconnected")

        except Exception as e:
            print(f"⚠️ Error during disconnect: {e}")

    def set_illumination(self, enabled: bool, brightness: int = 100) -> bool:
        """
        Control panel button illumination

        Args:
            enabled: True to turn on, False to turn off
            brightness: Brightness level 0-255 (default: 100 for medium brightness)

        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected or not self.device:
            print("❌ Panel not connected")
            return False

        try:
            if enabled:
                # Turn on illumination with specified brightness
                brightness = max(0, min(255, brightness))  # Clamp to valid range
                data = bytes([0x03, brightness, brightness])
                print(f"💡 Turning ON panel illumination (brightness: {brightness})")
            else:
                # Turn off illumination
                data = bytes([0x03, 0x00, 0x00])
                print("🔘 Turning OFF panel illumination")

            # Send HID SET_REPORT command
            result = self.device.ctrl_transfer(
                bmRequestType=0x21,  # Host->Device, Class, Interface
                bRequest=0x09,       # SET_REPORT
                wValue=0x0303,       # Report Type 3, Report ID 0x03
                wIndex=self.HID_INTERFACE,
                data_or_wLength=data
            )

            self.is_illuminated = enabled
            print(f"✅ Illumination {'ON' if enabled else 'OFF'} - Success!")
            return True

        except usb.core.USBError as e:
            print(f"❌ Failed to set illumination: {e}")
            return False

    def set_secondary_control(self, value: int = 0x01) -> bool:
        """
        Set secondary control (Report ID 0x0a)
        Purpose unclear, but seems to affect panel state
        """
        if not self.is_connected or not self.device:
            return False

        try:
            data = bytes([0x0a, value])

            result = self.device.ctrl_transfer(
                bmRequestType=0x21,
                bRequest=0x09,
                wValue=0x030a,  # Report Type 3, Report ID 0x0a
                wIndex=self.HID_INTERFACE,
                data_or_wLength=data
            )

            print(f"🔧 Set secondary control: 0x{value:02x}")
            return True

        except usb.core.USBError as e:
            print(f"❌ Failed to set secondary control: {e}")
            return False

    def start_input_monitoring(self):
        """Start monitoring input events from the panel"""
        if not self.is_connected or self.running:
            return

        self.running = True
        self.input_thread = threading.Thread(target=self._input_monitor_loop, daemon=True)
        self.input_thread.start()
        print("🎛️ Started input monitoring")

    def stop_input_monitoring(self):
        """Stop monitoring input events"""
        self.running = False
        if self.input_thread and self.input_thread.is_alive():
            self.input_thread.join(timeout=1.0)
        print("⏹️ Stopped input monitoring")

    def _input_monitor_loop(self):
        """Main input monitoring loop"""
        while self.running and self.is_connected:
            try:
                # Read input events from the panel
                # This would be implemented based on the HID input reports
                # For now, just a placeholder
                time.sleep(0.01)  # 100Hz polling

            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    print(f"⚠️ Input monitoring error: {e}")
                time.sleep(0.1)

    def register_button_callback(self, button_id: int, callback: Callable):
        """Register callback for button press events"""
        self.button_callbacks[button_id] = callback

    def register_encoder_callback(self, encoder_id: int, callback: Callable):
        """Register callback for encoder rotation events"""
        self.encoder_callbacks[encoder_id] = callback

    def register_trackball_callback(self, trackball_id: int, callback: Callable):
        """Register callback for trackball movement events"""
        self.trackball_callbacks[trackball_id] = callback

    def cleanup(self):
        """Cleanup resources and turn off illumination"""
        print("🧹 Cleaning up DaVinci panel...")
        self.disconnect()

    def __enter__(self):
        """Context manager entry"""
        if self.connect():
            return self
        else:
            raise RuntimeError("Failed to connect to DaVinci panel")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup"""
        self.cleanup()

# Test the illumination control
if __name__ == "__main__":
    print("🎯 Testing DaVinci Panel Illumination Control")
    print("=" * 50)

    try:
        with DaVinciMicroPanel() as panel:
            print("\n💡 Panel should be illuminated now!")

            # Test different brightness levels
            print("\n🌟 Testing brightness levels...")
            for brightness in [50, 100, 150, 200, 255]:
                print(f"Setting brightness to {brightness}")
                panel.set_illumination(True, brightness)
                time.sleep(1)

            # Test secondary control
            print("\n🔧 Testing secondary control...")
            panel.set_secondary_control(0xFF)
            time.sleep(1)
            panel.set_secondary_control(0x01)

            print("\n⏰ Keeping panel on for 5 seconds...")
            time.sleep(5)

            print("\n🔘 Panel will turn off when exiting...")

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

    print("✅ Test completed - panel should be OFF now")