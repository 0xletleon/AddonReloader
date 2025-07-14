# operators.py
import importlib
import importlib.util
import os
import sys
import traceback  # 替换直接导入 sys

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
            addon_path = os.path.dirname(addon_module.__file__)
            log.debug("Addon path: %s", addon_path)

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

            # 使用纯 importlib 方式重新加载模块
            # 首先清除 importlib 缓存
            importlib.invalidate_caches()
            
            # 记录需要重新加载的模块
            modules_to_reload = []
            
            # 查找主模块和所有子模块
            for root, dirs, files in os.walk(addon_path):
                for file in files:
                    if file.endswith('.py'):
                        # 计算相对路径
                        rel_path = os.path.relpath(os.path.join(root, file), addon_path)
                        # 将路径转换为模块名
                        if file == '__init__.py':
                            if root == addon_path:
                                # 主模块
                                module_name = addon_name
                            else:
                                # 子包
                                sub_path = os.path.relpath(root, addon_path)
                                module_name = f"{addon_name}.{sub_path.replace(os.sep, '.')}"
                        else:
                            # 普通模块
                            module_path = rel_path.replace(os.sep, '.').replace('.py', '')
                            module_name = f"{addon_name}.{module_path}"
                        
                        modules_to_reload.append(module_name)
            
            log.debug("Found modules to reload: %s", len(modules_to_reload))
            
            # 从sys.modules中移除所有相关模块
            for key in list(sys.modules.keys()):
                if key == addon_name or key.startswith(f"{addon_name}."):
                    # log.debug("Removing module from sys.modules: %s", key)
                    del sys.modules[key]
            
            # 重新导入主模块和所有子模块
            for module_name in sorted(modules_to_reload):
                try:
                    spec = importlib.util.find_spec(module_name)
                    if spec:
                        # log.debug("Reloading module: %s", module_name)
                        # 检查模块文件是否已更改
                        # module_file = spec.origin
                        # log.debug("Module file: %s", module_file)
                        if module_name == addon_name:
                            # 主模块特殊处理
                            main_module = importlib.util.module_from_spec(spec)
                            sys.modules[module_name] = main_module
                            spec.loader.exec_module(main_module)
                            # log.debug("Main module reloaded: %s", module_name)
                        else:
                            # 子模块
                            module = importlib.util.module_from_spec(spec)
                            sys.modules[module_name] = module
                            spec.loader.exec_module(module)
                            # log.debug("Submodule reloaded: %s", module_name)
                except Exception as e:
                    log.debug("Error reloading module %s: %s", module_name, str(e))

            # 重新启用插件
            try:
                # 使用 default_set=True 确保插件在 Blender 偏好设置中被标记为启用
                addon_utils.enable(addon_name, default_set=True)
            except Exception as e:
                log.error("Failed to enable plugin: %s, Err: %s", addon_name, str(e))
                log.error(traceback.format_exc())
                # 尝试使用备用方法启用
                try:
                    spec = importlib.util.find_spec(addon_name)
                    if spec:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[module_name] = module  # 确保模块被正确放入sys.modules
                        spec.loader.exec_module(module)
                        if hasattr(module, "register"):
                            module.register()
                            log.debug("Successfully enabled plugin using alternative methods")
                except Exception as e2:
                    log.error("Err: %s", str(e2))
                    self.report({"ERROR"}, f"Failed to reload addon {addon_name}")
                    return False

            return True

        except Exception as e:
            log.error("Failed to reload addon: %s, Err: %s", addon_name, str(e))
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

    enum_items: bpy.props.EnumProperty(items=get_items) # type: ignore

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
        # 先执行刷新列表操作
        log.debug("Auto refreshing addon list before showing dropdown")
        # 刷新插件列表
        utils.refresh_addon_list()
        
        # 保存当前鼠标位置
        current_mouse_x = event.mouse_x
        current_mouse_y = event.mouse_y
        
        # 修改鼠标位置（向左和向下偏移）
        offset_x = -50  # 向左偏移
        offset_y = -30  # 向下偏移
        context.window.cursor_warp(current_mouse_x + offset_x, current_mouse_y + offset_y)
        
        # 调用原始的搜索弹出窗口
        context.window_manager.invoke_search_popup(self)
        
        # 操作完成后将鼠标位置恢复
        context.window.cursor_warp(current_mouse_x, current_mouse_y)
        
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
