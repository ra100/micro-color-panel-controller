# Generated Data & Results

This folder contains generated data, analysis results, and raw captures from the investigation process.

## Files

### Raw USB Captures

- `davinci_interaction_capture.pcapng` - Wireshark USB capture of DaVinci Resolve interacting with the panel
  - Used to reverse engineer the USB protocol
  - Contains illumination commands and input data examples
  - Can be opened with Wireshark for analysis

### Generated Mapping Data

- `trackball_mapping_detailed.py` - Detailed trackball mapping results from systematic testing

  - Complete analysis of Report 0x05 byte patterns
  - Includes successful mappings for LEFT and CENTER trackballs
  - Documents failed mappings for RIGHT trackball (hardware limitation)

- `missing_trackball_results.py` - Results from re-testing missing trackball axes

  - Extended analysis with longer capture times
  - Confirms hardware limitations of RIGHT trackball
  - Documents investigation methodology

- `robust_control_mapping.py` - Generated control mapping constants
  - Intermediate mapping data from development process
  - Superseded by final mapping in root directory

### Control Lists

- `panel_controls_list.txt` - Complete list of all detected panel controls
  - 67+ controls documented with their functions
  - Button mappings, encoder assignments, trackball capabilities
  - Used as reference during mapping development

## Data Analysis Notes

### Trackball Hardware Findings

- **LEFT trackball**: Fully functional (X, Y, Wheel CW/CCW)
- **CENTER trackball**: Partially functional (X, Y only - wheel not connected)
- **RIGHT trackball**: Non-functional (not connected to USB interface)

### Button Mapping Results

- **61 buttons successfully mapped** using Report 0x02
- **12 encoder buttons** mapped with sequential bit patterns
- **6 encoder rotations** mapped using Report 0x06

### USB Protocol Discoveries

- **Report 0x03**: Global illumination control (brightness 0-255, non-linear)
- **Report 0x0a**: Secondary control required for stable illumination
- **Report 0x02**: Standard button events (8 bytes, bit-mapped)
- **Report 0x05**: Trackball data and special functions
- **Report 0x06**: Encoder rotation data (complex multi-byte patterns)

## Usage

These files document the complete investigation process and can be used to:

1. **Understand the discovery process** - See how each control was identified
2. **Verify mappings** - Cross-reference with raw data for accuracy
3. **Extend functionality** - Use patterns to decode additional features
4. **Debug issues** - Reference known working configurations

The final, clean mapping data is located in the root directory files:

- `davinci_panel_mapping.json` - Machine-readable mapping
- `davinci_panel_controls.py` - Python constants for development
