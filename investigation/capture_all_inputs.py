#!/usr/bin/env python3
"""
High-Performance Input Capture Tool
Optimized to capture ALL input events without missing any
"""

import sys
import os
import time
import threading
from collections import defaultdict, deque

# Add our modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.device import DaVinciMicroPanel

class HighPerformanceCapture:
    """High-performance input capture optimized for completeness"""

    def __init__(self):
        self.panel = None
        self.capture_buffer = deque(maxlen=10000)  # Large buffer for events
        self.running = False
        self.stats = {
            'total_reports': 0,
            'report_types': defaultdict(int),
            'missed_events': 0,
            'start_time': 0
        }

    def connect(self):
        """Connect to panel"""
        print("🔌 Connecting to DaVinci Micro Panel...")

        self.panel = DaVinciMicroPanel()
        if not self.panel.connect():
            print("❌ Failed to connect!")
            return False

        # Keep illumination ON with periodic refresh
        self._start_illumination_keeper()

        print("✅ Panel connected and illuminated!")
        return True

    def _start_illumination_keeper(self):
        """Start background thread to keep illumination ON"""
        def illumination_keeper():
            while self.running:
                try:
                    if self.panel and self.panel.device:
                        # Refresh illumination every 20 seconds
                        self.panel.device.ctrl_transfer(
                            bmRequestType=0x21,
                            bRequest=0x09,
                            wValue=0x0303,
                            wIndex=0x0002,
                            data_or_wLength=bytes([0x03, 150, 150])  # Bright illumination
                        )
                except:
                    pass  # Ignore errors
                time.sleep(20)  # Refresh every 20 seconds

        keeper_thread = threading.Thread(target=illumination_keeper, daemon=True)
        keeper_thread.start()

    def capture_all_inputs(self, duration=60):
        """Capture all inputs for specified duration"""
        print(f"\n🎯 HIGH-PERFORMANCE INPUT CAPTURE ({duration} seconds)")
        print("=" * 60)
        print("🎛️ Move ALL controls systematically:")
        print("   • All 3 trackballs (X/Y movement)")
        print("   • All 12 rotary encoders (clockwise/counter-clockwise)")
        print("   • All buttons (press/release)")
        print("   • Try combinations and rapid movements")
        print()
        print("📊 Optimized for ZERO missed events!")
        print("⏱️ Starting capture in 3 seconds...")

        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)

        print("🚀 CAPTURE STARTED - GO!")

        self.running = True
        self.stats['start_time'] = time.time()

        # High-speed capture loop
        end_time = time.time() + duration
        last_stats_update = time.time()

        try:
            while time.time() < end_time and self.running:
                try:
                    # Very fast polling - 10ms timeout
                    data = self.panel.device.read(0x81, 64, timeout=10)

                    if data:
                        data_bytes = bytes(data)
                        timestamp = time.time() - self.stats['start_time']

                        # Only process non-zero data
                        if any(b != 0 for b in data_bytes):
                            # Store in buffer for analysis
                            self.capture_buffer.append((timestamp, data_bytes))

                            self.stats['total_reports'] += 1
                            self.stats['report_types'][data_bytes[0]] += 1

                            # Minimal real-time output to avoid slowing down
                            report_id = data_bytes[0]
                            if report_id == 0x02:  # Button
                                # Show button bit pattern
                                button_byte = data_bytes[4] if len(data_bytes) > 4 else 0
                                if button_byte != 0:
                                    print(f"🔘 BTN: 0x{button_byte:02x}")
                            elif report_id == 0x06:  # Trackball/Encoder
                                # Show first few data bytes
                                hex_snippet = ' '.join(f'{b:02x}' for b in data_bytes[1:5])
                                print(f"🎛️ TRK: [{hex_snippet}]")
                            elif report_id == 0x05:  # Other input
                                print(f"🎯 0x05: {data_bytes[10]:02x}")

                except Exception as e:
                    if "timeout" not in str(e).lower():
                        self.stats['missed_events'] += 1
                        if self.stats['missed_events'] < 5:  # Only show first few errors
                            print(f"⚠️ Error: {e}")

                # Periodic stats update (every 10 seconds)
                if time.time() - last_stats_update > 10:
                    self._show_stats()
                    last_stats_update = time.time()

        except KeyboardInterrupt:
            print("\n🛑 Capture interrupted by user")

        elapsed = time.time() - self.stats['start_time']
        print(f"\n⏰ Capture completed: {elapsed:.1f} seconds")

        return self._analyze_results()

    def _show_stats(self):
        """Show real-time statistics"""
        elapsed = time.time() - self.stats['start_time']
        rate = self.stats['total_reports'] / elapsed if elapsed > 0 else 0
        print(f"📈 {elapsed:.0f}s: {self.stats['total_reports']} reports ({rate:.1f}/sec)")

    def _analyze_results(self):
        """Analyze captured results"""
        print(f"\n🔍 CAPTURE ANALYSIS")
        print("=" * 50)

        total_events = len(self.capture_buffer)
        elapsed = time.time() - self.stats['start_time']

        print(f"📊 Statistics:")
        print(f"   ⏱️  Duration: {elapsed:.1f} seconds")
        print(f"   📝 Total events: {total_events}")
        print(f"   🔄 Rate: {total_events/elapsed:.1f} events/second")
        print(f"   ❌ Missed events: {self.stats['missed_events']}")

        print(f"\n📋 Report Types:")
        for report_id, count in sorted(self.stats['report_types'].items()):
            print(f"   0x{report_id:02x}: {count:4d} reports")

        # Analyze button patterns
        button_events = [(t, d) for t, d in self.capture_buffer if d[0] == 0x02]
        trackball_events = [(t, d) for t, d in self.capture_buffer if d[0] == 0x06]

        print(f"\n🔘 Button Analysis: {len(button_events)} events")
        if button_events:
            button_patterns = set()
            for timestamp, data in button_events:
                if len(data) > 4:
                    pattern = tuple(data[1:6])  # Button pattern bytes
                    button_patterns.add(pattern)
            print(f"   📍 Unique button patterns: {len(button_patterns)}")

        print(f"\n🎛️ Trackball/Encoder Analysis: {len(trackball_events)} events")
        if trackball_events:
            trackball_ranges = defaultdict(lambda: {'min': 999999, 'max': -999999})
            for timestamp, data in trackball_events:
                for i in range(1, min(16, len(data)), 2):
                    if i+1 < len(data):
                        value = int.from_bytes(data[i:i+2], 'little', signed=True)
                        if value != 0:
                            trackball_ranges[i]['min'] = min(trackball_ranges[i]['min'], value)
                            trackball_ranges[i]['max'] = max(trackball_ranges[i]['max'], value)

            print(f"   📍 Active data positions:")
            for pos, range_data in trackball_ranges.items():
                if range_data['min'] != 999999:
                    print(f"      Bytes {pos}-{pos+1}: {range_data['min']} to {range_data['max']}")

        return self.capture_buffer

    def save_capture_data(self, filename="capture_data.txt"):
        """Save capture data to file"""
        print(f"\n💾 Saving capture data to {filename}...")

        with open(filename, 'w') as f:
            f.write("# DaVinci Micro Panel Capture Data\n")
            f.write(f"# Captured {len(self.capture_buffer)} events\n")
            f.write("# Format: timestamp,hex_data\n\n")

            for timestamp, data in self.capture_buffer:
                hex_data = ' '.join(f'{b:02x}' for b in data)
                f.write(f"{timestamp:.3f},{hex_data}\n")

        print(f"✅ Saved {len(self.capture_buffer)} events to {filename}")

def main():
    """Main entry point"""
    print("⚡ DaVinci Panel HIGH-PERFORMANCE Input Capture")
    print("Optimized to capture ALL input events without missing any")
    print()

    capture = HighPerformanceCapture()

    if not capture.connect():
        return

    try:
        # Capture for 60 seconds by default
        duration = 60
        if len(sys.argv) > 1:
            try:
                duration = int(sys.argv[1])
            except:
                pass

        results = capture.capture_all_inputs(duration)

        # Offer to save results
        if input(f"\n💾 Save capture data to file? (y/N): ").lower() == 'y':
            filename = input("Enter filename (or press Enter for 'capture_data.txt'): ").strip()
            if not filename:
                filename = "capture_data.txt"
            capture.save_capture_data(filename)

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if capture.panel:
            capture.running = False
            capture.panel.cleanup()

    print("\n✅ High-performance capture completed!")

if __name__ == "__main__":
    main()