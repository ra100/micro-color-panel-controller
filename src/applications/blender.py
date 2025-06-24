#!/usr/bin/env python3
"""
DaVinci Micro Panel → Blender Addon
Universal controller for Blender 3D navigation using the DaVinci panel
"""

bl_info = {
    "name": "DaVinci Micro Panel Controller",
    "author": "Micro Panel Project",
    "version": (1, 0, 0),
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
from typing import Optional

# Add the addon directory to sys.path to import our modules
addon_dir = os.path.dirname(__file__)
if addon_dir not in sys.path:
    sys.path.insert(0, os.path.join(addon_dir, '..', '..'))

try:
    from src.core.device import DaVinciMicroPanel
    from davinci_panel_controls import ENCODER_BUTTONS, FUNCTION_BUTTONS, TRACKBALL_AXES
    DEVICE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ DaVinci Panel device import failed: {e}")
    DEVICE_AVAILABLE = False

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
        if not DEVICE_AVAILABLE:
            return False, "Device driver not available"

        try:
            print("🔌 Connecting to DaVinci Micro Panel...")
            self.panel = DaVinciMicroPanel()

            if not self.panel.connect():
                return False, "Failed to connect to panel"

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

        if not DEVICE_AVAILABLE:
            self.report({'ERROR'}, "DaVinci Panel device driver not available")
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

        # Connection status
        if props.is_connected:
            layout.label(text="Status: Connected ✅", icon='LINKED')
            layout.operator("davinci.disconnect_panel", icon='UNLINKED')
        else:
            layout.label(text="Status: Disconnected ❌", icon='UNLINKED')
            layout.operator("davinci.connect_panel", icon='LINKED')

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


# Modal operator for handling panel input
class DAVINCI_OT_panel_modal(bpy.types.Operator):
    """Modal operator for DaVinci panel input handling"""
    bl_idname = "davinci.panel_modal"
    bl_label = "DaVinci Panel Input Handler"

    def modal(self, context, event):
        global panel_controller

        if event.type == 'TIMER' and panel_controller:
            panel_controller.process_input()

        if not (panel_controller and panel_controller.running):
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        if panel_controller and panel_controller.running:
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        return {'CANCELLED'}

# Classes to register
classes = (
    DaVinciPanelProperties,
    DAVINCI_OT_connect_panel,
    DAVINCI_OT_disconnect_panel,
    DAVINCI_PT_panel,
    DAVINCI_OT_panel_modal,
)

def register():
    """Register the addon"""
    print("🎯 Registering DaVinci Micro Panel addon...")

    # Register all classes
    for cls in classes:
        bpy.utils.register_class(cls)

    # Add properties to scene
    bpy.types.Scene.davinci_panel = bpy.props.PointerProperty(type=DaVinciPanelProperties)

    print("✅ DaVinci Micro Panel addon registered")

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

# For running as standalone script (development/testing)
def main():
    """Main entry point for standalone execution"""
    print("🎯 DaVinci Micro Panel → Blender Development Mode")
    print("🔗 For addon installation, use Blender's addon preferences")
    print()

    if DEVICE_AVAILABLE:
        print("✅ Device driver available")
        controller = BlenderController()
        success, message = controller.connect()
        print(f"Connection test: {message}")
        if success:
            controller.disconnect()
    else:
        print("❌ Device driver not available")
        print("   Make sure the micro-panel project is in the Python path")

if __name__ == "__main__":
    main()