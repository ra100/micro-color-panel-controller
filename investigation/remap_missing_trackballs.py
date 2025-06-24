#!/usr/bin/env python3
"""
Re-map Missing Trackball Axes
Focus on the trackball axes that didn't show clear patterns
"""

import sys
import os
import time
import usb.core
from collections import defaultdict, Counter

# Add our modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from core.device import DaVinciMicroPanel

class MissingTrackballMapper:
    """Re-test trackball axes that didn't show clear patterns"""

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

    def test_trackball_axis(self, axis_name, instruction, duration=10):
        """Test a specific trackball axis with extended analysis"""
        print(f"\n🎯 {instruction}")
        print("=" * 80)

        # Refresh illumination
        self.panel.set_illumination(True, 100)

        input("🟢 Press ENTER when ready, then follow the instruction...")
        print(f"⏱️ Recording for {duration} seconds - GO!")
        print("💡 TIP: Try both slow and fast movements, also try different pressure levels")

        events = []
        start_time = time.time()

        try:
            while time.time() - start_time < duration:
                try:
                    # Refresh illumination periodically
                    if time.time() - start_time > 5:
                        self.panel.set_illumination(True, 100)

                    data = self.panel.device.read(0x81, 64, timeout=50)
                    if data:
                        data_bytes = bytes(data)
                        if any(b != 0 for b in data_bytes):
                            timestamp = time.time() - start_time
                            events.append((timestamp, data_bytes))

                            # Show real-time feedback for ALL reports
                            if len(events) % 10 == 1:
                                report_id = data_bytes[0]
                                non_zero = [(i, b) for i, b in enumerate(data_bytes[1:20], 1) if b != 0]
                                if non_zero:
                                    print(f"  📊 Report 0x{report_id:02x}: {non_zero}")

                except usb.core.USBTimeoutError:
                    continue
                except Exception as e:
                    print(f"  ⚠️ Error: {e}")
                    break

        except KeyboardInterrupt:
            print("\n⏸️ Test stopped early")

        print(f"✅ Captured {len(events)} events")

        # Analyze ALL report types
        analysis = self.analyze_all_reports(events, axis_name)
        self.trackball_data[axis_name] = analysis

        return analysis

    def analyze_all_reports(self, events, axis_name):
        """Analyze ALL report types, not just 0x05"""
        if not events:
            return {"pattern": "no_data", "reports": {}}

        print(f"\n🔍 Analyzing ALL reports for {axis_name}")

        # Group events by report ID
        reports_by_id = defaultdict(list)
        for timestamp, data in events:
            report_id = data[0]
            reports_by_id[report_id].append((timestamp, data))

        print(f"  📋 Report types found: {list(reports_by_id.keys())}")
        for report_id, report_events in reports_by_id.items():
            print(f"    Report 0x{report_id:02x}: {len(report_events)} events")

        analysis = {"pattern": "multi_report", "reports": {}}

        # Analyze each report type
        for report_id, report_events in reports_by_id.items():
            if len(report_events) < 5:  # Skip reports with too few events
                continue

            print(f"\n  🔬 Analyzing Report 0x{report_id:02x} ({len(report_events)} events)")

            # Find changing bytes
            byte_patterns = {}
            for byte_idx in range(1, 20):  # Check bytes 1-19
                values = []
                for timestamp, data in report_events:
                    if byte_idx < len(data):
                        values.append(data[byte_idx])

                if values:
                    unique_values = set(values)
                    if len(unique_values) > 3:  # This byte changes significantly
                        value_counts = Counter(values)
                        min_val = min(values)
                        max_val = max(values)

                        byte_patterns[byte_idx] = {
                            'min': min_val,
                            'max': max_val,
                            'unique_count': len(unique_values),
                            'most_common': value_counts.most_common(3),
                            'sample_values': sorted(list(unique_values))[:8]
                        }

            if byte_patterns:
                # Find primary pattern bytes (most variation)
                primary_bytes = []
                for byte_idx, pattern in byte_patterns.items():
                    if pattern['unique_count'] > 5:
                        primary_bytes.append((byte_idx, pattern['unique_count']))

                primary_bytes.sort(key=lambda x: x[1], reverse=True)

                analysis["reports"][f"0x{report_id:02x}"] = {
                    "event_count": len(report_events),
                    "byte_patterns": byte_patterns,
                    "primary_bytes": [b[0] for b in primary_bytes[:3]]
                }

                if primary_bytes:
                    print(f"    📊 Primary bytes: {[b[0] for b in primary_bytes[:3]]}")
                    for byte_idx, count in primary_bytes[:3]:
                        pattern = byte_patterns[byte_idx]
                        print(f"      Byte{byte_idx}: {pattern['min']}-{pattern['max']} ({count} unique)")
                else:
                    print(f"    ❌ No significant patterns found")
            else:
                print(f"    ❌ No changing bytes found")

        return analysis

    def run_missing_trackball_mapping(self):
        """Run mapping for the missing trackball axes"""
        print("🔍 RE-MAPPING MISSING TRACKBALL AXES")
        print("=" * 60)
        print("Extended analysis with all report types and longer capture times")
        print()

        if not self.connect():
            return

        try:
            # Focus on the missing axes with extended capture time
            missing_tests = [
                # CENTER TRACKBALL WHEELS (these failed before)
                ("CENTER_TRACKBALL_WHEEL_CW", "Turn CENTER trackball wheel CLOCKWISE - try slow, medium, and fast speeds"),
                ("CENTER_TRACKBALL_WHEEL_CCW", "Turn CENTER trackball wheel COUNTER-CLOCKWISE - try slow, medium, and fast speeds"),

                # RIGHT TRACKBALL (all axes failed before)
                ("RIGHT_TRACKBALL_X", "Move RIGHT trackball LEFT and RIGHT - try light and firm pressure"),
                ("RIGHT_TRACKBALL_Y", "Move RIGHT trackball UP and DOWN - try light and firm pressure"),
                ("RIGHT_TRACKBALL_WHEEL_CW", "Turn RIGHT trackball wheel CLOCKWISE - try different speeds and pressure"),
                ("RIGHT_TRACKBALL_WHEEL_CCW", "Turn RIGHT trackball wheel COUNTER-CLOCKWISE - try different speeds and pressure"),
            ]

            for i, (axis_name, instruction) in enumerate(missing_tests, 1):
                print(f"\n🖱️ Missing Axis Test {i}/{len(missing_tests)}: {axis_name}")
                self.test_trackball_axis(axis_name, instruction, duration=10)
                time.sleep(2)

            # Show comprehensive analysis
            self.show_missing_analysis()

        except KeyboardInterrupt:
            print("\n🛑 Missing trackball mapping interrupted")
        finally:
            if self.panel:
                self.panel.cleanup()

    def show_missing_analysis(self):
        """Show analysis for the missing axes"""
        print("\n\n🎉 MISSING TRACKBALL AXES ANALYSIS")
        print("=" * 70)

        found_patterns = []
        still_missing = []

        for axis_name, analysis in self.trackball_data.items():
            print(f"\n🖱️ {axis_name}:")

            has_pattern = False
            if analysis.get('reports'):
                for report_id, report_data in analysis['reports'].items():
                    if report_data.get('primary_bytes'):
                        primary_bytes = report_data['primary_bytes']
                        event_count = report_data['event_count']
                        print(f"  ✅ Report {report_id}: Bytes {primary_bytes} ({event_count} events)")
                        found_patterns.append(axis_name)
                        has_pattern = True

            if not has_pattern:
                print(f"  ❌ No clear patterns found")
                still_missing.append(axis_name)

        print(f"\n📊 SUMMARY:")
        print(f"  ✅ Found patterns: {len(found_patterns)}")
        if found_patterns:
            for axis in found_patterns:
                print(f"    - {axis}")

        print(f"  ❌ Still missing: {len(still_missing)}")
        if still_missing:
            for axis in still_missing:
                print(f"    - {axis}")

        # Save results
        self.save_missing_results()

    def save_missing_results(self):
        """Save the missing trackball results"""
        filename = "missing_trackball_results.py"
        with open(filename, 'w') as f:
            f.write("# Missing Trackball Axes - Extended Analysis Results\n")
            f.write("# Re-mapping attempt with all report types\n\n")

            f.write("MISSING_TRACKBALL_RESULTS = {\n")
            for axis_name, analysis in self.trackball_data.items():
                f.write(f"    '{axis_name}': {{\n")
                if analysis.get('reports'):
                    for report_id, report_data in analysis['reports'].items():
                        if report_data.get('primary_bytes'):
                            f.write(f"        'report_{report_id}': {{\n")
                            f.write(f"            'primary_bytes': {report_data['primary_bytes']},\n")
                            f.write(f"            'event_count': {report_data['event_count']},\n")
                            f.write(f"            'byte_patterns': {{\n")
                            for byte_idx, pattern in report_data['byte_patterns'].items():
                                if byte_idx in report_data['primary_bytes']:
                                    f.write(f"                {byte_idx}: {{'min': {pattern['min']}, 'max': {pattern['max']}, 'unique': {pattern['unique_count']}}},\n")
                            f.write(f"            }}\n")
                            f.write(f"        }},\n")
                f.write(f"    }},\n")
            f.write("}\n")

        print(f"✅ Missing trackball results saved to {filename}")

def main():
    """Main entry point"""
    print("🔍 Re-mapping Missing DaVinci Panel Trackball Axes")
    print("Extended analysis for axes that didn't show clear patterns")
    print()
    print("⏱️ Estimated time: 12 minutes (6 axes × 10 seconds + analysis)")
    print()

    if input("Ready to re-test missing trackball axes? (y/N): ").lower() != 'y':
        print("👋 Maybe next time!")
        return

    mapper = MissingTrackballMapper()
    mapper.run_missing_trackball_mapping()

if __name__ == "__main__":
    main()