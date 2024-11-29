import importlib
import logging
import os
import sys
from typing import List, Tuple, Dict

import addon_utils
import bpy
from bpy.props import EnumProperty

# 设置日志 logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局变量 global variable
addon_list: List[Tuple[str, str, str, str, int]] = []
extension_list: List[Tuple[str, str, str, str, int]] = []
all_items_list: List[Tuple[str, str, str, str, int]] = []
last_selected: Dict[str, str] = {'ADDONS': None, 'EXTENSIONS': None, 'ALL': None}
lists_initialized: bool = False
last_addons: set = set()


def is_user_addon(module_name: str) -> bool:
    """检查是否为用户插件 Check if the module is a user addon."""
    addon_path = bpy.utils.user_resource('SCRIPTS', path="addons")
    return os.path.exists(os.path.join(addon_path, module_name))


def get_extension_source(module_name: str) -> str:
    """获取扩展来源目录名 Get the source directory name of the extension."""
    base_path = bpy.utils.user_resource('CONFIG')
    extensions_root = os.path.join(os.path.dirname(base_path), "extensions")

    if os.path.exists(extensions_root):
        for source_dir in os.listdir(extensions_root):
            source_path = os.path.join(extensions_root, source_dir)
            if os.path.isdir(source_path) and module_name in os.listdir(source_path):
                return source_dir
    return ""


def get_enabled_extensions() -> set:
    """获取所有已启用的扩展模块名称 Get all enabled extension module names."""
    current_addon_id = __name__
    return {
        mod.module.split('.')[-1]
        for mod in bpy.context.preferences.addons
        if mod.module.startswith('bl_ext.') and current_addon_id not in mod.module.lower()
    }


def update_addon_list():
    """更新可重新加载的项目列表 Update the list of items that can be reloaded."""
    global addon_list, extension_list, all_items_list, lists_initialized
    addon_list.clear()
    extension_list.clear()

    current_addon_id = __name__
    addon_counter = 1
    extension_counter = 1000

    # ADDONS
    user_addons_path = bpy.utils.user_resource('SCRIPTS', path="addons")
    for addon in bpy.context.preferences.addons:
        module_name = addon.module
        if current_addon_id in module_name.lower():
            continue
        addon_path = os.path.join(user_addons_path, module_name)
        module_path = os.path.join(user_addons_path, module_name + ".py")
        if os.path.exists(addon_path) or os.path.exists(module_path):
            addon_list.append((module_name, module_name, "", 'PLUGIN', addon_counter))
            addon_counter += 1

    # EXTENSIONS
    base_path = bpy.utils.user_resource('CONFIG')
    extensions_root = os.path.join(os.path.dirname(base_path), "extensions")
    enabled_extensions = get_enabled_extensions()

    if os.path.exists(extensions_root):
        for repo_name in os.listdir(extensions_root):
            repo_path = os.path.join(extensions_root, repo_name)
            if os.path.isdir(repo_path) and repo_name not in ['.cache']:
                for ext_name in os.listdir(repo_path):
                    if current_addon_id in ext_name.lower():
                        continue
                    ext_path = os.path.join(repo_path, ext_name)
                    if os.path.isdir(ext_path) and ext_name != '.blender_ext' and ext_name in enabled_extensions:
                        extension_list.append((ext_name, ext_name, "", 'LINKED', extension_counter))
                        extension_counter += 1

    # 如果列表为空，添加默认选项 Add default option if list is empty
    if not addon_list:
        addon_list.append(('NONE', 'No Add-ons', '', 'PLUGIN', 0))
    if not extension_list:
        extension_list.append(('NONE', 'No Extensions', '', 'LINKED', 0))

    all_items_list = addon_list + extension_list
    lists_initialized = True


def get_addon_list(self, context):
    """获取列表用于EnumProperty"""
    global lists_initialized
    if not lists_initialized:
        update_addon_list()

    wm = context.window_manager if context else bpy.context.window_manager

    # 确保至少返回一个默认选项 Make sure to return at least one default option
    default_option = [('NONE', 'No Items', '', 'PLUGIN', 0)]

    if wm.addon_list_mode == 'ADDONS':
        return addon_list if addon_list else default_option
    elif wm.addon_list_mode == 'EXTENSIONS':
        return extension_list if extension_list else default_option
    else:
        return all_items_list if all_items_list else default_option


def update_addon_list_mode(self, context):
    """切换标签页时更新选择"""
    global last_selected
    if not lists_initialized:
        update_addon_list()

    current_list = get_addon_list(None, context)

    last_selected_item = last_selected.get(self.addon_list_mode)

    if current_list:
        if last_selected_item and any(item[0] == last_selected_item for item in current_list):
            context.window_manager.addon_to_reload = last_selected_item
        else:
            context.window_manager.addon_to_reload = current_list[0][0]
    else:
        context.window_manager.addon_to_reload = 'NONE'


def update_addon_selection(self, context):
    """当选择改变时更新状态 Update the state when the selection changes."""
    global last_selected
    try:
        selected = self.addon_to_reload
        if selected and selected != 'NONE':
            last_selected[self.addon_list_mode] = selected
    except Exception as e:
        logger.error(f"Error in update_addon_selection: {str(e)}")
        self.addon_to_reload = 'NONE'


class AddonReloader(bpy.types.Panel):
    """面板类定义 Panel class definition."""
    bl_idname = "ADDON_PT_reloader"
    bl_label = "Addon Reloader"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Reload'

    def draw(self, context):
        """绘制面板 Draw the panel."""
        layout = self.layout
        wm = context.window_manager
        row = layout.row()
        row.prop(wm, "addon_list_mode", expand=True)
        row = layout.row(align=True)
        row.prop(wm, "addon_to_reload", text="")
        row.operator("addonreloader.refresh_list", text="", icon='FILE_REFRESH')
        layout.operator("addonreloader.reload_addon", text="Reload")


def is_addon_enabled(addon_name: str) -> bool:
    """检查插件是否启用 Check if the addon is enabled"""
    return addon_name in {addon.module for addon in bpy.context.preferences.addons}


def is_extension_enabled(ext_name: str) -> bool:
    """检查扩展是否启用 Check if the extension is enabled"""
    ext_source = get_extension_source(ext_name)
    if ext_source:
        full_module_name = f"bl_ext.{ext_source}.{ext_name}"
        return full_module_name in {addon.module for addon in bpy.context.preferences.addons}
    return False


class ADDONRELOADER_OT_reload_addon(bpy.types.Operator):
    """重新加载插件的操作类 Operator class to reload the addon."""
    bl_idname = "addonreloader.reload_addon"
    bl_label = "Reload Addon"
    bl_description = "Disable and re-enable the selected add-on or extension"

    @classmethod
    def poll(cls, context):
        """判断操作是否可用 Determine if the operator is available."""
        return context.window_manager.addon_to_reload not in {'', 'NONE'}

    def execute(self, context):
        addon_name = context.window_manager.addon_to_reload
        try:
            if is_user_addon(addon_name):
                if not is_addon_enabled(addon_name):
                    self.report({'WARNING'}, f"Add-on [ {addon_name} ] is disabled. Please enable it first!")
                    bpy.ops.addonreloader.refresh_list()
                    return {'CANCELLED'}
                self.reload_addon(addon_name)
            else:
                if not is_extension_enabled(addon_name):
                    self.report({'WARNING'}, f"Extension [ {addon_name} ] is disabled. Please enable it first!")
                    bpy.ops.addonreloader.refresh_list()
                    return {'CANCELLED'}
                self.reload_extension(addon_name)

            self.report({'INFO'}, f"Reloaded Successfully [ {addon_name} ] √")
            return {'FINISHED'}

        except Exception as e:
            logger.error(f"Error reloading {addon_name}: {str(e)}", exc_info=True)
            self.report({'ERROR'}, f"Error reloading {addon_name}: {str(e)}")
            bpy.ops.addonreloader.refresh_list()
            return {'CANCELLED'}

    def reload_addon(self, addon_name: str):
        """重新加载插件 Reload the addon."""
        addon_utils.disable(addon_name, default_set=False)
        addon_utils.enable(addon_name, default_set=False, persistent=True)

    def reload_extension(self, addon_name: str):
        """重新加载扩展及其所有子模块 Reload the extension and all its submodules."""
        ext_source = get_extension_source(addon_name)
        ext_module = f"bl_ext.{ext_source}.{addon_name}"
        addon_utils.disable(ext_module, default_set=False)
        module = sys.modules.get(ext_module)
        if module:
            submodules = [name for name in sys.modules if name.startswith(f"{ext_module}.")]
            importlib.reload(module)
            for submodule_name in submodules:
                if submodule_name in sys.modules:
                    importlib.reload(sys.modules[submodule_name])

            importlib.reload(module)

        addon_utils.enable(ext_module, default_set=False, persistent=True)


class ADDONRELOADER_OT_refresh_list(bpy.types.Operator):
    """刷新列表的操作类 Operator class to refresh the list."""
    bl_idname = "addonreloader.refresh_list"
    bl_label = "Refresh List"
    bl_description = "Refresh the list of items"

    def execute(self, context):
        global lists_initialized
        lists_initialized = False
        update_addon_list()
        update_addon_list_mode(context.window_manager, context)
        return {'FINISHED'}


classes = (
    AddonReloader,
    ADDONRELOADER_OT_reload_addon,
    ADDONRELOADER_OT_refresh_list
)


def on_depsgraph_update_post(scene, depsgraph):
    """在依赖图更新后检查插件状态 Check addon status after dependency graph update."""
    try:
        check_addon_status()
    except Exception as e:
        logger.error(f"Error in on_depsgraph_update_post: {str(e)}")
    finally:
        # 确保 EnumProperty 被更新
        bpy.context.window_manager.addon_to_reload = bpy.context.window_manager.addon_to_reload


def check_addon_status():
    """检查并记录插件状态的变化 Check and log changes in addon status."""
    global last_addons, lists_initialized
    current_addons = {addon.module for addon in bpy.context.preferences.addons}

    added_addons = current_addons - last_addons
    removed_addons = last_addons - current_addons

    if added_addons or removed_addons:
        lists_initialized = False
        update_addon_list()
        last_addons = current_addons
        
        # 确保当前选择的项目仍然有效 Ensure that the currently selected item is still valid
        wm = bpy.context.window_manager
        if wm.addon_to_reload not in [item[0] for item in get_addon_list(None, bpy.context)]:
            update_addon_list_mode(wm, bpy.context)


def register():
    for cls in classes:
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.addon_list_mode = EnumProperty(
        name="List Mode",
        description="Select type",
        items=[
            ('ADDONS', 'Add-ons', 'Show add-ons'),
            ('EXTENSIONS', 'Extensions', 'Show extensions'),
            ('ALL', 'All', 'Show all')
        ],
        default='ADDONS',
        update=update_addon_list_mode
    )
    
    # 首先更新列表
    update_addon_list()

    # 然后注册 addon_to_reload 属性
    bpy.types.WindowManager.addon_to_reload = EnumProperty(
        name="",
        description="Select add-on or extensions to reload",
        items=get_addon_list,
        update=update_addon_selection
    )

    # 最后设置初始值
    wm = bpy.context.window_manager
    items = get_addon_list(None, bpy.context)
    if items:
        wm.addon_to_reload = items[0][0]
    else:
        wm.addon_to_reload = 'NONE'

    bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update_post)
    


def unregister():
    if on_depsgraph_update_post in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update_post)

    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass

    try:
        del bpy.types.WindowManager.addon_to_reload
        del bpy.types.WindowManager.addon_list_mode
    except AttributeError:
        pass


if __name__ == "__main__":
    register()
