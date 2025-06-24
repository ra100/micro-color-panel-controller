#!/usr/bin/env python3
"""
HID Protocol Debugging Tool for DaVinci Micro Panel

This script helps reverse engineer the USB HID protocol by:
- Enumerating all device interfaces
- Capturing raw HID reports
- Testing different connection methods
- Analyzing data patterns

Usage: python debug_hid.py
"""

import hid
import time
import sys
import threading
from typing import List, Optional

# Device identifiers
VENDOR_ID = 0x1edb  # Blackmagic Design
PRODUCT_ID = 0xda0f  # DaVinci Resolve Micro Color Panel

def enumerate_devices():
    """List all HID devices and find our panel"""
    print("🔍 Enumerating HID devices...")
    devices = hid.enumerate()

    panel_devices = []
    for device in devices:
        if device['vendor_id'] == VENDOR_ID and device['product_id'] == PRODUCT_ID:
            panel_devices.append(device)
            print(f"✅ Found DaVinci Panel Interface:")
            print(f"   Path: {device['path']}")
            print(f"   Interface: {device.get('interface_number', 'N/A')}")
            print(f"   Usage Page: {device.get('usage_page', 'N/A')}")
            print(f"   Usage: {device.get('usage', 'N/A')}")
            print(f"   Product: {device.get('product_string', 'N/A')}")
            print()

    if not panel_devices:
        print("❌ No DaVinci Panel found")
        return []

    return panel_devices

def test_interface(device_info: dict, duration: int = 10):
    """Test a specific device interface"""
    path = device_info['path']
    interface = device_info.get('interface_number', 'Unknown')

    print(f"🧪 Testing interface {interface}...")
    print(f"   Path: {path}")

    try:
        device = hid.device()
        device.open_path(path)

        # Get device info
        print(f"   Manufacturer: {device.get_manufacturer_string()}")
        print(f"   Product: {device.get_product_string()}")
        print(f"   Serial: {device.get_serial_number_string()}")

        # Try to initialize the device first
        print(f"   Attempting device initialization...")
        init_commands = [
            [0x00] + [0] * 63,  # Null command
            [0x01, 0x00] + [0] * 62,  # Enable reporting?
            [0x02, 0x01] + [0] * 62,  # Different init
        ]

        for i, cmd in enumerate(init_commands):
            try:
                result = device.write(cmd)
                print(f"     Init command {i+1}: {result} bytes written")
                time.sleep(0.1)
            except Exception as e:
                print(f"     Init command {i+1} failed: {e}")

        # Try to read data
        print(f"   Reading data for {duration}s (move controls now)...")
        start_time = time.time()
        packet_count = 0

        while time.time() - start_time < duration:
            try:
                # Try non-blocking read first
                data = device.read(64, timeout_ms=50)
                if data and any(b != 0 for b in data):  # Only non-zero data
                    packet_count += 1
                    if packet_count <= 10:  # Only show first 10 packets
                        hex_data = ' '.join(f'{b:02x}' for b in data)
                        print(f"   📦 Packet {packet_count}: [{hex_data}]")
                    elif packet_count == 11:
                        print(f"   ... (showing first 10 packets only)")

            except Exception as e:
                if "Operation timed out" not in str(e):
                    print(f"   ⚠️  Read error: {e}")
                continue

        print(f"   📊 Total packets received: {packet_count}")

        # Try feature reports as well
        print(f"   Trying to read feature reports...")
        for report_id in [0, 1, 2, 3]:
            try:
                feature_data = device.get_feature_report(report_id, 64)
                if feature_data and any(b != 0 for b in feature_data):
                    hex_data = ' '.join(f'{b:02x}' for b in feature_data[:16])
                    print(f"   📋 Feature report {report_id}: [{hex_data}...]")
            except Exception as e:
                pass  # Feature reports might not be supported

        device.close()
        return packet_count > 0

    except Exception as e:
        print(f"   ❌ Failed to test interface: {e}")
        return False

def test_output_commands(device_path: str):
    """Test different output commands to control illumination"""
    print(f"💡 Testing output commands...")

    try:
        device = hid.device()
        device.open_path(device_path)

        # Common HID report formats for device control
        test_commands = [
            # Format: [report_id, command, value, padding...]
            [0x01, 0x01] + [0] * 62,  # Simple on/off
            [0x02, 0x01] + [0] * 62,  # Different report ID
            [0x00, 0x01, 0x01] + [0] * 61,  # No report ID
            [0x10, 0x01] + [0] * 62,  # Higher report ID
            [0xFF, 0x01] + [0] * 62,  # Max report ID
        ]

        for i, cmd in enumerate(test_commands):
            print(f"   Testing command {i+1}: [{' '.join(f'{b:02x}' for b in cmd[:8])}...]")
            try:
                result = device.write(cmd)
                print(f"     Result: {result} bytes written")
                time.sleep(0.5)  # Give time to see effect

                # Try to turn off
                off_cmd = cmd.copy()
                off_cmd[1] = 0x00  # Set command byte to 0
                device.write(off_cmd)
                time.sleep(0.5)

            except Exception as e:
                print(f"     Error: {e}")

        device.close()

    except Exception as e:
        print(f"   ❌ Failed to test output: {e}")

def monitor_continuous(device_path: str):
    """Continuously monitor HID data"""
    print(f"📡 Starting continuous monitoring...")
    print("   Move controls on the panel - press Ctrl+C to stop")

    try:
        device = hid.device()
        device.open_path(device_path)

        packet_count = 0
        last_data = None

        while True:
            try:
                data = device.read(64, timeout_ms=100)
                if data and data != last_data:  # Only show changed data
                    packet_count += 1
                    timestamp = time.strftime("%H:%M:%S.%f")[:-3]
                    hex_data = ' '.join(f'{b:02x}' for b in data[:16])
                    print(f"[{timestamp}] #{packet_count:04d}: [{hex_data}{'...' if len(data) > 16 else ''}]")
                    last_data = data

            except KeyboardInterrupt:
                break
            except Exception as e:
                if "Operation timed out" not in str(e):
                    print(f"Read error: {e}")

        device.close()
        print(f"\n📊 Monitoring complete. Total packets: {packet_count}")

    except Exception as e:
        print(f"❌ Monitoring failed: {e}")

def main():
    """Main debugging function"""
    print("🎛️  DaVinci Micro Panel HID Protocol Debugger")
    print("=" * 60)

    # Step 1: Find all panel interfaces
    panel_devices = enumerate_devices()
    if not panel_devices:
        return 1

    # Step 2: Test each interface briefly
    working_interfaces = []
    for device_info in panel_devices:
        if test_interface(device_info, duration=3):
            working_interfaces.append(device_info)
        print()

    if not working_interfaces:
        print("❌ No working interfaces found")
        return 1

    # Step 3: Use the first working interface for detailed testing
    primary_device = working_interfaces[0]
    print(f"🎯 Using primary interface: {primary_device.get('interface_number', 'Unknown')}")
    print()

    # Step 4: Test output commands
    test_output_commands(primary_device['path'])
    print()

    # Step 5: Offer continuous monitoring
    try:
        response = input("📡 Start continuous monitoring? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            monitor_continuous(primary_device['path'])
    except KeyboardInterrupt:
        pass

    print("\n✅ Debugging complete!")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)