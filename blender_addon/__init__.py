#!/usr/bin/env python3
"""
DaVinci Micro Panel → Blender Addon
Universal controller for Blender 3D navigation using the DaVinci panel
Self-contained version with embedded device code
"""

bl_info = {
    "name": "DaVinci Micro Panel Controller",
    "author": "Micro Panel Project",
    "version": (1, 1, 0),
    "blender": (3, 0, 0),
    "location": "3D Viewport > Sidebar > Panel",
    "description": "Use DaVinci Micro Color Panel for 3D navigation and tool control",
    "category": "3D View",
    "support": "COMMUNITY",
    "wiki_url": "",
    "tracker_url": "",
}

import bpy
import bmesh
import mathutils
from mathutils import Matrix, Vector, Euler
import sys
import os
import time
import threading
from typing import Optional, Callable, Dict, Any

# ===========================================================================
# EMBEDDED DEVICE CODE (to avoid import issues)
# ===========================================================================

# Try to import USB libraries
try:
    import usb.core
    import usb.util
    import signal
    import atexit
    USB_AVAILABLE = True
    print("✅ USB libraries available")
except ImportError as e:
    print(f"⚠️ USB libraries not available: {e}")
    USB_AVAILABLE = False

def install_pyusb():
    """Auto-install PyUSB using pip"""
    import subprocess
    import sys

    try:
        print("📦 Installing PyUSB...")

        # Try to find pip command
        pip_cmd = None
        for cmd in ['pip', 'pip3', 'python -m pip', 'python3 -m pip']:
            try:
                result = subprocess.run(cmd.split() + ['--version'],
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    pip_cmd = cmd.split()
                    break
            except:
                continue

        if not pip_cmd:
            return False, "Could not find pip command"

        # Install PyUSB
        result = subprocess.run(pip_cmd + ['install', 'pyusb'],
                              capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            print("✅ PyUSB installed successfully!")
            print("🔄 Please restart Blender to use the USB functionality")
            return True, "PyUSB installed successfully - restart Blender"
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            print(f"❌ Failed to install PyUSB: {error_msg}")
            return False, f"Installation failed: {error_msg}"

    except subprocess.TimeoutExpired:
        return False, "Installation timed out"
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False, f"Installation error: {str(e)}"

class DaVinciMicroPanel:
    """Embedded DaVinci Micro Panel interface"""

    # USB Device IDs
    VENDOR_ID = 0x1edb
    PRODUCT_ID = 0xda0f
    HID_INTERFACE = 2

    def __init__(self):
        self.device: Optional['usb.core.Device'] = None
        self.is_connected = False
        self.is_illuminated = False
        self.running = False

    def connect(self) -> bool:
        """Connect to the DaVinci panel"""
        if not USB_AVAILABLE:
            return False

        try:
            # Find the device
            self.device = usb.core.find(idVendor=self.VENDOR_ID, idProduct=self.PRODUCT_ID)
            if self.device is None:
                print("❌ DaVinci Micro Panel not found!")
                return False

            print(f"✅ Found DaVinci Micro Panel: {self.device}")

            # Detach kernel driver if necessary
            if self.device.is_kernel_driver_active(self.HID_INTERFACE):
                print(f"🔓 Detaching kernel driver from interface {self.HID_INTERFACE}")
                self.device.detach_kernel_driver(self.HID_INTERFACE)

            # Claim the HID interface
            usb.util.claim_interface(self.device, self.HID_INTERFACE)
            print(f"✅ Claimed HID interface {self.HID_INTERFACE}")

            self.is_connected = True

            # Turn on illumination when connected
            self.set_illumination(True)

            return True

        except Exception as e:
            print(f"❌ USB Error during connection: {e}")
            return False

    def set_illumination(self, enabled: bool, brightness: int = 100) -> bool:
        """Control panel button illumination"""
        if not self.is_connected or not self.device or not USB_AVAILABLE:
            return False

        try:
            # First send secondary control command
            secondary_data = bytes([0x0a, 0x01])
            self.device.ctrl_transfer(
                bmRequestType=0x21,
                bRequest=0x09,
                wValue=0x030a,
                wIndex=0x0002,
                data_or_wLength=secondary_data
            )

            # Then send illumination command
            if enabled:
                brightness = max(0, min(255, brightness))
                data = bytes([0x03, brightness, brightness])
                print(f"💡 Turning ON panel illumination (brightness: {brightness})")
            else:
                data = bytes([0x03, 0x00, 0x00])
                print("🔘 Turning OFF panel illumination")

            # Send HID SET_REPORT command
            result = self.device.ctrl_transfer(
                bmRequestType=0x21,
                bRequest=0x09,
                wValue=0x0303,
                wIndex=0x0002,
                data_or_wLength=data
            )

            self.is_illuminated = enabled
            print(f"✅ Illumination {'ON' if enabled else 'OFF'} - Success!")
            return True

        except Exception as e:
            print(f"❌ Failed to set illumination: {e}")
            return False

    def cleanup(self):
        """Cleanup resources and turn off illumination"""
        if self.is_connected:
            try:
                self.set_illumination(False)
                if self.device and USB_AVAILABLE:
                    usb.util.release_interface(self.device, self.HID_INTERFACE)
                self.is_connected = False
                print("📱 Panel disconnected")
            except Exception as e:
                print(f"⚠️ Error during cleanup: {e}")

# Embedded control mappings
ENCODER_BUTTONS = {
    'COLOR_BOOST_BUTTON': 14, 'CONTRAST_BUTTON': 11, 'HIGHLIGHTS_BUTTON': 16,
    'HUE_BUTTON': 18, 'LUM_MIX_BUTTON': 19, 'MID_DETAIL_BUTTON': 13,
    'PIVOT_BUTTON': 12, 'SATURATION_BUTTON': 17, 'SHADOWS_BUTTON': 15,
    'Y_GAIN_BUTTON': 10, 'Y_GAMMA_BUTTON': 9, 'Y_LIFT_BUTTON': 8,
}

FUNCTION_BUTTONS = {
    'ADD_KEYFRAME': 46, 'ADD_NODE': 44, 'ADD_WINDOW': 45, 'AUTO_COLOR': 20,
    'BACKWARD_PLAY': 57, 'BYPASS': 28, 'COPY': 22, 'CURSOR': 39,
    'DELETE': 26, 'DISABLE': 29, 'FORWARD_PLAY': 58, 'GRAB_STILL': 36,
    'H_LITE': 37, 'LOOP': 31, 'NEXT_CLIP': 56, 'NEXT_FRAME': 54,
    'NEXT_KEYFRAME': 50, 'NEXT_NODE': 52, 'NEXT_STILL': 48, 'OFFSET': 21,
    'PASTE': 23, 'PLAY_STILL': 34, 'PREV_CLIP': 55, 'PREV_FRAME': 53,
    'PREV_KEYFRAME': 49, 'PREV_NODE': 51, 'PREV_STILL': 47, 'REDO': 25,
    'RESET': 27, 'RESET_GAIN': 43, 'RESET_GAMMA': 42, 'RESET_LIFT': 41,
    'SELECT': 40, 'SPECIAL_LEFT': 32, 'SPECIAL_RIGHT': 33, 'STOP': 59,
    'UNDO': 24, 'USER': 30, 'VIEWER': 38, 'WIPE_STILL': 35,
}

TRACKBALL_AXES = {
    'LEFT_TRACKBALL_X': [2, 6, 3], 'LEFT_TRACKBALL_Y': [6, 2, 7], 'LEFT_TRACKBALL_WHEEL': [10],
    'CENTER_TRACKBALL_X': [14, 15], 'CENTER_TRACKBALL_Y': [14],
}

# ===========================================================================
# BLENDER ADDON CODE
# ===========================================================================

# Global controller instance
panel_controller = None

class DaVinciPanelProperties(bpy.types.PropertyGroup):
    """Properties for DaVinci Panel addon"""

    is_connected: bpy.props.BoolProperty(
        name="Panel Connected",
        description="Whether the DaVinci panel is connected",
        default=False
    )

    sensitivity: bpy.props.FloatProperty(
        name="Sensitivity",
        description="Control sensitivity multiplier",
        default=1.0,
        min=0.1,
        max=5.0
    )

    invert_x: bpy.props.BoolProperty(
        name="Invert X",
        description="Invert horizontal trackball movement",
        default=False
    )

    invert_y: bpy.props.BoolProperty(
        name="Invert Y",
        description="Invert vertical trackball movement",
        default=False
    )

class BlenderController:
    """DaVinci Micro Panel controller for Blender integration"""

    def __init__(self):
        self.panel: Optional[DaVinciMicroPanel] = None
        self.running = False
        self.timer = None

    def connect(self):
        """Connect to the DaVinci panel"""
        if not USB_AVAILABLE:
            return False, "USB libraries not available - install PyUSB"

        try:
            print("🔌 Connecting to DaVinci Micro Panel...")
            self.panel = DaVinciMicroPanel()

            if not self.panel.connect():
                return False, "Failed to connect to panel - check USB connection and permissions"

            print("✅ Panel connected and illuminated!")
            return True, "Panel connected successfully"

        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def disconnect(self):
        """Disconnect from the panel"""
        if self.panel:
            self.panel.cleanup()
            self.panel = None
            print("🔌 Panel disconnected")

    def start_monitoring(self):
        """Start input monitoring using Blender's timer system"""
        if self.panel and not self.running:
            self.running = True
            # Register a timer to check for input events
            self.timer = bpy.context.window_manager.event_timer_add(0.01, window=bpy.context.window)
            print("🎛️ Input monitoring started")
            return True
        return False

    def stop_monitoring(self):
        """Stop input monitoring"""
        if self.timer:
            bpy.context.window_manager.event_timer_remove(self.timer)
            self.timer = None
        self.running = False
        print("🛑 Input monitoring stopped")

    def process_input(self):
        """Process panel input and apply to Blender"""
        if not self.panel or not self.running:
            return

        try:
            # Get current 3D viewport
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            # Process trackball movement for viewport navigation
                            # This would be expanded with actual input processing
                            break

        except Exception as e:
            print(f"Input processing error: {e}")


class DAVINCI_OT_connect_panel(bpy.types.Operator):
    """Connect to DaVinci Micro Panel"""
    bl_idname = "davinci.connect_panel"
    bl_label = "Connect Panel"
    bl_description = "Connect to the DaVinci Micro Panel"

    def execute(self, context):
        global panel_controller

        if not USB_AVAILABLE:
            self.report({'ERROR'}, "USB libraries not available - install PyUSB")
            return {'CANCELLED'}

        if panel_controller is None:
            panel_controller = BlenderController()

        success, message = panel_controller.connect()

        if success:
            context.scene.davinci_panel.is_connected = True
            panel_controller.start_monitoring()
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}


class DAVINCI_OT_disconnect_panel(bpy.types.Operator):
    """Disconnect from DaVinci Micro Panel"""
    bl_idname = "davinci.disconnect_panel"
    bl_label = "Disconnect Panel"
    bl_description = "Disconnect from the DaVinci Micro Panel"

    def execute(self, context):
        global panel_controller

        if panel_controller:
            panel_controller.stop_monitoring()
            panel_controller.disconnect()
            context.scene.davinci_panel.is_connected = False
            self.report({'INFO'}, "Panel disconnected")

        return {'FINISHED'}


class DAVINCI_OT_install_pyusb(bpy.types.Operator):
    """Auto-install PyUSB library"""
    bl_idname = "davinci.install_pyusb"
    bl_label = "Install PyUSB"
    bl_description = "Automatically install PyUSB library using pip"

    def execute(self, context):
        self.report({'INFO'}, "Installing PyUSB... check console for progress")

        success, message = install_pyusb()

        if success:
            self.report({'INFO'}, message)
        else:
            self.report({'ERROR'}, message)

        return {'FINISHED'}


class DAVINCI_OT_test_connection(bpy.types.Operator):
    """Test DaVinci Panel connection and show debug info"""
    bl_idname = "davinci.test_connection"
    bl_label = "Test Connection"
    bl_description = "Test device connection and show debug information"

    def execute(self, context):
        # Debug information
        debug_info = []
        debug_info.append(f"USB Available: {USB_AVAILABLE}")
        debug_info.append(f"Addon Version: {bl_info['version']}")

        if USB_AVAILABLE:
            try:
                # Test device detection
                import usb.core
                device = usb.core.find(idVendor=0x1edb, idProduct=0xda0f)
                if device:
                    debug_info.append(f"✅ Device found: {device}")
                else:
                    debug_info.append("❌ Device not found")
            except Exception as e:
                debug_info.append(f"❌ USB test error: {e}")

        # Print to console
        print("\n" + "="*50)
        print("🔍 DAVINCI PANEL ADDON DEBUG INFO")
        print("="*50)
        for info in debug_info:
            print(info)
        print("="*50)

        # Show in Blender UI
        status = "✅" if USB_AVAILABLE else "❌"
        self.report({'INFO'}, f"Debug info printed to console {status}")
        return {'FINISHED'}


class DAVINCI_PT_panel(bpy.types.Panel):
    """DaVinci Panel control panel"""
    bl_label = "DaVinci Micro Panel"
    bl_idname = "DAVINCI_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Panel"

    def draw(self, context):
        layout = self.layout
        props = context.scene.davinci_panel

        # Status section
        box = layout.box()
        box.label(text="Status:", icon='CONSOLE')

        if USB_AVAILABLE:
            box.label(text="USB: ✅ Available", icon='CHECKMARK')
            box.operator("davinci.test_connection", text="Test Connection")
        else:
            box.label(text="USB: ❌ Not Available", icon='ERROR')
            row = box.row()
            row.operator("davinci.install_pyusb", text="Auto-Install PyUSB", icon='IMPORT')
            box.label(text="Or manually: pip install pyusb", icon='INFO')

        layout.separator()

        # Connection controls
        if props.is_connected:
            layout.label(text="Status: Connected ✅", icon='LINKED')
            layout.operator("davinci.disconnect_panel", icon='UNLINKED')
        else:
            layout.label(text="Status: Disconnected ❌", icon='UNLINKED')
            if USB_AVAILABLE:
                layout.operator("davinci.connect_panel", icon='LINKED')
            else:
                layout.label(text="Fix USB issues first", icon='ERROR')

        layout.separator()

        # Settings
        layout.prop(props, "sensitivity")
        layout.prop(props, "invert_x")
        layout.prop(props, "invert_y")

        layout.separator()

        # Info
        layout.label(text="Controls:")
        box = layout.box()
        box.label(text="• Left Trackball: Rotate view")
        box.label(text="• Center Trackball: Pan view")
        box.label(text="• Wheel: Zoom in/out")
        box.label(text="• Encoders: Various tools")
        box.label(text="• Buttons: Mode switching")


# Classes to register
classes = (
    DaVinciPanelProperties,
    DAVINCI_OT_connect_panel,
    DAVINCI_OT_disconnect_panel,
    DAVINCI_OT_install_pyusb,
    DAVINCI_OT_test_connection,
    DAVINCI_PT_panel,
)

def register():
    """Register the addon"""
    print("🎯 Registering DaVinci Micro Panel addon (self-contained)...")

    # Register all classes
    for cls in classes:
        bpy.utils.register_class(cls)

    # Add properties to scene
    bpy.types.Scene.davinci_panel = bpy.props.PointerProperty(type=DaVinciPanelProperties)

    print("✅ DaVinci Micro Panel addon registered successfully!")

def unregister():
    """Unregister the addon"""
    print("🔄 Unregistering DaVinci Micro Panel addon...")

    global panel_controller

    # Clean up controller if active
    if panel_controller:
        panel_controller.stop_monitoring()
        panel_controller.disconnect()
        panel_controller = None

    # Remove properties from scene
    del bpy.types.Scene.davinci_panel

    # Unregister all classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    print("✅ DaVinci Micro Panel addon unregistered")

if __name__ == "__main__":
    register()