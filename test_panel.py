#!/usr/bin/env python3
"""
DaVinci Micro Panel Test Script

Simple standalone test to verify panel connectivity and demonstrate
all 67 controls working correctly.

Usage:
    conda activate micro-panel
    python test_panel.py
"""

import time
import sys
import os

# Add project path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from core.device import MicroPanel, PanelEvent, EventType
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the conda environment: conda activate micro-panel")
    sys.exit(1)


def main():
    """Main test function"""
    print("🎛️  DaVinci Micro Panel Test")
    print("="*60)
    print("Testing connectivity and all 67 controls:")
    print("  • 15 Rotary encoders (12 main + 3 trackball wheels)")
    print("  • 52 Buttons (12 rotary buttons + 40 function buttons)")
    print("  • 3 Trackballs for X/Y movement")
    print("")

    # Connect to panel
    panel = MicroPanel()
    if not panel.connect():
        print("❌ Failed to connect to DaVinci Panel")
        print("\nTroubleshooting:")
        print("1. Check USB connection")
        print("2. Verify udev rules: sudo cp udev/99-davinci-micro-panel.rules /etc/udev/rules.d/")
        print("3. Reload udev: sudo udevadm control --reload-rules && sudo udevadm trigger")
        print("4. Try with sudo: sudo python test_panel.py")
        return 1

    print("✅ DaVinci Panel connected successfully!")
    print("")

    # Display device info
    info = panel.get_device_info()
    print("📱 Device Information:")
    for key, value in info.items():
        print(f"  {key.capitalize()}: {value}")
    print("")

    # Control tracking
    control_activity = {
        'rotary': set(),
        'button': set(),
        'trackball': set()
    }

    def test_event_handler(event):
        """Handle and display events from panel"""
        timestamp = time.strftime("%H:%M:%S.%f", time.localtime(event.timestamp))[:-3]

        if event.type == EventType.ROTARY:
            control_activity['rotary'].add(event.id)
            direction = "↻" if event.delta > 0 else "↺"
            control_type = "Main" if event.id < 12 else "Trackball"
            print(f"[{timestamp}] 🔄 {control_type} Rotary #{event.id:2d}: {direction} Δ={event.delta:+3d}")

        elif event.type == EventType.BUTTON:
            control_activity['button'].add(event.id)
            state = "🔴 PRESS  " if event.pressed else "⚪ RELEASE"
            button_type = "Rotary" if event.id < 12 else "Function"
            print(f"[{timestamp}] 🔘 {button_type} Button #{event.id:2d}: {state}")

        elif event.type == EventType.TRACKBALL:
            control_activity['trackball'].add(event.trackball_id)
            if event.x_delta != 0 or event.y_delta != 0:
                print(f"[{timestamp}] 🏀 Trackball #{event.trackball_id}: X={event.x_delta:+3d} Y={event.y_delta:+3d}")

    # Start event monitoring
    panel.start_reading(test_event_handler)

    # LED test sequence
    print("🔄 Testing LED control...")
    led_test_sequence = [0, 1, 2, 3, 4, 5]
    for led_id in led_test_sequence:
        print(f"  Turning on LED {led_id}")
        panel.set_led(led_id, True)
        time.sleep(0.4)
        panel.set_led(led_id, False)

    print("")
    print("🎮 Panel ready for testing!")
    print("Try all controls to verify functionality:")
    print("  • Rotate all 15 encoders")
    print("  • Press all 52 buttons")
    print("  • Move all 3 trackballs")
    print("")
    print("Press Ctrl+C to show summary and exit...")
    print("")

    try:
        start_time = time.time()
        while True:
            time.sleep(0.1)

            # Show activity summary every 30 seconds
            if int(time.time() - start_time) % 30 == 0 and int(time.time() - start_time) > 0:
                print(f"\n📊 Activity Summary after {int(time.time() - start_time)}s:")
                print(f"  Rotaries tested: {len(control_activity['rotary'])}/15")
                print(f"  Buttons tested:  {len(control_activity['button'])}/52")
                print(f"  Trackballs tested: {len(control_activity['trackball'])}/3")
                print("")

    except KeyboardInterrupt:
        print("\n")
        print("🛑 Test completed!")
        print("="*40)

        # Final summary
        print("📊 Final Test Results:")
        print(f"  ✅ Rotaries tested: {len(control_activity['rotary'])}/15")
        if control_activity['rotary']:
            print(f"     Active rotaries: {sorted(control_activity['rotary'])}")

        print(f"  ✅ Buttons tested:  {len(control_activity['button'])}/52")
        if control_activity['button']:
            print(f"     Active buttons: {sorted(control_activity['button'])}")

        print(f"  ✅ Trackballs tested: {len(control_activity['trackball'])}/3")
        if control_activity['trackball']:
            print(f"     Active trackballs: {sorted(control_activity['trackball'])}")

        print("")
        if (len(control_activity['rotary']) == 15 and
            len(control_activity['button']) == 52 and
            len(control_activity['trackball']) == 3):
            print("🎉 ALL CONTROLS TESTED SUCCESSFULLY!")
        else:
            print("ℹ️  Not all controls were tested. Try moving unused controls.")

    finally:
        print("\n🔌 Disconnecting panel...")
        panel.disconnect()
        print("✅ Panel disconnected cleanly")

    return 0


if __name__ == "__main__":
    sys.exit(main())