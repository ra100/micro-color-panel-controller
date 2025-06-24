#!/usr/bin/env python3
"""
Comprehensive Control Mapping Tool
Maps all 67+ controls from panel_controls_list.txt systematically
Includes robust USB error handling and reconnection logic
"""

import sys
import os
import time
import usb.core
import usb.util
from collections import defaultdict
import json

# Add our modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from core.device import DaVinciMicroPanel

class ComprehensiveMapper:
    """Comprehensive control mapper based on panel_controls_list.txt"""

    def __init__(self):
        self.panel = None
        self.control_map = {
            'encoder_rotations': {},    # encoder_id -> byte_positions
            'encoder_buttons': {},      # encoder_id -> button_bit
            'trackball_axes': {},       # axis_id -> byte_positions
            'function_buttons': {},     # button_name -> button_bit
            'special_reports': {}       # button_name -> special_report_data
        }
        self.last_illumination_refresh = 0
        self.connection_attempts = 0
        self.max_connection_attempts = 3

    def ensure_connection(self):
        """Ensure panel is connected and responsive"""
        if self.panel and self.panel.is_connected:
            try:
                self.panel.set_illumination(True, 100)
                self.last_illumination_refresh = time.time()
                return True
            except Exception as e:
                print(f"⚠️ Connection test failed: {e}")
                self.panel.cleanup()
                self.panel = None

        return self.reconnect()

    def reconnect(self):
        """Attempt to reconnect to the panel"""
        self.connection_attempts += 1

        if self.connection_attempts > self.max_connection_attempts:
            print(f"❌ Max connection attempts ({self.max_connection_attempts}) exceeded")
            return False

        print(f"🔌 Connection attempt {self.connection_attempts}...")

        if self.panel:
            try:
                self.panel.cleanup()
            except:
                pass
            self.panel = None

        time.sleep(2)

        self.panel = DaVinciMicroPanel()
        if self.panel.connect():
            print("✅ Reconnected successfully!")
            self.connection_attempts = 0
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
                    self.panel.set_illumination(True, 100)
                    self.last_illumination_refresh = current_time
                    print("💡 Illumination refreshed")
            except Exception as e:
                print(f"⚠️ Illumination refresh failed: {e}")

    def test_control_robust(self, instruction, control_id, duration=6):
        """Test a control with robust error handling"""
        print(f"\n🎯 {instruction}")
        print("=" * 70)

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
                    self.refresh_illumination_if_needed()

                    if not self.panel or not self.panel.is_connected:
                        print("⚠️ Lost connection during test, attempting to reconnect...")
                        if not self.ensure_connection():
                            print("❌ Cannot reestablish connection")
                            break

                    data = self.panel.device.read(0x81, 64, timeout=50)

                    if data:
                        data_bytes = bytes(data)

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
                                for i in range(1, min(20, len(data_bytes)), 2):
                                    if i+1 < len(data_bytes):
                                        value = int.from_bytes(data_bytes[i:i+2], 'little', signed=True)
                                        if value != 0:
                                            non_zero_positions.append(f"Pos{i}-{i+1}:{value:+d}")
                                if non_zero_positions:
                                    print(f"  🎛️ Movement: {' '.join(non_zero_positions)}")

                            elif report_id == 0x05:  # Special function
                                non_zero = [(i, b) for i, b in enumerate(data_bytes[1:10], 1) if b != 0]
                                if non_zero:
                                    print(f"  🔸 Special: {non_zero}")

                    consecutive_errors = 0

                except usb.core.USBTimeoutError:
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

    def analyze_events(self, events, control_name, control_type):
        """Analyze captured events and store mapping"""
        if not events:
            print("❌ No events captured")
            return

        print(f"\n🔍 Analysis for {control_name} ({control_type}):")

        # Group by report type
        by_report = defaultdict(list)
        for timestamp, data in events:
            by_report[data[0]].append((timestamp, data))

        for report_id, report_events in by_report.items():
            print(f"  📋 Report 0x{report_id:02x}: {len(report_events)} events")

            if report_id == 0x02:  # Button analysis
                self._analyze_button_events(report_events, control_name, control_type)
            elif report_id == 0x06:  # Movement analysis
                self._analyze_movement_events(report_events, control_name, control_type)
            elif report_id == 0x05:  # Special function analysis
                self._analyze_special_events(report_events, control_name)

    def _analyze_button_events(self, events, control_name, control_type):
        """Analyze button events"""
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
            print(f"    🎯 Button mapping detected:")
            for byte_idx, bit, bit_id in sorted(bit_patterns):
                print(f"      {control_name}: Byte{byte_idx} Bit{bit} = Button#{bit_id}")

                if control_type == "encoder_button":
                    self.control_map['encoder_buttons'][control_name] = bit_id
                else:
                    self.control_map['function_buttons'][control_name] = bit_id

    def _analyze_movement_events(self, events, control_name, control_type):
        """Analyze movement events"""
        position_ranges = defaultdict(lambda: {'min': 999999, 'max': -999999, 'count': 0})

        for timestamp, data in events:
            for i in range(1, min(20, len(data)), 2):
                if i+1 < len(data):
                    value = int.from_bytes(data[i:i+2], 'little', signed=True)
                    if value != 0:
                        position_ranges[i]['min'] = min(position_ranges[i]['min'], value)
                        position_ranges[i]['max'] = max(position_ranges[i]['max'], value)
                        position_ranges[i]['count'] += 1

        if position_ranges:
            print(f"    🎯 Movement mapping detected:")
            for pos, stats in sorted(position_ranges.items()):
                if stats['count'] > 0:
                    print(f"      {control_name}: Bytes{pos}-{pos+1} = Range {stats['min']:+d} to {stats['max']:+d}")

                    if control_type == "encoder_rotation":
                        self.control_map['encoder_rotations'][control_name] = pos
                    elif control_type == "trackball_axis":
                        self.control_map['trackball_axes'][control_name] = pos

    def _analyze_special_events(self, events, control_name):
        """Analyze special function events"""
        for timestamp, data in events[:1]:  # Just analyze first event
            non_zero = [(i, b) for i, b in enumerate(data[1:10], 1) if b != 0]
            if non_zero:
                print(f"    🔸 Special function mapping: {control_name} = {non_zero}")
                self.control_map['special_reports'][control_name] = non_zero

    def run_comprehensive_mapping(self):
        """Run complete systematic mapping based on panel_controls_list.txt"""
        print("🎯 COMPREHENSIVE DAVINCI PANEL MAPPING")
        print("=" * 70)
        print("✨ Mapping all 67+ controls systematically")
        print("🔋 Robust USB handling with auto-reconnection")
        print()

        if not self.ensure_connection():
            print("❌ Cannot establish initial connection")
            return

        try:
            # PHASE 1: ENCODER BUTTONS (12 total)
            print("\n" + "="*50)
            print("🔄 PHASE 1: ENCODER BUTTONS (12 total)")
            print("="*50)

            encoder_tests = [
                ("Push and release Y_LIFT encoder (top-left rotary)", "Y_LIFT_BUTTON"),
                ("Push and release Y_GAMMA encoder (2nd from left)", "Y_GAMMA_BUTTON"),
                ("Push and release Y_GAIN encoder (3rd from left)", "Y_GAIN_BUTTON"),
                ("Push and release CONTRAST encoder (4th from left)", "CONTRAST_BUTTON"),
                ("Push and release PIVOT encoder (5th from left)", "PIVOT_BUTTON"),
                ("Push and release MID_DETAIL encoder (6th from left)", "MID_DETAIL_BUTTON"),
                ("Push and release COLOR_BOOST encoder (7th from left)", "COLOR_BOOST_BUTTON"),
                ("Push and release SHADOWS encoder (8th from left)", "SHADOWS_BUTTON"),
                ("Push and release HIGHLIGHTS encoder (9th from left)", "HIGHLIGHTS_BUTTON"),
                ("Push and release SATURATION encoder (10th from left)", "SATURATION_BUTTON"),
                ("Push and release HUE encoder (11th from left)", "HUE_BUTTON"),
                ("Push and release LUM_MIX encoder (rightmost)", "LUM_MIX_BUTTON"),
            ]

            for i, (instruction, control_id) in enumerate(encoder_tests, 1):
                print(f"\n🔘 Encoder Button {i}/12: {control_id}")
                events = self.test_control_robust(instruction, control_id, duration=5)
                self.analyze_events(events, control_id, "encoder_button")
                time.sleep(2)

            # PHASE 2: ENCODER ROTATIONS (12 total)
            print("\n" + "="*50)
            print("🔄 PHASE 2: ENCODER ROTATIONS (12 total)")
            print("="*50)

            encoder_rotation_tests = [
                ("Turn Y_LIFT encoder (top-left) clockwise and counter-clockwise", "Y_LIFT_ROTATION"),
                ("Turn Y_GAMMA encoder clockwise and counter-clockwise", "Y_GAMMA_ROTATION"),
                ("Turn Y_GAIN encoder clockwise and counter-clockwise", "Y_GAIN_ROTATION"),
                ("Turn CONTRAST encoder clockwise and counter-clockwise", "CONTRAST_ROTATION"),
                ("Turn PIVOT encoder clockwise and counter-clockwise", "PIVOT_ROTATION"),
                ("Turn MID_DETAIL encoder clockwise and counter-clockwise", "MID_DETAIL_ROTATION"),
                ("Turn COLOR_BOOST encoder clockwise and counter-clockwise", "COLOR_BOOST_ROTATION"),
                ("Turn SHADOWS encoder clockwise and counter-clockwise", "SHADOWS_ROTATION"),
                ("Turn HIGHLIGHTS encoder clockwise and counter-clockwise", "HIGHLIGHTS_ROTATION"),
                ("Turn SATURATION encoder clockwise and counter-clockwise", "SATURATION_ROTATION"),
                ("Turn HUE encoder clockwise and counter-clockwise", "HUE_ROTATION"),
                ("Turn LUM_MIX encoder clockwise and counter-clockwise", "LUM_MIX_ROTATION"),
            ]

            for i, (instruction, control_id) in enumerate(encoder_rotation_tests, 1):
                print(f"\n🔄 Encoder Rotation {i}/12: {control_id}")
                events = self.test_control_robust(instruction, control_id, duration=6)
                self.analyze_events(events, control_id, "encoder_rotation")
                time.sleep(2)

            # PHASE 3: TRACKBALL AXES (9 total)
            print("\n" + "="*50)
            print("🖱️ PHASE 3: TRACKBALL AXES (9 total)")
            print("="*50)

            trackball_tests = [
                ("Move LEFT trackball LEFT and RIGHT only (shadows X-axis)", "LEFT_TRACKBALL_X"),
                ("Move LEFT trackball UP and DOWN only (shadows Y-axis)", "LEFT_TRACKBALL_Y"),
                ("Turn LEFT trackball wheel up and down (shadows wheel)", "LEFT_TRACKBALL_WHEEL"),
                ("Move CENTER trackball LEFT and RIGHT only (midtones X-axis)", "CENTER_TRACKBALL_X"),
                ("Move CENTER trackball UP and DOWN only (midtones Y-axis)", "CENTER_TRACKBALL_Y"),
                ("Turn CENTER trackball wheel up and down (midtones wheel)", "CENTER_TRACKBALL_WHEEL"),
                ("Move RIGHT trackball LEFT and RIGHT only (highlights X-axis)", "RIGHT_TRACKBALL_X"),
                ("Move RIGHT trackball UP and DOWN only (highlights Y-axis)", "RIGHT_TRACKBALL_Y"),
                ("Turn RIGHT trackball wheel up and down (highlights wheel)", "RIGHT_TRACKBALL_WHEEL"),
            ]

            for i, (instruction, control_id) in enumerate(trackball_tests, 1):
                print(f"\n🖱️ Trackball Axis {i}/9: {control_id}")
                events = self.test_control_robust(instruction, control_id, duration=6)
                self.analyze_events(events, control_id, "trackball_axis")
                time.sleep(2)

            # PHASE 4: LEFT SIDE FUNCTION BUTTONS
            print("\n" + "="*50)
            print("🔘 PHASE 4: LEFT SIDE FUNCTION BUTTONS")
            print("="*50)

            left_button_tests = [
                ("Press and release AUTO_COLOR button", "AUTO_COLOR"),
                ("Press and release OFFSET button", "OFFSET"),
                ("Press and release COPY button", "COPY"),
                ("Press and release PASTE button", "PASTE"),
                ("Press and release UNDO button", "UNDO"),
                ("Press and release REDO button", "REDO"),
                ("Press and release DELETE button", "DELETE"),
                ("Press and release RESET button", "RESET"),
                ("Press and release BYPASS button", "BYPASS"),
                ("Press and release DISABLE button", "DISABLE"),
            ]

            for i, (instruction, control_id) in enumerate(left_button_tests, 1):
                print(f"\n🔘 Left Button {i}/{len(left_button_tests)}: {control_id}")
                events = self.test_control_robust(instruction, control_id, duration=4)
                self.analyze_events(events, control_id, "function_button")
                time.sleep(2)

            # Continue with more phases...
            self.continue_button_mapping()

        except KeyboardInterrupt:
            print("\n🛑 Mapping interrupted by user")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
        finally:
            self.save_comprehensive_mapping()
            if self.panel:
                try:
                    self.panel.cleanup()
                except:
                    pass

    def continue_button_mapping(self):
        """Continue with remaining button phases"""

        # PHASE 5: BOTTOM LEFT BUTTONS
        print("\n" + "="*50)
        print("🔘 PHASE 5: BOTTOM LEFT BUTTONS")
        print("="*50)

        bottom_left_tests = [
            ("Press and release USER button", "USER"),
            ("Press and release LOOP button", "LOOP"),
            ("Press and release SPECIAL_LEFT button", "SPECIAL_LEFT"),
            ("Press and release SPECIAL_RIGHT button", "SPECIAL_RIGHT"),
        ]

        for i, (instruction, control_id) in enumerate(bottom_left_tests, 1):
            print(f"\n🔘 Bottom Left {i}/{len(bottom_left_tests)}: {control_id}")
            events = self.test_control_robust(instruction, control_id, duration=4)
            self.analyze_events(events, control_id, "function_button")
            time.sleep(2)

        # PHASE 6: TOP BUTTONS
        print("\n" + "="*50)
        print("🔘 PHASE 6: TOP AREA BUTTONS")
        print("="*50)

        top_button_tests = [
            ("Press and release PLAY_STILL button", "PLAY_STILL"),
            ("Press and release WIPE_STILL button", "WIPE_STILL"),
            ("Press and release GRAB_STILL button", "GRAB_STILL"),
            ("Press and release H_LITE button", "H_LITE"),
            ("Press and release VIEWER button", "VIEWER"),
            ("Press and release CURSOR button", "CURSOR"),
            ("Press and release SELECT button", "SELECT"),
            ("Press and release RESET_LIFT button", "RESET_LIFT"),
            ("Press and release RESET_GAMMA button", "RESET_GAMMA"),
            ("Press and release RESET_GAIN button", "RESET_GAIN"),
            ("Press and release ADD_NODE button", "ADD_NODE"),
            ("Press and release ADD_WINDOW button", "ADD_WINDOW"),
            ("Press and release ADD_KEYFRAME button", "ADD_KEYFRAME"),
        ]

        for i, (instruction, control_id) in enumerate(top_button_tests, 1):
            print(f"\n🔘 Top Button {i}/{len(top_button_tests)}: {control_id}")
            events = self.test_control_robust(instruction, control_id, duration=4)
            self.analyze_events(events, control_id, "function_button")
            time.sleep(2)

        # PHASE 7: RIGHT SIDE NAVIGATION BUTTONS
        print("\n" + "="*50)
        print("🔘 PHASE 7: RIGHT SIDE NAVIGATION BUTTONS")
        print("="*50)

        right_button_tests = [
            ("Press and release PREV_STILL button", "PREV_STILL"),
            ("Press and release NEXT_STILL button", "NEXT_STILL"),
            ("Press and release PREV_KEYFRAME button", "PREV_KEYFRAME"),
            ("Press and release NEXT_KEYFRAME button", "NEXT_KEYFRAME"),
            ("Press and release PREV_NODE button", "PREV_NODE"),
            ("Press and release NEXT_NODE button", "NEXT_NODE"),
            ("Press and release PREV_FRAME button", "PREV_FRAME"),
            ("Press and release NEXT_FRAME button", "NEXT_FRAME"),
            ("Press and release PREV_CLIP button", "PREV_CLIP"),
            ("Press and release NEXT_CLIP button", "NEXT_CLIP"),
            ("Press and release BACKWARD_PLAY button", "BACKWARD_PLAY"),
            ("Press and release FORWARD_PLAY button", "FORWARD_PLAY"),
            ("Press and release STOP button", "STOP"),
        ]

        for i, (instruction, control_id) in enumerate(right_button_tests, 1):
            print(f"\n🔘 Right Button {i}/{len(right_button_tests)}: {control_id}")
            events = self.test_control_robust(instruction, control_id, duration=4)
            self.analyze_events(events, control_id, "function_button")
            time.sleep(2)

    def save_comprehensive_mapping(self):
        """Save the complete mapping to files"""
        print(f"\n💾 SAVING COMPREHENSIVE MAPPING...")

        # Save as JSON for programming
        json_filename = "davinci_panel_mapping.json"
        with open(json_filename, 'w') as f:
            json.dump(self.control_map, f, indent=2)
        print(f"✅ JSON mapping saved to {json_filename}")

        # Save as Python module
        py_filename = "davinci_panel_controls.py"
        with open(py_filename, 'w') as f:
            f.write("# DaVinci Micro Panel Complete Control Mapping\n")
            f.write("# Generated by comprehensive mapping tool\n\n")

            f.write("# Encoder Buttons (push encoders)\n")
            f.write("ENCODER_BUTTONS = {\n")
            for control_name, bit_id in sorted(self.control_map['encoder_buttons'].items()):
                byte_pos = bit_id // 8
                bit_pos = bit_id % 8
                f.write(f"    '{control_name}': {bit_id},  # Byte{byte_pos} Bit{bit_pos}\n")
            f.write("}\n\n")

            f.write("# Encoder Rotations\n")
            f.write("ENCODER_ROTATIONS = {\n")
            for control_name, pos in sorted(self.control_map['encoder_rotations'].items()):
                f.write(f"    '{control_name}': {pos},  # Bytes {pos}-{pos+1}\n")
            f.write("}\n\n")

            f.write("# Trackball Axes\n")
            f.write("TRACKBALL_AXES = {\n")
            for control_name, pos in sorted(self.control_map['trackball_axes'].items()):
                f.write(f"    '{control_name}': {pos},  # Bytes {pos}-{pos+1}\n")
            f.write("}\n\n")

            f.write("# Function Buttons\n")
            f.write("FUNCTION_BUTTONS = {\n")
            for control_name, bit_id in sorted(self.control_map['function_buttons'].items()):
                byte_pos = bit_id // 8
                bit_pos = bit_id % 8
                f.write(f"    '{control_name}': {bit_id},  # Byte{byte_pos} Bit{bit_pos}\n")
            f.write("}\n\n")

            f.write("# Special Function Reports\n")
            f.write("SPECIAL_REPORTS = {\n")
            for control_name, data in sorted(self.control_map['special_reports'].items()):
                f.write(f"    '{control_name}': {data},\n")
            f.write("}\n")

        print(f"✅ Python mapping saved to {py_filename}")

        # Print summary
        print(f"\n📊 MAPPING SUMMARY:")
        print(f"   🔄 Encoder Buttons: {len(self.control_map['encoder_buttons'])}")
        print(f"   🔄 Encoder Rotations: {len(self.control_map['encoder_rotations'])}")
        print(f"   🖱️ Trackball Axes: {len(self.control_map['trackball_axes'])}")
        print(f"   🔘 Function Buttons: {len(self.control_map['function_buttons'])}")
        print(f"   🔸 Special Functions: {len(self.control_map['special_reports'])}")
        total = sum(len(v) for v in self.control_map.values())
        print(f"   🎯 TOTAL MAPPED: {total} controls")

def main():
    """Main entry point"""
    print("🎛️ DaVinci Panel COMPREHENSIVE Control Mapping")
    print("Based on panel_controls_list.txt")
    print()
    print("Features:")
    print("  ✨ Maps all 67+ controls systematically")
    print("  🔄 12 Encoder rotations + 12 push buttons")
    print("  🖱️ 9 Trackball axes (3 trackballs × 3 axes)")
    print("  🔘 52+ Function buttons")
    print("  🛡️ Robust USB error handling")
    print("  💡 Automatic illumination refresh")
    print()
    print("⏱️ Estimated time: 45-60 minutes")
    print()

    if input("Ready to start comprehensive mapping? (y/N): ").lower() != 'y':
        print("👋 Maybe next time!")
        return

    mapper = ComprehensiveMapper()
    mapper.run_comprehensive_mapping()

if __name__ == "__main__":
    main()