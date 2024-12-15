# operators.py
import importlib
import sys

import addon_utils
import bpy

from . import utils
from .data_manager import dm
from .log import log


class ADDONRELOADER_OT_reload_addon(bpy.types.Operator):
    bl_idname = "addonreloader.reload_addon"
    bl_label = "Reload Addon"
    bl_description = "Reload the currently selected addon"

    @classmethod
    def poll(cls, context):
        """检查当前选中的值是否为默认选项"""
        # current_tab = dm.tabs_index
        current_selected = dm.last_selected[0]
        return current_selected != "no_addons"

    def execute(self, context):
        # 将要被重载的插件名
        addon_idname = dm.last_selected[0]
        log.debug("开始重新载入: %s", addon_idname)
        try:
            # 是否是启用状态
            if not utils.is_addon_enabled(addon_idname):
                self.report(
                    {"WARNING"},
                    f"Extension [ {addon_idname} ] is disabled",
                )
                return {"CANCELLED"}

            # 重新加载插件
            self.reload_addons(context, addon_idname)

            self.report({"INFO"}, f"Reloaded Successfully [ {addon_idname} ]")
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"Error reloading {addon_idname}")
            log.debug("Error reloading {addon_idname}: %s", str(e))
            return {"CANCELLED"}

    def reload_addons(self, context, addon_name):
        """重新加载插件及其所有模块"""
        log.debug("Reloading addon: %s", addon_name)
        try:
            log.debug("Reloading addon: %s", addon_name)
            # 禁用插件
            addon_utils.disable(addon_name, default_set=True)

            # 获取插件的所有模块
            allmodules = [name for name in sys.modules if name.startswith(addon_name)]

            log.debug("子模块数量 %d", len(allmodules))
            if allmodules:
                log.debug("存在模块")
                # 重载模块
                for module_name in allmodules:
                    importlib.reload(sys.modules[module_name])
                    log.debug("Reloading module: %s", module_name)

            # 启用插件
            addon_utils.enable(addon_name, default_set=True)
        except Exception as e:
            self.report({"ERROR"}, f"Error reloading addon {addon_name}: {str(e)}")
            return {"CANCELLED"}


class ADDONRELOADER_OT_dropdown_list(bpy.types.Operator):
    bl_idname = "addonreloader.dropdown_list"
    bl_label = "Addon list"
    bl_description = "Select an addon to reload"
    bl_property = "enum_items"

    def get_items(self, context):
        items = dm.show_lists
        return items if items else dm.ddmenu_default_val

    enum_items: bpy.props.EnumProperty(items=get_items)

    def find_last_selected(self, idname: str) -> str:
        """根据idname查找插件"""
        last_selected = None
        for tup in dm.show_lists:
            if tup[0] == idname:
                last_selected = tup
                break

        return last_selected

    def execute(self, context):
        log.debug("下拉菜单操作类")
        if dm.show_lists != "no_addons":
            log.info("Selected addon %s", self.enum_items)
            # 更新最后选择的值
            last_selected = self.find_last_selected(self.enum_items)
            dm.last_selected = last_selected
            # 更新插件状态
            now_addon_state = utils.is_addon_enabled(last_selected[0])
            context.window_manager.addonreloader.addon_state = now_addon_state

        return {"FINISHED"}

    def invoke(self, context, event):
        context.window_manager.invoke_search_popup(self)
        return {"FINISHED"}


class ADDONRELOADER_OT_refresh_list(bpy.types.Operator):
    bl_idname = "addonreloader.refresh_list"
    bl_label = "Refresh"
    bl_description = "Refresh addon list"

    def execute(self, context):
        """执行刷新列表"""
        log.debug("~~~~ 执行刷新列 ~~~~")
        # 刷新插件列表
        utils.refresh_addon_list()
        return {"FINISHED"}


class ADDONRELOADER_OT_open_addon_folder(bpy.types.Operator):
    bl_idname = "addonreloader.open_addon_folder"
    bl_label = "Open folder"
    bl_description = "Open the currently selected addon folder"

    def execute(self, context):
        """打开插件文件夹"""
        log.debug("打开插件文件夹")
        try:
            selected_idname = dm.last_selected[0]
            if selected_idname == "no_addons":
                self.report({"ERROR"}, "No addon selected")
                return {"CANCELLED"}

            selected_addon_full_path = dm.addons_paths[selected_idname]
            selected_addon_path = selected_addon_full_path.replace("__init__.py", "")
            log.debug("插件路径: %s", selected_addon_path)

            # 使用示例：打开Blender项目文件夹
            utils.open_addon_folder(selected_addon_path)

            self.report({"INFO"}, f"Opening {dm.last_selected[0]} folder")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Error opening addon folder: {str(e)}")
            return {"CANCELLED"}
