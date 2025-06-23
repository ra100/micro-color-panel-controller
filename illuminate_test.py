#!/usr/bin/env python3
"""
DaVinci Micro Panel Illumination Test

Based on forum findings that DaVinci Resolve can light up the buttons,
this script systematically tests different command sequences to find
the correct button illumination protocol.
"""

import hid
import time
import sys

VENDOR_ID = 0x1edb
PRODUCT_ID = 0xda0f

def test_illumination_commands():
    """Test various illumination command sequences"""
    print("🔍 Finding DaVinci Micro Panel...")

    # Find device
    devices = hid.enumerate(VENDOR_ID, PRODUCT_ID)
    panel_device = None

    for device in devices:
        if device.get('interface_number') == 2:
            panel_device = device
            break

    if not panel_device:
        print("❌ Panel not found")
        return False

    print(f"✅ Found panel: {panel_device['path']}")

    try:
        device = hid.device()
        device.open_path(panel_device['path'])

        print("🧪 Testing illumination commands...")

        # Based on reverse engineering of similar devices and forum findings
        test_commands = [
            # Standard HID illumination patterns
            ([0x01, 0x01] + [0] * 62, "Standard HID on"),
            ([0x01, 0x00] + [0] * 62, "Standard HID off"),

            # Blackmagic specific patterns (based on other BMD devices)
            ([0x02, 0x01, 0x01] + [0] * 61, "BMD Pattern 1"),
            ([0x02, 0x00, 0x00] + [0] * 61, "BMD Pattern 1 off"),

            ([0x10, 0xFF] + [0] * 62, "High brightness"),
            ([0x10, 0x00] + [0] * 62, "Brightness off"),

            # DaVinci specific (guessing based on other panels)
            ([0x0A, 0x01, 0xFF, 0xFF, 0xFF] + [0] * 59, "RGB white"),
            ([0x0A, 0x00, 0x00, 0x00, 0x00] + [0] * 59, "RGB off"),

            # Feature report attempts
            ([0xE0, 0x01] + [0] * 62, "Feature enable"),
            ([0xE0, 0x00] + [0] * 62, "Feature disable"),

            # Longer command sequences (some devices need multiple bytes)
            ([0x01, 0x02, 0x03, 0x01] + [0] * 60, "Complex pattern 1"),
            ([0x01, 0x02, 0x03, 0x00] + [0] * 60, "Complex pattern 1 off"),

            ([0x80, 0x01] + [0] * 62, "High bit set"),
            ([0x80, 0x00] + [0] * 62, "High bit clear"),

            # Panel initialization + illumination
            ([0x00, 0x01, 0x01, 0x01, 0x01] + [0] * 59, "Init + illuminate"),
            ([0x00, 0x00, 0x00, 0x00, 0x00] + [0] * 59, "Init + off"),
        ]

        for i, (cmd, description) in enumerate(test_commands):
            print(f"  Test {i+1:2d}: {description}")
            print(f"          Command: [{' '.join(f'{b:02x}' for b in cmd[:8])}...]")

            try:
                result = device.write(cmd)
                print(f"          Result: {result} bytes written")

                # Give time to see the effect
                time.sleep(1.5)

                # Ask user if they saw anything
                response = input("          Did you see button illumination? (y/n/q): ").strip().lower()
                if response == 'y':
                    print(f"🎉 SUCCESS! Command that worked:")
                    print(f"    Description: {description}")
                    print(f"    Command: {cmd}")
                    return cmd
                elif response == 'q':
                    print("🛑 Stopped by user")
                    break

            except Exception as e:
                print(f"          Error: {e}")

            print()

        device.close()

    except Exception as e:
        print(f"❌ Failed to test: {e}")
        return False

    print("❌ No working illumination command found")
    return False

def test_input_activation():
    """Test if sending illumination commands activates input reporting"""
    print("\n🎮 Testing if illumination commands activate input...")

    devices = hid.enumerate(VENDOR_ID, PRODUCT_ID)
    panel_device = None

    for device in devices:
        if device.get('interface_number') == 2:
            panel_device = device
            break

    if not panel_device:
        return

    try:
        device = hid.device()
        device.open_path(panel_device['path'])

        # Try a few activation commands
        activation_commands = [
            [0x01, 0x01] + [0] * 62,
            [0x02, 0x01, 0x01] + [0] * 61,
            [0x10, 0xFF] + [0] * 62,
        ]

        for cmd in activation_commands:
            print(f"Sending activation command: [{' '.join(f'{b:02x}' for b in cmd[:4])}...]")
            device.write(cmd)
            time.sleep(0.5)

        print("Reading for 5 seconds (try moving controls)...")
        start_time = time.time()
        packet_count = 0

        while time.time() - start_time < 5:
            try:
                data = device.read(64, timeout_ms=100)
                if data and any(b != 0 for b in data):
                    packet_count += 1
                    hex_data = ' '.join(f'{b:02x}' for b in data[:16])
                    print(f"📦 Input data: [{hex_data}...]")

            except Exception:
                continue

        print(f"📊 Received {packet_count} input packets")
        device.close()

    except Exception as e:
        print(f"❌ Input test failed: {e}")

def main():
    print("🎛️  DaVinci Micro Panel Illumination Tester")
    print("=" * 60)
    print("This will systematically test illumination commands.")
    print("Watch the panel for any button lights turning on/off.")
    print()

    # Test illumination
    working_cmd = test_illumination_commands()

    if working_cmd:
        print(f"\n🎉 Found working command: {working_cmd}")

    # Test input activation
    test_input_activation()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")