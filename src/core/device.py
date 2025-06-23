"""
DaVinci Micro Panel HID Device Communication

This module handles low-level USB HID communication with the DaVinci Micro Color Panel.
Based on reverse engineering of USB HID reports and protocol analysis.
"""

import hid
import threading
import time
import logging
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Device identifiers
VENDOR_ID = 0x1edb  # Blackmagic Design
PRODUCT_ID = 0xda0f  # DaVinci Resolve Micro Color Panel


class EventType(Enum):
    """Types of events the panel can generate"""
    ROTARY = "rotary"
    BUTTON = "button"
    TRACKBALL = "trackball"
    UNKNOWN = "unknown"


@dataclass
class PanelEvent:
    """Represents an input event from the panel"""
    type: EventType
    id: int  # Control ID within its type (0-14 for rotaries, 0-51 for buttons, 0-2 for trackballs)
    value: int
    timestamp: float

    # For rotary encoders (15 total: 12 main + 3 trackball wheels)
    delta: int = 0

    # For buttons (52 total: 12 rotary push buttons + 40 other buttons)
    pressed: bool = False

    # For trackball (3 trackballs total)
    x_delta: int = 0
    y_delta: int = 0
    trackball_id: int = 0  # Which trackball (0, 1, or 2)


class MicroPanel:
    """
    Main interface for communicating with the DaVinci Micro Color Panel

    This class handles:
    - Device connection and initialization
    - Reading input events (rotaries, buttons, trackballs)
    - Sending output commands (LEDs, displays)
    - Event callbacks and processing
    """

    def __init__(self):
        self.device = None
        self.connected = False
        self.running = False
        self.read_thread = None
        self.event_callback = None

                # Panel state tracking - corrected hardware layout
        self.rotary_positions = [0] * 15  # 12 main rotaries + 3 trackball wheels
        self.button_states = [False] * 52  # 12 rotary buttons + 40 other buttons
        self.trackball_states = [(0, 0)] * 3  # 3 trackballs (x, y) positions
        self.led_states = [False] * 16  # LED indicators (estimate)

        # Previous state for delta calculation
        self._prev_rotary_raw = [0] * 15  # All rotary encoders
        self._prev_trackball_pos = [(0, 0)] * 3  # Previous trackball positions

    def connect(self) -> bool:
        """
        Connect to the DaVinci Micro Panel

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.info("Searching for DaVinci Micro Panel...")

            # Find the device
            devices = hid.enumerate(VENDOR_ID, PRODUCT_ID)
            if not devices:
                logger.error("DaVinci Micro Panel not found. Check USB connection.")
                return False

            logger.info(f"Found {len(devices)} interface(s)")

            # Try to connect to the HID interface (usually interface 2)
            for device_info in devices:
                if device_info.get('interface_number') == 2:
                    try:
                        self.device = hid.device()
                        self.device.open_path(device_info['path'])
                        logger.info(f"Connected to panel: {device_info['product_string']}")
                        self.connected = True
                        return True
                    except Exception as e:
                        logger.warning(f"Failed to open interface {device_info.get('interface_number', 'unknown')}: {e}")
                        continue

            # If specific interface not found, try the first available
            if devices:
                try:
                    self.device = hid.device()
                    self.device.open_path(devices[0]['path'])
                    logger.info(f"Connected to panel: {devices[0]['product_string']}")
                    self.connected = True
                    return True
                except Exception as e:
                    logger.error(f"Failed to connect: {e}")
                    return False

        except Exception as e:
            logger.error(f"Error connecting to device: {e}")
            return False

    def disconnect(self):
        """Disconnect from the panel"""
        self.stop_reading()
        if self.device:
            try:
                self.device.close()
                logger.info("Disconnected from panel")
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
        self.connected = False
        self.device = None

    def start_reading(self, callback: Optional[Callable[[PanelEvent], None]] = None):
        """
        Start reading events from the panel in a background thread

        Args:
            callback: Function to call when events are received
        """
        if not self.connected:
            logger.error("Device not connected")
            return

        self.event_callback = callback
        self.running = True
        self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.read_thread.start()
        logger.info("Started reading panel events")

    def stop_reading(self):
        """Stop reading events from the panel"""
        self.running = False
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join(timeout=1.0)
            logger.info("Stopped reading panel events")

    def _read_loop(self):
        """Main event reading loop (runs in background thread)"""
        while self.running and self.connected:
            try:
                # Read HID report with timeout
                data = self.device.read(64, timeout_ms=100)
                if data:
                    events = self._parse_hid_report(data)
                    for event in events:
                        if self.event_callback:
                            self.event_callback(event)

            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    logger.error(f"Error reading from device: {e}")
                    # Try to reconnect after a short delay
                    time.sleep(1.0)
                    if not self._attempt_reconnect():
                        break

    def _attempt_reconnect(self) -> bool:
        """Attempt to reconnect to the device"""
        logger.info("Attempting to reconnect...")
        self.connected = False
        if self.device:
            try:
                self.device.close()
            except:
                pass
        return self.connect()

    def _parse_hid_report(self, data: List[int]) -> List[PanelEvent]:
        """
        Parse raw HID report data into panel events

        This is where we interpret the USB HID reports from the panel.
        The actual format will need to be determined through reverse engineering.

        Args:
            data: Raw HID report data

        Returns:
            List of parsed events
        """
        events = []
        timestamp = time.time()

        if len(data) < 8:
            return events

        # This is a placeholder implementation
        # Real implementation would need reverse engineering of the HID protocol

        # Example parsing (to be replaced with actual protocol):
        # Report ID might be data[0]
        report_id = data[0] if data else 0

        if report_id == 0x01:  # Hypothetical rotary encoder report
            # Parse rotary encoder data (15 total: 12 main + 3 trackball wheels)
            # This is just an example - real format TBD
            for i in range(min(15, (len(data) - 1) // 2)):
                raw_value = data[1 + i * 2] | (data[2 + i * 2] << 8)
                delta = raw_value - self._prev_rotary_raw[i]
                self._prev_rotary_raw[i] = raw_value

                if delta != 0:
                    # Normalize delta (handle wrap-around)
                    if delta > 32767:
                        delta -= 65536
                    elif delta < -32768:
                        delta += 65536

                    events.append(PanelEvent(
                        type=EventType.ROTARY,
                        id=i,
                        value=raw_value,
                        delta=delta,
                        timestamp=timestamp
                    ))

        elif report_id == 0x02:  # Hypothetical button report
            # Parse button states
            button_data = data[1:5]  # Assume 4 bytes of button data
            for byte_idx, byte_val in enumerate(button_data):
                for bit_idx in range(8):
                    button_id = byte_idx * 8 + bit_idx
                    if button_id < len(self.button_states):
                        pressed = bool(byte_val & (1 << bit_idx))
                        if pressed != self.button_states[button_id]:
                            self.button_states[button_id] = pressed
                            events.append(PanelEvent(
                                type=EventType.BUTTON,
                                id=button_id,
                                value=1 if pressed else 0,
                                pressed=pressed,
                                timestamp=timestamp
                            ))

        elif report_id == 0x03:  # Hypothetical trackball report
            # Parse trackball movement
            if len(data) >= 5:
                x_delta = data[1] - 128  # Convert to signed
                y_delta = data[2] - 128

                if x_delta != 0 or y_delta != 0:
                    events.append(PanelEvent(
                        type=EventType.TRACKBALL,
                        id=0,  # Left trackball
                        value=0,
                        x_delta=x_delta,
                        y_delta=y_delta,
                        timestamp=timestamp
                    ))

        return events

    def set_led(self, led_id: int, state: bool) -> bool:
        """
        Control an LED on the panel

        Args:
            led_id: LED identifier (0-15)
            state: True to turn on, False to turn off

        Returns:
            bool: True if successful
        """
        if not self.connected or not self.device:
            return False

        if not (0 <= led_id < 16):
            logger.error(f"Invalid LED ID: {led_id}")
            return False

        try:
            # This is a placeholder - actual command format TBD
            command = [0x10, led_id, 1 if state else 0] + [0] * 61
            result = self.device.write(command)

            if result > 0:
                self.led_states[led_id] = state
                return True
            else:
                logger.error(f"Failed to set LED {led_id}")
                return False

        except Exception as e:
            logger.error(f"Error setting LED {led_id}: {e}")
            return False

    def set_display(self, display_id: int, text: str) -> bool:
        """
        Update text on a panel display

        Args:
            display_id: Display identifier
            text: Text to display (will be truncated if too long)

        Returns:
            bool: True if successful
        """
        if not self.connected or not self.device:
            return False

        try:
            # This is a placeholder - actual command format TBD
            text_bytes = text.encode('utf-8')[:32]  # Limit length
            command = [0x20, display_id] + list(text_bytes) + [0] * (62 - len(text_bytes))
            result = self.device.write(command)

            return result > 0

        except Exception as e:
            logger.error(f"Error setting display {display_id}: {e}")
            return False

    def get_device_info(self) -> Dict[str, Any]:
        """Get information about the connected device"""
        if not self.connected or not self.device:
            return {}

        try:
            return {
                'manufacturer': self.device.get_manufacturer_string(),
                'product': self.device.get_product_string(),
                'serial': self.device.get_serial_number_string(),
                'vendor_id': f"0x{VENDOR_ID:04x}",
                'product_id': f"0x{PRODUCT_ID:04x}",
            }
        except Exception as e:
            logger.error(f"Error getting device info: {e}")
            return {}

    def reset_panel(self) -> bool:
        """Reset panel to default state (turn off all LEDs, clear displays)"""
        if not self.connected:
            return False

        success = True

        # Turn off all LEDs
        for i in range(16):
            success &= self.set_led(i, False)

        # Clear displays (if any)
        # This would depend on the actual panel capabilities

        return success


# Convenience function for basic usage
def find_panel() -> Optional[MicroPanel]:
    """
    Find and connect to a DaVinci Micro Panel

    Returns:
        MicroPanel instance if found and connected, None otherwise
    """
    panel = MicroPanel()
    if panel.connect():
        return panel
    return None


if __name__ == "__main__":
    # Basic test/demo
    def on_event(event: PanelEvent):
        print(f"Event: {event.type.value} ID:{event.id} Value:{event.value}")
        if event.type == EventType.ROTARY:
            print(f"  Rotary delta: {event.delta}")
        elif event.type == EventType.BUTTON:
            print(f"  Button {'pressed' if event.pressed else 'released'}")
        elif event.type == EventType.TRACKBALL:
            print(f"  Trackball movement: x={event.x_delta}, y={event.y_delta}")

    panel = find_panel()
    if panel:
        print("Panel connected! Press Ctrl+C to exit.")
        panel.start_reading(on_event)

        try:
            # Test LED control
            for i in range(5):
                panel.set_led(i % 4, True)
                time.sleep(0.5)
                panel.set_led(i % 4, False)

            # Keep running
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            panel.disconnect()
    else:
        print("No panel found. Make sure it's connected and you have permissions.")
        print("Try running: sudo python device.py")