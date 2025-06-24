# Investigation Tools

This folder contains all the development, testing, and investigation tools used during the reverse engineering of the DaVinci Micro Panel.

## Mapping Tools

- `map_controls.py` - Basic control mapping tool
- `map_all_controls.py` - Comprehensive control mapping
- `map_all_controls_robust.py` - Robust mapping with error handling
- `map_comprehensive_controls.py` - Most advanced mapping tool (used for final mapping)
- `map_trackballs_detailed.py` - Detailed trackball analysis tool
- `remap_add_buttons.py` - Tool to fix ADD button mapping errors
- `remap_missing_trackballs.py` - Tool to re-test missing trackball axes

## USB Capture & Analysis Tools

- `capture_all_inputs.py` - Comprehensive USB input capture tool
- `simple_capture.py` - Basic USB data capture
- `raw_trackball_capture.py` - Raw trackball data capture (minimal interference)
- `analyze_captured_data.py` - Analysis tool for captured USB data
- `decode_capture.py` - Wireshark capture decoder

## Testing Tools

- `test_panel.py` - Basic panel connection testing
- `test_working_illumination.py` - Illumination functionality testing
- `test_hid_reports.py` - HID report analysis
- `test_hid_reports_v2.py` - Advanced HID report testing
- `test_focused_buttons.py` - Focused button mapping testing
- `test_individual_buttons.py` - Individual button testing
- `test_input_analysis.py` - Input data analysis and pattern detection
- `test_input_monitoring.py` - Real-time input monitoring
- `test_interface_0.py` - USB Interface 0 testing
- `test_report_0a_and_longer.py` - Specific report testing
- `test_usb_control.py` - USB control command testing

## Debug & Discovery Tools

- `debug_hid.py` - HID debugging and exploration
- `brute_force_vendor.py` - Vendor-specific command discovery
- `illuminate_test.py` - Illumination control testing

## Usage Notes

These tools were used during the development process to:

1. **Discover USB protocols** - Finding the correct interfaces, endpoints, and report formats
2. **Map all controls** - Systematically identifying every button, encoder, and trackball
3. **Analyze data patterns** - Understanding how each control encodes its data
4. **Test functionality** - Verifying illumination, input detection, and USB stability
5. **Debug issues** - Solving USB disconnection problems and mapping errors

Most of these tools require the panel to be connected and may need adjustment of USB parameters or timing based on your specific setup.

## Key Findings

- **Interface 2 (HID)** is used for both input (endpoint 0x81) and output (endpoint 0x01)
- **Report 0x03** controls global illumination with non-linear brightness mapping
- **Report 0x02** contains standard button events
- **Report 0x05** contains trackball and special function data
- **Report 0x06** contains encoder rotation data
- **Only LEFT and CENTER trackballs** are connected to USB (RIGHT trackball is not functional)

See the main project README for implementation details and final results.
