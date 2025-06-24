#!/usr/bin/env python3
"""
DaVinci Micro Panel → Blender Integration
Universal controller for Blender 3D navigation using the DaVinci panel
"""

import sys
import os
import time
import threading
from typing import Optional

# Add the parent directory to sys.path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.core.device import DaVinciMicroPanel

class BlenderController:
    """
    DaVinci Micro Panel controller for Blender

    Maps panel controls to Blender navigation:
    - Trackballs → 3D viewport navigation
    - Rotary encoders → Various Blender parameters
    - Buttons → Tool shortcuts and mode switching
    """

    def __init__(self):
        self.panel: Optional[DaVinciMicroPanel] = None
        self.running = False

    def start(self):
        """Start the Blender controller"""
        print("🎨 Starting DaVinci → Blender Controller")
        print("=" * 50)

        try:
            # Connect to panel with automatic illumination
            print("🔌 Connecting to DaVinci Micro Panel...")
            self.panel = DaVinciMicroPanel()

            if not self.panel.connect():
                print("❌ Failed to connect to panel")
                return False

            print("✅ Panel connected and illuminated!")

            # Set up input event callbacks
            self._setup_callbacks()

            # Start input monitoring
            self.panel.start_input_monitoring()

            self.running = True
            print("\n🎛️ Controller active - panel buttons should be lit!")
            print("📋 Available controls:")
            print("   • Trackballs → 3D viewport navigation")
            print("   • Rotary encoders → Zoom, rotate, pan")
            print("   • Buttons → Tool shortcuts")
            print("\n🔍 Input monitoring active - move any control to see raw data")
            print("⚠️  Press Ctrl+C to stop controller\n")

            # Main control loop
            self._run_main_loop()

        except KeyboardInterrupt:
            print("\n🛑 Controller stopped by user")
        except Exception as e:
            print(f"\n❌ Controller error: {e}")
        finally:
            self.stop()

        return True

    def stop(self):
        """Stop the controller and cleanup"""
        print("\n🔄 Stopping Blender controller...")
        self.running = False

        if self.panel:
            print("💡 Turning off panel illumination...")
            self.panel.cleanup()
            print("✅ Panel disconnected and lights OFF")

        print("🏁 Controller stopped")

    def _setup_callbacks(self):
        """Set up input event callbacks for panel controls"""
        if not self.panel:
            return

        # Register callbacks to receive input events
        # For now, just log them until we implement proper Blender integration

        def on_button_event(button_id: int, pressed: bool):
            button_name = f"BUTTON_{button_id}"
            state = "PRESS" if pressed else "RELEASE"
            print(f"🔘 {button_name}: {state}")

        def on_encoder_event(encoder_id: int, delta: int):
            encoder_name = f"ENCODER_{encoder_id}"
            direction = "↻" if delta > 0 else "↺"
            print(f"🔄 {encoder_name}: {direction} ({delta:+d})")

        def on_trackball_event(trackball_id: int, x_delta: int, y_delta: int):
            trackball_name = f"TRACKBALL_{trackball_id}"
            print(f"🖱️ {trackball_name}: X{x_delta:+3d} Y{y_delta:+3d}")

        # Register the callbacks (these will be triggered by raw input processing)
        # TODO: Wire these up once input parser format is discovered

        print("📋 Callback system ready - will show events once input format is discovered")

    def _run_main_loop(self):
        """Main application loop"""
        try:
            while self.running:
                # Main loop - controller runs via callbacks
                time.sleep(0.1)

                # Could add periodic tasks here:
                # - Update panel displays with Blender info
                # - Adjust illumination based on active tool
                # - Monitor Blender connection status

        except KeyboardInterrupt:
            self.running = False

def main():
    """Main entry point"""
    print("🎯 DaVinci Micro Panel → Blender Universal Controller")
    print("🔗 https://github.com/user/micro-panel")
    print()

    # Check if running with proper permissions
    if os.geteuid() == 0:
        print("⚠️  Running as root - this might not be necessary")
        print("   Try running without sudo first")
        print()

    controller = BlenderController()

    try:
        success = controller.start()
        if not success:
            print("\n❌ Failed to start controller")
            sys.exit(1)

    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)

    print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()