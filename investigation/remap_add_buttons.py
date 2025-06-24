#!/usr/bin/env python3
"""
Focused Re-mapping Tool for ADD buttons
Correctly map ADD_NODE, ADD_WINDOW, ADD_KEYFRAME that were confused during comprehensive scan
"""

import sys
import os
import time
import usb.core
from collections import defaultdict

# Add our modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from core.device import DaVinciMicroPanel

def test_button(panel, button_name, instruction):
    """Test a single button with clear feedback"""
    print(f"\n🎯 {instruction}")
    print("=" * 70)

    # Refresh illumination
    panel.set_illumination(True, 100)

    input("🟢 Press ENTER when ready, then press and release the button...")
    print("⏱️ Recording for 4 seconds - GO!")

    events = []
    start_time = time.time()

    try:
        while time.time() - start_time < 4:
            try:
                data = panel.device.read(0x81, 64, timeout=50)
                if data:
                    data_bytes = bytes(data)
                    if any(b != 0 for b in data_bytes):
                        events.append(data_bytes)

                        # Show immediate feedback
                        report_id = data_bytes[0]
                        if report_id == 0x02:  # Button
                            for byte_idx in range(1, 8):
                                if byte_idx < len(data_bytes) and data_bytes[byte_idx] != 0:
                                    byte_val = data_bytes[byte_idx]
                                    for bit in range(8):
                                        if byte_val & (1 << bit):
                                            bit_id = byte_idx * 8 + bit
                                            print(f"  🔘 {button_name}: Byte{byte_idx} Bit{bit} = Button#{bit_id}")

            except usb.core.USBTimeoutError:
                continue
    except KeyboardInterrupt:
        print("\n⏸️ Test stopped early")

    print(f"✅ Captured {len(events)} events")

    # Analyze and return button mapping
    for event in events:
        if event[0] == 0x02:  # Button report
            for byte_idx in range(1, 8):
                if byte_idx < len(event) and event[byte_idx] != 0:
                    byte_val = event[byte_idx]
                    for bit in range(8):
                        if byte_val & (1 << bit):
                            bit_id = byte_idx * 8 + bit
                            return bit_id

    return None

def main():
    """Main remapping function"""
    print("🔧 ADD BUTTONS RE-MAPPING TOOL")
    print("=" * 50)
    print("Correctly mapping ADD_NODE, ADD_WINDOW, ADD_KEYFRAME")
    print("These were confused during the comprehensive scan")
    print()

    # Connect to panel
    panel = DaVinciMicroPanel()
    if not panel.connect():
        print("❌ Failed to connect")
        return

    try:
        # Test the three ADD buttons in correct order
        button_tests = [
            ("ADD_NODE", "Press and release the ADD NODE button (adds new color correction node)"),
            ("ADD_WINDOW", "Press and release the ADD WINDOW button (adds power window/mask)"),
            ("ADD_KEYFRAME", "Press and release the ADD KEYFRAME button (adds keyframe at current position)"),
        ]

        corrected_mapping = {}

        for button_name, instruction in button_tests:
            print(f"\n📍 Testing {button_name}")
            button_id = test_button(panel, button_name, instruction)

            if button_id:
                corrected_mapping[button_name] = button_id
                byte_pos = button_id // 8
                bit_pos = button_id % 8
                print(f"✅ {button_name}: Button#{button_id} (Byte{byte_pos} Bit{bit_pos})")
            else:
                print(f"❌ {button_name}: No mapping detected")

            time.sleep(2)

        # Show corrected results
        print(f"\n🎉 CORRECTED ADD BUTTON MAPPING:")
        print("=" * 50)
        for button_name, button_id in corrected_mapping.items():
            byte_pos = button_id // 8
            bit_pos = button_id % 8
            print(f"  {button_name}: Button#{button_id} (Byte{byte_pos} Bit{bit_pos})")

        # Save corrected mapping
        if corrected_mapping:
            print(f"\n💾 CORRECTION NEEDED IN FILES:")
            print("Update davinci_panel_controls.py and davinci_panel_mapping.json with:")
            for button_name, button_id in corrected_mapping.items():
                byte_pos = button_id // 8
                bit_pos = button_id % 8
                print(f"  '{button_name}': {button_id},  # Byte{byte_pos} Bit{bit_pos}")

    except KeyboardInterrupt:
        print("\n🛑 Remapping interrupted")
    finally:
        panel.cleanup()

if __name__ == "__main__":
    main()