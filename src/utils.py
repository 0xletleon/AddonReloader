# utils.py
import os
import subprocess

import addon_utils
import bpy

from .data_manager import dm
from .log import log


def get_my_module_names(package_name):
    """获取自己的模块名"""
    try:
        log.debug("Get the module name of this addon:%s", package_name)
        # 如果是扩展
        if package_name.startswith("bl_ext."):
            addon_name = package_name.split(".")[-1]
            dm.my_addon_names["Addon"] = addon_name
            dm.my_addon_names["Extend"] = package_name
        else:  # 如果是插件
            dm.my_addon_names["Addon"] = package_name
    except Exception as e:
        log.error("Error getting self package name: %s", e)


def is_addon_enabled(addon_name: str) -> bool:
    """检查插件是否启用"""
    return addon_utils.check(addon_name)[1]


def refresh_addon_list() -> None:
    """刷新插件列表"""
    log.debug("Refresh addon list")

    # 插件列表
    addons_list = []

    # 获取所有插件
    all_addons = addon_utils.modules()

    # 本插件名称(Addon Reloader)
    my_module = dm.my_addon_names

    # 插件列表中是否存在上次的选择
    last_in_list = False

    for addon in all_addons:
        # 模块名称
        module_name = addon.__name__
        # 模块路径
        module_file = addon.__file__

        # 模块信息
        this_bl_info = addon.__dict__.get("bl_info", {})
        bl_addon_version = this_bl_info.get("version", "0.0.0")
        bl_addon_name = this_bl_info.get("name", "Unknown Name")
        bl_addon_description = f"Version: {bl_addon_version} \n"
        bl_addon_description += this_bl_info.get(
            "description", "No description available"
        )

        # 检查是否为上次选择的插件
        if not last_in_list:
            if dm.last_selected[0] == module_name:
                last_in_list = True
            else:
                last_in_list = False

        # 扩展
        if addon_utils.check_extension(module_name):
            # 分割模块名称
            module_name_split = module_name.split(".")
            # 排除自己(Addon Reloader)
            if my_module["Extend"]:
                if module_name == my_module["Extend"]:
                    log.debug("Exclude this extension")
                    continue
            else:
                if module_name_split[-1] == my_module["Addon"]:
                    log.debug("Exclude this addon")
                    continue

            # 排除系统扩展
            if (
                len(module_name_split) > 1
                and module_name_split[0] == "bl_ext"
                and module_name_split[1] == "system"
            ):
                # log.debug("[%s] system extension", module_name)
                continue

            # 添加到扩展列表
            addons_list.append(
                (
                    module_name,
                    bl_addon_name,
                    bl_addon_description,
                    "PLUGIN",
                    len(addons_list),
                )
            )
            # 添加到插件路径列表
            dm.addons_paths[module_name] = module_file
        else:  # 插件
            # 排除自己(Addon Reloader)
            if module_name == my_module["Addon"]:
                continue

            # 排除系统插件(v4.2+)
            if "addons_core" in module_file:
                # log.debug("[%s] system addon", module_name)
                continue

            # 添加到插件列表
            addons_list.append(
                (
                    module_name,
                    bl_addon_name,
                    bl_addon_description,
                    "FILE_SCRIPT",
                    len(addons_list),
                )
            )
            # 添加到插件路径列表
            dm.addons_paths[module_name] = module_file

    # 如列表为空则设置默认值
    if not addons_list:
        dm.show_lists = dm.ddmenu_default_val
        dm.last_selected = dm.ddmenu_default_val[0]
    else:
        # 更新插件列表
        dm.show_lists = addons_list
        # 如果上次的选择为默认或本次列表中没有上次的选择时 更新选择
        if not last_in_list or dm.last_selected[0] == "no_addons":
            dm.last_selected = addons_list[0]
            log.debug(
                "Last time, the selection was not updated in the list: %s",
                dm.last_selected[1],
            )
            # 更新插件状态
            now_addon_state = is_addon_enabled(addons_list[0][0])
            addon_state = bpy.context.window_manager.addonreloader.addon_state
            log.debug(
                "now_addon_state: %s addon_state: %s", now_addon_state, addon_state
            )
            if addon_state != now_addon_state:
                log.debug("addon_state != now_addon_state")
                bpy.context.window_manager.addonreloader.addon_state = now_addon_state

    log.info("Addons list refreshed")


def check_blender_ready():
    """检查 Blender 是否已完全初始化，并在初始化后刷新插件列表"""
    # 检查 Blender 是否已完全初始化
    if (
        bpy.context
        and bpy.context.scene
        and bpy.context.view_layer
        and bpy.data.objects
    ):
        log.debug("Blender is ready")
        # Blender 已就绪 刷新插件列表
        refresh_addon_list()

        # 停止定时器
        return None

    log.debug("Blender is not ready yet")
    # 继续检查
    return 0.1


def open_addon_folder(path):
    """打开插件文件夹"""
    # 检查操作系统类型
    if os.name == "nt":  # Windows
        os.startfile(path)
    elif os.name == "posix":  # macOS or Linux
        subprocess.call(("open", path))
