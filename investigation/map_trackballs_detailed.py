#!/usr/bin/env python3
"""
Detailed Trackball Mapping Tool
Properly analyze Report 0x05 data patterns for all trackball axes and wheel directions
"""

import sys
import os
import time
import usb.core
from collections import defaultdict, Counter

# Add our modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from core.device import DaVinciMicroPanel

class TrackballAnalyzer:
    """Analyze trackball Report 0x05 data patterns"""

    def __init__(self):
        self.panel = None
        self.trackball_data = {}

    def connect(self):
        """Connect to panel"""
        self.panel = DaVinciMicroPanel()
        if self.panel.connect():
            print("✅ Panel connected and illuminated!")
            return True
        else:
            print("❌ Failed to connect")
            return False

    def test_trackball_axis(self, axis_name, instruction, duration=8):
        """Test a specific trackball axis with detailed analysis"""
        print(f"\n🎯 {instruction}")
        print("=" * 70)

        # Refresh illumination
        self.panel.set_illumination(True, 100)

        input("🟢 Press ENTER when ready, then follow the instruction...")
        print(f"⏱️ Recording for {duration} seconds - GO!")

        events = []
        start_time = time.time()

        try:
            while time.time() - start_time < duration:
                try:
                    # Refresh illumination periodically
                    if time.time() - start_time > 4:
                        self.panel.set_illumination(True, 100)

                    data = self.panel.device.read(0x81, 64, timeout=50)
                    if data:
                        data_bytes = bytes(data)
                        if any(b != 0 for b in data_bytes):
                            timestamp = time.time() - start_time
                            events.append((timestamp, data_bytes))

                            # Show some real-time feedback (but not too much)
                            if len(events) % 20 == 1:
                                report_id = data_bytes[0]
                                if report_id == 0x05:
                                    non_zero = [(i, b) for i, b in enumerate(data_bytes[1:12], 1) if b != 0]
                                    if non_zero:
                                        print(f"  📊 Sample data: {non_zero}")

                except usb.core.USBTimeoutError:
                    continue
                except Exception as e:
                    print(f"  ⚠️ Error: {e}")
                    break

        except KeyboardInterrupt:
            print("\n⏸️ Test stopped early")

        print(f"✅ Captured {len(events)} events")

        # Analyze the data
        analysis = self.analyze_trackball_data(events, axis_name)
        self.trackball_data[axis_name] = analysis

        return analysis

    def analyze_trackball_data(self, events, axis_name):
        """Analyze Report 0x05 data patterns"""
        if not events:
            return {"pattern": "no_data", "byte_patterns": {}}

        # Filter to Report 0x05 events only
        report_05_events = []
        for timestamp, data in events:
            if data[0] == 0x05:
                report_05_events.append((timestamp, data))

        if not report_05_events:
            return {"pattern": "no_report_05", "byte_patterns": {}}

        print(f"\n🔍 Analyzing {len(report_05_events)} Report 0x05 events for {axis_name}")

        # Analyze patterns in each byte position
        byte_patterns = {}

        for byte_idx in range(1, 16):  # Check bytes 1-15 in the report
            values = []
            for timestamp, data in report_05_events:
                if byte_idx < len(data):
                    values.append(data[byte_idx])

            if values:
                unique_values = set(values)
                if len(unique_values) > 1:  # This byte changes
                    value_counts = Counter(values)
                    min_val = min(values)
                    max_val = max(values)

                    byte_patterns[byte_idx] = {
                        'min': min_val,
                        'max': max_val,
                        'unique_count': len(unique_values),
                        'most_common': value_counts.most_common(5),
                        'sample_values': sorted(list(unique_values))[:10]
                    }

        # Find the primary pattern (bytes that change the most)
        if byte_patterns:
            primary_bytes = []
            for byte_idx, pattern in byte_patterns.items():
                if pattern['unique_count'] > 5:  # Significant variation
                    primary_bytes.append((byte_idx, pattern['unique_count']))

            primary_bytes.sort(key=lambda x: x[1], reverse=True)

            print(f"  📊 Primary data bytes: {[b[0] for b in primary_bytes[:3]]}")
            for byte_idx, count in primary_bytes[:3]:
                pattern = byte_patterns[byte_idx]
                print(f"    Byte{byte_idx}: {pattern['min']}-{pattern['max']} ({count} unique values)")

        return {
            "pattern": "report_05",
            "event_count": len(report_05_events),
            "byte_patterns": byte_patterns,
            "primary_bytes": primary_bytes[:3] if byte_patterns else []
        }

    def run_trackball_mapping(self):
        """Run complete trackball mapping"""
        print("🖱️ DETAILED TRACKBALL MAPPING")
        print("=" * 60)
        print("Analyzing Report 0x05 data patterns for all trackball axes")
        print()

        if not self.connect():
            return

        try:
            # Test all trackball axes systematically
            trackball_tests = [
                # LEFT TRACKBALL
                ("LEFT_TRACKBALL_X", "Move LEFT trackball LEFT and RIGHT only - smooth movements"),
                ("LEFT_TRACKBALL_Y", "Move LEFT trackball UP and DOWN only - smooth movements"),
                ("LEFT_TRACKBALL_WHEEL_CW", "Turn LEFT trackball wheel CLOCKWISE only"),
                ("LEFT_TRACKBALL_WHEEL_CCW", "Turn LEFT trackball wheel COUNTER-CLOCKWISE only"),

                # CENTER TRACKBALL
                ("CENTER_TRACKBALL_X", "Move CENTER trackball LEFT and RIGHT only - smooth movements"),
                ("CENTER_TRACKBALL_Y", "Move CENTER trackball UP and DOWN only - smooth movements"),
                ("CENTER_TRACKBALL_WHEEL_CW", "Turn CENTER trackball wheel CLOCKWISE only"),
                ("CENTER_TRACKBALL_WHEEL_CCW", "Turn CENTER trackball wheel COUNTER-CLOCKWISE only"),

                # RIGHT TRACKBALL
                ("RIGHT_TRACKBALL_X", "Move RIGHT trackball LEFT and RIGHT only - smooth movements"),
                ("RIGHT_TRACKBALL_Y", "Move RIGHT trackball UP and DOWN only - smooth movements"),
                ("RIGHT_TRACKBALL_WHEEL_CW", "Turn RIGHT trackball wheel CLOCKWISE only"),
                ("RIGHT_TRACKBALL_WHEEL_CCW", "Turn RIGHT trackball wheel COUNTER-CLOCKWISE only"),
            ]

            for i, (axis_name, instruction) in enumerate(trackball_tests, 1):
                print(f"\n🖱️ Trackball Test {i}/{len(trackball_tests)}: {axis_name}")
                self.test_trackball_axis(axis_name, instruction, duration=6)
                time.sleep(2)

            # Show comprehensive analysis
            self.show_trackball_analysis()

        except KeyboardInterrupt:
            print("\n🛑 Trackball mapping interrupted")
        finally:
            if self.panel:
                self.panel.cleanup()

    def show_trackball_analysis(self):
        """Show comprehensive trackball analysis"""
        print("\n\n🎉 COMPREHENSIVE TRACKBALL ANALYSIS")
        print("=" * 70)

        # Group by trackball
        trackballs = {
            'LEFT': ['LEFT_TRACKBALL_X', 'LEFT_TRACKBALL_Y', 'LEFT_TRACKBALL_WHEEL_CW', 'LEFT_TRACKBALL_WHEEL_CCW'],
            'CENTER': ['CENTER_TRACKBALL_X', 'CENTER_TRACKBALL_Y', 'CENTER_TRACKBALL_WHEEL_CW', 'CENTER_TRACKBALL_WHEEL_CCW'],
            'RIGHT': ['RIGHT_TRACKBALL_X', 'RIGHT_TRACKBALL_Y', 'RIGHT_TRACKBALL_WHEEL_CW', 'RIGHT_TRACKBALL_WHEEL_CCW']
        }

        for trackball_name, axes in trackballs.items():
            print(f"\n🖱️ {trackball_name} TRACKBALL:")
            for axis_name in axes:
                if axis_name in self.trackball_data:
                    analysis = self.trackball_data[axis_name]
                    if analysis['pattern'] == 'report_05' and analysis['primary_bytes']:
                        primary_bytes = [str(b[0]) for b in analysis['primary_bytes']]
                        print(f"  📊 {axis_name}: Bytes {', '.join(primary_bytes)} ({analysis['event_count']} events)")
                    else:
                        print(f"  ❌ {axis_name}: No clear pattern")
                else:
                    print(f"  ❓ {axis_name}: Not tested")

        # Generate mapping code
        self.generate_trackball_mapping()

    def generate_trackball_mapping(self):
        """Generate improved trackball mapping code"""
        print(f"\n💾 IMPROVED TRACKBALL MAPPING:")
        print("=" * 50)

        print("# Trackball Report 0x05 Data Patterns")
        print("TRACKBALL_PATTERNS = {")

        for axis_name, analysis in self.trackball_data.items():
            if analysis['pattern'] == 'report_05' and analysis['primary_bytes']:
                primary_bytes = [b[0] for b in analysis['primary_bytes']]
                print(f"    '{axis_name}': {{'bytes': {primary_bytes}, 'events': {analysis['event_count']}}},")

        print("}")

        # Save to file
        filename = "trackball_mapping_detailed.py"
        with open(filename, 'w') as f:
            f.write("# DaVinci Micro Panel Detailed Trackball Mapping\n")
            f.write("# Generated by detailed trackball mapping tool\n\n")

            f.write("TRACKBALL_PATTERNS = {\n")
            for axis_name, analysis in self.trackball_data.items():
                if analysis['pattern'] == 'report_05' and analysis['primary_bytes']:
                    primary_bytes = [b[0] for b in analysis['primary_bytes']]
                    f.write(f"    '{axis_name}': {{'bytes': {primary_bytes}, 'events': {analysis['event_count']}}},\n")
            f.write("}\n\n")

            f.write("# Detailed byte patterns for each axis\n")
            f.write("DETAILED_PATTERNS = {\n")
            for axis_name, analysis in self.trackball_data.items():
                if analysis['pattern'] == 'report_05':
                    f.write(f"    '{axis_name}': {{\n")
                    for byte_idx, pattern in analysis['byte_patterns'].items():
                        f.write(f"        {byte_idx}: {{'min': {pattern['min']}, 'max': {pattern['max']}, 'unique': {pattern['unique_count']}}},\n")
                    f.write(f"    }},\n")
            f.write("}\n")

        print(f"✅ Detailed mapping saved to {filename}")

def main():
    """Main entry point"""
    print("🖱️ DaVinci Panel Detailed Trackball Mapping")
    print("This will properly analyze Report 0x05 data patterns")
    print()
    print("⏱️ Estimated time: 15 minutes (12 axes)")
    print()

    if input("Ready to start detailed trackball mapping? (y/N): ").lower() != 'y':
        print("👋 Maybe next time!")
        return

    analyzer = TrackballAnalyzer()
    analyzer.run_trackball_mapping()

if __name__ == "__main__":
    main()