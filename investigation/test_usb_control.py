#!/usr/bin/env python3
"""
USB Control Transfer Test for DaVinci Micro Panel Interface 0

Based on USB analysis showing Interface 0 is vendor-specific with no endpoints,
this script uses libusb (pyusb) to communicate via control transfers.
"""

import usb.core
import usb.util
import time
import sys

VENDOR_ID = 0x1edb
PRODUCT_ID = 0xda0f

def test_usb_control():
    """Test USB control transfers to vendor-specific interface 0"""
    print("🎯 USB Control Transfer Test for Interface 0")
    print("=" * 60)

    # Find the device
    device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if device is None:
        print("❌ Device not found")
        return False

    print(f"✅ Found device: {device}")
    print(f"   Manufacturer: {usb.util.get_string(device, device.iManufacturer)}")
    print(f"   Product: {usb.util.get_string(device, device.iProduct)}")
    print(f"   Serial: {usb.util.get_string(device, device.iSerialNumber)}")
    print()

    # Check if kernel driver is attached and detach if necessary
    try:
        if device.is_kernel_driver_active(0):
            print("📌 Detaching kernel driver from interface 0...")
            device.detach_kernel_driver(0)
    except usb.core.USBError as e:
        print(f"⚠️  Kernel driver info: {e}")

    # Set configuration
    try:
        device.set_configuration()
        print("✅ Device configuration set")
    except usb.core.USBError as e:
        print(f"⚠️  Configuration warning: {e}")

    # Claim interface 0
    try:
        usb.util.claim_interface(device, 0)
        print("✅ Successfully claimed interface 0")
    except usb.core.USBError as e:
        print(f"❌ Failed to claim interface 0: {e}")
        return False

    print()

    try:
        # Test various control transfer requests
        # Control transfer format: bmRequestType, bRequest, wValue, wIndex, data

        print("💡 Testing illumination control transfers...")

        # Vendor requests for illumination (educated guesses)
        illumination_tests = [
            # (bmRequestType, bRequest, wValue, wIndex, data_or_length, description)
            (0x40, 0x01, 0x0001, 0x0000, [0x01], "Vendor out: Enable"),
            (0x40, 0x01, 0x0000, 0x0000, [0x00], "Vendor out: Disable"),
            (0x40, 0x02, 0x00FF, 0x0000, [0xFF, 0xFF, 0xFF], "Vendor out: RGB white"),
            (0x40, 0x02, 0x0000, 0x0000, [0x00, 0x00, 0x00], "Vendor out: RGB off"),
            (0x40, 0x10, 0x0001, 0x0000, [0x01, 0x01, 0x01, 0x01], "Vendor out: Multi-byte on"),
            (0x40, 0x10, 0x0000, 0x0000, [0x00, 0x00, 0x00, 0x00], "Vendor out: Multi-byte off"),

            # Class requests
            (0x21, 0x09, 0x0001, 0x0000, [0x01], "Class out: HID set_report"),
            (0x21, 0x0A, 0x0000, 0x0000, [], "Class out: HID set_idle"),
        ]

        for bmRequestType, bRequest, wValue, wIndex, data, description in illumination_tests:
            print(f"   Testing: {description}")
            print(f"   Request: type=0x{bmRequestType:02x}, req=0x{bRequest:02x}, val=0x{wValue:04x}, idx=0x{wIndex:04x}")

            try:
                if data:
                    result = device.ctrl_transfer(bmRequestType, bRequest, wValue, wIndex, data)
                    print(f"   Result: {result} bytes transferred")
                else:
                    result = device.ctrl_transfer(bmRequestType, bRequest, wValue, wIndex)
                    print(f"   Result: {result}")

                time.sleep(1.5)
                response = input("   Did you see illumination? (y/n/s=skip): ").strip().lower()
                if response == 'y':
                    print(f"🎉 SUCCESS! Working control transfer:")
                    print(f"    {description}")
                    print(f"    bmRequestType=0x{bmRequestType:02x}, bRequest=0x{bRequest:02x}")
                    print(f"    wValue=0x{wValue:04x}, wIndex=0x{wIndex:04x}, data={data}")
                    return True
                elif response == 's':
                    continue

            except usb.core.USBError as e:
                print(f"   Error: {e}")

            print()

        # Test input via control transfers (vendor-specific get requests)
        print("🎮 Testing input via control transfers...")

        input_tests = [
            (0xC0, 0x01, 0x0000, 0x0000, 64, "Vendor in: Get status"),
            (0xC0, 0x02, 0x0000, 0x0000, 64, "Vendor in: Get controls"),
            (0xA1, 0x01, 0x0000, 0x0000, 64, "Class in: HID get_report"),
        ]

        for bmRequestType, bRequest, wValue, wIndex, length, description in input_tests:
            print(f"   Testing: {description}")
            try:
                result = device.ctrl_transfer(bmRequestType, bRequest, wValue, wIndex, length)
                if result and any(b != 0 for b in result):
                    hex_data = ' '.join(f'{b:02x}' for b in result[:16])
                    print(f"   Data: [{hex_data}{'...' if len(result) > 16 else ''}] ({len(result)} bytes)")
                else:
                    print(f"   No data or all zeros ({len(result)} bytes)")

            except usb.core.USBError as e:
                print(f"   Error: {e}")

        print()

        # Monitor for input changes
        print("📡 Monitoring for control state changes (5 seconds)...")
        print("   Move controls now...")

        baseline = None
        changes = 0

        for i in range(25):  # 5 seconds at 0.2s intervals
            try:
                # Try to read current state
                result = device.ctrl_transfer(0xC0, 0x01, 0x0000, 0x0000, 64)

                if baseline is None:
                    baseline = result
                elif result != baseline:
                    changes += 1
                    hex_data = ' '.join(f'{b:02x}' for b in result[:16])
                    print(f"   Change {changes}: [{hex_data}...]")
                    baseline = result

                time.sleep(0.2)

            except usb.core.USBError:
                pass

        print(f"   📊 Detected {changes} state changes")

    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

    finally:
        # Release interface
        try:
            usb.util.release_interface(device, 0)
            print("✅ Released interface 0")
        except:
            pass

    return False

def main():
    print("🎛️  DaVinci Micro Panel USB Control Transfer Test")
    print("Testing vendor-specific interface 0 with control transfers")
    print("Based on USB analysis and DaVinci Control USB log")
    print()

    try:
        result = test_usb_control()
        if result:
            print("\n🎉 Found working control transfer!")
        else:
            print("\n⚠️  No working control transfers found")

    except PermissionError:
        print("❌ Permission denied. Try running with sudo:")
        print("sudo /home/ra100/miniconda3/envs/micro-panel/bin/python test_usb_control.py")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()