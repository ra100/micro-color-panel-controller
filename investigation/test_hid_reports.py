#!/usr/bin/env python3
"""
Test HID SET_REPORT commands discovered from DaVinci capture
These are the exact patterns DaVinci uses to control the panel!
"""

import usb.core
import usb.util
import time

# DaVinci Micro Panel USB IDs
VENDOR_ID = 0x1edb
PRODUCT_ID = 0xda0f

def test_hid_reports():
    """Test the HID SET_REPORT patterns discovered from capture"""

    # Find the device
    device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if device is None:
        print("❌ DaVinci Micro Panel not found!")
        return False

    print(f"✅ Found DaVinci Micro Panel: {device}")

    # The patterns we discovered from DaVinci capture
    # These are HID SET_REPORT commands (bmRequestType=0x21, bRequest=0x02)
    test_patterns = [
        # Report ID 0x13 with 10 bytes of data
        {
            'report_id': 0x13,
            'data_length': 10,
            'test_data': bytes([0x13, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])  # Simple test pattern
        },
        # Report ID 0x14 with 7 bytes of data
        {
            'report_id': 0x14,
            'data_length': 7,
            'test_data': bytes([0x14, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00])  # Simple test pattern
        },
        # Report ID 0x15 with 10 bytes of data
        {
            'report_id': 0x15,
            'data_length': 10,
            'test_data': bytes([0x15, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])  # All on pattern
        },
        # Report ID 0x16 with 7 bytes of data
        {
            'report_id': 0x16,
            'data_length': 7,
            'test_data': bytes([0x16, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])  # All on pattern
        },
        # Report ID 0x17 with 14 bytes of data
        {
            'report_id': 0x17,
            'data_length': 14,
            'test_data': bytes([0x17, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80])  # Medium brightness
        },
        # Report ID 0x18 with 10 bytes of data
        {
            'report_id': 0x18,
            'data_length': 10,
            'test_data': bytes([0x18, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x01])  # Pattern test
        }
    ]

    try:
        # Detach kernel driver if necessary
        if device.is_kernel_driver_active(2):  # Interface 2 is HID
            print("🔓 Detaching kernel driver from interface 2")
            device.detach_kernel_driver(2)

        # Claim interface 2 (HID interface)
        usb.util.claim_interface(device, 2)
        print("✅ Claimed HID interface 2")

        print("\n🚀 Testing HID SET_REPORT patterns from DaVinci capture...")

        for i, pattern in enumerate(test_patterns):
            report_id = pattern['report_id']
            data = pattern['test_data']

            print(f"\n📡 Test {i+1}: Sending HID SET_REPORT for Report ID 0x{report_id:02x}")
            print(f"   Data: {data.hex()}")

            try:
                # Send HID SET_REPORT command
                # bmRequestType=0x21 (Host->Device, Class, Interface)
                # bRequest=0x02 (SET_REPORT)
                # wValue=(2<<8)|report_id (Report Type 2 = Output, Report ID)
                # wIndex=2 (Interface 2)
                # data=report data

                result = device.ctrl_transfer(
                    bmRequestType=0x21,  # Host->Device, Class, Interface
                    bRequest=0x02,       # SET_REPORT
                    wValue=(2 << 8) | report_id,  # Report Type 2 (Output), Report ID
                    wIndex=2,            # Interface 2 (HID interface)
                    data_or_wLength=data
                )

                print(f"   ✅ Success! Sent {len(data)} bytes")
                time.sleep(0.5)  # Wait a bit to see any changes

            except usb.core.USBError as e:
                print(f"   ❌ Failed: {e}")
                continue

        print("\n🎉 All HID report tests completed!")
        print("👀 Check your panel - any buttons lighting up?")

        # Try to read some reports back to see device status
        print("\n📖 Trying to read back some reports...")
        for report_id in [0x13, 0x14, 0x15]:
            try:
                # HID GET_REPORT
                result = device.ctrl_transfer(
                    bmRequestType=0xa1,  # Device->Host, Class, Interface
                    bRequest=0x01,       # GET_REPORT
                    wValue=(3 << 8) | report_id,  # Report Type 3 (Feature), Report ID
                    wIndex=2,            # Interface 2
                    data_or_wLength=255   # Max length
                )
                print(f"   Report 0x{report_id:02x}: {bytes(result).hex()}")
            except usb.core.USBError as e:
                print(f"   Report 0x{report_id:02x}: Failed - {e}")

    except usb.core.USBError as e:
        print(f"❌ USB Error: {e}")
        return False

    finally:
        # Release interface
        try:
            usb.util.release_interface(device, 2)
            print("🔓 Released interface 2")
        except:
            pass

    return True

if __name__ == "__main__":
    print("🎯 Testing HID SET_REPORT patterns discovered from DaVinci capture!")
    print("=" * 70)
    test_hid_reports()