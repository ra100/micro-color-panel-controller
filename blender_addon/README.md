# DaVinci Micro Panel → Blender Addon v1.3.0

## Overview

Transform your DaVinci Micro Color Panel into a powerful 3D navigation controller for Blender. This addon provides smooth, professional-grade viewport control using the panel's trackballs, buttons, and encoders.

## Features

### 🎮 3D Navigation

- **LEFT Trackball**: Smooth 3D viewport rotation with proper multi-axis control
- **CENTER Trackball**: Viewport panning (when available on hardware)
- **Trackball Wheel**: Zoom in/out with configurable sensitivity
- **Responsive Controls**: Low-latency input processing with stability optimizations

### 🔘 Button Integration

- **AUTO_COLOR**: Select All/Deselect All toggle
- **COPY/PASTE**: 3D viewport copy/paste operations
- **UNDO/REDO**: Standard Blender undo/redo
- **DELETE**: Delete selected objects
- **PLAY_STILL/STOP**: Animation playback control
- **CURSOR**: Cycle viewport shading (Wireframe → Solid → Material → Rendered)
- **40+ Additional Buttons**: Framework ready for custom mapping

### ⚙️ Advanced Settings

- **Sensitivity Control**: Adjustable responsiveness (0.1x - 10x)
- **Axis Inversion**: Optional X/Y movement direction reversal
- **Debug Mode**: Toggle verbose console output for troubleshooting
- **Auto-Reconnection**: Handles USB disconnections gracefully
- **Connection Testing**: Built-in device detection and diagnostics

## Modular Architecture

### `device_control.py` - Hardware Interface

- **DaVinciMicroPanel**: Low-level USB communication
- **InputProcessor**: Configurable input processing with callbacks
- **Mapping Data**: Complete control definitions for reuse
- **Standalone Design**: Can be used outside of Blender

### `__init__.py` - Blender Integration

- **BlenderController**: Viewport manipulation and UI integration
- **Operator Classes**: Connect/disconnect, settings management
- **Panel UI**: Intuitive control interface
- **Modal Processing**: Non-blocking input handling

## Installation

### Requirements

- **Blender 3.0+**
- **Linux** (tested on 6.9.3-060903-generic)
- **DaVinci Micro Color Panel** (USB ID: 1edb:da0f)
- **USB Permissions** (udev rules recommended)

### Method 1: Automatic Installation

1. Place addon files in Blender addons directory
2. Enable addon in Blender Preferences
3. Click **"Auto-Install PyUSB"** if USB libraries missing
4. Restart Blender
5. Connect panel via addon interface

### Method 2: Manual PyUSB Installation

```bash
# Find Blender's Python executable
blender_python="/path/to/blender/python/bin/python"

# Install PyUSB
$blender_python -m pip install pyusb
```

### Method 3: Development Setup (Symbolic Link)

```bash
# Navigate to your addon development directory
cd /path/to/your/blender_addon

# Create symbolic link to Blender's addons directory
ln -s $(pwd) ~/.config/blender/4.4/scripts/addons/davinci_micro_panel

# Now you can edit files directly and see changes in Blender
```

## Usage

### Initial Setup

1. **Connect Hardware**: Plug in DaVinci Micro Panel
2. **Open Blender**: Navigate to 3D Viewport sidebar
3. **Find Panel**: Look for "DaVinci Micro Panel" tab
4. **Test Connection**: Click "Test Connection" for diagnostics
5. **Connect**: Click "Connect Panel" - panel should illuminate

### Navigation Controls

- **Rotate View**: Move LEFT trackball in any direction
- **Pan View**: Move CENTER trackball (if available)
- **Zoom**: Scroll LEFT trackball wheel
- **Fine Control**: Adjust sensitivity slider (0.1x - 10x)
- **Custom Axes**: Enable X/Y axis inversion if needed

### Troubleshooting

#### Connection Issues

```
❌ Device not found or connection failed
```

**Solutions:**

- Verify USB connection and cable
- Check device permissions (udev rules)
- Try different USB port
- Restart Blender and try again

#### Rotation Problems

```
Error rotating viewport: 'tuple' object has no attribute 'normalized'
```

**Solution:** Update to v1.3.0+ - this was fixed with proper mathutils Vector handling

#### Sensitivity Issues

- **Too sensitive**: Lower sensitivity setting
- **Too slow**: Increase sensitivity setting
- **Jumpy movement**: Enable debug mode to check input patterns

#### Debug Mode

Enable debug output to see detailed input processing:

1. Check "Debug Output" in addon panel
2. Open Blender Console (Window → Toggle System Console)
3. Move trackballs to see input data
4. Share console output when reporting issues

## Hardware Compatibility

### Tested Features

- ✅ **LEFT Trackball**: Full X/Y movement + wheel (fully functional)
- ⚠️ **CENTER Trackball**: X/Y movement only (wheel not connected)
- ❌ **RIGHT Trackball**: Not connected to USB interface
- ✅ **12 Encoder Buttons**: All buttons working
- ✅ **40+ Function Buttons**: Most buttons mapped and working
- ✅ **Panel Illumination**: Full brightness control with auto-refresh

### Known Limitations

- CENTER trackball wheel is not hardware-connected
- RIGHT trackball is not hardware-connected
- Some encoder rotations need further mapping
- Panel may disconnect during intensive use (auto-reconnection enabled)

## Development

### Extending Functionality

The modular design makes it easy to:

- Add new button mappings in `execute_button_action()`
- Implement encoder controls in `handle_encoder_input()`
- Create custom input processors using `device_control.InputProcessor`
- Use the hardware interface in other applications

### Button Mapping Reference

```python
device_control.FUNCTION_BUTTONS = {
    'AUTO_COLOR': 20, 'COPY': 22, 'PASTE': 23, 'UNDO': 24, 'REDO': 25,
    'DELETE': 26, 'PLAY_STILL': 34, 'CURSOR': 39, 'STOP': 59,
    # ... 40+ more buttons available
}
```

### Testing

Use the built-in test connection feature:

```python
bpy.ops.davinci.test_connection()
```

## Version History

### v1.3.0 (Current)

- ✅ **Modular Architecture**: Separated device control from Blender code
- ✅ **Fixed Rotation Issues**: Proper mathutils Vector handling
- ✅ **Improved Sensitivity**: Reduced base sensitivity, better scaling
- ✅ **Auto-Reconnection**: Handles USB disconnections gracefully
- ✅ **Debug Mode**: User-toggleable verbose output
- ✅ **Better UI**: Enhanced settings and status indicators
- ✅ **Stability**: Reduced timer frequency, improved error handling

### v1.2.0

- Self-contained addon with embedded device code
- Basic trackball navigation and button support
- Auto-installation system for PyUSB

### v1.1.0

- Initial working trackball integration
- Basic USB communication established

## Support

### Reporting Issues

When reporting problems, please include:

1. **Blender Version**: Help → About Blender
2. **Addon Version**: Check addon preferences
3. **Operating System**: `uname -a` output
4. **Debug Output**: Enable debug mode and include console output
5. **USB Device Info**: `lsusb | grep 1edb` output

### Development

This project is open for contributions. The modular architecture makes it easy to:

- Add support for other color panels
- Implement additional Blender integrations
- Create standalone applications using `device_control.py`

### License

Community support - designed for educational and creative use.

---

**Transform your color grading panel into a 3D navigation powerhouse!** 🎨✨
