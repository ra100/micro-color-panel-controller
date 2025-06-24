#!/usr/bin/env python3
"""
Robust Control Mapping Tool with USB error handling and auto-reconnection
Handles disconnections, timeouts, and device sleep issues
"""

import sys
import os
import time
import usb.core
import usb.util
from collections import defaultdict

# Add our modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.device import DaVinciMicroPanel

class RobustControlMapper:
    """Robust control mapper with USB error handling and reconnection"""

    def __init__(self):
        self.panel = None
        self.control_map = {
            'buttons': {},      # bit_position -> control_name
            'encoders': {},     # byte_position -> control_name
            'trackballs': {}    # axis_position -> control_name
        }
        self.last_illumination_refresh = 0
        self.connection_attempts = 0
        self.max_connection_attempts = 3

    def ensure_connection(self):
        """Ensure panel is connected and responsive"""
        if self.panel and self.panel.is_connected:
            # Test if connection is still working
            try:
                # Try a simple illumination refresh as a connectivity test
                self.panel.set_illumination(True, 100)
                self.last_illumination_refresh = time.time()
                return True
            except Exception as e:
                print(f"⚠️ Connection test failed: {e}")
                self.panel.cleanup()
                self.panel = None

        # Need to (re)connect
        return self.reconnect()

    def reconnect(self):
        """Attempt to reconnect to the panel"""
        self.connection_attempts += 1

        if self.connection_attempts > self.max_connection_attempts:
            print(f"❌ Max connection attempts ({self.max_connection_attempts}) exceeded")
            return False

        print(f"🔌 Connection attempt {self.connection_attempts}...")

        # Clean up any existing connection
        if self.panel:
            try:
                self.panel.cleanup()
            except:
                pass
            self.panel = None

        # Wait a moment for USB to stabilize
        time.sleep(2)

        # Create new connection
        self.panel = DaVinciMicroPanel()
        if self.panel.connect():
            print("✅ Reconnected successfully!")
            self.connection_attempts = 0  # Reset counter on success
            self.last_illumination_refresh = time.time()
            return True
        else:
            print(f"❌ Reconnection attempt {self.connection_attempts} failed")
            return False

    def refresh_illumination_if_needed(self):
        """Refresh illumination every 15 seconds to prevent sleep"""
        current_time = time.time()
        if current_time - self.last_illumination_refresh > 15:
            try:
                if self.panel and self.panel.is_connected:
                    self.panel.set_illumination(True, 100)  # Bright setting
                    self.last_illumination_refresh = current_time
                    print("💡 Illumination refreshed (preventing sleep)")
            except Exception as e:
                print(f"⚠️ Illumination refresh failed: {e}")
                # Don't fail completely, just note the issue

    def test_control_robust(self, instruction, duration=8):
        """Test a control with robust error handling"""
        print(f"\n🎯 {instruction}")
        print("=" * 60)

        # Ensure connection before starting
        if not self.ensure_connection():
            print("❌ Cannot establish connection for this test")
            return []

        input("🟢 Press ENTER when ready, then follow the instruction...")
        print(f"⏱️ Recording for {duration} seconds - GO!")

        events = []
        start_time = time.time()
        consecutive_errors = 0
        max_consecutive_errors = 10

        try:
            while time.time() - start_time < duration:
                try:
                    # Refresh illumination periodically
                    self.refresh_illumination_if_needed()

                    # Ensure we still have connection
                    if not self.panel or not self.panel.is_connected:
                        print("⚠️ Lost connection during test, attempting to reconnect...")
                        if not self.ensure_connection():
                            print("❌ Cannot reestablish connection")
                            break

                    # Try to read data
                    data = self.panel.device.read(0x81, 64, timeout=50)

                    if data:
                        data_bytes = bytes(data)

                        # Store all non-zero events
                        if any(b != 0 for b in data_bytes):
                            timestamp = time.time() - start_time
                            events.append((timestamp, data_bytes))

                            # Show real-time feedback
                            report_id = data_bytes[0]
                            if report_id == 0x02:  # Button
                                for byte_idx in range(1, 8):
                                    if byte_idx < len(data_bytes) and data_bytes[byte_idx] != 0:
                                        byte_val = data_bytes[byte_idx]
                                        for bit in range(8):
                                            if byte_val & (1 << bit):
                                                print(f"  🔘 Button: Byte{byte_idx} Bit{bit} (0x{byte_val:02x})")

                            elif report_id == 0x06:  # Trackball/Encoder
                                non_zero_positions = []
                                for i in range(1, min(16, len(data_bytes)), 2):
                                    if i+1 < len(data_bytes):
                                        value = int.from_bytes(data_bytes[i:i+2], 'little', signed=True)
                                        if value != 0:
                                            non_zero_positions.append(f"Pos{i}-{i+1}:{value:+d}")
                                if non_zero_positions:
                                    print(f"  🎛️ Track/Enc: {' '.join(non_zero_positions)}")

                    consecutive_errors = 0  # Reset error counter on successful read

                except usb.core.USBTimeoutError:
                    # Timeouts are normal when no input
                    consecutive_errors = 0
                    continue

                except usb.core.USBError as e:
                    consecutive_errors += 1
                    print(f"⚠️ USB Error ({consecutive_errors}/{max_consecutive_errors}): {e}")

                    if consecutive_errors >= max_consecutive_errors:
                        print("❌ Too many consecutive USB errors, attempting reconnection...")
                        if not self.ensure_connection():
                            print("❌ Cannot reestablish connection")
                            break
                        consecutive_errors = 0

                except Exception as e:
                    print(f"⚠️ Unexpected error: {e}")
                    time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n⏸️ Test stopped early")

        print(f"✅ Captured {len(events)} events")
        return events

    def analyze_events(self, events, control_name):
        """Analyze captured events for patterns"""
        if not events:
            print("❌ No events captured - try again or check connection")
            return

        print(f"\n🔍 Analysis for {control_name}:")

        # Group by report type
        by_report = defaultdict(list)
        for timestamp, data in events:
            by_report[data[0]].append((timestamp, data))

        for report_id, report_events in by_report.items():
            print(f"  📋 Report 0x{report_id:02x}: {len(report_events)} events")

            if report_id == 0x02:  # Button analysis
                self._analyze_button_events(report_events, control_name)
            elif report_id == 0x06:  # Trackball/Encoder analysis
                self._analyze_movement_events(report_events, control_name)

    def _analyze_button_events(self, events, control_name):
        """Analyze button events to find bit positions"""
        bit_patterns = set()

        for timestamp, data in events:
            for byte_idx in range(1, min(8, len(data))):
                byte_val = data[byte_idx]
                if byte_val != 0:
                    for bit in range(8):
                        if byte_val & (1 << bit):
                            bit_id = byte_idx * 8 + bit
                            bit_patterns.add((byte_idx, bit, bit_id))

        if bit_patterns:
            print(f"    🎯 Button bits detected:")
            for byte_idx, bit, bit_id in sorted(bit_patterns):
                print(f"      Byte{byte_idx} Bit{bit} → Button#{bit_id}")
                self.control_map['buttons'][bit_id] = control_name
        else:
            print(f"    ❌ No button patterns found")

    def _analyze_movement_events(self, events, control_name):
        """Analyze trackball/encoder movement events"""
        position_ranges = defaultdict(lambda: {'min': 999999, 'max': -999999, 'count': 0})

        for timestamp, data in events:
            for i in range(1, min(16, len(data)), 2):
                if i+1 < len(data):
                    value = int.from_bytes(data[i:i+2], 'little', signed=True)
                    if value != 0:
                        position_ranges[i]['min'] = min(position_ranges[i]['min'], value)
                        position_ranges[i]['max'] = max(position_ranges[i]['max'], value)
                        position_ranges[i]['count'] += 1

        if position_ranges:
            print(f"    🎯 Movement data detected:")
            for pos, stats in sorted(position_ranges.items()):
                if stats['count'] > 0:
                    print(f"      Bytes{pos}-{pos+1}: {stats['min']:+d} to {stats['max']:+d} ({stats['count']} events)")
                    axis_name = f"{control_name}_bytes_{pos}_{pos+1}"
                    self.control_map['trackballs'][pos] = axis_name
        else:
            print(f"    ❌ No movement data found")

    def check_panel_status(self):
        """Check if panel is still responsive"""
        try:
            if not self.panel or not self.panel.is_connected:
                return False

            # Quick read test with very short timeout
            self.panel.device.read(0x81, 64, timeout=10)
            return True
        except usb.core.USBTimeoutError:
            # Timeout is normal, means panel is responsive
            return True
        except:
            # Any other error means panel is not responsive
            return False

    def run_robust_mapping(self):
        """Run mapping with robust error handling"""
        print("🎯 ROBUST CONTROL MAPPING")
        print("=" * 60)
        print("✨ Features: Auto-reconnection, illumination refresh, error recovery")
        print("🔋 Prevents panel sleep during long sessions")
        print()

        if not self.ensure_connection():
            print("❌ Cannot establish initial connection")
            return

        try:
            # Test a few key controls with robust handling
            test_controls = [
                ("Press and release the SHOT COLOR button (left side, top)", "SHOT_COLOR"),
                ("Press and release the COPY button (left side)", "COPY"),
                ("Press and release the PASTE button (left side)", "PASTE"),
                ("Turn Y LIFT encoder (top-left) both directions", "Y_LIFT_ENCODER"),
                ("Move LEFT trackball LEFT and RIGHT", "LEFT_TRACKBALL_X"),
                ("Move LEFT trackball UP and DOWN", "LEFT_TRACKBALL_Y"),
                ("Press and release Y LIFT encoder button", "Y_LIFT_BUTTON"),
                ("Press and release the PREV button (right side)", "PREV"),
                ("Press and release the NEXT button (right side)", "NEXT"),
                ("Turn CENTER encoder both directions", "CENTER_ENCODER"),
            ]

            for i, (instruction, control_name) in enumerate(test_controls, 1):
                print(f"\n🎮 Test {i}/{len(test_controls)}: {control_name}")

                # Check panel status before each test
                if not self.check_panel_status():
                    print("⚠️ Panel not responsive, attempting reconnection...")
                    if not self.ensure_connection():
                        retry = input("❓ Reconnection failed. Retry? (y/N): ").lower() == 'y'
                        if not retry:
                            break
                        continue

                events = self.test_control_robust(instruction, duration=6)
                self.analyze_events(events, control_name)

                # Brief pause between tests
                print("⏸️ 3 second pause...")
                time.sleep(3)

            # Show results
            self.show_final_mapping()

        except KeyboardInterrupt:
            print("\n🛑 Mapping interrupted by user")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
        finally:
            if self.panel:
                try:
                    self.panel.cleanup()
                except:
                    pass

    def show_final_mapping(self):
        """Show the complete control mapping discovered"""
        print("\n\n🎉 ROBUST MAPPING RESULTS")
        print("=" * 60)

        print(f"🔘 Button Mapping ({len(self.control_map['buttons'])} buttons):")
        for bit_id, name in sorted(self.control_map['buttons'].items()):
            byte_pos = bit_id // 8
            bit_pos = bit_id % 8
            print(f"   Button #{bit_id:2d} (Byte{byte_pos} Bit{bit_pos}): {name}")

        print(f"\n🎛️ Movement Controls ({len(self.control_map['trackballs'])} axes):")
        for pos, name in sorted(self.control_map['trackballs'].items()):
            print(f"   Bytes {pos}-{pos+1}: {name}")

        # Save mapping
        self.save_mapping()

    def save_mapping(self):
        """Save the mapping to a file"""
        filename = "robust_control_mapping.py"
        print(f"\n💾 Saving mapping to {filename}...")

        with open(filename, 'w') as f:
            f.write("# DaVinci Micro Panel Control Mapping\n")
            f.write("# Generated by robust mapping tool\n")
            f.write("# Includes error handling and reconnection logic\n\n")

            f.write("BUTTON_MAP = {\n")
            for bit_id, name in sorted(self.control_map['buttons'].items()):
                byte_pos = bit_id // 8
                bit_pos = bit_id % 8
                f.write(f"    {bit_id}: '{name}',  # Byte{byte_pos} Bit{bit_pos}\n")
            f.write("}\n\n")

            f.write("MOVEMENT_MAP = {\n")
            for pos, name in sorted(self.control_map['trackballs'].items()):
                f.write(f"    {pos}: '{name}',  # Bytes {pos}-{pos+1}\n")
            f.write("}\n")

        print(f"✅ Robust mapping saved to {filename}")

def main():
    """Main entry point"""
    print("🛡️ DaVinci Panel ROBUST Control Mapping")
    print("Features:")
    print("  ✨ Automatic reconnection on USB errors")
    print("  💡 Prevents panel sleep with illumination refresh")
    print("  🔄 Recovers from timeouts and disconnections")
    print("  📊 Better error reporting and status checking")
    print()
    print("⏱️ Estimated time: 10-15 minutes (shorter test set)")
    print()

    if input("Ready to start robust mapping? (y/N): ").lower() != 'y':
        print("👋 Maybe next time!")
        return

    mapper = RobustControlMapper()
    mapper.run_robust_mapping()

if __name__ == "__main__":
    main()