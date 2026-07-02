# operators.py
import importlib
import os
import subprocess
import sys
import traceback
from typing import List, Optional, Set, Tuple

import addon_utils
import bpy

from . import utils
from .data_manager import dm
from .log import log


class ADDONRELOADER_OT_reload_addon(bpy.types.Operator):
    """Reload selected addon"""
    bl_idname = "addonreloader.reload_addon"
    bl_label = ""
    bl_description = "Reload"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        """Check if addon can be reloaded"""
        return dm.last_selected[0] != "no_addons"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Execute reload"""
        target_item = dm.last_selected
        log.debug("Reload: %s", target_item[1])

        try:
            my_addon = dm.my_addon_names.get("Addon")
            my_extend = dm.my_addon_names.get("Extend")
            if target_item[0] in {my_addon, my_extend}:
                self.report({"WARNING"}, "Cannot reload Addon Reloader itself")
                return {"CANCELLED"}

            # Check if addon is enabled
            was_enabled = utils.is_addon_enabled(target_item[0])

            # Execute reload
            success = self._reload_modules(context, target_item[0], was_enabled)

            if success:
                utils.refresh_addon_list(force=True)
                utils.sync_addon_state(context)
                log.info("%s reloaded", target_item[1])
                self.report({"INFO"}, f"{target_item[1]} Reloaded!")
                return {"FINISHED"}

            self.report({"ERROR"}, f"{target_item[1]} Reload Failed!")
            return {"CANCELLED"}

        except Exception as e:
            log.error("Reload failed: %s", str(e))
            self.report({"ERROR"}, f"Error: {str(e)}")
            return {"CANCELLED"}

    def _reload_modules(self, context: bpy.types.Context, module_name: str, was_enabled: bool) -> bool:
        """Reload addon and all related modules"""
        root_module_name = module_name

        try:
            # Get module
            target_module = None
            for mod in addon_utils.modules():
                if mod.__name__ == root_module_name:
                    target_module = mod
                    break

            # If module not found
            if not target_module:
                log.error("Module not found: %s", root_module_name)
                return False

            # Disable module
            addon_utils.disable(root_module_name)

            # Manually unregister all classes
            if hasattr(target_module, "classes"):
                for cls in reversed(target_module.classes):
                    try:
                        bpy.utils.unregister_class(cls)
                    except Exception:
                        pass

            # Call module's unregister function
            if hasattr(target_module, "unregister"):
                try:
                    target_module.unregister()
                except Exception as e:
                    log.warning("Unregister failed: %s", str(e))

            # Remove all related modules from sys.modules
            modules_to_remove: List[str] = [
                name for name in sys.modules
                if name == root_module_name or name.startswith(f"{root_module_name}.")
            ]

            for name in modules_to_remove:
                del sys.modules[name]

            # Clear importlib cache
            importlib.invalidate_caches()

            # Re-enable module if it was enabled
            if was_enabled:
                try:
                    result = addon_utils.enable(root_module_name, default_set=True)
                    if result is not None:
                        return True

                    log.error("Re-enable failed: %s", root_module_name)
                    return False

                except Exception as e:
                    log.error("Enable failed: %s, %s", root_module_name, str(e))
                    return False

            return True

        except Exception as e:
            log.error("Reload error: %s, %s", root_module_name, str(e))
            return False


class ADDONRELOADER_OT_dropdown_list(bpy.types.Operator):
    """List"""
    bl_idname = "addonreloader.dropdown_list"
    bl_label = ""
    bl_description = "List"
    bl_property = "enum_items"

    def _get_enum_items(self, context: bpy.types.Context) -> List[Tuple[str, str, str, str, int]]:
        """Get enum items"""
        items = dm.show_lists
        return items if items else dm.ddmenu_default_val

    enum_items: bpy.props.EnumProperty(items=_get_enum_items)  # type: ignore

    def _find_selected_item(self, idname: str) -> Optional[Tuple[str, str, str, str, int]]:
        """Find addon by idname"""
        for item_tuple in dm.show_lists:
            if item_tuple[0] == idname:
                return item_tuple
        return None

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Execute selection"""
        if not dm.show_lists:
            return {"CANCELLED"}

        # Update last selected
        last_selected = self._find_selected_item(self.enum_items)
        if last_selected:
            log.debug("Selected: %s (%s)", last_selected[1], last_selected[0])
            dm.last_selected = last_selected
            utils.sync_addon_state(context)
            utils.save_last_selection(last_selected[0], last_selected[1])

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        """Invoke dropdown list"""
        # Refresh list before showing
        utils.refresh_addon_list(force=True)

        # Save current mouse position
        current_mouse_x = event.mouse_x
        current_mouse_y = event.mouse_y

        # Adjust mouse position
        offset_x = 0
        offset_y = -30
        context.window.cursor_warp(current_mouse_x + offset_x, current_mouse_y + offset_y)

        # Invoke search popup
        context.window_manager.invoke_search_popup(self)

        # Restore mouse position
        context.window.cursor_warp(current_mouse_x, current_mouse_y)

        return {"FINISHED"}


class ADDONRELOADER_OT_refresh_list(bpy.types.Operator):
    """Refresh addon list"""
    bl_idname = "addonreloader.refresh_list"
    bl_label = "Refresh"
    bl_description = "Refresh the addon list"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Execute refresh"""
        utils.refresh_addon_list(force=True)
        self.report({"INFO"}, "List refreshed")
        return {"FINISHED"}


class ADDONRELOADER_OT_open_addon_folder(bpy.types.Operator):
    """Open addon folder"""
    bl_idname = "addonreloader.open_addon_folder"
    bl_label = ""
    bl_description = "Open Folder"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Execute open folder"""

        # Check if addon selected
        selected_idname = dm.last_selected[0]
        if selected_idname == "no_addons":
            self.report({"WARNING"}, "No addon selected!")
            return {"CANCELLED"}

        try:
            selected_item_full_path = dm.addons_paths[selected_idname]
            selected_item_path = os.path.dirname(selected_item_full_path)

            # Check OS type
            if os.name == "nt":  # Windows
                os.startfile(selected_item_path)
            elif os.name == "posix":  # macOS or Linux
                if sys.platform == "darwin":
                    subprocess.Popen(("open", selected_item_path))
                else:
                    subprocess.Popen(("xdg-open", selected_item_path))

            log.debug("Folder opened: %s", dm.last_selected[1])
            self.report({"INFO"}, f"{dm.last_selected[1]} Folder Opened!")
            return {"FINISHED"}
        except Exception as e:
            log.error("Open folder failed: %s", str(e))
            self.report({"ERROR"}, f"Error: {str(e)}")
            return {"CANCELLED"}


class ADDONRELOADER_OT_enable_or_disable_addon(bpy.types.Operator):
    """Toggle addon state"""
    bl_idname = "addonreloader.enable_or_disable_addon"
    bl_label = ""
    bl_description = "Toggle"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """Execute toggle"""
        log.debug("Toggle state")

        # Check if addon selected
        last_selected = dm.last_selected
        if last_selected[0] == "no_addons":
            self.report({"WARNING"}, "No addon selected!")
            return {"CANCELLED"}

        try:
            # Get current state
            now_item_state = utils.is_addon_enabled(last_selected[0])

            if not now_item_state:
                # Enable addon
                enabled = addon_utils.enable(last_selected[0], default_set=True)
                if enabled is not None:
                    log.info("%s enabled", last_selected[1])
                    self.report({"INFO"}, f"{last_selected[1]} Enabled!")
                    utils.refresh_addon_list(force=True)
                    utils.sync_addon_state(context)
                    return {"FINISHED"}

                log.warning("%s enable failed", last_selected[1])
                self.report({"WARNING"}, f"{last_selected[1]} Enable Failed!")
                utils.sync_addon_state(context)
                return {"CANCELLED"}

            # Disable addon
            disabled = addon_utils.disable(last_selected[0], default_set=True)
            if disabled is None:
                log.info("%s disabled", last_selected[1])
                self.report({"INFO"}, f"{last_selected[1]} Disabled!")
                utils.refresh_addon_list(force=True)
                utils.sync_addon_state(context)
                return {"FINISHED"}

            log.warning("%s disable failed", last_selected[1])
            self.report({"ERROR"}, f"{last_selected[1]} Disable Failed!")
            utils.sync_addon_state(context)
            return {"CANCELLED"}

        except Exception as e:
            log.error("Toggle error: %s", str(e))
            self.report({"ERROR"}, f"Error: {str(e)}")
            return {"CANCELLED"}