#!/usr/bin/env python3
"""
Raw Trackball Data Capture
Minimal tool to capture raw USB data without interference
"""

import sys
import os
import time
import usb.core
from collections import defaultdict

# Add our modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from core.device import DaVinciMicroPanel

class RawTrackballCapture:
    """Simple raw data capture for trackballs"""

    def __init__(self):
        self.panel = None

    def connect(self):
        """Connect to panel"""
        self.panel = DaVinciMicroPanel()
        if self.panel.connect():
            print("✅ Panel connected!")
            # Set illumination once and leave it
            self.panel.set_illumination(True, 100)
            return True
        else:
            print("❌ Failed to connect")
            return False

    def raw_capture(self, test_name, duration=15):
        """Capture raw USB data without any processing"""
        print(f"\n🎯 RAW CAPTURE: {test_name}")
        print("=" * 60)

        input("🟢 Press ENTER when ready, then move the trackball...")
        print(f"⏱️ Recording RAW data for {duration} seconds - GO!")

        all_events = []
        start_time = time.time()

        try:
            while time.time() - start_time < duration:
                try:
                    # Read raw data without any filtering
                    data = self.panel.device.read(0x81, 64, timeout=100)
                    if data:
                        timestamp = time.time() - start_time
                        data_bytes = bytes(data)
                        all_events.append((timestamp, data_bytes))

                        # Show ALL data, not just non-zero
                        if len(all_events) % 50 == 1:  # Show every 50th event
                            report_id = data_bytes[0]
                            print(f"  📊 Raw[{len(all_events)}]: Report 0x{report_id:02x} = {list(data_bytes[:16])}")

                except usb.core.USBTimeoutError:
                    continue
                except Exception as e:
                    print(f"  ⚠️ Error: {e}")
                    break

        except KeyboardInterrupt:
            print("\n⏸️ Test stopped early")

        print(f"✅ Captured {len(all_events)} total events")

        # Quick analysis
        self.quick_analysis(all_events, test_name)

        return all_events

    def quick_analysis(self, events, test_name):
        """Quick analysis of captured data"""
        if not events:
            print("❌ No data captured")
            return

        print(f"\n🔍 Quick analysis for {test_name}:")

        # Group by report type
        reports_by_type = defaultdict(list)
        for timestamp, data in events:
            report_id = data[0]
            reports_by_type[report_id].append(data)

        for report_id, report_events in reports_by_type.items():
            print(f"  📋 Report 0x{report_id:02x}: {len(report_events)} events")

            # Look for changing bytes in this report type
            if len(report_events) > 10:  # Only analyze if we have enough data
                changing_bytes = []
                for byte_idx in range(1, min(20, len(report_events[0]))):
                    values = [data[byte_idx] for data in report_events if byte_idx < len(data)]
                    if len(set(values)) > 3:  # This byte changes significantly
                        changing_bytes.append(byte_idx)

                if changing_bytes:
                    print(f"    📊 Changing bytes: {changing_bytes}")
                    # Show sample values for first changing byte
                    if changing_bytes:
                        byte_idx = changing_bytes[0]
                        values = [data[byte_idx] for data in report_events[:20] if byte_idx < len(data)]
                        print(f"    📈 Byte{byte_idx} samples: {values}")
                else:
                    print(f"    ❌ No changing bytes found")

    def test_single_trackball(self):
        """Test a single trackball with minimal interference"""
        print("🖱️ RAW TRACKBALL DATA CAPTURE")
        print("=" * 50)
        print("This will capture ALL USB data without filtering or processing")
        print()

        if not self.connect():
            return

        try:
            print("📋 Available tests:")
            print("1. RIGHT_TRACKBALL_X")
            print("2. RIGHT_TRACKBALL_Y")
            print("3. RIGHT_TRACKBALL_WHEEL")
            print("4. CENTER_TRACKBALL_WHEEL")
            print("5. ALL_TRACKBALLS_MIXED")

            choice = input("\nSelect test (1-5): ").strip()

            if choice == "1":
                self.raw_capture("RIGHT_TRACKBALL_X - Move right trackball LEFT and RIGHT only")
            elif choice == "2":
                self.raw_capture("RIGHT_TRACKBALL_Y - Move right trackball UP and DOWN only")
            elif choice == "3":
                self.raw_capture("RIGHT_TRACKBALL_WHEEL - Turn right trackball wheel both directions")
            elif choice == "4":
                self.raw_capture("CENTER_TRACKBALL_WHEEL - Turn center trackball wheel both directions")
            elif choice == "5":
                self.raw_capture("ALL_TRACKBALLS - Move ANY trackball in ANY direction")
            else:
                print("Invalid choice")
                return

        except KeyboardInterrupt:
            print("\n🛑 Testing interrupted")
        finally:
            if self.panel:
                print("\n🧹 Cleaning up...")
                self.panel.cleanup()

def main():
    """Main entry point"""
    print("🖱️ Raw Trackball Data Capture Tool")
    print("Minimal interference - just raw data capture")
    print()

    capture = RawTrackballCapture()
    capture.test_single_trackball()

if __name__ == "__main__":
    main()