#!/usr/bin/env python3
"""
Working illumination control based on captured DaVinci traffic!
These are the EXACT commands that work for controlling panel illumination.
"""

import usb.core
import usb.util
import time

# DaVinci Micro Panel USB IDs
VENDOR_ID = 0x1edb
PRODUCT_ID = 0xda0f

def test_working_illumination():
    """Test the exact working HID commands discovered from DaVinci capture"""

    # Find the device
    device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if device is None:
        print("❌ DaVinci Micro Panel not found!")
        return False

    print(f"✅ Found DaVinci Micro Panel")

    # Working patterns from successful capture
    working_commands = [
        {
            'name': 'Initial State',
            'bmRequestType': 0x21,
            'bRequest': 0x09,
            'wValue': 0x0303,  # Report Type 3, Report ID 0x03
            'wIndex': 0x0002,  # Interface 2
            'data': bytes([0x03, 0x00, 0x00])  # Report ID + OFF data
        },
        {
            'name': 'Secondary Control',
            'bmRequestType': 0x21,
            'bRequest': 0x09,
            'wValue': 0x030a,  # Report Type 3, Report ID 0x0a
            'wIndex': 0x0002,  # Interface 2
            'data': bytes([0x0a, 0x01])  # Report ID + control data
        },
        {
            'name': 'ILLUMINATE ON (Medium Brightness)',
            'bmRequestType': 0x21,
            'bRequest': 0x09,
            'wValue': 0x0303,  # Report Type 3, Report ID 0x03
            'wIndex': 0x0002,  # Interface 2
            'data': bytes([0x03, 0x64, 0x64])  # Report ID + ON data (0x64 = 100)
        },
        {
            'name': 'ILLUMINATE OFF',
            'bmRequestType': 0x21,
            'bRequest': 0x09,
            'wValue': 0x0303,  # Report Type 3, Report ID 0x03
            'wIndex': 0x0002,  # Interface 2
            'data': bytes([0x03, 0x00, 0x00])  # Report ID + OFF data
        },
        {
            'name': 'Full Brightness Test',
            'bmRequestType': 0x21,
            'bRequest': 0x09,
            'wValue': 0x0303,  # Report Type 3, Report ID 0x03
            'wIndex': 0x0002,  # Interface 2
            'data': bytes([0x03, 0xFF, 0xFF])  # Report ID + MAX brightness
        },
    ]

    try:
        # Detach kernel driver if necessary
        if device.is_kernel_driver_active(2):
            print("🔓 Detaching kernel driver from interface 2")
            device.detach_kernel_driver(2)

        # Claim interface 2 (HID interface)
        usb.util.claim_interface(device, 2)
        print("✅ Claimed HID interface 2")

        print("\n🚀 Testing WORKING illumination commands from DaVinci capture...")

        for i, cmd in enumerate(working_commands):
            print(f"\n💡 Test {i+1}: {cmd['name']}")
            print(f"   Command: {cmd['data'].hex()}")

            try:
                result = device.ctrl_transfer(
                    bmRequestType=cmd['bmRequestType'],
                    bRequest=cmd['bRequest'],
                    wValue=cmd['wValue'],
                    wIndex=cmd['wIndex'],
                    data_or_wLength=cmd['data']
                )

                print(f"   ✅ SUCCESS! Sent {len(cmd['data'])} bytes")
                print("   👀 Check your panel - any illumination changes?")
                time.sleep(2)  # Wait to see the effect

            except usb.core.USBError as e:
                print(f"   ❌ Failed: {e}")

        # Demo sequence: OFF -> DIM -> BRIGHT -> DIM (255 is actually dim!) -> OFF
        # Note: Device has non-linear brightness - 100 is brighter than 255!
        print("\n🎆 DEMO SEQUENCE: Cycling illumination...")
        demo_sequence = [
            (bytes([0x03, 0x00, 0x00]), "OFF"),
            (bytes([0x03, 0x32, 0x32]), "DIM"),     # 0x32 = 50
            (bytes([0x03, 0x64, 0x64]), "BRIGHT"),  # 0x64 = 100 (actually brightest!)
            (bytes([0x03, 0xFF, 0xFF]), "DIM (255)"), # 0xFF = 255 (actually dim!)
            (bytes([0x03, 0x00, 0x00]), "OFF"),
        ]

        for data, name in demo_sequence:
            print(f"   → {name}")
            try:
                device.ctrl_transfer(
                    bmRequestType=0x21,
                    bRequest=0x09,
                    wValue=0x0303,
                    wIndex=0x0002,
                    data_or_wLength=data
                )
                time.sleep(1)
            except usb.core.USBError as e:
                print(f"     Error: {e}")

        print("\n🎉 Working illumination test completed!")

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
    print("🎯 Testing WORKING illumination patterns from DaVinci capture!")
    print("🔥 These are the exact commands that DaVinci uses!")
    print("=" * 70)
    test_working_illumination()