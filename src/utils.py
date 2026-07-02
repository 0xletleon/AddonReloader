# utils.py
import addon_utils
import bpy
import os
import time
import tomllib
from typing import Optional, Dict

from .data_manager import dm
from .log import log


_LAST_REFRESH_TS: float = 0.0
_MIN_REFRESH_INTERVAL_S: float = 0.75


def save_last_selection(idname: str, display_name: str) -> None:
    """Save last selected addon idname and display name to preferences."""
    try:
        prefs = bpy.context.preferences.addons.get(__package__)
        if prefs and prefs.preferences:
            prefs.preferences.last_selected_addon = idname
            prefs.preferences.last_selected_name = display_name
    except Exception:
        pass


def _load_saved_selection() -> None:
    """Load last selected addon from preferences into dm."""
    try:
        prefs = bpy.context.preferences.addons.get(__package__)
        if prefs and prefs.preferences:
            saved = prefs.preferences.last_selected_addon
            if saved:
                dm.last_selected = (saved, "", "", "", 0)
                log.debug("Restored selection: %s", saved)
    except Exception:
        pass


def get_my_module_names(package_name):
    """Get addon module name"""
    try:
        # log.debug("Module name: %s", package_name)
        # Extension
        if package_name.startswith("bl_ext."):
            addon_name = package_name.split(".")[-1]
            dm.my_addon_names["Addon"] = addon_name
            dm.my_addon_names["Extend"] = package_name
        else:  # Addon
            dm.my_addon_names["Addon"] = package_name
    except Exception as e:
        log.error("Get module name failed: %s", e)


def is_addon_enabled(addon_name: str) -> bool:
    """Check if addon is enabled"""
    return addon_utils.check(addon_name)[1]


def sync_addon_state(context: bpy.types.Context) -> None:
    """Sync addon state to UI"""
    try:
        selected_idname = dm.last_selected[0]
        if selected_idname == "no_addons":
            desired = False
        else:
            desired = dm.enabled_map.get(selected_idname)
            if desired is None:
                desired = is_addon_enabled(selected_idname)
        group = context.window_manager.addonreloader
        if group.addon_state != desired:
            group.addon_state = desired
    except Exception:
        return


def refresh_addon_list(force: bool = False) -> None:
    """Refresh addon list"""
    global _LAST_REFRESH_TS
    now = time.monotonic()
    if not force and now - _LAST_REFRESH_TS < _MIN_REFRESH_INTERVAL_S:
        return
    _LAST_REFRESH_TS = now
    log.debug("Refresh list")

    # Restore saved selection on first run
    if dm.last_selected[0] == "no_addons":
        _load_saved_selection()

    # Target idname to restore after refresh
    target_idname = dm.last_selected[0]

    # Raw addon data: (module_name, bl_addon_name, addon_type, state_icon)
    raw_addons = []

    # Get all addons
    all_addons = addon_utils.modules()

    # Current addon name (Addon Reloader)
    my_module = dm.my_addon_names

    dm.addons_paths = {}
    dm.enabled_map = {}

    for addon in all_addons:
        # Module name
        module_name = addon.__name__
        # Module path
        module_file = addon.__file__

        # Module info
        this_bl_info = addon.__dict__.get("bl_info", {})
        bl_addon_name = this_bl_info.get("name", "Unknown")

        check_res = addon_utils.check(module_name)
        is_enabled = check_res[1]
        dm.enabled_map[module_name] = is_enabled
        state_icon = "NODE_SOCKET_SHADER" if is_enabled else "RECORD_ON"

        # Extension
        if addon_utils.check_extension(module_name):
            # Split module name
            module_name_split = module_name.split(".")
            # Exclude self (Addon Reloader)
            if my_module["Extend"]:
                if module_name == my_module["Extend"]:
                    continue
            else:
                if module_name_split[-1] == my_module["Addon"]:
                    continue

            # Exclude system extensions
            if (
                len(module_name_split) > 1
                and module_name_split[0] == "bl_ext"
                and module_name_split[1] == "system"
            ):
                continue

            # Add to raw list (store raw name for sorting)
            raw_addons.append((module_name, bl_addon_name, "E", state_icon))

            # Add to addon paths
            dm.addons_paths[module_name] = module_file
        else:  # Addon
            # Exclude self (Addon Reloader)
            if module_name == my_module["Addon"]:
                continue

            # Exclude system addons (v4.2+)
            if "addons_core" in module_file:
                continue

            # Add to raw list (store raw name for sorting)
            raw_addons.append((module_name, bl_addon_name, "A", state_icon))

            # Add to addon paths
            dm.addons_paths[module_name] = module_file

    # Sort by addon name (A-Z, case-insensitive)
    raw_addons.sort(key=lambda e: e[1].lower())

    # Build enum items: (identifier, display_name, description, icon, index)
    addons_list = [
        (mod, f"({typ}) {name}", "", icon, i)
        for i, (mod, name, typ, icon) in enumerate(raw_addons)
    ]

    # Set default if list is empty
    if not addons_list:
        dm.show_lists = dm.ddmenu_default_val
        dm.last_selected = dm.ddmenu_default_val[0]
        save_last_selection("", "")
    else:
        dm.show_lists = addons_list
        # Restore previous selection if still in list
        found_entry = None
        for entry in addons_list:
            if entry[0] == target_idname:
                found_entry = entry
                break
        if found_entry:
            dm.last_selected = found_entry
        else:
            dm.last_selected = addons_list[0]
            log.debug("Auto select: %s", dm.last_selected[1])
        save_last_selection(dm.last_selected[0], dm.last_selected[1])

    sync_addon_state(bpy.context)


def load_manifest_info() -> Optional[Dict]:
    """Load version info from blender_manifest.toml."""
    manifest_path = os.path.join(os.path.dirname(__file__), "blender_manifest.toml")
    try:
        with open(manifest_path, "rb") as f:
            data = tomllib.load(f)
        return {
            "version": data.get("version", ""),
            "blender_version_min": data.get("blender_version_min", ""),
            "name": data.get("name", ""),
        }
    except Exception as e:
        log.warning("Load manifest failed: %s", str(e))
        return None


def check_blender_ready():
    """Check if Blender is ready and refresh addon list"""
    try:
        # Check if Blender is fully initialized
        if (
            bpy.context and
            hasattr(bpy.context, 'window_manager') and
            bpy.context.window_manager and
            hasattr(bpy.context, 'scene') and
            bpy.context.scene
        ):
            log.debug("Blender ready")

            # Print version info from manifest
            info = load_manifest_info()
            if info:
                sep = "=" * 50
                log.info(sep)
                log.info("%s v%s enabled", info["name"], info["version"])
                log.info("Supports Blender %s+", info["blender_version_min"])
                log.info(sep)

            # Blender ready, refresh addon list
            refresh_addon_list(force=True)

            # Stop timer
            return None
        else:
            # Continue checking
            return 0.5
    except Exception as e:
        log.warning("Check blender ready failed: %s", str(e))
        # Retry later
        return 0.5