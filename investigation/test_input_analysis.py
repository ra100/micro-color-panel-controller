#!/usr/bin/env python3
"""
DaVinci Micro Panel Input Analysis Tool
Discovers the HID input report format by analyzing real panel interactions
"""

import sys
import os
import time
import usb.core
import usb.util
from collections import defaultdict, Counter

# Add our modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.device import DaVinciMicroPanel
from core.input_parser import InputParser, EventType, analyze_input_reports

class InputAnalyzer:
    """Advanced input analysis and format discovery"""

    def __init__(self):
        self.panel = None
        self.parser = InputParser()
        self.report_patterns = defaultdict(list)
        self.report_counts = Counter()
        self.interaction_log = []

    def connect(self):
        """Connect to the panel"""
        print("🔌 Connecting to DaVinci Micro Panel...")

        self.panel = DaVinciMicroPanel()
        if not self.panel.connect():
            print("❌ Failed to connect to panel!")
            return False

        print("✅ Panel connected and illuminated!")
        return True

    def analyze_input_endpoints(self):
        """Analyze available input endpoints"""
        if not self.panel or not self.panel.device:
            print("❌ Panel not connected")
            return

        print("🔍 Analyzing USB endpoints...")
        print("=" * 50)

        device = self.panel.device

        for cfg in device:
            print(f"📋 Configuration {cfg.bConfigurationValue}")
            for intf in cfg:
                print(f"  🔌 Interface {intf.bInterfaceNumber}")
                print(f"     Class: {intf.bInterfaceClass}")
                print(f"     Subclass: {intf.bInterfaceSubClass}")
                print(f"     Protocol: {intf.bInterfaceProtocol}")

                for ep in intf:
                    ep_type = "IN" if ep.bEndpointAddress & 0x80 else "OUT"
                    ep_addr = ep.bEndpointAddress & 0x7F
                    print(f"     📊 Endpoint 0x{ep.bEndpointAddress:02x} ({ep_type}{ep_addr})")
                    print(f"        Type: {ep.bmAttributes & 0x3}")
                    print(f"        Max packet: {ep.wMaxPacketSize}")

                print()

    def capture_input_data(self, duration=30):
        """Capture raw input data with user interaction guidance"""
        if not self.panel or not self.panel.device:
            print("❌ Panel not connected")
            return

        print(f"🎛️ INTERACTIVE INPUT ANALYSIS ({duration} seconds)")
        print("=" * 60)
        print("Please interact with controls as instructed:")
        print()

        device = self.panel.device
        reports_captured = {}
        start_time = time.time()

        # Instructions for systematic testing
        instructions = [
            (5, "🔄 Turn EACH rotary encoder (top row) one by one"),
            (5, "🖱️ Move EACH trackball (left, center, right)"),
            (5, "🔘 Press EACH button around the panel"),
            (5, "🎯 Try COMBINED movements (trackball + encoder)"),
            (5, "🏃 Rapid movements to test data rate"),
            (5, "🎭 Hold buttons while moving other controls")
        ]

        instruction_index = 0
        last_instruction_time = start_time

        print(f"⏰ Starting with: {instructions[0][1]}")

        try:
            while time.time() - start_time < duration:
                # Show next instruction
                elapsed = time.time() - last_instruction_time
                if instruction_index < len(instructions) and elapsed >= instructions[instruction_index][0]:
                    instruction_index += 1
                    if instruction_index < len(instructions):
                        last_instruction_time = time.time()
                        print(f"\n⏰ Next: {instructions[instruction_index][1]}")

                try:
                    # Try to read from input endpoints
                    # First try Interface 2 (HID)
                    endpoint_addr = 0x81  # IN endpoint 1
                    data = device.read(endpoint_addr, 64, timeout=50)

                    if data:
                        data_bytes = bytes(data)

                        # Log the raw data
                        timestamp = time.time() - start_time
                        hex_data = ' '.join(f'{b:02x}' for b in data_bytes)

                        # Only show non-zero data
                        if any(b != 0 for b in data_bytes):
                            print(f"[{timestamp:6.2f}s] 📥 {hex_data}")

                            # Store for analysis
                            report_id = data_bytes[0] if data_bytes else 0
                            self.report_counts[report_id] += 1

                            # Store unique patterns
                            pattern_key = tuple(data_bytes[:8])
                            if pattern_key not in self.report_patterns:
                                self.report_patterns[pattern_key] = {
                                    'first_seen': timestamp,
                                    'full_data': data_bytes,
                                    'count': 1
                                }
                            else:
                                self.report_patterns[pattern_key]['count'] += 1

                            # Try to parse with our parser
                            try:
                                events = self.parser.parse_hid_report(data_bytes)
                                if events:
                                    for event in events:
                                        print(f"  🎯 Parsed: {event.type.value} #{event.control_id}")
                            except Exception as e:
                                pass  # Parsing errors expected until we get format right

                except usb.core.USBTimeoutError:
                    # Timeouts are normal when no input
                    continue
                except Exception as e:
                    if "timeout" not in str(e).lower():
                        print(f"⚠️ USB Error: {e}")

        except KeyboardInterrupt:
            print("\n🛑 Analysis stopped by user")

        print(f"\n📊 Analysis Results:")
        print(f"   ⏱️ Duration: {time.time() - start_time:.1f} seconds")
        print(f"   📝 Unique patterns: {len(self.report_patterns)}")
        print(f"   📈 Total reports: {sum(self.report_counts.values())}")

        return self.report_patterns

    def analyze_patterns(self):
        """Analyze captured patterns to understand data format"""
        if not self.report_patterns:
            print("❌ No patterns captured")
            return

        print("\n🔍 PATTERN ANALYSIS")
        print("=" * 50)

        # Group by report ID
        by_report_id = defaultdict(list)
        for pattern, info in self.report_patterns.items():
            report_id = pattern[0]
            by_report_id[report_id].append((pattern, info))

        for report_id, patterns in by_report_id.items():
            print(f"\n📋 Report ID 0x{report_id:02x} ({len(patterns)} patterns)")

            for pattern, info in sorted(patterns, key=lambda x: x[1]['count'], reverse=True):
                hex_pattern = ' '.join(f'{b:02x}' for b in pattern)
                print(f"   {info['count']:3d}x: [{hex_pattern}...] @{info['first_seen']:.1f}s")

                # Show full data for most common patterns
                if info['count'] >= 5:
                    full_hex = ' '.join(f'{b:02x}' for b in info['full_data'][:32])
                    print(f"        Full: [{full_hex}...]")

        print(f"\n📊 Report ID Summary:")
        for report_id, count in self.report_counts.most_common():
            print(f"   0x{report_id:02x}: {count:4d} reports")

    def test_specific_controls(self):
        """Test specific controls systematically"""
        print("\n🎯 SYSTEMATIC CONTROL TESTING")
        print("=" * 50)
        print("Testing individual controls to map data format...")

        control_tests = [
            ("Y_LIFT encoder (top-left)", "Turn the Y LIFT encoder slowly"),
            ("LEFT trackball", "Move left trackball left/right only"),
            ("LEFT trackball", "Move left trackball up/down only"),
            ("Y_LIFT button", "Press and release Y LIFT encoder button"),
            ("SHOT COLOR button", "Press and release SHOT COLOR button (left side)"),
            ("CENTER trackball", "Move center trackball in circles"),
            ("HUE encoder", "Turn HUE encoder (top-right)"),
        ]

        for control_name, instruction in control_tests:
            print(f"\n🎛️ Testing: {control_name}")
            print(f"   📋 Instruction: {instruction}")
            print("   ⏰ You have 5 seconds, then press ENTER...")

            input("   🟢 Press ENTER when ready...")

            # Capture for 5 seconds
            start_time = time.time()
            control_data = []

            try:
                while time.time() - start_time < 5:
                    try:
                        data = self.panel.device.read(0x81, 64, timeout=50)
                        if data and any(b != 0 for b in data):
                            data_bytes = bytes(data)
                            control_data.append(data_bytes)
                            hex_data = ' '.join(f'{b:02x}' for b in data_bytes[:16])
                            print(f"      📥 [{hex_data}...]")
                    except usb.core.USBTimeoutError:
                        continue

            except KeyboardInterrupt:
                break

            if control_data:
                print(f"   ✅ Captured {len(control_data)} reports for {control_name}")
            else:
                print(f"   ❌ No data captured for {control_name}")

    def run_full_analysis(self):
        """Run complete input analysis workflow"""
        print("🎯 DaVinci Micro Panel Input Analysis Tool")
        print("=" * 60)

        if not self.connect():
            return False

        try:
            # Step 1: Analyze USB structure
            self.analyze_input_endpoints()

            # Step 2: Interactive capture
            input("\n🟢 Press ENTER to start interactive capture...")
            patterns = self.capture_input_data(duration=30)

            # Step 3: Analyze patterns
            self.analyze_patterns()

            # Step 4: Systematic testing
            if input("\n🎯 Run systematic control tests? (y/N): ").lower() == 'y':
                self.test_specific_controls()

            print("\n✅ Analysis complete!")
            print("💡 Use the pattern data to update the InputParser format")

        except Exception as e:
            print(f"❌ Analysis error: {e}")
        finally:
            if self.panel:
                self.panel.cleanup()

def main():
    """Main entry point"""
    print("🔬 Advanced Input Analysis for DaVinci Micro Panel")
    print("This tool will help discover the HID input report format")
    print()

    if os.geteuid() == 0:
        print("⚠️  Running as root - make sure you have USB permissions")

    analyzer = InputAnalyzer()
    analyzer.run_full_analysis()

if __name__ == "__main__":
    main()