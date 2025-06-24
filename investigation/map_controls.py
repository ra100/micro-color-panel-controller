#!/usr/bin/env python3
"""
Systematic Control Mapping Tool
Maps each physical control to its corresponding data bytes
"""

import sys
import os
import time
import threading
from collections import defaultdict

# Add our modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.device import DaVinciMicroPanel

class ControlMapper:
    """Maps physical controls to HID report data"""

    def __init__(self):
        self.panel = None
        self.data_log = []
        self.baseline = None

    def connect(self):
        """Connect to the panel"""
        print("🔌 Connecting to DaVinci Micro Panel...")

        self.panel = DaVinciMicroPanel()
        if not self.panel.connect():
            print("❌ Failed to connect!")
            return False

        print("✅ Panel connected!")
        return True

    def capture_baseline(self, duration=2):
        """Capture baseline data with no input"""
        print(f"\n📊 Capturing baseline (no input) for {duration}s...")
        print("🚫 DON'T TOUCH any controls!")

        start_time = time.time()
        baseline_data = []

        while time.time() - start_time < duration:
            try:
                data = self.panel.device.read(0x81, 64, timeout=100)
                if data:
                    data_bytes = bytes(data)
                    if any(b != 0 for b in data_bytes):
                        baseline_data.append(data_bytes)
            except:
                continue

        # Find the most common pattern as baseline
        if baseline_data:
            # Use the first non-zero pattern as baseline
            self.baseline = baseline_data[0]
            hex_data = ' '.join(f'{b:02x}' for b in self.baseline[:16])
            print(f"📍 Baseline: [{hex_data}...]")
        else:
            print("📍 No baseline data captured (panel might be idle)")

    def test_control(self, control_name, instruction, duration=5):
        """Test a specific control and capture its data"""
        print(f"\n🎛️ Testing: {control_name}")
        print(f"📋 {instruction}")

        input("🟢 Press ENTER when ready, then perform the action...")

        print(f"⏱️ Recording for {duration} seconds... GO!")

        start_time = time.time()
        control_data = []

        while time.time() - start_time < duration:
            try:
                data = self.panel.device.read(0x81, 64, timeout=50)
                if data:
                    data_bytes = bytes(data)
                    if any(b != 0 for b in data_bytes):
                        control_data.append((time.time() - start_time, data_bytes))

                        # Show real-time data
                        hex_data = ' '.join(f'{b:02x}' for b in data_bytes[:16])
                        print(f"  📥 [{hex_data}...]")

            except:
                continue

        if control_data:
            print(f"✅ Captured {len(control_data)} reports for {control_name}")
            self.analyze_control_data(control_name, control_data)
        else:
            print(f"❌ No data captured for {control_name}")

        return control_data

    def analyze_control_data(self, control_name, data_list):
        """Analyze captured data to find patterns"""
        if not data_list:
            return

        print(f"🔍 Analysis for {control_name}:")

        # Look for changing bytes
        byte_changes = defaultdict(set)

        for timestamp, data in data_list:
            for i, byte_val in enumerate(data):
                if self.baseline is None or i >= len(self.baseline) or byte_val != self.baseline[i]:
                    byte_changes[i].add(byte_val)

        # Report significant changes
        for byte_pos, values in byte_changes.items():
            if len(values) > 1:  # Byte position with changing values
                values_str = ', '.join(f'0x{v:02x}' for v in sorted(values))
                print(f"  📍 Byte {byte_pos}: [{values_str}]")

                # Interpret patterns
                if len(values) == 2 and 0x00 in values:
                    print(f"      💡 Likely button: OFF/ON")
                elif max(values) - min(values) > 50:
                    print(f"      💡 Likely analog: encoder/trackball")

    def run_systematic_test(self):
        """Run systematic test of all controls"""
        print("🎯 Systematic Control Mapping")
        print("=" * 60)

        if not self.connect():
            return

        try:
            # Capture baseline
            self.capture_baseline()

            # Define test cases based on panel layout
            test_cases = [
                # Trackballs
                ("LEFT Trackball X", "Move LEFT trackball LEFT and RIGHT only"),
                ("LEFT Trackball Y", "Move LEFT trackball UP and DOWN only"),
                ("CENTER Trackball X", "Move CENTER trackball LEFT and RIGHT only"),
                ("CENTER Trackball Y", "Move CENTER trackball UP and DOWN only"),
                ("RIGHT Trackball X", "Move RIGHT trackball LEFT and RIGHT only"),
                ("RIGHT Trackball Y", "Move RIGHT trackball UP and DOWN only"),

                # First few encoders
                ("Y_LIFT Encoder", "Turn Y LIFT encoder (top-left) clockwise and counter-clockwise"),
                ("Y_GAMMA Encoder", "Turn Y GAMMA encoder (2nd from left) both directions"),
                ("Y_GAIN Encoder", "Turn Y GAIN encoder (3rd from left) both directions"),

                # Some buttons
                ("Y_LIFT Button", "Press and release Y LIFT encoder button"),
                ("SHOT COLOR Button", "Press and release SHOT COLOR button (left side)"),
                ("COPY Button", "Press and release COPY button"),

                # Transport controls
                ("PREV Button", "Press and release PREV button (right side)"),
                ("NEXT Button", "Press and release NEXT button (right side)"),
            ]

            print(f"\n📋 Will test {len(test_cases)} controls")

            for control_name, instruction in test_cases:
                self.test_control(control_name, instruction)

                # Short break between tests
                if input("\n⏸️ Continue to next test? (Enter=yes, 'q'=quit): ").lower() == 'q':
                    break

            print("\n🎉 Systematic testing complete!")
            print("💡 Use the byte position data to update the InputParser")

        except KeyboardInterrupt:
            print("\n🛑 Testing interrupted")
        finally:
            if self.panel:
                self.panel.cleanup()

def main():
    """Main entry point"""
    print("🎛️ DaVinci Panel Control Mapping Tool")
    print("This will systematically test each control to map data bytes")
    print()

    mapper = ControlMapper()
    mapper.run_systematic_test()

if __name__ == "__main__":
    main()