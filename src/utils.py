# utils.py
import os

import bpy

from .data_manager import dm
from .log import log


def get_user_addons_path():
    """获取用户插件路径 - Get user addons path"""

    try:
        # 优先使用新API - New API first
        script_path = bpy.utils.user_resource("SCRIPTS")
        log.debug(f"新API获取用户插件路径: {script_path}")
        dm.dm_user_addon_path = script_path

        # 获取扩展路径 - Get extension path
        extensions_path = bpy.utils.user_resource('EXTENSIONS')
        log.debug(f"获取扩展路径: {extensions_path}")
        dm.dm_user_extend_path = extensions_path
    except Exception as e:
        log.error(f"Error getting user addons path: {e}")


def get_my_module_name(package_name):
    """获取自己的模块名 - Get my module name"""
    try:
        log.debug(f"获取自己的模块名: {package_name}")
        # 如果是扩展 - If it is an extension
        if package_name.startswith("bl_ext."):
            addon_name = package_name.split(".")[-1]
            dm.dm_my_module_name["Addon"] = addon_name
            dm.dm_my_module_name["Extend"] = package_name
        else:  # 如果是插件 - If it is an addon
            dm.dm_my_module_name["Addon"] = package_name
    except Exception as e:
        log.error(f"Error getting self package name: {e}")


def is_extension_enabled(ext_name: str) -> bool:
    """检查扩展是否启用 - Check if the extension is enabled"""
    log.debug(f"检查扩展是否启用: {ext_name}")

    # 此扩展完整路径 - Full path of the extension
    ext_full_path = dm.dm_user_addon_path_dict[ext_name]

    # 扩展是否已经失效 - Check if the extension is invalid
    if not os.path.exists(ext_full_path):
        return False

    # 检查扩展是否启用 - Check if the extension is enabled
    return ext_name in {addon.module for addon in bpy.context.preferences.addons}


def is_addon_enabled(addon_name: str) -> bool:
    """检查插件是否启用 - Check if the addon is enabled"""
    return addon_name in {addon.module for addon in bpy.context.preferences.addons}


def refresh_addon_list(self, context) -> None:
    """刷新插件列表 - Refresh the addon list"""
    log.debug("刷新插件列表 - Refresh the addon list")

    # 用户插件路径 - User addon path
    user_addons_path = dm.dm_user_addon_path

    # 插件和扩展列表 - Addon and extension list
    addons_list = []
    extensions_list = []

    # 获取所有已启用的用户插件和扩展 - Get all enabled user addons and extensions
    enabled_addons = {addon.module for addon in context.preferences.addons}

    # 本插件名称(Addon Reloader) - This addon name (Addon Reloader)
    my_module = dm.dm_my_module_name

    for user_module in enabled_addons:
        log.debug(f"用户模块: {user_module}")

        # 扩展 - Extensions
        if user_module.startswith("bl_ext."):
            # 排除系统扩展 - Exclude system extensions
            user_module_split = user_module.split('.')
            if len(user_module_split) > 1 and user_module_split[0] == 'bl_ext' and user_module_split[1] == 'system':
                log.debug(f"{user_module} 是系统扩展。")
                continue

            # 排除自己(Addon Reloader) - Exclude self (Addon Reloader)
            if my_module["Extend"]:
                if user_module == my_module["Extend"]:
                    log.debug("排除自己 Extend")
                    continue
            else:
                if user_module_split[-1] == my_module["Addon"]:
                    log.debug("排除自己 Addon")
                    continue

            # 排除已失效扩展 - Exclude invalid extensions
            # 此扩展完整路径 - Full path of the extension
            extension_full_path = os.path.join(dm.dm_user_extend_path, user_module_split[1], user_module_split[-1])
            log.debug(f"extension_full_path: {extension_full_path}")
            # 判断扩展路径是否存在 - Check if the extension path exists
            if os.path.exists(extension_full_path):
                log.debug("扩展目录存在！")
                # 记录扩展路径 - Record extension path
                dm.dm_user_addon_path_dict[user_module] = extension_full_path
                # 添加到扩展列表 - Add to extension list
                extensions_list.append((user_module, user_module_split[-1], "", "LINKED", len(extensions_list)))
        else:  # 插件 - Addons
            log.debug(f"{user_module} 是插件。")
            # 排除自己(Addon Reloader) - Exclude self (Addon Reloader)
            if user_module == my_module["Addon"]:
                continue

            # 拼接插件路径 - Concatenate addon path
            addon_path = os.path.join(user_addons_path, "addons", user_module)
            # 判断是否为用户插件 - Check if it is a user addon
            if os.path.exists(addon_path):
                # 记录扩展路径 - Record extension path
                dm.dm_user_addon_path_dict[user_module] = addon_path
                # 添加到插件列表 - Add to addon list
                addons_list.append((user_module, user_module, "", "PLUGIN", len(addons_list)))

    log.debug(f"插件列表: {addons_list}")
    # 更新插件列表 - Update addon list
    dm.dm_show_lists = {"ADDONS": addons_list, "EXTENSIONS": extensions_list}

    # 如列表为空则设置默认值 - If the list is empty, set the default value
    if not addons_list:
        dm.dm_show_lists["ADDONS"] = dm.dm_ddmenu_default_val["ADDONS"]
    if not extensions_list:
        dm.dm_show_lists["EXTENSIONS"] = dm.dm_ddmenu_default_val["EXTENSIONS"]
