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
    bl_description = "Disable and re-enable the selected add-on or extension"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        """检查当前选中的值是否为默认选项 - Check whether the currently selected value is the default option"""
        current_tab = dm.dm_tabs_index
        current_selected = dm.dm_last_selected[current_tab]
        return current_selected != "def_opt"

    def execute(self, context):
        # 将要被重载的插件名 - The name of the plugin to be reloaded
        addon_name = dm.dm_last_selected[dm.dm_tabs_index]
        log.debug(f"addon_name: {addon_name}")
        try:
            # 扩展 - Extension
            if addon_name.startswith("bl_ext."):
                # 是否是启用状态 - Whether it is enabled status
                if not utils.is_extension_enabled(addon_name):
                    self.report({'WARNING'}, f"Extension [ {addon_name} ] is disabled or does not exist!")
                    # 刷新列表 - Refresh list
                    # utils.refresh_addon_list(self, context)
                    return {'CANCELLED'}
                # 重新加载扩展 - Reload Extension
                self.reload_extension(context, addon_name)
            else:  # 插件 - Addon
                # 是否是启用状态 - Whether it is enabled status
                if not utils.is_addon_enabled(addon_name):
                    self.report({'WARNING'}, f"Add-on [ {addon_name} ] is disabled or does not exist!")
                    # 刷新列表 - Refresh list
                    # utils.refresh_addon_list(self, context)
                    return {'CANCELLED'}
                # 重新加载插件 - Reload Addon
                self.reload_addon(context, addon_name)

            # 刷新插件列表
            # core.refresh_addon_list(self, context)

            self.report({'INFO'}, f"Reloaded Successfully [ {addon_name} ] √")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Error reloading {addon_name}: {str(e)}")
            # 刷新插件列表 - Refresh addon list
            # utils.refresh_addon_list(self, context)
            return {'CANCELLED'}

    def reload_addon(self, context, addon_name):
        """重新加载插件 - Reload Addon"""
        try:
            log.debug(f"Reloading addon: {addon_name}")
            # 禁用插件 - Disable addon
            addon_utils.disable(addon_name)
            # 启用插件 - Enable addon
            addon_utils.enable(addon_name, default_set=True)
        except Exception as e:
            self.report({'ERROR'}, f"Error reloading addon {addon_name}: {str(e)}")
            # 刷新列表 - Refresh list
            # utils.refresh_addon_list(self, context)
            return {'CANCELLED'}

    def reload_extension(self, context, extend_name):
        """重新加载扩展及其所有模块 - Reload Extension and all its modules"""
        try:
            log.debug(f"Reloading extension: {extend_name}")
            # 禁用扩展 - Disable extension
            addon_utils.disable(extend_name)

            # 获取扩展的所有模块 - Get all modules of the extension
            allmodules = [name for name in sys.modules if name.startswith(extend_name)]

            # 重新加载所有模块 - Reload all modules
            for module_name in allmodules:
                importlib.reload(sys.modules[module_name])
                log.debug(f"Reloading module: {module_name}")

            # 启用扩展 - Enable extension
            addon_utils.enable(extend_name, default_set=True)
        except Exception as e:
            self.report({'ERROR'}, f"Error reloading extension {extend_name}: {str(e)}")
            # 刷新插件列表 - Refresh addon list
            # utils.refresh_addon_list(self, context)
            return {'CANCELLED'}


class ADDONRELOADER_OT_refresh_list(bpy.types.Operator):
    """刷新列表 - Refresh the list"""
    bl_idname = "addonreloader.refresh_list"
    bl_label = "Refresh List"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        """执行刷新列表 - Execute refresh list"""
        log.debug("~~~~ 执行刷新列表 - Execute refresh list ~~~~")
        # 刷新插件列表 - Refresh the addon list
        utils.refresh_addon_list(self, context)
        return {'FINISHED'}
