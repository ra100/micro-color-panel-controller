#!/usr/bin/env python3
"""
DaVinci Micro Panel Input Event Parser
Decodes HID input reports into structured events based on physical layout
"""

import time
import threading
from typing import Dict, List, Callable, Optional, NamedTuple
from dataclasses import dataclass
from enum import Enum

class EventType(Enum):
    """Types of input events from the panel"""
    ENCODER = "encoder"      # 12 rotary encoders + 3 trackball wheels
    BUTTON = "button"        # All push buttons including encoder buttons
    TRACKBALL = "trackball"  # 3 trackball X/Y movement

@dataclass
class InputEvent:
    """Represents a single input event from the panel"""
    type: EventType
    control_id: int
    value: int
    timestamp: float

    # Encoder-specific
    delta: int = 0

    # Button-specific
    pressed: bool = False

    # Trackball-specific
    x_delta: int = 0
    y_delta: int = 0

class ControlLayout:
    """Physical control layout mapping based on panel image"""

    # 12 Main rotary encoders (top row, left to right)
    ENCODERS = {
        0: "Y_LIFT",
        1: "Y_GAMMA",
        2: "Y_GAIN",
        3: "CONTRAST",
        4: "PIVOT",
        5: "MID_DETAIL",
        6: "COLOR_BOOST",
        7: "SHADOWS",
        8: "HIGHLIGHTS",
        9: "SATURATION",
        10: "HUE",
        11: "LUM_MIX"
    }

    # 3 Trackball wheels (encoder function of trackballs)
    TRACKBALL_WHEELS = {
        12: "LEFT_TRACKBALL_WHEEL",
        13: "CENTER_TRACKBALL_WHEEL",
        14: "RIGHT_TRACKBALL_WHEEL"
    }

    # 3 Trackballs for X/Y movement
    TRACKBALLS = {
        0: "LEFT_TRACKBALL",
        1: "CENTER_TRACKBALL",
        2: "RIGHT_TRACKBALL"
    }

    # Button layout (approximate based on visible labels)
    BUTTONS = {
        # Left side buttons
        0: "SHOT_COLOR",
        1: "OFFSET",
        2: "COPY",
        3: "PASTE",
        4: "UNDO",
        5: "REDO",
        6: "DELETE",
        7: "RESET",
        8: "BYPASS",
        9: "DISABLE",
        10: "USER",
        11: "LOOP",

        # Encoder push buttons (top row)
        12: "Y_LIFT_BTN",
        13: "Y_GAMMA_BTN",
        14: "Y_GAIN_BTN",
        15: "CONTRAST_BTN",
        16: "PIVOT_BTN",
        17: "MID_DETAIL_BTN",
        18: "COLOR_BOOST_BTN",
        19: "SHADOWS_BTN",
        20: "HIGHLIGHTS_BTN",
        21: "SATURATION_BTN",
        22: "HUE_BTN",
        23: "LUM_MIX_BTN",

        # Center area buttons
        24: "DPX",
        25: "LOG",
        26: "REC_709",
        27: "REC_2020",
        28: "WHITE",
        29: "VENUE",
        30: "CHROME",
        31: "SELECT",
        32: "LUT",
        33: "CAMERA",
        34: "FULL_DETAIL",
        35: "AUTO_BALANCE",

        # Right side buttons
        36: "PREV_MEM",
        37: "NEXT_MEM",
        38: "FULL_BYPASS",
        39: "NODE_BYPASS",
        40: "FULL_AUTO",
        41: "AUTO_COLOR",
        42: "STILL_AUTO",
        43: "PREV",
        44: "NEXT",
        45: "STOP",

        # Transport/additional
        46: "PLAY_REV",
        47: "PLAY_FWD",
        48: "RECORD",
        49: "JOG_MODE",
        50: "SHUTTLE_MODE",
        51: "SPECIAL_FUNCTION"
    }

class InputParser:
    """Parses HID input reports into structured events"""

    def __init__(self):
        self.callbacks: Dict[EventType, List[Callable]] = {
            EventType.ENCODER: [],
            EventType.BUTTON: [],
            EventType.TRACKBALL: []
        }

        # State tracking for delta calculation
        self.encoder_positions = [0] * 15  # 12 main + 3 trackball wheels
        self.button_states = [False] * 52  # All buttons
        self.trackball_positions = [(0, 0)] * 3  # 3 trackballs

        # Previous raw values for delta calculation
        self._prev_encoder_raw = [0] * 15
        self._prev_trackball_raw = [(0, 0)] * 3

        self.layout = ControlLayout()

    def register_callback(self, event_type: EventType, callback: Callable[[InputEvent], None]):
        """Register callback for specific event type"""
        self.callbacks[event_type].append(callback)

    def parse_hid_report(self, data: bytes) -> List[InputEvent]:
        """
        Parse raw HID input report into events

        Args:
            data: Raw HID report bytes

        Returns:
            List of parsed input events
        """
        events = []
        timestamp = time.time()

        if len(data) < 2:
            return events

        # Debug: Print non-zero data
        if any(b != 0 for b in data):
            hex_data = ' '.join(f'{b:02x}' for b in data[:16])
            print(f"📥 HID INPUT: [{hex_data}{'...' if len(data) > 16 else ''}] (len={len(data)})")

        # Report ID determines data format
        report_id = data[0]

        if report_id == 0x01:
            # Encoder data (hypothetical format)
            events.extend(self._parse_encoder_data(data[1:], timestamp))

        elif report_id == 0x02:
            # Button data (hypothetical format)
            events.extend(self._parse_button_data(data[1:], timestamp))

        elif report_id == 0x03:
            # Trackball data (hypothetical format)
            events.extend(self._parse_trackball_data(data[1:], timestamp))

        elif report_id == 0x04:
            # Combined data format (most likely)
            events.extend(self._parse_combined_data(data[1:], timestamp))

        else:
            # Unknown report ID - log for analysis
            if any(b != 0 for b in data):
                print(f"🔍 Unknown report ID 0x{report_id:02x}: {hex_data}")

        # Fire callbacks for each event
        for event in events:
            for callback in self.callbacks[event.type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"⚠️ Callback error: {e}")

        return events

    def _parse_encoder_data(self, data: bytes, timestamp: float) -> List[InputEvent]:
        """Parse rotary encoder data"""
        events = []

        # Assume 2 bytes per encoder (15 encoders = 30 bytes)
        if len(data) >= 30:
            for i in range(15):
                offset = i * 2
                raw_value = int.from_bytes(data[offset:offset+2], 'little', signed=True)

                delta = raw_value - self._prev_encoder_raw[i]
                self._prev_encoder_raw[i] = raw_value

                if delta != 0:
                    # Determine control name
                    if i < 12:
                        control_name = self.layout.ENCODERS.get(i, f"ENCODER_{i}")
                    else:
                        control_name = self.layout.TRACKBALL_WHEELS.get(i, f"TRACKBALL_WHEEL_{i-12}")

                    events.append(InputEvent(
                        type=EventType.ENCODER,
                        control_id=i,
                        value=raw_value,
                        delta=delta,
                        timestamp=timestamp
                    ))

                    print(f"🔄 {control_name}: {delta:+3d}")

        return events

    def _parse_button_data(self, data: bytes, timestamp: float) -> List[InputEvent]:
        """Parse button press/release data"""
        events = []

        # Assume button data is packed in bits
        # 52 buttons = 7 bytes (56 bits, 4 spare)
        if len(data) >= 7:
            for byte_idx in range(7):
                if byte_idx >= len(data):
                    break

                byte_val = data[byte_idx]
                for bit_idx in range(8):
                    button_id = byte_idx * 8 + bit_idx
                    if button_id >= 52:  # Only 52 buttons
                        break

                    pressed = bool(byte_val & (1 << bit_idx))

                    if pressed != self.button_states[button_id]:
                        self.button_states[button_id] = pressed

                        button_name = self.layout.BUTTONS.get(button_id, f"BUTTON_{button_id}")

                        events.append(InputEvent(
                            type=EventType.BUTTON,
                            control_id=button_id,
                            value=1 if pressed else 0,
                            pressed=pressed,
                            timestamp=timestamp
                        ))

                        state = "🔴 PRESS" if pressed else "⚪ RELEASE"
                        print(f"🔘 {button_name}: {state}")

        return events

    def _parse_trackball_data(self, data: bytes, timestamp: float) -> List[InputEvent]:
        """Parse trackball X/Y movement data"""
        events = []

        # Assume 4 bytes per trackball (2 for X, 2 for Y)
        # 3 trackballs = 12 bytes
        if len(data) >= 12:
            for trackball_id in range(3):
                offset = trackball_id * 4
                x_raw = int.from_bytes(data[offset:offset+2], 'little', signed=True)
                y_raw = int.from_bytes(data[offset+2:offset+4], 'little', signed=True)

                prev_x, prev_y = self._prev_trackball_raw[trackball_id]
                x_delta = x_raw - prev_x
                y_delta = y_raw - prev_y

                self._prev_trackball_raw[trackball_id] = (x_raw, y_raw)

                if x_delta != 0 or y_delta != 0:
                    trackball_name = self.layout.TRACKBALLS.get(trackball_id, f"TRACKBALL_{trackball_id}")

                    events.append(InputEvent(
                        type=EventType.TRACKBALL,
                        control_id=trackball_id,
                        value=0,
                        x_delta=x_delta,
                        y_delta=y_delta,
                        timestamp=timestamp
                    ))

                    print(f"🖱️ {trackball_name}: X{x_delta:+3d} Y{y_delta:+3d}")

        return events

    def _parse_combined_data(self, data: bytes, timestamp: float) -> List[InputEvent]:
        """Parse combined data format (most likely scenario)"""
        events = []

        # This is the format we'll need to determine through testing
        # For now, try to identify patterns in the data

        if len(data) >= 64:  # Typical HID report size
            # Try different parsing strategies based on data patterns

            # Strategy 1: Look for encoder data (first 30 bytes)
            encoder_events = self._parse_encoder_data(data[:30], timestamp)
            events.extend(encoder_events)

            # Strategy 2: Look for button data (next 7 bytes)
            button_events = self._parse_button_data(data[30:37], timestamp)
            events.extend(button_events)

            # Strategy 3: Look for trackball data (next 12 bytes)
            trackball_events = self._parse_trackball_data(data[37:49], timestamp)
            events.extend(trackball_events)

        return events

# Test function to identify input report format
def analyze_input_reports(device, duration_seconds=10):
    """
    Analyze input reports to understand the data format

    Args:
        device: USB device object
        duration_seconds: How long to capture data
    """
    print(f"🔍 Analyzing input reports for {duration_seconds} seconds...")
    print("🎛️ Please interact with ALL controls: trackballs, encoders, buttons")
    print("=" * 60)

    parser = InputParser()
    reports_seen = set()
    start_time = time.time()

    def on_event(event):
        print(f"📊 {event.type.value.upper()}: ID={event.control_id} Value={event.value}")

    parser.register_callback(EventType.ENCODER, on_event)
    parser.register_callback(EventType.BUTTON, on_event)
    parser.register_callback(EventType.TRACKBALL, on_event)

    try:
        while time.time() - start_time < duration_seconds:
            try:
                # Read input endpoint (endpoint 1 typically)
                endpoint = device[0][(2,0)][0]  # Interface 2, endpoint 0
                data = endpoint.read(64, timeout=100)  # 64 byte buffer, 100ms timeout

                if data:
                    data_bytes = bytes(data)
                    report_id = data_bytes[0] if data_bytes else 0

                    # Track unique report formats
                    data_pattern = tuple(data_bytes[:8])  # First 8 bytes as pattern
                    if data_pattern not in reports_seen:
                        reports_seen.add(data_pattern)
                        hex_str = ' '.join(f'{b:02x}' for b in data_bytes[:16])
                        print(f"🆕 NEW PATTERN: [{hex_str}...]")

                    # Parse the data
                    events = parser.parse_hid_report(data_bytes)

            except Exception as e:
                # Timeouts are normal, other errors we should see
                if "timeout" not in str(e).lower():
                    print(f"⚠️ Read error: {e}")

    except KeyboardInterrupt:
        print("\n🛑 Analysis stopped by user")

    print(f"\n📈 Analysis complete! Saw {len(reports_seen)} unique report patterns")
    return reports_seen