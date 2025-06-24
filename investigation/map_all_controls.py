#!/usr/bin/env python3
"""
Systematic Control Mapping Tool
Guides you through mapping every control on the DaVinci panel
"""

import sys
import os
import time
import usb.core
from collections import defaultdict

# Add our modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.device import DaVinciMicroPanel

class ControlMapper:
    """Systematic control mapping with guided instructions"""

    def __init__(self):
        self.panel = None
        self.control_map = {
            'buttons': {},      # bit_position -> control_name
            'encoders': {},     # byte_position -> control_name
            'trackballs': {}    # axis_position -> control_name
        }

    def connect(self):
        """Connect to panel"""
        print("🔌 Connecting to DaVinci Micro Panel...")

        self.panel = DaVinciMicroPanel()
        if not self.panel.connect():
            print("❌ Failed to connect!")
            return False

        print("✅ Panel connected and illuminated!")
        return True

    def test_control(self, instruction, duration=8):
        """Test a specific control with guided instruction"""
        print(f"\n🎯 {instruction}")
        print("=" * 60)

        input("🟢 Press ENTER when ready, then follow the instruction...")

        print(f"⏱️ Recording for {duration} seconds - GO!")

        events = []
        start_time = time.time()

        try:
            while time.time() - start_time < duration:
                try:
                    data = self.panel.device.read(0x81, 64, timeout=50)

                    if data:
                        data_bytes = bytes(data)

                        # Store all non-zero events
                        if any(b != 0 for b in data_bytes):
                            timestamp = time.time() - start_time
                            events.append((timestamp, data_bytes))

                            # Show real-time feedback
                            report_id = data_bytes[0]
                            if report_id == 0x02:  # Button
                                # Find which bits are set
                                for byte_idx in range(1, 8):
                                    if byte_idx < len(data_bytes) and data_bytes[byte_idx] != 0:
                                        byte_val = data_bytes[byte_idx]
                                        for bit in range(8):
                                            if byte_val & (1 << bit):
                                                print(f"  🔘 Button: Byte{byte_idx} Bit{bit} (0x{byte_val:02x})")

                            elif report_id == 0x06:  # Trackball/Encoder
                                # Show position data
                                non_zero_positions = []
                                for i in range(1, min(16, len(data_bytes)), 2):
                                    if i+1 < len(data_bytes):
                                        value = int.from_bytes(data_bytes[i:i+2], 'little', signed=True)
                                        if value != 0:
                                            non_zero_positions.append(f"Pos{i}-{i+1}:{value:+d}")
                                if non_zero_positions:
                                    print(f"  🎛️ Track/Enc: {' '.join(non_zero_positions)}")

                except usb.core.USBTimeoutError:
                    continue

        except KeyboardInterrupt:
            print("\n⏸️ Test stopped early")

        print(f"✅ Captured {len(events)} events")
        return events

    def analyze_events(self, events, control_name):
        """Analyze captured events for patterns"""
        if not events:
            print("❌ No events captured - try again")
            return

        print(f"\n🔍 Analysis for {control_name}:")

        # Group by report type
        by_report = defaultdict(list)
        for timestamp, data in events:
            by_report[data[0]].append((timestamp, data))

        for report_id, report_events in by_report.items():
            print(f"  📋 Report 0x{report_id:02x}: {len(report_events)} events")

            if report_id == 0x02:  # Button analysis
                self._analyze_button_events(report_events, control_name)
            elif report_id == 0x06:  # Trackball/Encoder analysis
                self._analyze_movement_events(report_events, control_name)

    def _analyze_button_events(self, events, control_name):
        """Analyze button events to find bit positions"""
        bit_patterns = set()

        for timestamp, data in events:
            for byte_idx in range(1, min(8, len(data))):
                byte_val = data[byte_idx]
                if byte_val != 0:
                    for bit in range(8):
                        if byte_val & (1 << bit):
                            bit_id = byte_idx * 8 + bit
                            bit_patterns.add((byte_idx, bit, bit_id))

        if bit_patterns:
            print(f"    🎯 Button bits detected:")
            for byte_idx, bit, bit_id in sorted(bit_patterns):
                print(f"      Byte{byte_idx} Bit{bit} → Button#{bit_id}")
                self.control_map['buttons'][bit_id] = control_name
        else:
            print(f"    ❌ No button patterns found")

    def _analyze_movement_events(self, events, control_name):
        """Analyze trackball/encoder movement events"""
        position_ranges = defaultdict(lambda: {'min': 999999, 'max': -999999, 'count': 0})

        for timestamp, data in events:
            for i in range(1, min(16, len(data)), 2):
                if i+1 < len(data):
                    value = int.from_bytes(data[i:i+2], 'little', signed=True)
                    if value != 0:
                        position_ranges[i]['min'] = min(position_ranges[i]['min'], value)
                        position_ranges[i]['max'] = max(position_ranges[i]['max'], value)
                        position_ranges[i]['count'] += 1

        if position_ranges:
            print(f"    🎯 Movement data detected:")
            for pos, stats in sorted(position_ranges.items()):
                if stats['count'] > 0:
                    print(f"      Bytes{pos}-{pos+1}: {stats['min']:+d} to {stats['max']:+d} ({stats['count']} events)")
                    axis_name = f"{control_name}_bytes_{pos}_{pos+1}"
                    self.control_map['trackballs'][pos] = axis_name
        else:
            print(f"    ❌ No movement data found")

    def run_systematic_mapping(self):
        """Run complete systematic mapping"""
        print("🎯 SYSTEMATIC CONTROL MAPPING")
        print("=" * 60)
        print("We'll test each control type systematically")
        print("Follow the instructions carefully for best results")
        print()

        if not self.connect():
            return

        try:
            # Button mapping
            print("\n🔘 BUTTON MAPPING PHASE")
            print("=" * 40)

            button_tests = [
                "Press and release the SHOT COLOR button (left side, top)",
                "Press and release the COPY button (left side)",
                "Press and release the PASTE button (left side)",
                "Press and release the Y LIFT encoder button (top row, leftmost)",
                "Press and release the Y GAMMA encoder button (top row, 2nd)",
                "Press and release the HUE encoder button (top row, rightmost)",
                "Press and release the PREV button (right side)",
                "Press and release the NEXT button (right side)",
                "Press and release the REC 709 button (center area)",
                "Press and release the AUTO BALANCE button (center-right)",
            ]

            for i, instruction in enumerate(button_tests, 1):
                print(f"\n🔘 Button Test {i}/{len(button_tests)}")
                events = self.test_control(instruction, duration=6)
                self.analyze_events(events, f"BUTTON_{i}")

            # Encoder mapping
            print("\n\n🔄 ENCODER MAPPING PHASE")
            print("=" * 40)

            encoder_tests = [
                "Turn Y LIFT encoder (top-left) clockwise and counter-clockwise",
                "Turn Y GAMMA encoder (2nd from left) both directions",
                "Turn Y GAIN encoder (3rd from left) both directions",
                "Turn CONTRAST encoder (4th from left) both directions",
                "Turn HUE encoder (top-right) both directions",
                "Turn LUM MIX encoder (rightmost) both directions",
            ]

            for i, instruction in enumerate(encoder_tests, 1):
                print(f"\n🔄 Encoder Test {i}/{len(encoder_tests)}")
                events = self.test_control(instruction, duration=8)
                self.analyze_events(events, f"ENCODER_{i}")

            # Trackball mapping
            print("\n\n🖱️ TRACKBALL MAPPING PHASE")
            print("=" * 40)

            trackball_tests = [
                "Move LEFT trackball LEFT and RIGHT only",
                "Move LEFT trackball UP and DOWN only",
                "Move CENTER trackball LEFT and RIGHT only",
                "Move CENTER trackball UP and DOWN only",
                "Move RIGHT trackball LEFT and RIGHT only",
                "Move RIGHT trackball UP and DOWN only",
                "Turn LEFT trackball wheel (if it has one)",
                "Turn CENTER trackball wheel (if it has one)",
                "Turn RIGHT trackball wheel (if it has one)",
            ]

            for i, instruction in enumerate(trackball_tests, 1):
                print(f"\n🖱️ Trackball Test {i}/{len(trackball_tests)}")
                events = self.test_control(instruction, duration=8)
                self.analyze_events(events, f"TRACKBALL_{i}")

            # Show final mapping
            self.show_final_mapping()

        except KeyboardInterrupt:
            print("\n🛑 Mapping interrupted")
        finally:
            if self.panel:
                self.panel.cleanup()

    def show_final_mapping(self):
        """Show the complete control mapping discovered"""
        print("\n\n🎉 COMPLETE CONTROL MAPPING")
        print("=" * 60)

        print(f"🔘 Button Mapping ({len(self.control_map['buttons'])} buttons):")
        for bit_id, name in sorted(self.control_map['buttons'].items()):
            byte_pos = bit_id // 8
            bit_pos = bit_id % 8
            print(f"   Button #{bit_id:2d} (Byte{byte_pos} Bit{bit_pos}): {name}")

        print(f"\n🎛️ Movement Controls ({len(self.control_map['trackballs'])} axes):")
        for pos, name in sorted(self.control_map['trackballs'].items()):
            print(f"   Bytes {pos}-{pos+1}: {name}")

        # Save mapping to file
        self.save_mapping()

    def save_mapping(self):
        """Save the mapping to a file"""
        filename = "control_mapping.py"
        print(f"\n💾 Saving mapping to {filename}...")

        with open(filename, 'w') as f:
            f.write("# DaVinci Micro Panel Control Mapping\n")
            f.write("# Generated by systematic mapping tool\n\n")

            f.write("BUTTON_MAP = {\n")
            for bit_id, name in sorted(self.control_map['buttons'].items()):
                byte_pos = bit_id // 8
                bit_pos = bit_id % 8
                f.write(f"    {bit_id}: '{name}',  # Byte{byte_pos} Bit{bit_pos}\n")
            f.write("}\n\n")

            f.write("MOVEMENT_MAP = {\n")
            for pos, name in sorted(self.control_map['trackballs'].items()):
                f.write(f"    {pos}: '{name}',  # Bytes {pos}-{pos+1}\n")
            f.write("}\n")

        print(f"✅ Mapping saved to {filename}")

def main():
    """Main entry point"""
    print("🎛️ DaVinci Panel Systematic Control Mapping")
    print("This will test EVERY control to build a complete mapping")
    print()
    print("⏱️ Estimated time: 15-20 minutes")
    print("🎯 Please follow instructions carefully for best results")
    print()

    if input("Ready to start systematic mapping? (y/N): ").lower() != 'y':
        print("👋 Maybe next time!")
        return

    mapper = ControlMapper()
    mapper.run_systematic_mapping()

if __name__ == "__main__":
    main()