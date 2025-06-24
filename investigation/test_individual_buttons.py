#!/usr/bin/env python3
"""
Test individual button illumination control
Exploring if we can control individual buttons or button groups
"""

import usb.core
import usb.util
import time

# DaVinci Micro Panel USB IDs
VENDOR_ID = 0x1edb
PRODUCT_ID = 0xda0f

def send_illumination_command(device, byte1, byte2, description=""):
    """Send illumination command and handle errors"""
    data = bytes([0x03, byte1, byte2])
    print(f"   Testing: {data.hex()} {description}")

    try:
        device.ctrl_transfer(
            bmRequestType=0x21,
            bRequest=0x09,
            wValue=0x0303,
            wIndex=0x0002,
            data_or_wLength=data
        )
        print(f"   ✅ SUCCESS - Check panel illumination!")
        return True
    except usb.core.USBError as e:
        print(f"   ❌ Failed: {e}")
        return False

def test_individual_buttons():
    """Test individual button and group illumination patterns"""

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

        # Start with all off
        print("\n🔄 Resetting all buttons to OFF...")
        send_illumination_command(device, 0x00, 0x00, "(All OFF)")
        time.sleep(1)

        print("\n🔍 Testing different bit patterns for individual button control...")

        # Test if the two bytes control different button groups
        test_patterns = [
            # Test individual bits in first byte
            (0x01, 0x00, "First byte bit 0"),
            (0x02, 0x00, "First byte bit 1"),
            (0x04, 0x00, "First byte bit 2"),
            (0x08, 0x00, "First byte bit 3"),
            (0x10, 0x00, "First byte bit 4"),
            (0x20, 0x00, "First byte bit 5"),
            (0x40, 0x00, "First byte bit 6"),
            (0x80, 0x00, "First byte bit 7"),

            # Test individual bits in second byte
            (0x00, 0x01, "Second byte bit 0"),
            (0x00, 0x02, "Second byte bit 1"),
            (0x00, 0x04, "Second byte bit 2"),
            (0x00, 0x08, "Second byte bit 3"),
            (0x00, 0x10, "Second byte bit 4"),
            (0x00, 0x20, "Second byte bit 5"),
            (0x00, 0x40, "Second byte bit 6"),
            (0x00, 0x80, "Second byte bit 7"),

            # Test some combinations
            (0xFF, 0x00, "All first byte bits"),
            (0x00, 0xFF, "All second byte bits"),
            (0x0F, 0x0F, "Lower nibbles"),
            (0xF0, 0xF0, "Upper nibbles"),

            # Test different brightness levels on different groups
            (0x32, 0x64, "Dim first group, Medium second group"),
            (0x64, 0x32, "Medium first group, Dim second group"),
            (0xFF, 0x32, "Bright first group, Dim second group"),
            (0x32, 0xFF, "Dim first group, Bright second group"),
        ]

        for byte1, byte2, description in test_patterns:
            print(f"\n🎯 Test: {description}")
            success = send_illumination_command(device, byte1, byte2, f"({description})")
            if success:
                time.sleep(2)  # Wait to observe the effect

                # Ask user for feedback
                print("   💭 Do you see any illumination change? (Press Enter to continue)")
                input()

            # Reset to off between tests
            send_illumination_command(device, 0x00, 0x00, "(Reset OFF)")
            time.sleep(0.5)

        print("\n🎆 Final test: Cycling through different patterns...")
        cycle_patterns = [
            (0x55, 0x55, "Alternating bits pattern 1"),
            (0xAA, 0xAA, "Alternating bits pattern 2"),
            (0x0F, 0xF0, "Checkerboard pattern 1"),
            (0xF0, 0x0F, "Checkerboard pattern 2"),
            (0xFF, 0xFF, "All ON"),
            (0x00, 0x00, "All OFF"),
        ]

        for byte1, byte2, description in cycle_patterns:
            print(f"   → {description}")
            send_illumination_command(device, byte1, byte2)
            time.sleep(1)

        print("\n🎉 Individual button test completed!")
        print("📝 Based on what you observed, we can map the button control scheme!")

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
    print("🔍 Testing Individual Button Illumination Control")
    print("🎯 Let's see if we can control individual buttons or groups!")
    print("=" * 70)
    test_individual_buttons()