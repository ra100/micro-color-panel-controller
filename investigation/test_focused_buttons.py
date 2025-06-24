#!/usr/bin/env python3
"""
Focused Button Test - Test specific buttons to identify report types
Quick test to see which buttons use Report 0x02 vs 0x05 vs others
"""

import sys
import os
import time
import usb.core

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from core.device import DaVinciMicroPanel

def test_focused_buttons():
    """Test specific buttons to identify report patterns"""

    print("🎯 FOCUSED BUTTON TESTING")
    print("=" * 50)
    print("Quick test of key buttons to identify report types")
    print()

    # Connect with our robust device class
    panel = DaVinciMicroPanel()
    if not panel.connect():
        print("❌ Failed to connect")
        return

    # Test specific buttons
    button_tests = [
        ("SHOT COLOR button (left side, special orange button)", "SHOT_COLOR"),
        ("COPY button (left side, smaller button)", "COPY"),
        ("PASTE button (left side, smaller button)", "PASTE"),
        ("Y LIFT encoder BUTTON (push the top-left rotary)", "Y_LIFT_BUTTON"),
        ("PREV button (right side)", "PREV"),
        ("NEXT button (right side)", "NEXT"),
    ]

    results = {}

    try:
        for i, (instruction, button_name) in enumerate(button_tests, 1):
            print(f"\n🔘 Test {i}/{len(button_tests)}: {button_name}")
            print(f"📝 {instruction}")
            print("-" * 50)

            # Refresh illumination before each test
            panel.set_illumination(True, 100)

            input("🟢 Press ENTER, then press and release the button...")
            print("⏱️ Recording for 4 seconds - press the button NOW!")

            events = []
            start_time = time.time()

            while time.time() - start_time < 4:
                try:
                    data = panel.device.read(0x81, 64, timeout=50)
                    if data:
                        data_bytes = bytes(data)
                        if any(b != 0 for b in data_bytes):
                            events.append(data_bytes)

                            # Show immediate feedback
                            report_id = data_bytes[0]
                            print(f"  🎯 Report 0x{report_id:02x}: {data_bytes[:8].hex()}")

                except usb.core.USBTimeoutError:
                    continue
                except Exception as e:
                    print(f"  ⚠️ Error: {e}")
                    break

            # Analyze results
            if events:
                report_types = {}
                for event in events:
                    report_id = event[0]
                    if report_id not in report_types:
                        report_types[report_id] = []
                    report_types[report_id].append(event)

                print(f"  ✅ Captured {len(events)} events")
                for report_id, report_events in report_types.items():
                    print(f"    📋 Report 0x{report_id:02x}: {len(report_events)} events")

                    if report_id == 0x02:  # Standard button report
                        # Find button bits
                        for event in report_events[:1]:  # Just first event
                            for byte_idx in range(1, 8):
                                if byte_idx < len(event) and event[byte_idx] != 0:
                                    byte_val = event[byte_idx]
                                    for bit in range(8):
                                        if byte_val & (1 << bit):
                                            bit_id = byte_idx * 8 + bit
                                            print(f"      🎯 Button bit: Byte{byte_idx} Bit{bit} = Button#{bit_id}")

                    elif report_id == 0x05:  # Special button report
                        for event in report_events[:1]:  # Just first event
                            non_zero = [(i, b) for i, b in enumerate(event[1:10], 1) if b != 0]
                            if non_zero:
                                print(f"      🔸 Special data: {non_zero}")

                results[button_name] = report_types
            else:
                print(f"  ❌ No events captured for {button_name}")
                results[button_name] = {}

            print("  ⏸️ 2 second pause...")
            time.sleep(2)

        # Summary
        print("\n\n📊 SUMMARY OF BUTTON REPORT TYPES")
        print("=" * 50)
        for button_name, report_types in results.items():
            if report_types:
                types = ', '.join(f"0x{rid:02x}" for rid in report_types.keys())
                print(f"🔘 {button_name}: Reports {types}")
            else:
                print(f"❌ {button_name}: No events")

        # Report type classification
        print(f"\n🔍 REPORT TYPE CLASSIFICATION:")
        standard_buttons = [name for name, types in results.items() if 0x02 in types]
        special_buttons = [name for name, types in results.items() if 0x05 in types]

        if standard_buttons:
            print(f"📋 Report 0x02 (Standard buttons): {', '.join(standard_buttons)}")
        if special_buttons:
            print(f"📋 Report 0x05 (Special buttons): {', '.join(special_buttons)}")

    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    finally:
        panel.cleanup()
        print("\n✅ Test completed!")

if __name__ == "__main__":
    test_focused_buttons()