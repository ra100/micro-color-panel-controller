#!/usr/bin/env python3
"""
Improved HID report testing using Interface 0 and different approaches
"""

import usb.core
import usb.util
import time

# DaVinci Micro Panel USB IDs
VENDOR_ID = 0x1edb
PRODUCT_ID = 0xda0f

def test_interface_0_reports():
    """Test HID reports using Interface 0 (vendor-specific)"""

    # Find the device
    device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if device is None:
        print("❌ DaVinci Micro Panel not found!")
        return False

    print(f"✅ Found DaVinci Micro Panel")

    # Check if DaVinci process is running
    import subprocess
    try:
        result = subprocess.run(['pgrep', '-f', 'DaVinci'], capture_output=True, text=True)
        if result.stdout.strip():
            print("⚠️  DaVinci process detected - this might interfere!")
            print("   Consider closing DaVinci Resolve if tests fail")
    except:
        pass

    # Test patterns with different interfaces and report types
    test_configs = [
        # Interface 0 with Feature reports (Type 3)
        {'interface': 0, 'report_type': 3, 'name': 'Interface 0, Feature Reports'},
        # Interface 0 with Output reports (Type 2)
        {'interface': 0, 'report_type': 2, 'name': 'Interface 0, Output Reports'},
        # Interface 2 with Feature reports (Type 3)
        {'interface': 2, 'report_type': 3, 'name': 'Interface 2, Feature Reports'},
    ]

    # Test data patterns
    test_data = [
        {'id': 0x13, 'data': bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])},  # 9 bytes
        {'id': 0x14, 'data': bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00])},  # 6 bytes
        {'id': 0x15, 'data': bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])},  # All on
        {'id': 0x16, 'data': bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])},  # All on
        {'id': 0x17, 'data': bytes([0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80])},  # 13 bytes
        {'id': 0x18, 'data': bytes([0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x01])},  # Pattern
    ]

    for config in test_configs:
        interface = config['interface']
        report_type = config['report_type']
        name = config['name']

        print(f"\n🧪 Testing: {name}")
        print("=" * 50)

        try:
            # Detach kernel driver if necessary
            if device.is_kernel_driver_active(interface):
                print(f"🔓 Detaching kernel driver from interface {interface}")
                device.detach_kernel_driver(interface)

            # Claim interface
            usb.util.claim_interface(device, interface)
            print(f"✅ Claimed interface {interface}")

            # Test each report
            for test in test_data:
                report_id = test['id']
                data = test['data']

                print(f"\n📡 Testing Report ID 0x{report_id:02x} ({len(data)} bytes)")
                print(f"   Data: {data.hex()}")

                try:
                    # Send HID SET_REPORT command
                    result = device.ctrl_transfer(
                        bmRequestType=0x21,  # Host->Device, Class, Interface
                        bRequest=0x09,       # SET_REPORT (standard HID)
                        wValue=(report_type << 8) | report_id,  # Report Type, Report ID
                        wIndex=interface,    # Interface number
                        data_or_wLength=data
                    )

                    print(f"   ✅ Success! Sent {len(data)} bytes")
                    time.sleep(0.2)

                    # Also try reading it back
                    try:
                        result = device.ctrl_transfer(
                            bmRequestType=0xa1,  # Device->Host, Class, Interface
                            bRequest=0x01,       # GET_REPORT
                            wValue=(report_type << 8) | report_id,
                            wIndex=interface,
                            data_or_wLength=64
                        )
                        print(f"   📖 Read back: {bytes(result).hex()}")
                    except:
                        print(f"   📖 Could not read back")

                except usb.core.USBError as e:
                    print(f"   ❌ Failed: {e}")

        except usb.core.USBError as e:
            print(f"❌ Interface {interface} error: {e}")

        finally:
            # Release interface
            try:
                usb.util.release_interface(device, interface)
                print(f"🔓 Released interface {interface}")
            except:
                pass

    print("\n🎉 All interface tests completed!")
    return True

def try_davinci_exact_patterns():
    """Try the exact control transfer patterns from DaVinci capture"""

    device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if device is None:
        print("❌ Device not found!")
        return

    print("\n🎯 Trying exact DaVinci patterns...")

    # Exact patterns from capture (without the report ID in data)
    davinci_patterns = [
        # From capture: 21 02 13 00 00 00 0a 00 + 10 bytes data
        {'setup': [0x21, 0x02, 0x13, 0x00, 0x00, 0x00], 'data': b'DeviceName'},
        # From capture: 21 02 14 00 00 00 07 00 + 7 bytes data
        {'setup': [0x21, 0x02, 0x14, 0x00, 0x00, 0x00], 'data': b'BuildId'},
        # Try simple illumination pattern
        {'setup': [0x21, 0x02, 0x15, 0x00, 0x00, 0x00], 'data': b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF'},
    ]

    for i, pattern in enumerate(davinci_patterns):
        print(f"\n📡 DaVinci Pattern {i+1}")
        setup = pattern['setup']
        data = pattern['data']
        print(f"   Setup: {bytes(setup).hex()}")
        print(f"   Data: {data.hex() if isinstance(data, bytes) else data}")

        try:
            result = device.ctrl_transfer(
                bmRequestType=setup[0],
                bRequest=setup[1],
                wValue=(setup[3] << 8) | setup[2],
                wIndex=(setup[5] << 8) | setup[4],
                data_or_wLength=data
            )
            print(f"   ✅ Success!")
        except usb.core.USBError as e:
            print(f"   ❌ Failed: {e}")

if __name__ == "__main__":
    print("🔬 Advanced HID Report Testing")
    print("=" * 50)
    test_interface_0_reports()
    try_davinci_exact_patterns()