#!/usr/bin/env python3
"""
Simple Input Monitoring Test
Tests basic input capture from the DaVinci panel
"""

import sys
import os
import time

# Add our modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.device import DaVinciMicroPanel

def main():
    """Test input monitoring"""
    print("🎛️ DaVinci Panel Input Monitoring Test")
    print("=" * 50)

    try:
        with DaVinciMicroPanel() as panel:
            print("✅ Panel connected and illuminated!")
            print("\n🎯 Starting input monitoring...")
            print("⏰ Try moving any controls (trackballs, encoders, buttons)")
            print("   Raw input data will be displayed")
            print("🛑 Press Ctrl+C to stop\n")

            # Start input monitoring
            panel.start_input_monitoring()

            # Keep running until interrupted
            try:
                while True:
                    time.sleep(0.1)

            except KeyboardInterrupt:
                print("\n🛑 Stopping input monitoring...")

    except Exception as e:
        print(f"❌ Error: {e}")

    print("✅ Test completed")

if __name__ == "__main__":
    main()