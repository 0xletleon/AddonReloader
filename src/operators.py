# operators.py
import importlib
import os
import subprocess
import sys
import traceback
from typing import List, Optional, Set, Tuple

import addon_utils
import bpy

from . import utils
from .data_manager import dm
from .log import log


class ADDONRELOADER_OT_reload_addon(bpy.types.Operator):
    """负责重新加载选定的插件或扩展"""
    bl_idname = "addonreloader.reload_addon"
    bl_label = "Reload Addon"
    bl_description = "Fast Reload"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        """检查是否可以选择插件/扩展进行重载"""
        return dm.last_selected[0] != "no_addons"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """执行插件/扩展重载操作"""
        target_item = dm.last_selected
        log.info("开始重载: %s", target_item[1])

        try:
            my_addon = dm.my_addon_names.get("Addon")
            my_extend = dm.my_addon_names.get("Extend")
            if target_item[0] in {my_addon, my_extend}:
                self.report({"WARNING"}, "Cannot reload Addon Reloader itself")
                return {"CANCELLED"}

            # 检查插件/扩展是否启用
            was_enabled = utils.is_addon_enabled(target_item[0])

            # 执行重载
            success = self._reload_modules(
                context, target_item[0], was_enabled)

            if success:
                utils.refresh_addon_list(force=True)
                utils.sync_addon_state(context)
                self.report(
                    {"INFO"}, f"[ {target_item[1]} ] Reloaded!")
                return {"FINISHED"}

            self.report({"ERROR"}, f"[ {target_item[1]} ] Reload Failed!")
            return {"CANCELLED"}

        except Exception as e:
            self.report(
                {"ERROR"}, f"Error reloading {target_item[0]}: {str(e)}")
            log.debug("重载时发生错误 %s : %s", target_item[0], str(e))
            return {"CANCELLED"}

    def _reload_modules(self, context: bpy.types.Context, module_name: str, was_enabled: bool) -> bool:
        """重新加载插件/扩展及其所有相关模块"""
        root_module_name = module_name
        log.debug("正在重载模块: %s", root_module_name)

        try:
            # 获取模块
            target_module = None
            for mod in addon_utils.modules():
                if mod.__name__ == root_module_name:
                    target_module = mod
                    break

            # 如果未找到模块，记录错误并返回False
            if not target_module:
                log.error("未找到模块: %s", root_module_name)
                return False

            # 保存模块路径
            module_path = os.path.dirname(target_module.__file__)
            log.debug("模块路径: %s", module_path)

            # 完全卸载模块，就像Blender卸载时一样
            log.debug("正在完全移除模块: %s", root_module_name)

            # 确保模块被完全禁用
            addon_utils.disable(root_module_name)

            # 手动注销所有已注册的类
            if hasattr(target_module, "classes"):
                for cls in reversed(target_module.classes):
                    try:
                        log.debug("手动注销类: %s", cls.__name__)
                        bpy.utils.unregister_class(cls)
                    except Exception as e:
                        log.debug("注销类失败 %s: %s", cls.__name__, str(e))

            # 调用模块的unregister函数
            if hasattr(target_module, "unregister"):
                try:
                    target_module.unregister()
                    log.debug("模块注销成功")
                except Exception as e:
                    log.error("模块注销失败: %s", str(e))

            # 从sys.modules中完全移除所有相关模块
            modules_to_remove: List[str] = [
                name for name in sys.modules
                if name == root_module_name or name.startswith(f"{root_module_name}.")
            ]

            for name in modules_to_remove:
                log.debug("从sys.modules移除模块: %s", name)
                del sys.modules[name]

            # 清除importlib缓存
            importlib.invalidate_caches()

            # 如果模块原来已启用，则重新启用它
            if was_enabled:
                try:
                    # 使用addon_utils重新启用模块，就像Blender安装时一样
                    result = addon_utils.enable(root_module_name, default_set=True)
                    if result is not None:
                        log.debug("模块重新启用成功")
                        return True

                    log.error("模块重新启用失败")
                    return False

                except Exception as e:
                    log.error("启用模块失败: %s, 错误: %s", root_module_name, str(e))
                    log.error(traceback.format_exc())
                    self.report(
                        {"ERROR"}, f"Failed to reload module {root_module_name}")
                    return False

            return True

        except Exception as e:
            log.error("模块重载失败: %s, 错误: %s", root_module_name, str(e))
            log.error(traceback.format_exc())
            self.report(
                {"ERROR"}, f"Error reloading module {root_module_name}: {str(e)}")
            return False


class ADDONRELOADER_OT_dropdown_list(bpy.types.Operator):
    """提供插件/扩展选择下拉列表"""
    bl_idname = "addonreloader.dropdown_list"
    bl_label = "Addon List"
    bl_description = "List"
    bl_property = "enum_items"

    def _get_enum_items(self, context: bpy.types.Context) -> List[Tuple[str, str, str, str, int]]:
        """获取枚举项列表"""
        items = dm.show_lists
        return items if items else dm.ddmenu_default_val

    enum_items: bpy.props.EnumProperty(items=_get_enum_items)  # type: ignore

    def _find_selected_item(self, idname: str) -> Optional[Tuple[str, str, str, str, int]]:
        """根据ID名称查找插件/扩展"""
        for item_tuple in dm.show_lists:
            if item_tuple[0] == idname:
                return item_tuple
        return None

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """执行插件/扩展选择操作"""
        if not dm.show_lists:
            return {"CANCELLED"}

        log.info("选择 %s", self.enum_items)

        # 更新最后选择的值
        last_selected = self._find_selected_item(self.enum_items)
        if last_selected:
            dm.last_selected = last_selected
            utils.sync_addon_state(context)

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        """调用插件/扩展选择下拉列表"""
        # 显示下拉列表前先刷新列表
        log.debug("显示下拉列表前自动刷新")
        utils.refresh_addon_list(force=True)

        # 保存当前鼠标位置
        current_mouse_x = event.mouse_x
        current_mouse_y = event.mouse_y

        # 调整鼠标位置（偏移以在按钮下方显示弹窗）
        offset_x = 0   # 水平偏移
        offset_y = -30  # 垂直偏移
        context.window.cursor_warp(
            current_mouse_x + offset_x, current_mouse_y + offset_y)

        # 调用原始搜索弹窗
        context.window_manager.invoke_search_popup(self)

        # 操作完成后恢复鼠标位置
        context.window.cursor_warp(current_mouse_x, current_mouse_y)

        return {"FINISHED"}


class ADDONRELOADER_OT_refresh_list(bpy.types.Operator):
    """刷新可用插件/扩展列表"""
    bl_idname = "addonreloader.refresh_list"
    bl_label = "Refresh"
    bl_description = "Refresh addon/extension list"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """执行列表刷新操作"""
        log.debug("执行列表刷新")
        refreshed = utils.refresh_addon_list(force=True)
        log.debug("刷新结果: %s", refreshed)

        if refreshed is None:
            self.report({"INFO"}, "List refreshed")
            return {"FINISHED"}

        self.report({"ERROR"}, "No items found")
        return {"CANCELLED"}


class ADDONRELOADER_OT_open_addon_folder(bpy.types.Operator):
    """打开选定的插件/扩展文件夹"""
    bl_idname = "addonreloader.open_addon_folder"
    bl_label = "Open Folder"
    bl_description = "Open the folder of the currently selected addon or extension"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """执行文件夹打开操作"""

        # 检查是否选择了项
        selected_idname = dm.last_selected[0]
        if selected_idname == "no_addons":
            self.report({"WARNING"}, "No addon/extension selected!")
            return {"CANCELLED"}

        try:
            selected_item_full_path = dm.addons_paths[selected_idname]
            selected_item_path = os.path.dirname(selected_item_full_path)

            # 检查操作系统类型
            if os.name == "nt":  # Windows
                os.startfile(selected_item_path)
            elif os.name == "posix":  # macOS or Linux
                if sys.platform == "darwin":
                    subprocess.Popen(("open", selected_item_path))
                else:
                    subprocess.Popen(("xdg-open", selected_item_path))

            log.debug(f"打开文件夹: {dm.last_selected[1]}")
            self.report({"INFO"}, f"[ {dm.last_selected[1]} ] Folder Opened!")
            return {"FINISHED"}
        except Exception as e:
            log.error(f"打开文件夹失败: {str(e)}")
            self.report({"ERROR"}, f"Open Folder Failed: {str(e)}")
            return {"CANCELLED"}


class ADDONRELOADER_OT_enable_or_disable_addon(bpy.types.Operator):
    """切换选定插件/扩展的状态"""
    bl_idname = "addonreloader.enable_or_disable_addon"
    bl_label = "Toggle State"
    bl_description = "Toggle the state of the currently selected addon or extension"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """执行启用/禁用切换操作"""
        log.info("启用或禁用项")

        # 检查是否选择了项
        last_selected = dm.last_selected
        if last_selected[0] == "no_addons":
            self.report(
                {"WARNING"}, "Operation failed, no addon/extension selected!")
            log.warning("操作失败，未选中插件/扩展！")
            return {"CANCELLED"}

        try:
            log.debug("上次选择的项: %s", last_selected[1])

            # 获取当前项状态
            now_item_state = utils.is_addon_enabled(last_selected[0])
            log.debug("当前项状态: %s", now_item_state)

            if not now_item_state:
                # 启用项
                enabled = addon_utils.enable(
                    last_selected[0], default_set=True)
                if enabled is not None:
                    log.info("[%s] 启用成功!", last_selected[1])
                    self.report(
                        {"INFO"}, f"[{last_selected[1]}] Enabled!")
                    utils.refresh_addon_list(force=True)
                    utils.sync_addon_state(context)
                    return {"FINISHED"}

                log.info("[%s] 启用失败!", last_selected[1])
                self.report(
                    {"WARNING"}, f"[{last_selected[1]}] Enable Failed!")
                utils.sync_addon_state(context)
                return {"CANCELLED"}

            # 禁用项
            disabled = addon_utils.disable(last_selected[0], default_set=True)
            if disabled is None:
                log.info("[%s] 禁用成功!", last_selected[1])
                self.report({"INFO"}, f"[{last_selected[1]}] Disabled!")
                utils.refresh_addon_list(force=True)
                utils.sync_addon_state(context)
                return {"FINISHED"}

            log.info("[%s] 禁用失败!", last_selected[1])
            self.report(
                {"ERROR"}, f"[{last_selected[1]}] Disable Failed!")
            utils.sync_addon_state(context)
            return {"CANCELLED"}

        except Exception as e:
            log.error("切换项状态时发生错误: %s", str(e))
            self.report({"ERROR"}, f"Error toggling item state: {str(e)}")
            return {"CANCELLED"}
