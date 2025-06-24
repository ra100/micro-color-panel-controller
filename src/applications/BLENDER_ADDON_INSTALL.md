# DaVinci Micro Panel Blender Addon Installation

## 🎯 Overview

This addon allows you to use your DaVinci Micro Color Panel as a 3D navigation controller in Blender. Control viewport rotation, panning, zooming, and tool switching using the panel's trackballs, encoders, and buttons.

## 📋 Requirements

- **Blender 3.0+** (tested with Blender 3.0 and newer)
- **DaVinci Micro Color Panel** (USB ID: 1edb:da0f)
- **Linux system** with proper USB permissions
- **micro-panel project** installed and working

## 🔧 Installation Steps

### 1. Prepare the Addon Files

From your micro-panel project directory:

```bash
# Create addon package directory
mkdir -p ~/blender_addons/davinci_micro_panel/

# Copy the addon file
cp src/applications/blender.py ~/blender_addons/davinci_micro_panel/__init__.py

# Copy required dependencies
cp -r src/ ~/blender_addons/davinci_micro_panel/
cp davinci_panel_controls.py ~/blender_addons/davinci_micro_panel/
cp davinci_panel_mapping.json ~/blender_addons/davinci_micro_panel/
```

### 2. Install in Blender

**Method A: Manual Installation**

1. Open Blender
2. Go to **Edit → Preferences → Add-ons**
3. Click **Install...**
4. Navigate to `~/blender_addons/davinci_micro_panel/`
5. Select `__init__.py` and click **Install Add-on**
6. Enable the addon by checking the box next to "**DaVinci Micro Panel Controller**"

**Method B: Development Installation**

1. Copy the entire `davinci_micro_panel` folder to Blender's addons directory:

   ```bash
   # For user installation
   cp -r ~/blender_addons/davinci_micro_panel/ ~/.config/blender/3.*/scripts/addons/

   # For system-wide installation
   sudo cp -r ~/blender_addons/davinci_micro_panel/ /usr/share/blender/3.*/scripts/addons/
   ```

2. Restart Blender and enable the addon in Preferences

### 3. USB Permissions

Make sure your system has proper USB permissions:

```bash
# Install udev rules (if not already done)
sudo cp udev/99-davinci-micro-panel.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger

# Add your user to dialout group
sudo usermod -a -G dialout $USER

# Log out and log back in for changes to take effect
```

## 🎮 Usage

### Accessing the Panel

1. Open Blender with a 3D viewport active
2. In the 3D viewport, open the **Sidebar** (press `N` if not visible)
3. Look for the **Panel** tab in the sidebar
4. You should see **DaVinci Micro Panel** section

### Connecting the Device

1. **Connect your DaVinci panel** via USB
2. In the addon panel, click **"Connect Panel"**
3. If successful, you'll see **"Status: Connected ✅"**
4. Panel buttons should illuminate
5. **Start using the controls!**

### Control Mapping

| Control                  | Function                   |
| ------------------------ | -------------------------- |
| **Left Trackball**       | Rotate 3D viewport         |
| **Center Trackball**     | Pan 3D viewport            |
| **Left Trackball Wheel** | Zoom in/out                |
| **Rotary Encoders**      | Various tool parameters    |
| **Function Buttons**     | Mode switching & shortcuts |

### Settings

- **Sensitivity**: Adjust control responsiveness (0.1 - 5.0)
- **Invert X/Y**: Reverse trackball movement directions

## 🐛 Troubleshooting

### "Device driver not available"

- Ensure the micro-panel project is properly installed
- Check that `src/core/device.py` is accessible
- Verify Python path includes the micro-panel directory

### "Failed to connect to panel"

- Check USB connection
- Verify udev rules are installed: `ls -la /etc/udev/rules.d/*davinci*`
- Test panel with standalone script: `python src/core/device.py`
- Check permissions: `ls -la /dev/hidraw*`

### Panel doesn't respond

- Try disconnecting and reconnecting the panel
- Restart Blender
- Check console for error messages (Window → Toggle System Console)

### Addon not showing up

- Ensure addon is enabled in Preferences → Add-ons
- Search for "DaVinci" in the addon list
- Check Blender's console for import errors

## 🔧 Development

### Testing the Addon

You can test the addon development by running:

```bash
# Test device connection outside Blender
cd /path/to/micro-panel/
python src/applications/blender.py
```

### Modifying Controls

Edit the `process_input()` method in `BlenderController` to customize how panel controls map to Blender functions. Use the control mappings from `davinci_panel_controls.py`.

### Adding Features

The addon structure supports:

- Custom viewport navigation
- Tool parameter control
- Mode switching
- Display updates
- User preferences

## 📚 References

- [Blender Addon Development](https://docs.blender.org/manual/en/latest/advanced/scripting/addon_tutorial.html)
- [DaVinci Panel Control Mapping](../../davinci_panel_controls.py)
- [Device Interface Documentation](../core/device.py)

---

**Note**: This addon is part of the micro-panel project and requires the core device drivers to function.
