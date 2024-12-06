# operators.py
import importlib
import sys

import addon_utils
import bpy

from . import utils
from .data_manager import dm
from .log import log


class ADDONRELOADER_OT_reload_addon(bpy.types.Operator):
    """重新加载插件 - Reload Addon"""

    bl_idname = "addonreloader.reload_addon"
    bl_label = "Reload Addon"
    bl_description = "Reload addon or extension"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context):
        """检查当前选中的值是否为默认选项 - Check whether the currently selected value is the default option"""
        current_tab = dm.dm_tabs_index
        current_selected = dm.dm_last_selected[current_tab]
        return current_selected != "def_opt"

    def execute(self, context):
        # 将要被重载的插件名 - The name of the plugin to be reloaded
        addon_name = dm.dm_last_selected[dm.dm_tabs_index]
        log.debug("开始重新载入: %s", addon_name)
        try:
            # 是否是启用状态 - Whether it is enabled status
            if not utils.is_addon_enabled(addon_name):
                self.report(
                    {"WARNING"},
                    f"Extension [ {addon_name} ] is disabled or does not exist!",
                )
                return {"CANCELLED"}

            # 扩展 - Extension
            if addon_name.startswith("bl_ext."):
                # 重新加载扩展 - Reload Extension
                self.reload_addon_or_extension(context, addon_name)
            else:  # 插件 - Addon
                # 重新加载插件 - Reload Addon
                self.reload_addon_or_extension(context, addon_name)

            # 刷新插件列表
            # core.refresh_addon_list(self, context)

            self.report({"INFO"}, f"Reloaded Successfully [ {addon_name} ] √")
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"Error reloading {addon_name}")
            log.debug("Error reloading {addon_name}: %s", str(e))
            # 刷新插件列表 - Refresh addon list
            # utils.refresh_addon_list(self, context)
            return {"CANCELLED"}

    def reload_addon_or_extension(self, context, extend_name):
        """重新加载插件或扩展及其所有模块 - Reload the plugin or extension and all its modules"""
        try:
            log.debug("Reloading extension: %s", extend_name)
            # 禁用扩展 - Disable extension
            addon_utils.disable(extend_name, default_set=True)

            # 获取扩展的所有模块 - Get all modules of the extension
            allmodules = [name for name in sys.modules if name.startswith(extend_name)]

            log.debug("子模块数量 %d", len(allmodules))
            if allmodules:
                log.debug("存在模块: %s", allmodules)
                # 重载模块 - Reload all modules
                for module_name in allmodules:
                    importlib.reload(sys.modules[module_name])
                    log.debug("Reloading module: %s", module_name)

            # 启用扩展 - Enable extension
            addon_utils.enable(extend_name, default_set=True)
        except Exception as e:
            self.report({"ERROR"}, f"Error reloading extension {extend_name}: {str(e)}")
            # 刷新插件列表 - Refresh addon list
            # utils.refresh_addon_list(self, context)
            return {"CANCELLED"}


class ADDONRELOADER_OT_refresh_list(bpy.types.Operator):
    """刷新列表 - Refresh the list"""

    bl_idname = "addonreloader.refresh_list"
    bl_label = "Refresh List"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        """执行刷新列表 - Execute refresh list"""
        log.debug("~~~~ 执行刷新列表 - Execute refresh list ~~~~")
        # 刷新插件列表 - Refresh the addon list
        utils.refresh_addon_list(self, context)
        return {"FINISHED"}
