#!/usr/bin/env python3
"""
DaVinci Micro Panel Device Control Module
Standalone USB interface and input processing for the DaVinci Micro Color Panel
"""

import time
import threading
from typing import Optional, Callable, Dict, Any, Tuple

# Try to import USB libraries
try:
    import usb.core
    import usb.util
    import signal
    import atexit
    USB_AVAILABLE = True
    print("✅ USB libraries available")
except ImportError as e:
    print(f"⚠️ USB libraries not available: {e}")
    USB_AVAILABLE = False

class DaVinciMicroPanel:
    """DaVinci Micro Panel hardware interface"""

    # USB Device IDs
    VENDOR_ID = 0x1edb
    PRODUCT_ID = 0xda0f
    HID_INTERFACE = 2

    def __init__(self):
        self.device: Optional['usb.core.Device'] = None
        self.is_connected = False
        self.is_illuminated = False
        self.last_illumination_refresh = 0
        self.illumination_interval = 15.0  # Refresh every 15 seconds

    def connect(self) -> bool:
        """Connect to the DaVinci panel"""
        if not USB_AVAILABLE:
            print("❌ USB libraries not available")
            return False

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
            self.last_illumination_refresh = time.time()

            # Turn on illumination when connected
            self.set_illumination(True)

            return True

        except Exception as e:
            print(f"❌ USB Error during connection: {e}")
            return False

    def test_connection(self) -> bool:
        """Test if the panel is still connected and responsive"""
        if not self.is_connected or not self.device:
            return False

        try:
            # Try a simple illumination refresh as connection test
            current_time = time.time()
            if current_time - self.last_illumination_refresh > self.illumination_interval:
                self.set_illumination(True)
                self.last_illumination_refresh = current_time
            return True
        except Exception:
            print("⚠️ Panel connection lost, attempting reconnection...")
            self.is_connected = False
            return False

    def reconnect(self) -> bool:
        """Attempt to reconnect to the panel"""
        if self.is_connected:
            return True

        try:
            self.cleanup()
            return self.connect()
        except Exception as e:
            print(f"❌ Reconnection failed: {e}")
            return False

    def set_illumination(self, enabled: bool, brightness: int = 100) -> bool:
        """Control panel button illumination"""
        if not self.is_connected or not self.device or not USB_AVAILABLE:
            return False

        try:
            # First send secondary control command
            secondary_data = bytes([0x0a, 0x01])
            self.device.ctrl_transfer(
                bmRequestType=0x21,
                bRequest=0x09,
                wValue=0x030a,
                wIndex=0x0002,
                data_or_wLength=secondary_data
            )

            # Then send illumination command
            if enabled:
                brightness = max(0, min(255, brightness))
                data = bytes([0x03, brightness, brightness])
            else:
                data = bytes([0x03, 0x00, 0x00])

            # Send HID SET_REPORT command
            result = self.device.ctrl_transfer(
                bmRequestType=0x21,
                bRequest=0x09,
                wValue=0x0303,
                wIndex=0x0002,
                data_or_wLength=data
            )

            self.is_illuminated = enabled
            return True

        except Exception as e:
            print(f"❌ Failed to set illumination: {e}")
            self.is_connected = False  # Mark as disconnected on illumination failure
            return False

    def read_input(self) -> Optional[bytes]:
        """Read input data from panel with automatic reconnection"""
        if not self.is_connected:
            # Try to reconnect
            if not self.reconnect():
                return None

        if not self.device or not USB_AVAILABLE:
            return None

        try:
            # Test connection periodically
            if not self.test_connection():
                return None

            # Read from HID input endpoint with short timeout
            data = self.device.read(0x81, 64, timeout=10)
            if data and any(b != 0 for b in data):  # Only return non-zero data
                return bytes(data)
            return None

        except usb.core.USBTimeoutError:
            # Timeouts are normal during polling, don't log
            return None
        except Exception as e:
            print(f"⚠️ USB read error: {e}")
            self.is_connected = False
            return None

    def cleanup(self):
        """Cleanup resources and turn off illumination"""
        if self.is_connected:
            try:
                self.set_illumination(False)
                if self.device and USB_AVAILABLE:
                    usb.util.release_interface(self.device, self.HID_INTERFACE)
                self.is_connected = False
                print("📱 Panel disconnected")
            except Exception as e:
                print(f"⚠️ Error during cleanup: {e}")


class InputProcessor:
    """Process input data from DaVinci panel with configurable callbacks"""

    def __init__(self):
        self.trackball_callback: Optional[Callable] = None
        self.button_callback: Optional[Callable] = None
        self.encoder_callback: Optional[Callable] = None
        self.last_trackball_data = {}  # Store last values for delta calculation
        # Simple smoothing filters with shorter history for responsiveness
        self.x_history = []  # Keep last N X movements for smoothing
        self.y_history = []  # Keep last N Y movements for smoothing
        self.history_size = 4  # Reduced from 8 for more responsiveness

    def set_callbacks(self, trackball_cb=None, button_cb=None, encoder_cb=None):
        """Set callback functions for different input types"""
        if trackball_cb:
            self.trackball_callback = trackball_cb
        if button_cb:
            self.button_callback = button_cb
        if encoder_cb:
            self.encoder_callback = encoder_cb

    def process_input_data(self, data: bytes, sensitivity: float = 1.0,
                          invert_x: bool = False, invert_y: bool = False,
                          debug: bool = False) -> Dict[str, Any]:
        """Process raw input data and return structured information"""
        if not data:
            return {}

        report_id = data[0]
        result = {'report_id': report_id, 'processed': False}

        if debug:
            hex_data = ' '.join(f'{b:02x}' for b in data[:16])
            print(f"📥 Input: ID={report_id:02x} [{hex_data}]")

        try:
            if report_id == 0x05:  # Trackball and special functions
                trackball_data = self._process_trackball_data(data, sensitivity, invert_x, invert_y, debug)
                if trackball_data and self.trackball_callback:
                    self.trackball_callback(trackball_data)
                result.update(trackball_data)
                result['processed'] = True

            elif report_id == 0x02:  # Standard buttons
                button_data = self._process_button_data(data, debug)
                if button_data and self.button_callback:
                    self.button_callback(button_data)
                result.update(button_data)
                result['processed'] = True

            elif report_id == 0x06:  # Encoder rotations
                encoder_data = self._process_encoder_data(data, sensitivity, debug)
                if encoder_data and self.encoder_callback:
                    self.encoder_callback(encoder_data)
                result.update(encoder_data)
                result['processed'] = True

        except Exception as e:
            print(f"❌ Error processing input: {e}")
            result['error'] = str(e)

        return result

    def _process_trackball_data(self, data: bytes, sensitivity: float,
                               invert_x: bool, invert_y: bool, debug: bool) -> Dict[str, Any]:
        """Process trackball movement with weighted average filter"""
        trackball_data = {'type': 'trackball'}

        def signed_byte(value):
            """Convert unsigned byte to signed value"""
            return value if value < 128 else value - 256

        # Get raw movement from both potential X sources
        byte2_raw = signed_byte(data[2]) if len(data) > 2 else 0
        byte6_raw = signed_byte(data[6]) if len(data) > 6 else 0
        byte7_raw = signed_byte(data[7]) if len(data) > 7 else 0

        # Simple approach: use whichever byte has movement, but filter heavily
        x_movement = 0
        if abs(byte2_raw) > abs(byte6_raw):
            x_movement = byte2_raw
        elif abs(byte6_raw) > 0:
            x_movement = byte6_raw

        # Y movement from byte 7
        y_movement = byte7_raw if abs(byte7_raw) > 1 else 0

        # Add to history for smoothing
        self.x_history.append(x_movement)
        self.y_history.append(y_movement)

        # Keep history size manageable
        if len(self.x_history) > self.history_size:
            self.x_history.pop(0)
        if len(self.y_history) > self.history_size:
            self.y_history.pop(0)

        # Calculate weighted average - favor recent samples to reduce lag
        def weighted_average(history):
            if not history:
                return 0
            # Give more weight to recent samples: [1, 2, 3, 4] weights for [oldest, ..., newest]
            weights = list(range(1, len(history) + 1))
            weighted_sum = sum(val * weight for val, weight in zip(history, weights))
            weight_total = sum(weights)
            return weighted_sum / weight_total if weight_total > 0 else 0

        smooth_x = weighted_average(self.x_history)
        smooth_y = weighted_average(self.y_history)

        # Apply scaling and sensitivity - boost Y movement significantly
        left_x_delta = smooth_x * 0.25  # Slightly reduced X for better control
        left_y_delta = smooth_y * 0.8   # Much higher Y sensitivity (was 0.3)

        # Wheel movement (byte 10)
        wheel_raw = data[10] if len(data) > 10 else 0
        wheel_delta = 0
        if wheel_raw != 0:
            wheel_delta = signed_byte(wheel_raw) * 0.3

        # CENTER trackball analysis (bytes 14, 15)
        center_x_delta = 0
        center_y_delta = 0
        if len(data) > 15:
            center_x_delta = signed_byte(data[14]) * 0.3
            center_y_delta = signed_byte(data[15]) * 0.3

        # Apply sensitivity and inversion
        if invert_x:
            left_x_delta = -left_x_delta
            center_x_delta = -center_x_delta
        if invert_y:
            left_y_delta = -left_y_delta
            center_y_delta = -center_y_delta

        left_x_delta *= sensitivity
        left_y_delta *= sensitivity
        center_x_delta *= sensitivity
        center_y_delta *= sensitivity
        wheel_delta *= sensitivity

        # Adjusted threshold for new sensitivity levels
        movement_threshold = 0.05  # Reduced from 0.1 for better responsiveness
        has_left_movement = abs(left_x_delta) > movement_threshold or abs(left_y_delta) > movement_threshold
        has_center_movement = abs(center_x_delta) > movement_threshold or abs(center_y_delta) > movement_threshold
        has_wheel_movement = abs(wheel_delta) > movement_threshold

        if has_left_movement:
            trackball_data['left_trackball'] = {
                'x': left_x_delta,
                'y': left_y_delta,
                'raw': {'byte2': byte2_raw, 'byte6': byte6_raw, 'byte7': byte7_raw, 'smooth_x': smooth_x, 'smooth_y': smooth_y}
            }
            if debug:
                print(f"🎮 LEFT trackball: delta=({left_x_delta:.2f},{left_y_delta:.2f}) raw: b2={byte2_raw} b6={byte6_raw} b7={byte7_raw} smooth: x={smooth_x:.1f} y={smooth_y:.1f}")

        if has_center_movement:
            trackball_data['center_trackball'] = {
                'x': center_x_delta,
                'y': center_y_delta,
                'raw': {'x': data[14], 'y': data[15]}
            }
            if debug:
                print(f"🎮 CENTER trackball: delta=({center_x_delta:.2f},{center_y_delta:.2f})")

        if has_wheel_movement:
            trackball_data['wheel'] = {
                'delta': wheel_delta,
                'raw': wheel_raw
            }
            if debug:
                print(f"🎮 Wheel: delta={wheel_delta:.2f}")

        return trackball_data if (has_left_movement or has_center_movement or has_wheel_movement) else {}

    def _process_button_data(self, data: bytes, debug: bool) -> Dict[str, Any]:
        """Process button press data"""
        if len(data) < 8:
            return {}

        pressed_buttons = []

        # Check each byte for button changes
        for byte_idx in range(1, 8):  # Skip report ID
            byte_val = data[byte_idx]
            if byte_val != 0:  # Button pressed
                # Calculate button ID based on byte position and bit
                for bit in range(8):
                    if byte_val & (1 << bit):
                        button_id = (byte_idx - 1) * 8 + bit + 8  # Offset for encoder buttons
                        pressed_buttons.append(button_id)

        if pressed_buttons:
            if debug:
                print(f"🔘 Buttons pressed: {pressed_buttons}")
            return {'type': 'button', 'buttons': pressed_buttons}

        return {}

    def _process_encoder_data(self, data: bytes, sensitivity: float, debug: bool) -> Dict[str, Any]:
        """Process encoder rotation data"""
        if debug:
            hex_data = ' '.join(f'{b:02x}' for b in data[:16])
            print(f"🔄 Encoder data: [{hex_data}]")

        # TODO: Implement encoder delta calculation based on mapping data
        return {'type': 'encoder', 'raw_data': list(data[:16])}

    def _calculate_trackball_delta(self, *bytes_data) -> float:
        """Legacy method - replaced by simplified approach"""
        # This method is no longer used, keeping for compatibility
        return 0.0

# Control mappings for reference
ENCODER_BUTTONS = {
    'COLOR_BOOST_BUTTON': 14, 'CONTRAST_BUTTON': 11, 'HIGHLIGHTS_BUTTON': 16,
    'HUE_BUTTON': 18, 'LUM_MIX_BUTTON': 19, 'MID_DETAIL_BUTTON': 13,
    'PIVOT_BUTTON': 12, 'SATURATION_BUTTON': 17, 'SHADOWS_BUTTON': 15,
    'Y_GAIN_BUTTON': 10, 'Y_GAMMA_BUTTON': 9, 'Y_LIFT_BUTTON': 8,
}

FUNCTION_BUTTONS = {
    'ADD_KEYFRAME': 46, 'ADD_NODE': 44, 'ADD_WINDOW': 45, 'AUTO_COLOR': 20,
    'BACKWARD_PLAY': 57, 'BYPASS': 28, 'COPY': 22, 'CURSOR': 39,
    'DELETE': 26, 'DISABLE': 29, 'FORWARD_PLAY': 58, 'GRAB_STILL': 36,
    'H_LITE': 37, 'LOOP': 31, 'NEXT_CLIP': 56, 'NEXT_FRAME': 54,
    'NEXT_KEYFRAME': 50, 'NEXT_NODE': 52, 'NEXT_STILL': 48, 'OFFSET': 21,
    'PASTE': 23, 'PLAY_STILL': 34, 'PREV_CLIP': 55, 'PREV_FRAME': 53,
    'PREV_KEYFRAME': 49, 'PREV_NODE': 51, 'PREV_STILL': 47, 'REDO': 25,
    'RESET': 27, 'RESET_GAIN': 43, 'RESET_GAMMA': 42, 'RESET_LIFT': 41,
    'SELECT': 40, 'SPECIAL_LEFT': 32, 'SPECIAL_RIGHT': 33, 'STOP': 59,
    'UNDO': 24, 'USER': 30, 'VIEWER': 38, 'WIPE_STILL': 35,
}

TRACKBALL_AXES = {
    'LEFT_TRACKBALL_X': [2, 6, 3], 'LEFT_TRACKBALL_Y': [6, 2, 7], 'LEFT_TRACKBALL_WHEEL': [10],
    'CENTER_TRACKBALL_X': [14, 15], 'CENTER_TRACKBALL_Y': [14],
}