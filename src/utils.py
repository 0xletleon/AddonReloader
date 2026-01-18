# utils.py
import addon_utils
import bpy
import time

from .data_manager import dm
from .log import log


_LAST_REFRESH_TS: float = 0.0
_MIN_REFRESH_INTERVAL_S: float = 0.75


def get_my_module_names(package_name):
    """获取当前插件的模块名称"""
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


def sync_addon_state(context: bpy.types.Context) -> None:
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
    """刷新插件列表"""
    log.debug("Refresh List")
    global _LAST_REFRESH_TS
    now = time.monotonic()
    if not force and now - _LAST_REFRESH_TS < _MIN_REFRESH_INTERVAL_S:
        return
    _LAST_REFRESH_TS = now

    # 插件列表
    addons_list = []

    # 获取所有插件
    all_addons = addon_utils.modules()

    # 当前插件名称(Addon Reloader)
    my_module = dm.my_addon_names

    # 检查上次选择的插件是否仍在列表中
    last_in_list = False
    dm.addons_paths = {}
    dm.enabled_map = {}

    for addon in all_addons:
        # 模块名称
        module_name = addon.__name__
        # 模块路径
        module_file = addon.__file__

        # 模块信息
        this_bl_info = addon.__dict__.get("bl_info", {})
        bl_addon_version = this_bl_info.get("version", "0.0.0")
        bl_addon_name = this_bl_info.get("name", "Unknown Name")

        check_res = addon_utils.check(module_name)
        is_enabled = check_res[1]
        dm.enabled_map[module_name] = is_enabled
        enabled_status = " [Enabled]" if is_enabled else " [Disabled]"
        state_icon = "COLORSET_03_VEC" if is_enabled else "COLORSET_02_VEC"

        bl_addon_description = f"Version: {bl_addon_version}{enabled_status}"

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
                    log.debug("Exclude this extension (Addon Reloader)")
                    continue
            else:
                if module_name_split[-1] == my_module["Addon"]:
                    log.debug("Exclude this addon (Addon Reloader)")
                    continue

            # 排除系统扩展
            if (
                len(module_name_split) > 1
                and module_name_split[0] == "bl_ext"
                and module_name_split[1] == "system"
            ):
                # log.debug("[%s] system extension", module_name)
                continue

            # 添加到扩展列表（无论是否启用）
            addon_entry = (
                module_name,
                f"[E] {bl_addon_name}",
                bl_addon_description,
                state_icon,
                len(addons_list),
            )
            addons_list.append(addon_entry)

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

            # 添加到插件列表（无论是否启用）
            addon_entry = (
                module_name,
                f"[A] {bl_addon_name}",
                bl_addon_description,
                state_icon,
                len(addons_list),
            )
            addons_list.append(addon_entry)

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
                "No addon/extension selected, updating to: %s",
                dm.last_selected[1],
            )

    log.debug("Re-refresh List")
    sync_addon_state(bpy.context)


def check_blender_ready():
    """检查 Blender 是否已完全初始化，并在初始化后刷新插件列表"""
    try:
        # 检查 Blender 是否已完全初始化
        # 更可靠的检查方法
        if (
            bpy.context and
            hasattr(bpy.context, 'window_manager') and
            bpy.context.window_manager and
            hasattr(bpy.context, 'scene') and
            bpy.context.scene
        ):
            log.debug("Blender Ready")
            # Blender 已就绪 刷新插件列表
            refresh_addon_list(force=True)

            # 停止定时器
            return None
        else:
            log.debug("Blender is not ready yet")
            # 继续检查
            return 0.5  # 增加间隔时间以减少日志输出
    except Exception as e:
        log.debug("Error checking Blender readiness: %s", str(e))
        # 如果出现异常，稍后再检查
        return 0.5
