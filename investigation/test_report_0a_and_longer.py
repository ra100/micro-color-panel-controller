#!/usr/bin/env python3
"""
Test Report ID 0x0a and explore longer data packets for individual button control
"""

import usb.core
import usb.util
import time

# DaVinci Micro Panel USB IDs
VENDOR_ID = 0x1edb
PRODUCT_ID = 0xda0f

def send_hid_command(device, report_id, data, description=""):
    """Send HID command and handle errors"""
    full_data = bytes([report_id] + list(data))
    print(f"   Testing Report ID 0x{report_id:02x}: {full_data.hex()} {description}")

    try:
        device.ctrl_transfer(
            bmRequestType=0x21,
            bRequest=0x09,
            wValue=(3 << 8) | report_id,  # Report Type 3, Report ID
            wIndex=0x0002,
            data_or_wLength=full_data
        )
        print(f"   ✅ SUCCESS - Check panel!")
        return True
    except usb.core.USBError as e:
        print(f"   ❌ Failed: {e}")
        return False

def test_report_0a_and_longer():
    """Test Report ID 0x0a and longer data packets for individual button control"""

    # Find the device
    device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if device is None:
        print("❌ DaVinci Micro Panel not found!")
        return False

    print(f"✅ Found DaVinci Micro Panel")

    try:
        # Detach kernel driver if necessary
        if device.is_kernel_driver_active(2):
            print("🔓 Detaching kernel driver from interface 2")
            device.detach_kernel_driver(2)

        # Claim interface 2 (HID interface)
        usb.util.claim_interface(device, 2)
        print("✅ Claimed HID interface 2")

        # First, turn on global illumination
        print("\n🔧 Setting global illumination ON...")
        send_hid_command(device, 0x03, [0x64, 0x64], "(Global ON)")
        time.sleep(1)

        print("\n🧪 Testing Report ID 0x0a (from capture)...")

        # Test Report ID 0x0a patterns from capture
        test_0a_patterns = [
            ([0x01], "Basic control from capture"),
            ([0x00], "Try OFF"),
            ([0xFF], "Try MAX"),
            ([0x64], "Try medium"),
            ([0x01, 0x00], "Extended with zero"),
            ([0x01, 0xFF], "Extended with max"),
        ]

        for data, desc in test_0a_patterns:
            print(f"\n🎯 Test 0x0a: {desc}")
            success = send_hid_command(device, 0x0a, data, f"({desc})")
            if success:
                time.sleep(2)
                print("   💭 Any change in button illumination? (Press Enter)")
                input()

        print("\n🔍 Testing other Report IDs for individual button control...")

        # Test different report IDs with longer data for individual buttons
        # Panel has 52 buttons + 15 encoders = 67 controls
        # Might need 8+ bytes for individual control

        other_report_ids = [0x01, 0x02, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0b, 0x0c]

        for report_id in other_report_ids:
            print(f"\n📡 Testing Report ID 0x{report_id:02x} with different data lengths...")

            test_patterns = [
                # Short patterns
                ([0x01], "Single byte ON"),
                ([0xFF], "Single byte MAX"),
                ([0x00], "Single byte OFF"),

                # Longer patterns for individual buttons
                ([0x01, 0x00, 0x00, 0x00], "4-byte pattern"),
                ([0xFF, 0x00, 0x00, 0x00], "First group only"),
                ([0x00, 0xFF, 0x00, 0x00], "Second group only"),
                ([0x00, 0x00, 0xFF, 0x00], "Third group only"),
                ([0x00, 0x00, 0x00, 0xFF], "Fourth group only"),

                # Even longer for all buttons
                ([0x01] * 8, "8-byte pattern (64 bits)"),
                ([0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00], "Alternating 8-byte"),
            ]

            for data, desc in test_patterns:
                success = send_hid_command(device, report_id, data, f"({desc})")
                if success:
                    time.sleep(1)
                    # Check if user sees any change
                    response = input("   💭 See any button changes? (y/n/Enter): ").strip().lower()
                    if response == 'y':
                        print(f"   🎉 FOUND WORKING PATTERN! Report 0x{report_id:02x}: {bytes([report_id] + data).hex()}")
                        # Test more variations of this working pattern
                        print("   🔬 Testing variations of this working pattern...")
                        for i in range(len(data)):
                            test_data = data.copy()
                            test_data[i] = 0x00 if test_data[i] != 0x00 else 0xFF
                            send_hid_command(device, report_id, test_data, f"(Variation {i+1})")
                            time.sleep(1)
                            input("   Press Enter for next variation...")

                # Reset to off
                send_hid_command(device, 0x03, [0x00, 0x00], "(Reset global OFF)")
                send_hid_command(device, 0x03, [0x64, 0x64], "(Reset global ON)")
                time.sleep(0.5)

        print("\n🎉 Exploration completed!")

    except usb.core.USBError as e:
        print(f"❌ USB Error: {e}")
        return False

    finally:
        try:
            usb.util.release_interface(device, 2)
            print("🔓 Released interface 2")
        except:
            pass

    return True

if __name__ == "__main__":
    print("🔍 Testing Report ID 0x0a and Individual Button Control")
    print("🎯 Looking for individual button illumination patterns!")
    print("=" * 70)
    test_report_0a_and_longer()