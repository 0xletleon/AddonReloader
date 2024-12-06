# utils.py
import os

import addon_utils

from .data_manager import dm
from .log import log


def get_my_module_name(package_name):
    """获取自己的模块名 - Get my module name"""
    try:
        log.debug("获取自己的模块名:%s", package_name)
        # 如果是扩展 - If it is an extension
        if package_name.startswith("bl_ext."):
            addon_name = package_name.split(".")[-1]
            dm.dm_my_module_name["Addon"] = addon_name
            dm.dm_my_module_name["Extend"] = package_name
        else:  # 如果是插件 - If it is an addon
            dm.dm_my_module_name["Addon"] = package_name
    except Exception as e:
        log.error("Error getting self package name: %s", e)


def is_addon_enabled(addon_name: str) -> bool:
    """检查插件是否启用 - Check if the addon is enabled"""
    loaded_state = addon_utils.check(addon_name)[1]
    log.debug(f"Addon '{addon_name}' is {'loaded' if loaded_state else 'not loaded'}.")
    return loaded_state


def refresh_addon_list(self, context) -> None:
    """刷新插件列表 - Refresh the addon list"""
    log.debug("刷新插件列表 - Refresh the addon list")

    # 插件和扩展列表 - Addon and extension list
    addons_list = []
    extensions_list = []

    # 获取所有插件和扩展 - Get all addons and extensions
    all_addons = addon_utils.modules()

    # 本插件名称(Addon Reloader) - This addon name (Addon Reloader)
    my_module = dm.dm_my_module_name

    for addon in all_addons:
        # 模块名称 - Module name
        module_name = addon.__name__

        # 排除未启用 - Exclude disabled
        if not is_addon_enabled(module_name):
            log.debug("%s 未启用", module_name)
            continue

        # 模块路径 - Module path
        module_file = addon.__file__
        # 模块信息 - Module information
        this_bl_info = addon_utils.module_bl_info(addon)
        bl_addon_name = this_bl_info.get("name", "Unknown Name")
        bl_addon_description = this_bl_info.get(
            "description", "No description available"
        )
        log.debug(
            "模块名称: %s 模块路径: %s 插件名称: %s 插件描述: %s",
            module_name,
            module_file,
            bl_addon_name,
            bl_addon_description,
        )

        # 扩展 - Extensions
        if addon_utils.check_extension(module_name):
            # 分割模块名称 - Split module name
            module_name_split = module_name.split(".")
            # 排除自己(Addon Reloader) - Exclude self (Addon Reloader)
            if my_module["Extend"]:
                if module_name == my_module["Extend"]:
                    log.debug("排除自己 Extend")
                    continue
            else:
                if module_name_split[-1] == my_module["Addon"]:
                    log.debug("排除自己 Addon")
                    continue

            # 排除系统扩展 - Exclude system extensions
            if (
                len(module_name_split) > 1
                and module_name_split[0] == "bl_ext"
                and module_name_split[1] == "system"
            ):
                log.debug("%s 是系统扩展", module_name)
                continue

            # 添加到扩展列表 - Add to extension list
            extensions_list.append(
                (
                    module_name,
                    bl_addon_name,
                    bl_addon_description,
                    "LINKED",
                    len(extensions_list),
                )
            )
        else:  # 插件 - Addons
            log.debug("%s 是插件", module_name)
            # 排除自己(Addon Reloader) - Exclude self (Addon Reloader)
            if module_name == my_module["Addon"]:
                continue

            # 排除系统插件(v4.2+) - Exclude system addons
            if "addons_core" in module_file:
                log.debug("%s 是系统插件", module_name)
                continue

            # 判断是否为用户插件(v4.1) - Check if it is a user addon
            if not os.path.exists(module_file):
                log.debug("%s 不是用户插件", module_name)
                continue

            # 添加到插件列表 - Add to addon list
            addons_list.append(
                (
                    module_name,
                    bl_addon_name,
                    bl_addon_description,
                    "PLUGIN",
                    len(addons_list),
                )
            )

    log.debug("插件列表: %s", addons_list)
    log.debug("扩展列表: %s", extensions_list)
    # 更新插件列表 - Update addon list
    dm.dm_show_lists = {"ADDONS": addons_list, "EXTENSIONS": extensions_list}

    # 如列表为空则设置默认值 - If the list is empty, set the default value
    if not addons_list:
        dm.dm_show_lists["ADDONS"] = dm.dm_ddmenu_default_val["ADDONS"]
    if not extensions_list:
        dm.dm_show_lists["EXTENSIONS"] = dm.dm_ddmenu_default_val["EXTENSIONS"]
