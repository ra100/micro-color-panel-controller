#!/usr/bin/env python3
"""
DaVinci USB Capture Pattern Decoder
Analyzes the captured USB traffic to extract control transfer patterns
"""

import struct

def decode_usb_control_transfer(hex_data):
    """Decode USB control transfer setup packet"""
    # USB setup packet is 8 bytes:
    # bmRequestType, bRequest, wValue (2 bytes), wIndex (2 bytes), wLength (2 bytes)
    if len(hex_data) >= 8:
        setup = hex_data[:8]
        bmRequestType = setup[0]
        bRequest = setup[1]
        wValue = struct.unpack('<H', setup[2:4])[0]  # little-endian
        wIndex = struct.unpack('<H', setup[4:6])[0]
        wLength = struct.unpack('<H', setup[6:8])[0]

        return {
            'bmRequestType': f"0x{bmRequestType:02x}",
            'bRequest': f"0x{bRequest:02x}",
            'wValue': f"0x{wValue:04x}",
            'wIndex': f"0x{wIndex:04x}",
            'wLength': wLength,
            'raw_setup': setup.hex()
        }
    return None

def analyze_patterns():
    """Analyze the patterns we found in the capture"""

    # These are the control transfer patterns I spotted in the capture
    patterns = [
        # HID GET_REPORT patterns
        bytes([0xa1, 0x01, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00]),  # Get report type 1
        bytes([0xa1, 0x03, 0x13, 0x00, 0x00, 0x00, 0xff, 0x00]),  # Get report type 3, report ID 0x13
        bytes([0xa1, 0x03, 0x14, 0x00, 0x00, 0x00, 0xff, 0x00]),  # Get report type 3, report ID 0x14
        bytes([0xa1, 0x03, 0x15, 0x00, 0x00, 0x00, 0xff, 0x00]),  # Get report type 3, report ID 0x15
        bytes([0xa1, 0x03, 0x16, 0x00, 0x00, 0x00, 0xff, 0x00]),  # Get report type 3, report ID 0x16
        bytes([0xa1, 0x03, 0x17, 0x00, 0x00, 0x00, 0xff, 0x00]),  # Get report type 3, report ID 0x17
        bytes([0xa1, 0x03, 0x18, 0x00, 0x00, 0x00, 0xff, 0x00]),  # Get report type 3, report ID 0x18

        # Other control transfer patterns
        bytes([0xc0, 0x08, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00]),  # Vendor-specific?

        # HID SET_REPORT patterns (potentially for illumination)
        bytes([0x21, 0x02, 0x13, 0x00, 0x00, 0x00, 0x0a, 0x00]),  # Set report type 2, report ID 0x13
        bytes([0x21, 0x02, 0x14, 0x00, 0x00, 0x00, 0x07, 0x00]),  # Set report type 2, report ID 0x14
        bytes([0x21, 0x02, 0x15, 0x00, 0x00, 0x00, 0x0a, 0x00]),  # Set report type 2, report ID 0x15
        bytes([0x21, 0x02, 0x16, 0x00, 0x00, 0x00, 0x07, 0x00]),  # Set report type 2, report ID 0x16
        bytes([0x21, 0x02, 0x17, 0x00, 0x00, 0x00, 0x0e, 0x00]),  # Set report type 2, report ID 0x17
        bytes([0x21, 0x02, 0x18, 0x00, 0x00, 0x00, 0x0a, 0x00]),  # Set report type 2, report ID 0x18
    ]

    print("🔍 DECODED USB CONTROL TRANSFER PATTERNS FROM DAVINCI:")
    print("=" * 70)

    for i, pattern in enumerate(patterns):
        decoded = decode_usb_control_transfer(pattern)
        if decoded:
            print(f"\nPattern {i+1}:")
            print(f"  bmRequestType: {decoded['bmRequestType']} ", end="")

            # Decode bmRequestType
            req_type = int(decoded['bmRequestType'], 16)
            direction = "Host->Device" if (req_type & 0x80) == 0 else "Device->Host"
            req_class = (req_type >> 5) & 0x03
            recipient = req_type & 0x1f

            class_names = {0: "Standard", 1: "Class", 2: "Vendor", 3: "Reserved"}
            recipient_names = {0: "Device", 1: "Interface", 2: "Endpoint", 3: "Other"}

            print(f"({direction}, {class_names.get(req_class, 'Unknown')}, {recipient_names.get(recipient, 'Unknown')})")
            print(f"  bRequest:      {decoded['bRequest']}")
            print(f"  wValue:        {decoded['wValue']}")
            print(f"  wIndex:        {decoded['wIndex']}")
            print(f"  wLength:       {decoded['wLength']} bytes")
            print(f"  Raw bytes:     {decoded['raw_setup']}")

            # Analyze specific patterns
            if req_type == 0xa1:  # HID GET_REPORT
                report_type = (int(decoded['wValue'], 16) >> 8) & 0xff
                report_id = int(decoded['wValue'], 16) & 0xff
                type_names = {1: "Input", 2: "Output", 3: "Feature"}
                print(f"  📋 HID GET_REPORT: {type_names.get(report_type, 'Unknown')} Report, ID: 0x{report_id:02x}")

            elif req_type == 0x21:  # HID SET_REPORT
                report_type = (int(decoded['wValue'], 16) >> 8) & 0xff
                report_id = int(decoded['wValue'], 16) & 0xff
                type_names = {1: "Input", 2: "Output", 3: "Feature"}
                print(f"  💡 HID SET_REPORT: {type_names.get(report_type, 'Unknown')} Report, ID: 0x{report_id:02x}")
                if report_type == 2:
                    print(f"  🔥 POTENTIAL ILLUMINATION COMMAND!")

if __name__ == "__main__":
    analyze_patterns()