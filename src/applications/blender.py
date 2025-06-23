"""
Blender Integration for DaVinci Micro Panel

This module provides integration with Blender, allowing the panel to control:
- Viewport navigation (rotation, panning, zoom)
- Timeline playback
- Object transformation
- Material/shader parameters
- Rendering controls

Note: This requires Blender's Python API (bpy) which is only available when
running inside Blender or with a properly configured Blender Python environment.
"""

try:
    import bpy
    import bmesh
    from mathutils import Vector, Euler
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print("Blender API not available. This module only works inside Blender.")

import math
import time
import threading
import sys
import os
from typing import Dict, Callable, Any, Optional
from enum import Enum

# Handle imports for both direct execution and module import
if __name__ == "__main__":
    # When run directly, add parent directories to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    sys.path.insert(0, project_root)
    from src.core.device import MicroPanel, PanelEvent, EventType
else:
    # When imported as module
    from ..core.device import MicroPanel, PanelEvent, EventType


class BlenderMode(Enum):
    """Different modes for panel operation in Blender"""
    VIEWPORT = "viewport"      # Viewport navigation
    TIMELINE = "timeline"      # Animation timeline control
    MODELING = "modeling"      # Modeling tools
    SHADING = "shading"        # Material/shader editing
    RENDERING = "rendering"    # Render settings


class BlenderController:
    """
    Main controller for Blender integration with DaVinci Micro Panel
    """

    def __init__(self, panel: MicroPanel):
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender API not available")

        self.panel = panel
        self.mode = BlenderMode.VIEWPORT
        self.running = False

        # Control sensitivity settings
        self.rotation_sensitivity = 0.01
        self.pan_sensitivity = 0.1
        self.zoom_sensitivity = 0.1
        self.timeline_sensitivity = 1.0

        # State tracking
        self.current_frame = 1
        self.is_playing = False

        # Control mappings for different modes
        self.control_mappings = {
            BlenderMode.VIEWPORT: self._setup_viewport_mappings(),
            BlenderMode.TIMELINE: self._setup_timeline_mappings(),
            BlenderMode.MODELING: self._setup_modeling_mappings(),
            BlenderMode.SHADING: self._setup_shading_mappings(),
        }

        # Button illumination indicates panel activity
        self.illumination_active = False

    def start(self):
        """Start the Blender controller"""
        if not self.panel.connected:
            raise RuntimeError("Panel not connected")

        self.running = True
        self.panel.start_reading(self._on_panel_event)
        self._update_button_illumination()
        print(f"Blender controller started in {self.mode.value} mode")

    def stop(self):
        """Stop the Blender controller"""
        self.running = False
        self.panel.stop_reading()
        self.panel.reset_panel()
        print("Blender controller stopped")

    def set_mode(self, mode: BlenderMode):
        """Change the current operating mode"""
        self.mode = mode
        self._update_button_illumination()
        print(f"Switched to {mode.value} mode")

    def _on_panel_event(self, event: PanelEvent):
        """Handle events from the panel"""
        if not self.running:
            return

        try:
            # Get the current mode's control mappings
            mappings = self.control_mappings.get(self.mode, {})

            # Find the appropriate handler for this event
            handler_key = f"{event.type.value}_{event.id}"
            if handler_key in mappings:
                handler = mappings[handler_key]
                handler(event)
            else:
                # Handle global controls (mode switching, etc.)
                self._handle_global_event(event)

        except Exception as e:
            print(f"Error handling panel event: {e}")

    def _handle_global_event(self, event: PanelEvent):
        """Handle global events that work in all modes"""
        if event.type == EventType.BUTTON and event.pressed:
            # Mode switching buttons (using button IDs 20-23)
            if event.id == 20:
                self.set_mode(BlenderMode.VIEWPORT)
            elif event.id == 21:
                self.set_mode(BlenderMode.TIMELINE)
            elif event.id == 22:
                self.set_mode(BlenderMode.MODELING)
            elif event.id == 23:
                self.set_mode(BlenderMode.SHADING)

    def _update_button_illumination(self):
        """Update button illumination to indicate panel activity"""
        # Turn on button illumination when panel is active
        self.illumination_active = True
        self.panel.set_button_illumination(True)

    # ==================== VIEWPORT MODE ====================

    def _setup_viewport_mappings(self) -> Dict[str, Callable]:
        """Setup control mappings for viewport navigation mode"""
        return {
            'rotary_0': self._viewport_rotate_x,
            'rotary_1': self._viewport_rotate_y,
            'rotary_2': self._viewport_rotate_z,
            'rotary_3': self._viewport_zoom,
            'trackball_0': self._viewport_pan,
            'trackball_1': self._viewport_orbit,
            'button_0': self._viewport_reset_view,
            'button_1': self._viewport_frame_selected,
        }

    def _viewport_rotate_x(self, event: PanelEvent):
        """Rotate viewport around X axis"""
        if not hasattr(bpy.context, 'region_data'):
            return

        region_data = bpy.context.region_data
        if region_data:
            # Apply rotation delta
            rotation = event.delta * self.rotation_sensitivity
            # This is a simplified example - real implementation would use proper matrix math
            bpy.ops.view3d.rotate(delta=rotation, axis=(1, 0, 0))

    def _viewport_rotate_y(self, event: PanelEvent):
        """Rotate viewport around Y axis"""
        if bpy.context.region_data:
            rotation = event.delta * self.rotation_sensitivity
            bpy.ops.view3d.rotate(delta=rotation, axis=(0, 1, 0))

    def _viewport_rotate_z(self, event: PanelEvent):
        """Rotate viewport around Z axis"""
        if bpy.context.region_data:
            rotation = event.delta * self.rotation_sensitivity
            bpy.ops.view3d.rotate(delta=rotation, axis=(0, 0, 1))

    def _viewport_zoom(self, event: PanelEvent):
        """Zoom viewport in/out"""
        zoom_factor = 1.0 + (event.delta * self.zoom_sensitivity * 0.01)
        bpy.ops.view3d.zoom(delta=zoom_factor)

    def _viewport_pan(self, event: PanelEvent):
        """Pan viewport using trackball"""
        if event.x_delta != 0 or event.y_delta != 0:
            # Convert trackball movement to pan
            pan_x = event.x_delta * self.pan_sensitivity
            pan_y = event.y_delta * self.pan_sensitivity
            bpy.ops.view3d.move(delta=(pan_x, pan_y))

    def _viewport_orbit(self, event: PanelEvent):
        """Orbit around object using trackball"""
        if event.x_delta != 0 or event.y_delta != 0:
            # Convert to rotation
            rot_x = event.y_delta * self.rotation_sensitivity
            rot_z = event.x_delta * self.rotation_sensitivity
            bpy.ops.view3d.rotate(delta=rot_x, axis=(1, 0, 0))
            bpy.ops.view3d.rotate(delta=rot_z, axis=(0, 0, 1))

    def _viewport_reset_view(self, event: PanelEvent):
        """Reset viewport to default view"""
        if event.pressed:
            bpy.ops.view3d.view_all()

    def _viewport_frame_selected(self, event: PanelEvent):
        """Frame selected objects in viewport"""
        if event.pressed:
            bpy.ops.view3d.view_selected()

    # ==================== TIMELINE MODE ====================

    def _setup_timeline_mappings(self) -> Dict[str, Callable]:
        """Setup control mappings for timeline control mode"""
        return {
            'rotary_0': self._timeline_scrub,
            'rotary_1': self._timeline_zoom,
            'button_0': self._timeline_play_pause,
            'button_1': self._timeline_goto_start,
            'button_2': self._timeline_goto_end,
            'button_3': self._timeline_next_keyframe,
            'button_4': self._timeline_prev_keyframe,
        }

    def _timeline_scrub(self, event: PanelEvent):
        """Scrub through timeline"""
        frame_delta = event.delta * self.timeline_sensitivity
        new_frame = max(1, bpy.context.scene.frame_current + frame_delta)
        bpy.context.scene.frame_set(int(new_frame))

    def _timeline_zoom(self, event: PanelEvent):
        """Zoom timeline view"""
        # This would require more complex timeline manipulation
        pass

    def _timeline_play_pause(self, event: PanelEvent):
        """Toggle timeline playback"""
        if event.pressed:
            if bpy.context.screen.is_animation_playing:
                bpy.ops.screen.animation_cancel()
                # Button illumination stays on during active control
            else:
                bpy.ops.screen.animation_play()
                # Button illumination indicates panel activity

    def _timeline_goto_start(self, event: PanelEvent):
        """Go to start of timeline"""
        if event.pressed:
            bpy.context.scene.frame_set(bpy.context.scene.frame_start)

    def _timeline_goto_end(self, event: PanelEvent):
        """Go to end of timeline"""
        if event.pressed:
            bpy.context.scene.frame_set(bpy.context.scene.frame_end)

    def _timeline_next_keyframe(self, event: PanelEvent):
        """Jump to next keyframe"""
        if event.pressed:
            bpy.ops.screen.keyframe_jump(next=True)

    def _timeline_prev_keyframe(self, event: PanelEvent):
        """Jump to previous keyframe"""
        if event.pressed:
            bpy.ops.screen.keyframe_jump(next=False)

    # ==================== MODELING MODE ====================

    def _setup_modeling_mappings(self) -> Dict[str, Callable]:
        """Setup control mappings for modeling mode"""
        return {
            'rotary_0': self._modeling_extrude,
            'rotary_1': self._modeling_inset,
            'rotary_2': self._modeling_bevel,
            'button_0': self._modeling_toggle_edit,
            'button_1': self._modeling_select_all,
            'button_2': self._modeling_delete,
        }

    def _modeling_extrude(self, event: PanelEvent):
        """Control extrude amount"""
        if bpy.context.mode == 'EDIT_MESH':
            # This is a simplified example
            extrude_amount = event.delta * 0.01
            bpy.ops.mesh.extrude_region_move(
                TRANSFORM_OT_translate={"value": (0, 0, extrude_amount)}
            )

    def _modeling_inset(self, event: PanelEvent):
        """Control inset faces"""
        if event.delta != 0 and bpy.context.mode == 'EDIT_MESH':
            inset_amount = abs(event.delta) * 0.01
            bpy.ops.mesh.inset_faces(thickness=inset_amount)

    def _modeling_bevel(self, event: PanelEvent):
        """Control bevel"""
        if event.delta != 0 and bpy.context.mode == 'EDIT_MESH':
            bevel_amount = abs(event.delta) * 0.01
            bpy.ops.mesh.bevel(offset=bevel_amount)

    def _modeling_toggle_edit(self, event: PanelEvent):
        """Toggle edit mode"""
        if event.pressed:
            if bpy.context.mode == 'EDIT_MESH':
                bpy.ops.object.mode_set(mode='OBJECT')
            else:
                bpy.ops.object.mode_set(mode='EDIT')

    def _modeling_select_all(self, event: PanelEvent):
        """Select all"""
        if event.pressed:
            bpy.ops.mesh.select_all(action='SELECT')

    def _modeling_delete(self, event: PanelEvent):
        """Delete selected"""
        if event.pressed:
            bpy.ops.mesh.delete(type='VERT')

    # ==================== SHADING MODE ====================

    def _setup_shading_mappings(self) -> Dict[str, Callable]:
        """Setup control mappings for shading/material mode"""
        return {
            'rotary_0': self._shading_roughness,
            'rotary_1': self._shading_metallic,
            'rotary_2': self._shading_emission,
            'rotary_3': self._shading_subsurface,
        }

    def _shading_roughness(self, event: PanelEvent):
        """Control material roughness"""
        self._adjust_material_property('Roughness', event.delta * 0.01)

    def _shading_metallic(self, event: PanelEvent):
        """Control material metallic value"""
        self._adjust_material_property('Metallic', event.delta * 0.01)

    def _shading_emission(self, event: PanelEvent):
        """Control material emission strength"""
        self._adjust_material_property('Emission Strength', event.delta * 0.1)

    def _shading_subsurface(self, event: PanelEvent):
        """Control subsurface scattering"""
        self._adjust_material_property('Subsurface', event.delta * 0.01)

    def _adjust_material_property(self, property_name: str, delta: float):
        """Helper to adjust material properties"""
        obj = bpy.context.active_object
        if not obj or not obj.active_material:
            return

        material = obj.active_material
        if material.use_nodes:
            # Find the Principled BSDF node
            for node in material.node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    if property_name in node.inputs:
                        current_value = node.inputs[property_name].default_value
                        new_value = max(0, min(1, current_value + delta))
                        node.inputs[property_name].default_value = new_value
                        break


# Blender Addon Integration
if BLENDER_AVAILABLE:

    bl_info = {
        "name": "DaVinci Micro Panel Control",
        "author": "DaVinci Panel Project",
        "version": (1, 0, 0),
        "blender": (3, 0, 0),
        "location": "View3D > Sidebar > Panel",
        "description": "Control Blender with DaVinci Micro Panel",
        "category": "3D View",
    }

    class PANEL_OT_connect(bpy.types.Operator):
        """Connect to DaVinci Panel"""
        bl_idname = "panel.connect"
        bl_label = "Connect Panel"

        def execute(self, context):
            try:
                panel = MicroPanel()
                if panel.connect():
                    context.scene.panel_controller = BlenderController(panel)
                    context.scene.panel_controller.start()
                    self.report({'INFO'}, "Panel connected successfully")
                else:
                    self.report({'ERROR'}, "Failed to connect to panel")
            except Exception as e:
                self.report({'ERROR'}, f"Error: {str(e)}")
            return {'FINISHED'}

    class PANEL_OT_disconnect(bpy.types.Operator):
        """Disconnect from DaVinci Panel"""
        bl_idname = "panel.disconnect"
        bl_label = "Disconnect Panel"

        def execute(self, context):
            if hasattr(context.scene, 'panel_controller'):
                context.scene.panel_controller.stop()
                delattr(context.scene, 'panel_controller')
                self.report({'INFO'}, "Panel disconnected")
            return {'FINISHED'}

    class PANEL_PT_main(bpy.types.Panel):
        """Main panel UI"""
        bl_label = "DaVinci Panel Control"
        bl_idname = "PANEL_PT_main"
        bl_space_type = 'VIEW_3D'
        bl_region_type = 'UI'
        bl_category = "Panel"

        def draw(self, context):
            layout = self.layout

            if hasattr(context.scene, 'panel_controller'):
                layout.operator("panel.disconnect")

                controller = context.scene.panel_controller
                layout.label(text=f"Mode: {controller.mode.value}")

                # Mode selection
                row = layout.row()
                row.scale_y = 1.5
                col = row.column()
                col.operator("panel.set_mode", text="Viewport").mode = "VIEWPORT"
                col = row.column()
                col.operator("panel.set_mode", text="Timeline").mode = "TIMELINE"

            else:
                layout.operator("panel.connect")

    def register():
        bpy.utils.register_class(PANEL_OT_connect)
        bpy.utils.register_class(PANEL_OT_disconnect)
        bpy.utils.register_class(PANEL_PT_main)

    def unregister():
        bpy.utils.unregister_class(PANEL_PT_main)
        bpy.utils.unregister_class(PANEL_OT_disconnect)
        bpy.utils.unregister_class(PANEL_OT_connect)


# Standalone usage (when running outside Blender addon system)
def demo_mode():
    """Demo mode for testing panel without Blender"""
    print("🎛️  DaVinci Micro Panel - Demo Mode")
    print("="*50)
    print("Running outside Blender - showing panel events only")
    print("This demonstrates panel connectivity and control detection.")
    print("")

    # Connect to panel
    panel = MicroPanel()
    if not panel.connect():
        print("❌ Failed to connect to DaVinci Panel")
        print("Make sure the panel is connected and you have permissions.")
        return

    print("✅ DaVinci Panel connected successfully!")
    print("")
    print("Panel Information:")
    info = panel.get_device_info()
    for key, value in info.items():
        print(f"  {key.capitalize()}: {value}")
    print("")

    print("🎮 Panel Controls Detected:")
    print("  • 15 Rotary encoders (12 main + 3 trackball wheels)")
    print("  • 52 Buttons (12 rotary buttons + 40 function buttons)")
    print("  • 3 Trackballs for X/Y movement")
    print("")
    print("Try moving controls to see events...")
    print("Press Ctrl+C to exit")
    print("")

    def demo_event_handler(event):
        """Handle events in demo mode"""
        timestamp = time.strftime("%H:%M:%S", time.localtime(event.timestamp))

        if event.type == EventType.ROTARY:
            direction = "↻" if event.delta > 0 else "↺"
            print(f"[{timestamp}] 🔄 Rotary #{event.id:2d}: {direction} Delta: {event.delta:+3d}")

        elif event.type == EventType.BUTTON:
            state = "🔴 PRESS" if event.pressed else "⚪ RELEASE"
            print(f"[{timestamp}] 🔘 Button #{event.id:2d}: {state}")

        elif event.type == EventType.TRACKBALL:
            if event.x_delta != 0 or event.y_delta != 0:
                print(f"[{timestamp}] 🏀 Trackball #{event.trackball_id}: X:{event.x_delta:+3d} Y:{event.y_delta:+3d}")

    # Start reading events
    panel.start_reading(demo_event_handler)

    # Test button illumination control
    print("Testing button illumination...")
    for i in range(3):
        panel.set_button_illumination(True)
        time.sleep(0.4)
        panel.set_button_illumination(False)
        time.sleep(0.4)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        panel.disconnect()
        print("✅ Panel disconnected")

def main():
    """Main function for standalone usage"""
    if not BLENDER_AVAILABLE:
        print("⚠️  Blender API not available")
        print("Running in demo mode instead...")
        print("")
        demo_mode()
        return

    # Connect to panel
    panel = MicroPanel()
    if not panel.connect():
        print("Failed to connect to DaVinci Panel")
        return

    # Create and start controller
    controller = BlenderController(panel)
    controller.start()

    print("DaVinci Panel connected to Blender!")
    print("Controls:")
    print("  Rotary 0-2: Rotate viewport X/Y/Z")
    print("  Rotary 3: Zoom")
    print("  Trackballs: Pan and orbit")
    print("  Buttons 20-23: Switch modes")
    print("Press Ctrl+C to exit...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        controller.stop()
        panel.disconnect()


if __name__ == "__main__":
    main()