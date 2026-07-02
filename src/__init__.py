# __init__.py
import bpy

from . import ui, operators, utils


# Addon property group
class AddonReloaderPropertyGroup(bpy.types.PropertyGroup):
    addon_state: bpy.props.BoolProperty(
        name="Addon Status",
        description="Status of the addon",
        default=False,
        options={'SKIP_SAVE'},
    )  # type: ignore


# Addon preferences
class AddonReloaderPreferences(bpy.types.AddonPreferences):
    """Addon Preferences"""
    bl_idname = __package__

    last_selected_addon: bpy.props.StringProperty(
        name="Last Selected",
        description="Remember the last selected addon module name across sessions",
        default="",
        options={'HIDDEN'},
    )  # type: ignore

    last_selected_name: bpy.props.StringProperty(
        name="Last Selected",
        description="",
        default="",
    )  # type: ignore

    def draw(self, context):
        layout = self.layout

        # Last selected addon (read-only)
        row = layout.row()
        row.enabled = False
        row.prop(self, "last_selected_name")


# Addon classes list
classes = (
    AddonReloaderPropertyGroup,
    AddonReloaderPreferences,
    operators.ADDONRELOADER_OT_reload_addon,
    operators.ADDONRELOADER_OT_dropdown_list,
    operators.ADDONRELOADER_OT_refresh_list,
    operators.ADDONRELOADER_OT_open_addon_folder,
    operators.ADDONRELOADER_OT_enable_or_disable_addon,
)


def register():
    """Register addon"""
    # Get current addon module name
    utils.get_my_module_names(__package__)

    # Register all classes
    for cls in classes:
        bpy.utils.register_class(cls)

    # Register property group
    bpy.types.WindowManager.addonreloader = bpy.props.PointerProperty(
        type=AddonReloaderPropertyGroup
    )

    # Register topbar menu draw function
    bpy.types.TOPBAR_HT_upper_bar.append(ui.draw_topbar_menu)

    # Register timer to refresh addon list after Blender is ready
    bpy.app.timers.register(utils.check_blender_ready)


def unregister():
    """Unregister addon"""
    # Unregister timer (if registered)
    if bpy.app.timers.is_registered(utils.check_blender_ready):
        bpy.app.timers.unregister(utils.check_blender_ready)

    # Remove topbar menu draw function
    bpy.types.TOPBAR_HT_upper_bar.remove(ui.draw_topbar_menu)

    # Unregister property group
    del bpy.types.WindowManager.addonreloader

    # Unregister all classes (reverse order)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)