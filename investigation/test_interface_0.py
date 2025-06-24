#!/usr/bin/env python3
"""
Test Interface 0 for DaVinci Micro Panel

Based on the USB log showing DaVinci Control trying to access interface 0,
this script tests interface 0 with proper interface claiming.
"""

import hid
import time
import sys

VENDOR_ID = 0x1edb
PRODUCT_ID = 0xda0f

def test_interface_0():
    """Test interface 0 specifically"""
    print("🎯 Testing Interface 0 (based on DaVinci USB log)")
    print("=" * 60)

    # Find all device interfaces
    devices = hid.enumerate(VENDOR_ID, PRODUCT_ID)
    interface_0 = None

    for device in devices:
        print(f"Found interface {device.get('interface_number', 'N/A')}: {device['path']}")
        if device.get('interface_number') == 0:
            interface_0 = device

    if not interface_0:
        print("❌ Interface 0 not found!")
        return False

    print(f"✅ Found interface 0: {interface_0['path']}")
    print(f"   Usage Page: {interface_0.get('usage_page', 'N/A')}")
    print(f"   Usage: {interface_0.get('usage', 'N/A')}")
    print()

    try:
        device = hid.device()
        device.open_path(interface_0['path'])

        print("📋 Device Info:")
        print(f"   Manufacturer: {device.get_manufacturer_string()}")
        print(f"   Product: {device.get_product_string()}")
        print(f"   Serial: {device.get_serial_number_string()}")
        print()

        # Test illumination commands on interface 0
        print("💡 Testing illumination on interface 0...")
        illumination_commands = [
            ([0x01, 0x01] + [0] * 62, "Standard on"),
            ([0x02, 0x01, 0x01] + [0] * 61, "Pattern 1"),
            ([0x10, 0xFF] + [0] * 62, "High brightness"),
            ([0x0A, 0x01, 0xFF, 0xFF, 0xFF] + [0] * 59, "RGB white"),
            ([0x80, 0x01] + [0] * 62, "High bit set"),
            ([0x00, 0x01, 0x01, 0x01] + [0] * 60, "Multi-byte init"),
        ]

        for cmd, desc in illumination_commands:
            print(f"   Testing: {desc}")
            print(f"   Command: [{' '.join(f'{b:02x}' for b in cmd[:8])}...]")
            try:
                result = device.write(cmd)
                print(f"   Result: {result} bytes written")
                time.sleep(1.5)

                response = input("   Did you see illumination? (y/n/s=skip): ").strip().lower()
                if response == 'y':
                    print(f"🎉 SUCCESS! Working command: {cmd}")
                    return cmd
                elif response == 's':
                    continue

                # Try turning off
                off_cmd = cmd.copy()
                off_cmd[1] = 0x00
                device.write(off_cmd)
                time.sleep(0.5)

            except Exception as e:
                print(f"   Error: {e}")

            print()

        # Test input reading on interface 0
        print("🎮 Testing input reading on interface 0...")
        print("   Move controls for 5 seconds...")

        start_time = time.time()
        packet_count = 0

        while time.time() - start_time < 5:
            try:
                data = device.read(64, timeout_ms=100)
                if data and any(b != 0 for b in data):
                    packet_count += 1
                    hex_data = ' '.join(f'{b:02x}' for b in data[:16])
                    print(f"   📦 Input: [{hex_data}...]")

            except Exception:
                continue

        print(f"   📊 Total input packets: {packet_count}")

        device.close()
        return packet_count > 0

    except Exception as e:
        print(f"❌ Failed to test interface 0: {e}")
        return False

def test_all_interfaces():
    """Test all interfaces to see which ones work"""
    print("\n🔍 Testing all available interfaces...")

    devices = hid.enumerate(VENDOR_ID, PRODUCT_ID)
    for device in devices:
        interface_num = device.get('interface_number', 'Unknown')
        print(f"\n--- Interface {interface_num} ---")
        print(f"Path: {device['path']}")
        print(f"Usage Page: {device.get('usage_page', 'N/A')}")
        print(f"Usage: {device.get('usage', 'N/A')}")

        try:
            hid_device = hid.device()
            hid_device.open_path(device['path'])

            # Quick test write
            test_cmd = [0x01, 0x01] + [0] * 62
            result = hid_device.write(test_cmd)
            print(f"Write test: {result} bytes written")

            # Quick read test
            data = hid_device.read(64, timeout_ms=500)
            if data and any(b != 0 for b in data):
                hex_data = ' '.join(f'{b:02x}' for b in data[:8])
                print(f"Read test: [{hex_data}...]")
            else:
                print("Read test: No data")

            hid_device.close()

        except Exception as e:
            print(f"Test failed: {e}")

def main():
    print("🎛️  DaVinci Micro Panel Interface 0 Test")
    print("Based on USB log: DaVinci Control trying to access interface 0")
    print()

    # Test interface 0 specifically
    result = test_interface_0()

    if not result:
        print("\n⚠️  Interface 0 test unsuccessful")
        print("Testing all interfaces for comparison...")
        test_all_interfaces()

    print("\n✅ Test complete!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")