# Technology Stack

## Core Technologies

### USB Communication

- **PyUSB**: Cross-platform USB device communication
- **HID Protocol**: Human Interface Device standard for input/output
- **USB HID Reports**: Structured data packets for device communication
- **Linux Udev**: Device permission management and hotplug support

### Programming Languages

- **Python 3.10+**: Primary development language
- **Blender Python API**: Integration with Blender's scripting system

### Development Environment

- **Conda**: Package and environment management
- **pip**: Additional package installation
- **Linux**: Primary development and target platform

## Dependencies

### Core Dependencies

- `pyusb>=0.12.0` - USB device communication
- `pyudev>=0.24.0` - Linux device monitoring
- `numpy>=1.21.0` - Numerical processing for input smoothing
- `pynput>=1.7.6` - Cross-platform input simulation (optional)

### GUI Dependencies

- `PyQt5>=5.15.0` - Cross-platform GUI framework
- `tkinter` - Built-in Python GUI (fallback)

### MIDI Support (Optional)

- `python-rtmidi>=1.4.9` - MIDI input/output
- `mido>=1.3.0` - MIDI message handling

### Development Dependencies

- `pytest>=7.0.0` - Testing framework
- `black>=22.0.0` - Code formatting
- `isort>=5.10.0` - Import sorting
- `flake8>=5.0.0` - Linting

## Hardware Interface

### USB Device Specifications

- **Vendor ID**: 0x1edb (Blackmagic Design)
- **Product ID**: 0xda0f (DaVinci Micro Color Panel)
- **Interface**: 2 (HID)
- **Endpoints**: Input (0x81), Output (0x01)

### Control Mapping

- **12 Rotary Encoders**: Multi-turn with push buttons
- **52+ Buttons**: Function buttons and encoder buttons
- **3 Trackballs**: X/Y movement and wheel rotation
- **Global Illumination**: Button lighting control

## Development Tools

### Investigation Tools (25+ scripts)

- USB protocol reverse engineering
- Control mapping and discovery
- Data capture and analysis
- Testing and validation

### Build System

- **Conda Environment**: `environment.yml` for reproducible setup
- **Requirements Files**: `requirements.txt` for pip-based installation
- **Udev Rules**: Linux device permissions

## Platform Support

### Primary Platform

- **Linux**: Full support with udev rules and PyUSB

### Planned Platforms

- **Windows**: PyUSB compatibility
- **macOS**: PyUSB compatibility

### Blender Integration

- **Blender 3.0+**: Timer-based input polling
- **Addon System**: Standard Blender addon architecture
- **UI Integration**: Sidebar panel for controls

## Technical Constraints

### USB Limitations

- Hardware trackball limitations (RIGHT trackball not connected)
- Proprietary authentication requirements (periodic reconnection needed)
- USB timeout handling and recovery

### Performance Considerations

- Input polling frequency (20ms for responsiveness)
- Memory usage for input smoothing
- Threading for non-blocking operation

### Compatibility Issues

- Blender's Python environment isolation
- USB permission requirements
- Platform-specific USB handling
