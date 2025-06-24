#!/usr/bin/env python3
"""
Simple Input Capture - Handles timeouts properly
Errno 110 (Operation timed out) is NORMAL when no input is happening
"""

import sys
import os
import time
import usb.core
import usb.util

# Add our modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.device import DaVinciMicroPanel

def simple_capture(duration=30):
    """Simple input capture that handles timeouts correctly"""
    print("🎛️ Simple Input Capture")
    print("=" * 40)

    # Connect to panel
    panel = DaVinciMicroPanel()
    if not panel.connect():
        print("❌ Failed to connect")
        return

    print(f"✅ Panel connected! Capturing for {duration} seconds...")
    print("🎯 Move any control to see input events")
    print("💡 Panel should stay illuminated throughout")
    print()

    start_time = time.time()
    event_count = 0
    last_illumination_refresh = time.time()

    try:
        while time.time() - start_time < duration:
            try:
                # Refresh illumination every 20 seconds to prevent timeout
                if time.time() - last_illumination_refresh > 20:
                    panel.set_illumination(True, 150)  # Refresh bright
                    last_illumination_refresh = time.time()
                    print("💡 Illumination refreshed")

                # Read input (timeout is NORMAL when no input)
                data = panel.device.read(0x81, 64, timeout=100)

                if data:
                    data_bytes = bytes(data)

                    # Only show non-zero data (actual events)
                    if any(b != 0 for b in data_bytes):
                        event_count += 1
                        report_id = data_bytes[0]

                        # Simple event display
                        if report_id == 0x02:  # Buttons
                            button_data = data_bytes[1:6]
                            non_zero = [f"{i}:{b:02x}" for i, b in enumerate(button_data) if b != 0]
                            if non_zero:
                                print(f"🔘 Button: {' '.join(non_zero)}")

                        elif report_id == 0x06:  # Trackballs/Encoders
                            # Show first 8 data bytes
                            hex_data = ' '.join(f'{b:02x}' for b in data_bytes[1:9])
                            print(f"🎛️ Track/Enc: [{hex_data}]")

                        elif report_id == 0x05:  # Other input
                            # Show byte 10 which seemed active
                            if len(data_bytes) > 10 and data_bytes[10] != 0:
                                print(f"🎯 Other: byte10={data_bytes[10]:02x}")

                        # Show raw data occasionally for analysis
                        if event_count % 20 == 1:  # Every 20th event
                            full_hex = ' '.join(f'{b:02x}' for b in data_bytes[:16])
                            print(f"   📄 Raw: [{full_hex}...]")

            except usb.core.USBTimeoutError:
                # This is NORMAL when no input - not an error!
                continue

            except Exception as e:
                # Only real errors get logged
                print(f"⚠️ Real error: {e}")
                break

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")

    elapsed = time.time() - start_time
    print(f"\n📊 Captured {event_count} events in {elapsed:.1f} seconds")
    print(f"📈 Rate: {event_count/elapsed:.1f} events/second")

    # Cleanup
    panel.cleanup()
    print("✅ Done!")

def main():
    """Main entry point"""
    duration = 30
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except:
            pass

    print(f"⚡ Simple capture for {duration} seconds")
    print("💡 Errno 110 timeouts are NORMAL (means no input)")
    print()

    simple_capture(duration)

if __name__ == "__main__":
    main()