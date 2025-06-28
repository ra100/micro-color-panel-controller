#!/usr/bin/env python3
"""
DaVinci Micro Panel → Blender Addon
Universal controller for Blender 3D navigation using the DaVinci panel
Uses device_control module for USB interface
"""

bl_info = {
    "name": "DaVinci Micro Panel Controller",
    "author": "Micro Panel Project",
    "version": (1, 3, 0),
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
from typing import Optional, Callable, Dict, Any

# Import device control module
try:
    from . import device_control
    USB_AVAILABLE = device_control.USB_AVAILABLE
    print("✅ Device control module imported successfully")
except ImportError as e:
    print(f"⚠️ Device control module not available: {e}")
    USB_AVAILABLE = False
    device_control = None

def install_pyusb():
    """Auto-install PyUSB using pip to Blender's Python"""
    import subprocess
    import sys
    import os

    try:
        print("📦 Installing PyUSB to Blender's Python...")
        print(f"Blender Python: {sys.executable}")

        # Use Blender's Python executable directly
        blender_python = sys.executable

        # Try multiple installation methods
        install_commands = [
            # Method 1: Use Blender's Python with -m pip
            [blender_python, '-m', 'pip', 'install', 'pyusb'],
            # Method 2: Use Blender's Python with ensurepip first
            [blender_python, '-m', 'ensurepip', '--default-pip'],
            # Method 3: Try system pip with --target to Blender's site-packages
        ]

        # Get Blender's site-packages directory
        import site
        blender_site_packages = site.getsitepackages()
        if blender_site_packages:
            target_dir = blender_site_packages[0]
            print(f"Target directory: {target_dir}")
            # Add targeted installation as fallback
            for pip_cmd in ['pip', 'pip3']:
                install_commands.append([pip_cmd, 'install', 'pyusb', '--target', target_dir])

        # Try each installation method
        for i, cmd in enumerate(install_commands):
            try:
                print(f"Trying installation method {i+1}: {' '.join(cmd)}")

                if i == 1:  # ensurepip step
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        print("✅ pip ensured, now installing PyUSB...")
                        # Now try to install PyUSB
                        cmd = [blender_python, '-m', 'pip', 'install', 'pyusb']
                    else:
                        continue

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                if result.returncode == 0:
                    print("✅ PyUSB installed successfully!")
                    print(f"Output: {result.stdout}")

                    # Test if import works now
                    try:
                        test_result = subprocess.run([blender_python, '-c', 'import usb.core; print("Import test: OK")'],
                                                   capture_output=True, text=True, timeout=10)
                        if test_result.returncode == 0 and "Import test: OK" in test_result.stdout:
                            print("✅ Import test successful!")
                            print("🔄 Please restart Blender to use the USB functionality")
                            return True, "PyUSB installed successfully - restart Blender"
                        else:
                            print(f"⚠️ Import test failed: {test_result.stderr}")
                    except:
                        pass

                    return True, "PyUSB installed - restart Blender and check again"
                else:
                    error_msg = result.stderr or result.stdout or "Unknown error"
                    print(f"Method {i+1} failed: {error_msg}")
                    continue

            except subprocess.TimeoutExpired:
                print(f"Method {i+1} timed out")
                continue
            except Exception as e:
                print(f"Method {i+1} error: {e}")
                continue

        return False, "All installation methods failed - try manual installation"

    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False, f"Installation error: {str(e)}"

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
        default=0.1,
        min=0.001,
        max=0.5
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

    debug_mode: bpy.props.BoolProperty(
        name="Debug Output",
        description="Enable verbose debug output in console",
        default=False
    )

class BlenderController:
    """DaVinci Micro Panel controller for Blender integration"""

    def __init__(self):
        self.panel: Optional[device_control.DaVinciMicroPanel] = None
        self.processor: Optional[device_control.InputProcessor] = None
        self.running = False
        self.timer = None
        self.initial_view_matrix = None  # Store initial view state

    def connect(self):
        """Connect to the DaVinci panel"""
        if not USB_AVAILABLE or not device_control:
            return False, "Device control module not available - install PyUSB"

        try:
            print("🔌 Connecting to DaVinci Micro Panel...")
            self.panel = device_control.DaVinciMicroPanel()
            self.processor = device_control.InputProcessor()

            if not self.panel.connect():
                return False, "Failed to connect to panel - check USB connection and permissions"

            # Set up input processing callbacks
            self.processor.set_callbacks(
                trackball_cb=self.handle_trackball_input,
                button_cb=self.handle_button_input,
                encoder_cb=self.handle_encoder_input
            )

            print("✅ Panel connected and illuminated!")
            return True, "Panel connected successfully"

        except Exception as e:
            return False, f"Connection error: {str(e)}"

    def disconnect(self):
        """Disconnect from the panel"""
        if self.panel:
            self.panel.cleanup()
            self.panel = None
        if self.processor:
            self.processor = None
        print("🔌 Panel disconnected")

    def start_monitoring(self):
        """Start input monitoring using Blender's timer system"""
        if self.panel and not self.running:
            self.running = True

            # Store initial view state to prevent jumping
            self._store_initial_view_state()

            # Register a timer to check for input events (slower for stability)
            self.timer = bpy.context.window_manager.event_timer_add(0.02, window=bpy.context.window)
            print("🎛️ Input monitoring started")
            print("🔍 Move trackballs or press buttons to see input...")

            # Start the modal operator to handle timer events
            bpy.ops.davinci.panel_modal()
            return True
        return False

    def stop_monitoring(self):
        """Stop input monitoring"""
        if self.timer:
            bpy.context.window_manager.event_timer_remove(self.timer)
            self.timer = None
        self.running = False
        print("🛑 Input monitoring stopped")

    def _store_initial_view_state(self):
        """Store the initial view state to prevent jumping"""
        try:
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    rv3d = area.spaces[0].region_3d
                    self.initial_view_matrix = rv3d.view_matrix.copy()
                    break
        except Exception as e:
            print(f"⚠️ Could not store initial view state: {e}")

    def process_input(self):
        """Process panel input and apply to Blender"""
        if not self.panel or not self.processor or not self.running:
            return

        try:
            # Read input from panel
            data = self.panel.read_input()
            if data:
                # Get user preferences
                props = bpy.context.scene.davinci_panel
                sensitivity = props.sensitivity
                invert_x = props.invert_x
                invert_y = props.invert_y
                debug_mode = props.debug_mode

                # Process with user-controlled debug output
                self.processor.process_input_data(
                    data, sensitivity, invert_x, invert_y, debug=debug_mode
                )

        except Exception as e:
            print(f"Input processing error: {e}")

    def handle_trackball_input(self, trackball_data):
        """Handle trackball input from the input processor"""
        try:
            # LEFT trackball: Rotate viewport
            if 'left_trackball' in trackball_data:
                left = trackball_data['left_trackball']
                self.rotate_viewport_smooth(left['x'], left['y'])

            # CENTER trackball: Pan viewport
            if 'center_trackball' in trackball_data:
                center = trackball_data['center_trackball']
                self.pan_viewport_smooth(center['x'], center['y'])

            # Wheel: Zoom viewport
            if 'wheel' in trackball_data:
                wheel = trackball_data['wheel']
                self.zoom_viewport_smooth(wheel['delta'])

        except Exception as e:
            print(f"Error handling trackball input: {e}")

    def rotate_viewport_smooth(self, delta_x, delta_y):
        """Orbit viewport around object center with reduced sensitivity"""
        try:
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    rv3d = area.spaces[0].region_3d

                    # Much lower rotation sensitivity for smoother orbiting
                    rotation_speed = 0.02  # Reduced from 0.5 to 0.02

                    # Find center point to orbit around
                    orbit_center = Vector((0, 0, 0))  # Default to world origin

                    # Use selected object center if available
                    if bpy.context.selected_objects:
                        active_obj = bpy.context.active_object
                        if active_obj:
                            orbit_center = active_obj.location.copy()
                        else:
                            # Use center of selected objects
                            locations = [obj.location for obj in bpy.context.selected_objects]
                            orbit_center = sum(locations, Vector()) / len(locations)

                    rotation_applied = False

                    # Apply horizontal rotation (around Z-axis)
                    if abs(delta_x) > 0.01:
                        # Create rotation matrix around world Z-axis
                        rot_z = Matrix.Rotation(-delta_x * rotation_speed, 4, 'Z')

                        # Translate to origin, rotate, translate back
                        self._orbit_around_point(rv3d, rot_z, orbit_center)
                        rotation_applied = True

                    # Apply vertical rotation (around view's right axis)
                    if abs(delta_y) > 0.01:
                        # Get view right vector for vertical rotation
                        view_matrix = rv3d.view_matrix.copy()
                        right_vec = Vector(view_matrix[0][:3]).normalized()

                        # Create rotation matrix around right axis
                        rot_right = Matrix.Rotation(-delta_y * rotation_speed, 4, right_vec)

                        # Apply orbit rotation
                        self._orbit_around_point(rv3d, rot_right, orbit_center)
                        rotation_applied = True

                    if rotation_applied:
                        area.tag_redraw()
                    break

        except Exception as e:
            print(f"Error rotating viewport: {e}")

    def _orbit_around_point(self, rv3d, rotation_matrix, center_point):
        """Helper to orbit the view around a specific point"""
        try:
            # Get current view location and target point
            view_location = rv3d.view_location.copy()

            # Calculate vector from center to view location
            to_view = view_location - center_point

            # Convert to 4D vector for matrix multiplication
            to_view_4d = Vector((to_view.x, to_view.y, to_view.z, 0.0))

            # Apply rotation to this vector
            rotated_4d = rotation_matrix @ to_view_4d

            # Convert back to 3D vector
            rotated_to_view = Vector((rotated_4d.x, rotated_4d.y, rotated_4d.z))

            # Set new view location
            rv3d.view_location = center_point + rotated_to_view

            # Also rotate the view matrix to maintain orientation
            rv3d.view_matrix = rotation_matrix @ rv3d.view_matrix

        except Exception as e:
            print(f"Error in orbit calculation: {e}")

    def pan_viewport_smooth(self, delta_x, delta_y):
        """Improved 3D viewport panning"""
        try:
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    rv3d = area.spaces[0].region_3d

                    # Get current view matrix
                    view_matrix = rv3d.view_matrix.copy()

                    # Extract view vectors and convert to Vector objects
                    right_vec = Vector(view_matrix[0][:3]).normalized()
                    up_vec = Vector(view_matrix[1][:3]).normalized()

                    # Calculate pan factor based on view distance
                    pan_factor = rv3d.view_distance * 0.0001

                    pan_applied = False

                    # Pan horizontally (right vector)
                    if abs(delta_x) > 0.01:
                        rv3d.view_location += right_vec * delta_x * pan_factor
                        pan_applied = True

                    # Pan vertically (up vector)
                    if abs(delta_y) > 0.01:
                        rv3d.view_location += up_vec * delta_y * pan_factor
                        pan_applied = True

                    if pan_applied:
                        area.tag_redraw()
                    break

        except Exception as e:
            print(f"Error panning viewport: {e}")

    def zoom_viewport_smooth(self, delta):
        """Improved 3D viewport zooming with better sensitivity"""
        try:
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    rv3d = area.spaces[0].region_3d

                    if abs(delta) > 0.01:
                        # More gradual zoom factor
                        zoom_factor = 1.0 + (delta * 0.02)  # Reduced sensitivity

                        # Apply zoom
                        new_distance = rv3d.view_distance * zoom_factor

                        # Clamp zoom to reasonable limits
                        rv3d.view_distance = max(0.01, min(1000.0, new_distance))

                        area.tag_redraw()
                    break

        except Exception as e:
            print(f"Error zooming viewport: {e}")

    def handle_button_input(self, button_data):
        """Handle button input from the input processor"""
        try:
            if 'buttons' in button_data:
                for button_id in button_data['buttons']:
                    self.execute_button_action(button_id)
        except Exception as e:
            print(f"Error handling button input: {e}")

    def execute_button_action(self, button_id):
        """Execute action for specific button ID"""
        try:
            # Map common buttons to Blender operations
            button_actions = {
                20: lambda: self.select_all_toggle(),          # AUTO_COLOR -> Select All
                22: lambda: bpy.ops.view3d.copybuffer(),       # COPY
                23: lambda: bpy.ops.view3d.pastebuffer(),      # PASTE
                24: lambda: bpy.ops.ed.undo(),                 # UNDO
                25: lambda: bpy.ops.ed.redo(),                 # REDO
                26: lambda: bpy.ops.object.delete(),           # DELETE
                34: lambda: bpy.ops.screen.animation_play(),   # PLAY_STILL -> Play Animation
                59: lambda: bpy.ops.screen.animation_cancel(), # STOP -> Stop Animation
                39: lambda: self.cycle_viewport_shading(),     # CURSOR -> Cycle Viewport Shading
            }

            if button_id in button_actions:
                print(f"🔘 Button {button_id} pressed")
                button_actions[button_id]()
            else:
                print(f"🔘 Unmapped button {button_id} pressed")

        except Exception as e:
            print(f"Error handling button press {button_id}: {e}")

    def handle_encoder_input(self, encoder_data):
        """Handle encoder input from the input processor"""
        try:
            # TODO: Implement encoder actions
            print(f"🔄 Encoder input received")
        except Exception as e:
            print(f"Error handling encoder input: {e}")

    def select_all_toggle(self):
        """Toggle select all/none"""
        try:
            if bpy.context.mode == 'OBJECT':
                if bpy.context.selected_objects:
                    bpy.ops.object.select_all(action='DESELECT')
                else:
                    bpy.ops.object.select_all(action='SELECT')
        except:
            pass

    def cycle_viewport_shading(self):
        """Cycle through viewport shading modes"""
        try:
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    shading = area.spaces[0].shading
                    modes = ['WIREFRAME', 'SOLID', 'MATERIAL', 'RENDERED']
                    current_idx = modes.index(shading.type) if shading.type in modes else 0
                    next_idx = (current_idx + 1) % len(modes)
                    shading.type = modes[next_idx]
                    area.tag_redraw()
                    print(f"🎨 Viewport shading: {modes[next_idx]}")
                    break
        except Exception as e:
            print(f"Error cycling viewport shading: {e}")


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
    bl_description = "Automatically install PyUSB library to Blender's Python"

    def execute(self, context):
        self.report({'INFO'}, "Installing PyUSB to Blender's Python... check console for progress")

        success, message = install_pyusb()

        if success:
            self.report({'INFO'}, message)
        else:
            self.report({'ERROR'}, message)

        return {'FINISHED'}


class DAVINCI_OT_show_python_info(bpy.types.Operator):
    """Show Blender's Python information"""
    bl_idname = "davinci.show_python_info"
    bl_label = "Python Info"
    bl_description = "Show Blender's Python path and manual installation command"

    def execute(self, context):
        import sys
        import site

        # Print Python info to console
        print("\n" + "="*60)
        print("🐍 BLENDER PYTHON INFORMATION")
        print("="*60)
        print(f"Python executable: {sys.executable}")
        print(f"Python version: {sys.version}")
        print(f"Site packages: {site.getsitepackages()}")
        print("\n💡 MANUAL INSTALLATION COMMANDS:")
        print(f"   {sys.executable} -m pip install pyusb")
        print("   OR")
        print("   pip install pyusb --target {site.getsitepackages()[0] if site.getsitepackages() else 'SITE_PACKAGES'}")
        print("="*60)

        self.report({'INFO'}, "Python info printed to console")
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

        if USB_AVAILABLE and device_control:
            try:
                # Test device detection using device_control module
                test_panel = device_control.DaVinciMicroPanel()
                if test_panel.connect():
                    debug_info.append(f"✅ Device found and connected successfully")
                    test_panel.cleanup()
                else:
                    debug_info.append("❌ Device not found or connection failed")
            except Exception as e:
                debug_info.append(f"❌ Device test error: {e}")
        elif not device_control:
            debug_info.append("❌ Device control module not available")

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


class DAVINCI_OT_panel_modal(bpy.types.Operator):
    """Modal operator for DaVinci panel input handling"""
    bl_idname = "davinci.panel_modal"
    bl_label = "DaVinci Panel Input Handler"

    def modal(self, context, event):
        global panel_controller

        if event.type == 'TIMER' and panel_controller and panel_controller.running:
            # Process input from panel
            panel_controller.process_input()

        # Continue running while controller is active
        if panel_controller and panel_controller.running:
            return {'PASS_THROUGH'}
        else:
            return {'FINISHED'}

    def execute(self, context):
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


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
            row = box.row()
            row.operator("davinci.show_python_info", text="Python Info", icon='CONSOLE')
            box.label(text="Check console for manual commands", icon='INFO')

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
        layout.prop(props, "debug_mode")

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
    DAVINCI_OT_show_python_info,
    DAVINCI_OT_test_connection,
    DAVINCI_OT_panel_modal,
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