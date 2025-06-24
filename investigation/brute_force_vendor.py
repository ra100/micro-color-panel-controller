#!/usr/bin/env python3
"""
Brute Force Vendor Command Discovery for DaVinci Micro Panel

Since we can claim interface 0 but don't know the vendor command codes,
this script systematically tries different combinations to find working commands.
"""

import usb.core
import usb.util
import time
import sys

VENDOR_ID = 0x1edb
PRODUCT_ID = 0xda0f

def brute_force_vendor_commands():
    """Systematically try vendor command combinations"""
    print("🔍 Brute Force Vendor Command Discovery")
    print("=" * 60)

    # Find and claim device
    device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if device is None:
        print("❌ Device not found")
        return

    try:
        device.set_configuration()
        usb.util.claim_interface(device, 0)
        print("✅ Successfully claimed interface 0")
        print()
    except usb.core.USBError as e:
        print(f"❌ Failed to claim interface: {e}")
        return

    working_commands = []

    try:
        print("🔍 Phase 1: Testing vendor OUT commands (illumination control)")
        print("   Testing bmRequestType=0x40 (vendor, device to host, standard)")

        # Test vendor OUT commands (0x40 = vendor, out, device)
        for bRequest in range(0x01, 0x21):  # Test request codes 1-32
            for wValue in [0x0000, 0x0001, 0x00FF, 0x0100, 0x0101]:  # Common values
                try:
                    # Simple single-byte command
                    result = device.ctrl_transfer(0x40, bRequest, wValue, 0x0000, [0x01], timeout=500)

                    print(f"✅ SUCCESS: req=0x{bRequest:02x}, val=0x{wValue:04x} -> {result} bytes")
                    working_commands.append((0x40, bRequest, wValue, 0x0000, [0x01]))

                    # Test if it does something visible
                    response = input(f"   Did you see any effect? (y/n): ").strip().lower()
                    if response == 'y':
                        print(f"🎉 VISUAL EFFECT! Command: 0x40, 0x{bRequest:02x}, 0x{wValue:04x}")

                        # Try turning it off
                        try:
                            device.ctrl_transfer(0x40, bRequest, 0x0000, 0x0000, [0x00], timeout=500)
                            print("   Sent OFF command")
                        except:
                            pass

                except usb.core.USBTimeoutError:
                    # Timeout means device got command but no response expected - might still work
                    pass
                except usb.core.USBError as e:
                    if "Pipe error" not in str(e):
                        print(f"   Unexpected error for req=0x{bRequest:02x}, val=0x{wValue:04x}: {e}")

        print(f"\n📊 Phase 1 complete. Found {len(working_commands)} working commands.")

        if working_commands:
            print("✅ Working vendor OUT commands:")
            for cmd in working_commands:
                print(f"   bmRequestType=0x{cmd[0]:02x}, bRequest=0x{cmd[1]:02x}, wValue=0x{cmd[2]:04x}")

        print("\n🔍 Phase 2: Testing vendor IN commands (reading state)")
        print("   Testing bmRequestType=0xC0 (vendor, host to device, standard)")

        working_reads = []

        # Test vendor IN commands (0xC0 = vendor, in, device)
        for bRequest in range(0x01, 0x21):  # Test request codes 1-32
            for wValue in [0x0000, 0x0001, 0x00FF]:
                try:
                    result = device.ctrl_transfer(0xC0, bRequest, wValue, 0x0000, 64, timeout=500)

                    if result and any(b != 0 for b in result):
                        hex_data = ' '.join(f'{b:02x}' for b in result[:16])
                        print(f"✅ READ SUCCESS: req=0x{bRequest:02x}, val=0x{wValue:04x}")
                        print(f"   Data: [{hex_data}{'...' if len(result) > 16 else ''}]")
                        working_reads.append((0xC0, bRequest, wValue, result))

                except usb.core.USBTimeoutError:
                    pass
                except usb.core.USBError:
                    pass

        print(f"\n📊 Phase 2 complete. Found {len(working_reads)} working read commands.")

        # Phase 3: Test the most promising commands with different data
        if working_commands:
            print("\n🔍 Phase 3: Testing successful commands with different data patterns")

            best_cmd = working_commands[0]  # Use first working command
            bmRequestType, bRequest, wValue, wIndex, _ = best_cmd

            test_patterns = [
                ([0x00], "Zero"),
                ([0x01], "One"),
                ([0xFF], "Max byte"),
                ([0x01, 0x01], "Double one"),
                ([0xFF, 0xFF, 0xFF], "Triple max"),
                ([0x01, 0x02, 0x03, 0x04], "Sequence"),
            ]

            for data, description in test_patterns:
                try:
                    print(f"   Testing {description}: {data}")
                    result = device.ctrl_transfer(bmRequestType, bRequest, wValue, wIndex, data, timeout=500)
                    print(f"   Result: {result} bytes")

                    time.sleep(1)
                    response = input(f"   Any visual effect? (y/n/s=skip): ").strip().lower()
                    if response == 'y':
                        print(f"🎉 EFFECT with {description}!")
                    elif response == 's':
                        break

                except Exception as e:
                    print(f"   Error: {e}")

    finally:
        try:
            usb.util.release_interface(device, 0)
            print("\n✅ Released interface 0")
        except:
            pass

    print(f"\n📈 Summary:")
    print(f"   Working OUT commands: {len(working_commands)}")
    print(f"   Working IN commands: {len(working_reads) if 'working_reads' in locals() else 0}")

def main():
    print("🎛️  DaVinci Micro Panel Vendor Command Discovery")
    print("Systematically testing vendor command codes")
    print("This may take a few minutes...")
    print()

    try:
        brute_force_vendor_commands()
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()