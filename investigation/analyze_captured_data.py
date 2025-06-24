#!/usr/bin/env python3
"""
Quick analysis of captured input data patterns
"""

def analyze_reports():
    """Analyze the captured input reports"""
    print("🔍 Analysis of Captured Input Data")
    print("=" * 50)

    # The reports we captured
    reports = [
        "05 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00",  # Report 1
        "05 00 c0 01 00 00 30 ff ff 00 00 00 00 00 00 00",  # Report 2 (activity!)
        "08 00 64"  # Report 3
    ]

    print("📊 Report Analysis:")
    print()

    for i, report_hex in enumerate(reports, 1):
        bytes_list = [int(b, 16) for b in report_hex.split()]
        report_id = bytes_list[0]
        data = bytes_list[1:]

        print(f"📋 Report {i}: ID=0x{report_id:02x}")
        print(f"   Raw: [{report_hex}]")
        print(f"   Length: {len(bytes_list)} bytes")

        if report_id == 0x05:
            print("   🎛️ Likely main input report (trackballs, encoders, buttons)")

            # Look for patterns in the data
            non_zero_positions = [(j, val) for j, val in enumerate(data) if val != 0]
            if non_zero_positions:
                print("   📍 Non-zero bytes:")
                for pos, val in non_zero_positions:
                    print(f"      Byte {pos+1}: 0x{val:02x} ({val})")

                    # Interpret some common patterns
                    if pos == 1 and val == 0xc0:  # Position 2, value 192
                        print(f"         🎯 Could be trackball/encoder data")
                    elif pos == 2 and val == 0x01:  # Position 3, value 1
                        print(f"         🎯 Could be button/status data")
                    elif val == 0xff:
                        print(f"         🎯 Maximum value - could be button press")

        elif report_id == 0x08:
            print("   🔧 Secondary report type")
            if len(data) >= 2 and data[1] == 0x64:  # 100 decimal
                print("   💡 Value 0x64 (100) - could be related to illumination brightness")

        print()

    print("🎯 Preliminary Analysis:")
    print("• Report ID 0x05: Main input data (64 bytes)")
    print("• Report ID 0x08: Secondary/status data (3 bytes)")
    print("• Activity detected in bytes 2-3 and 6-8 of report 0x05")
    print("• Pattern suggests trackball/encoder movement")
    print()
    print("🚀 Next Steps:")
    print("1. Run input monitoring again with improved timeout handling")
    print("2. Move SPECIFIC controls to map bytes to functions")
    print("3. Test each trackball, encoder, and button systematically")

if __name__ == "__main__":
    analyze_reports()