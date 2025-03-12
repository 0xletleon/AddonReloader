# operators.py
import importlib
import sys
import os

import addon_utils
import bpy

from . import utils
from .data_manager import dm
from .log import log


class ADDONRELOADER_OT_reload_addon(bpy.types.Operator):
    bl_idname = "addonreloader.reload_addon"
    bl_label = "Reload Addon"
    bl_description = "Reload the selected addon"

    @classmethod
    def poll(cls, context):
        """检查当前选中的值是否为默认选项"""
        current_selected = dm.last_selected[0]
        return current_selected != "no_addons"

    def execute(self, context):
        # 将要被重载的插件名
        addon_idname = dm.last_selected
        log.info("Start reloading: %s", addon_idname[1])
        try:
            # 是否是启用状态
            was_enabled = utils.is_addon_enabled(addon_idname[0])
            if not was_enabled:
                self.report(
                    {"WARNING"},
                    f"Extension [ {addon_idname[1]} ] is disabled",
                )
                log.warning("Extension [%s] is disabled", addon_idname[1])
                return {"CANCELLED"}

            # 重新加载插件
            self.reload_addons(context, addon_idname[0])

            self.report({"INFO"}, f"Reloaded Successfully [ {addon_idname[1]} ]")
            return {"FINISHED"}

        except Exception as e:
            self.report({"ERROR"}, f"Error reloading {addon_idname[0]}")
            log.debug("Error reloading %s : %s", addon_idname[0], str(e))
            return {"CANCELLED"}

    def reload_addons(self, context, addon_name):
        """重新加载插件及其所有模块"""
        log.debug("Reloading addon: %s", addon_name)
        try:
            # 获取插件模块
            addon_module = None
            for mod in addon_utils.modules():
                if mod.__name__ == addon_name:
                    addon_module = mod
                    break

            if not addon_module:
                log.error("Module not found: %s", addon_name)
                return False

            # 保存插件路径
            # addon_path = os.path.dirname(addon_module.__file__)
            # log.debug("Addon path: %s", addon_path)

            # 先尝试完全卸载插件
            log.debug("Remove addon: %s", addon_name)

            # 确保插件被完全禁用
            addon_utils.disable(addon_name)

            # 手动注销所有已注册的类
            if hasattr(addon_module, "classes"):
                for cls in reversed(addon_module.classes):
                    try:
                        log.debug("Manual logout class: %s", cls.__name__)
                        bpy.utils.unregister_class(cls)
                    except Exception as e:
                        log.debug("Cancel class failed %s: %s", cls.__name__, str(e))

            # 调用插件的 unregister 函数
            if hasattr(addon_module, "unregister"):
                try:
                    addon_module.unregister()
                    log.debug("Addon successfully logged out")
                except Exception as e:
                    log.error("Addon logout failed: %s", str(e))

            # 清除模块缓存
            related_modules = [
                m
                for m in sys.modules.keys()
                if m == addon_name or m.startswith(addon_name + ".")
            ]

            log.debug("Related Modules: %s", len(related_modules))

            # 从后向前删除模块（先删除子模块）
            for m in sorted(related_modules, reverse=True):
                if m in sys.modules:
                    log.debug("Delete module cache: %s", m)
                    del sys.modules[m]

            # 重新导入主模块
            importlib.invalidate_caches()

            # 重新启用插件
            try:
                # 使用 default_set=True 确保插件在 Blender 偏好设置中被标记为启用
                addon_utils.enable(addon_name, default_set=True)
            except Exception as e:
                log.error("Failed to enable plugin: %s, Err: %s", addon_name, str(e))
                import traceback

                log.error(traceback.format_exc())
                # 尝试使用备用方法启用
                try:
                    spec = importlib.util.find_spec(addon_name)
                    if spec:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        if hasattr(module, "register"):
                            module.register()
                            log.debug("Successfully enabled plugin using alternative methods")
                except Exception as e2:
                    log.error("Err: %s", str(e2))
                    self.report({"ERROR"}, f"Failed to reload addon {addon_name}")
                    return False

            # 刷新UI
            # for window in context.window_manager.windows:
            #     for area in window.screen.areas:
            #         area.tag_redraw()

            return True

        except Exception as e:
            log.error("Failed to reload addon: %s, Err: %s", addon_name, str(e))
            import traceback

            log.error(traceback.format_exc())
            self.report({"ERROR"}, f"Error reloading addon {addon_name}: {str(e)}")
            return False


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
        log.debug("Execute refresh list")
        # 刷新插件列表
        refreshed = utils.refresh_addon_list()
        log.debug("refreshed: %s", refreshed)
        if refreshed is None:
            self.report({"INFO"}, "Addon list refreshed")
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, "No addons found")
            return {"CANCELLED"}


class ADDONRELOADER_OT_open_addon_folder(bpy.types.Operator):
    bl_idname = "addonreloader.open_addon_folder"
    bl_label = "Open folder"
    bl_description = "Open the currently selected addon folder"

    def execute(self, context):
        """打开插件文件夹"""
        log.debug("Open the plugin folder")
        try:
            selected_idname = dm.last_selected[0]
            if selected_idname == "no_addons":
                self.report({"ERROR"}, "No addon selected")
                return {"CANCELLED"}

            selected_addon_full_path = dm.addons_paths[selected_idname]
            selected_addon_path = selected_addon_full_path.replace("__init__.py", "")

            # 打开Blender项目文件夹
            utils.open_addon_folder(selected_addon_path)

            self.report({"INFO"}, f"Opening {dm.last_selected[0]} folder")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Error opening addon folder: {str(e)}")
            return {"CANCELLED"}


class ADDONRELOADER_OT_enable_or_disable_addon(bpy.types.Operator):
    bl_idname = "addonreloader.enable_or_disable_addon"
    bl_label = "Enable or disable addon"
    bl_description = "Toggle the state of the currently selected addon"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        log.info("Enable or disable addon")

        try:
            # 当前状态
            current_state = context.window_manager.addonreloader.addon_state
            log.debug("now state: %s", current_state)
            # 上次选择的插件或扩展
            last_selected = dm.last_selected
            log.debug("Last selected: %s", last_selected[1])

            # 如果没有选择插件则返回
            if last_selected[0] == "no_addons":
                # 使用popup_menu显示警告
                errortext = "Operation failed, please select a plugin"
                self.report({"ERROR"}, errortext)
                log.error(errortext)
                return {"CANCELLED"}

            # 切换插件的启用状态
            # 获取插件当前状态
            now_addon_state = utils.is_addon_enabled(last_selected[0])
            log.debug("now_addon_state : %s", now_addon_state)
            if now_addon_state is not True:
                enabled = addon_utils.enable(last_selected[0], default_set=True)
                if enabled is not None:
                    log.info("Addon [%s] started successfully!", last_selected[1])
                    self.report({"INFO"}, f"Addon [{last_selected[1]}] started successfully!")
                    context.window_manager.addonreloader.addon_state = True
                    return {"FINISHED"}
                else:
                    log.info("Addon [%s] start failed!", last_selected[1])
                    self.report({"WARNING"}, f"Addon [{last_selected[1]}] start failed!")
                    # 修改按钮状态
                    context.window_manager.addonreloader.addon_state = False
                    return {"CANCELLED"}
            else:
                disabled = addon_utils.disable(last_selected[0], default_set=True)
                if disabled is None:
                    log.info("Addon [%s] disabled successfully!", last_selected[1])
                    self.report({"INFO"}, f"Addon [{last_selected[1]}] disabled successfully!")
                    context.window_manager.addonreloader.addon_state = False
                    return {"FINISHED"}
                else:
                    log.info("Addon [%s] disabled failed!", last_selected[1])
                    self.report({"ERROR"}, f"Addon [{last_selected[1]}] disabled failed!")
                    context.window_manager.addonreloader.addon_state = True
                    return {"CANCELLED"}

        except Exception as e:
            log.error("Error toggling addon state: %s ", str(e))
            self.report({"ERROR"}, f"Error switching addon state: {str(e)}")
            return {"CANCELLED"}
