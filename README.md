# DaVinci Micro Panel Universal Controller

Use your DaVinci Micro Color Panel outside of DaVinci Resolve for any application - Blender scene navigation, audio mixing, photo editing, and more!

## 🎯 Project Goals

- **Universal Control**: Map panel controls to any application (Blender, Photoshop, OBS, etc.)
- **Flexible Mapping**: Customizable control schemes for different applications
- **Real-time Feedback**: Button illumination and display updates
- **Plugin Architecture**: Easy to extend for new applications

## 🔧 Hardware Details

**Device Info:**

- USB Vendor ID: `1edb` (Blackmagic Design)
- Product ID: `da0f` (DaVinci Resolve Micro Color Panel)
- Protocol: USB HID (Human Interface Device)
- Interfaces: 3 (HID, vendor-specific control, vendor-specific data)

**Controls Available:**

- 12 Rotary encoders with push buttons
- 3 Trackballs with rotary wheels around each trackball
- 40 Additional function buttons
- Illuminated buttons (global on/off control)
- Small displays/labels

**Total Controls:**

- 15 Rotary encoders (12 main + 3 trackball wheels)
- 52 Buttons (12 rotary buttons + 40 function buttons)
- 3 Trackballs for X/Y movement

## 📋 Implementation Steps (POC)

### Phase 1: Device Communication ✅

1. [x] Research USB HID protocol for the panel
2. [x] Identify device interfaces and endpoints
3. [x] Create basic HID communication layer
4. [ ] Parse input reports from rotaries, buttons, trackballs
5. [ ] Implement output reports for button illumination and displays

### Phase 2: Application Integration

1. [ ] Create Blender addon for viewport navigation
2. [ ] Implement virtual MIDI controller mode
3. [ ] Add support for mouse/keyboard simulation
4. [ ] Create configuration GUI

### Phase 3: Advanced Features

1. [ ] Application auto-detection
2. [ ] Profile switching
3. [ ] Custom scripting support
4. [ ] Community plugin marketplace

## 🚀 Quick Start

### Prerequisites

**Linux:**

```bash
# Install conda (if not already installed)
# Visit: https://docs.conda.io/en/latest/miniconda.html

# Add udev rules for device access
sudo cp udev/99-davinci-micro-panel.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

**Requirements:**

- Conda package manager
- Linux/Windows/macOS
- DaVinci Micro Color Panel connected via USB

### Basic Usage

```bash
# Clone and setup
git clone <repo-url>
cd micro-panel

# Create conda environment
conda env create -f environment.yml
conda activate micro-panel

# Run basic device test
python src/core/device.py

# Start Blender integration
python src/applications/blender.py

# Alternative: pip installation (if you prefer)
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

## 🗂️ Project Structure

```
micro-panel/
├── src/
│   ├── core/
│   │   ├── device.py          # HID device communication
│   │   ├── protocol.py        # Panel protocol implementation
│   │   └── mapping.py         # Control mapping engine
│   ├── applications/
│   │   ├── blender.py         # Blender integration
│   │   ├── obs.py             # OBS Studio control
│   │   └── midi.py            # Virtual MIDI controller
│   ├── config/
│   │   ├── profiles/          # Control profiles
│   │   └── mappings/          # Application mappings
│   └── gui/
│       └── config_app.py      # Configuration interface
├── udev/
│   └── 99-davinci-micro-panel.rules  # Linux device permissions
├── docs/
│   ├── PROTOCOL.md            # Reverse engineering notes
│   ├── API.md                 # API documentation
│   └── APPLICATIONS.md        # Supported applications
└── examples/
    ├── basic_usage.py         # Simple usage examples
    └── custom_mapping.py      # Custom control mapping
```

## 🎮 Supported Applications

### Current

- [x] **Blender**: Viewport navigation, timeline control, property adjustment
- [x] **Virtual MIDI**: Use as MIDI controller for DAWs
- [x] **Mouse/Keyboard**: Simulate standard input devices

### Planned

- [ ] **OBS Studio**: Scene switching, filter control, audio mixing
- [ ] **Adobe Photoshop**: Brush controls, layer adjustments
- [ ] **Lightroom**: Photo editing controls
- [ ] **Fusion 360**: CAD navigation and tool control
- [ ] **DCS/Flight Sims**: Aircraft systems control
- [ ] **Custom Applications**: Plugin API for any software

## 🔧 Technical Architecture

### Device Communication Layer

```python
# Core device interface
from micro_panel import MicroPanel

panel = MicroPanel()
panel.connect()

# Read controls
for event in panel.read_events():
    if event.type == 'rotary':
        print(f"Rotary {event.id} turned {event.delta}")
    elif event.type == 'button':
        print(f"Button {event.id} {'pressed' if event.pressed else 'released'}")

# Control feedback
panel.set_button_illumination(True)  # Turn on button lights
panel.set_display(0, "Blender")  # Update display
```

### Application Integration

```python
# Blender example
from applications.blender import BlenderController

controller = BlenderController(panel)
controller.map_rotary(0, 'viewport.rotate_x')
controller.map_rotary(1, 'viewport.rotate_y')
controller.map_trackball(0, 'viewport.pan')
controller.start()
```

## 🐛 Troubleshooting

### Linux Permissions

If you get permission denied errors:

```bash
# Check device permissions
ls -la /dev/hidraw*

# Add user to dialout group
sudo usermod -a -G dialout $USER

# Log out and log back in
```

### Device Not Found

```bash
# Check if device is connected
lsusb | grep 1edb:da0f

# Check kernel logs
dmesg | tail
```

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone and setup development environment
git clone <repo-url>
cd micro-panel

# Create conda environment (includes dev dependencies)
conda env create -f environment.yml
conda activate micro-panel

# Run tests
python -m pytest tests/

# Format code
black src/
isort src/

# Alternative: pip development setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Blackmagic Design for creating excellent hardware
- The DaVinci Resolve community
- HID protocol reverse engineering community
- Open source projects that inspired this work

## 📚 Resources

- [USB HID Protocol Documentation](docs/PROTOCOL.md)
- [Control Mapping Reference](docs/API.md)
- [Application Integration Guide](docs/APPLICATIONS.md)
- [Community Forum](https://github.com/your-repo/discussions)

---

**Note**: This project is not affiliated with Blackmagic Design. DaVinci and related names are trademarks of Blackmagic Design.
