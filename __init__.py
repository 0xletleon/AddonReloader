import importlib
import os
import sys

import addon_utils
import bpy
from bpy.props import EnumProperty

# 插件元数据 Addon metadata
bl_info = {
    "name": "Addon Reloader",
    "author": "letleon, claude-3-5-sonnet",
    "version": (1, 2, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Reload",
    "description": "Fast reload of user add-on or extensions.\n快速重新加载用户插件或扩展",
    "category": "Development",
    "doc_url": "https://github.com/0xletleon/AddonReloader",
    "tracker_url": "https://github.com/0xletleon/AddonReloader/issues",
}

# 全局变量 Global variables
addon_list = []
extension_list = []
last_selected_addon = None
last_selected_extension = None
last_selected_all = None
addon_list_loaded = False


def is_user_addon(module_name):
    """
    检查是否为用户插件
    Check if it's a user addon in scripts/addons directory
    """
    addon_path = bpy.utils.user_resource('SCRIPTS', path="addons")
    return os.path.exists(os.path.join(addon_path, module_name))


def get_extension_source(module_name):
    """
    获取扩展来源目录名
    Get the source directory name of the extension
    """
    base_path = bpy.utils.user_resource('CONFIG')
    extensions_root = os.path.join(os.path.dirname(base_path), "extensions")

    # 只检查直接子目录
    if os.path.exists(extensions_root):
        for source_dir in os.listdir(extensions_root):
            source_path = os.path.join(extensions_root, source_dir)
            if os.path.isdir(source_path):
                if module_name in os.listdir(source_path):
                    return source_dir
    return ""


def get_enabled_extensions():
    """
    获取所有已启用的扩展模块名称
    Get all enabled extension module names
    """
    current_addon_id = "addon_reloader"
    return {
        mod.module.split('.')[-1]
        for mod in bpy.context.preferences.addons
        if mod.module.startswith('bl_ext.') and current_addon_id not in mod.module.lower()
    }


def update_addon_list():
    """
    更新可重新加载的项目列表
    Update the list of reloadable items
    """
    global addon_list, extension_list, addon_list_loaded
    if addon_list_loaded:
        return
    addon_list.clear()
    extension_list.clear()

    current_addon_id = "addon_reloader"
    wm = bpy.context.window_manager
    addon_counter = 1
    extension_counter = 1000

    # ADDONS
    if wm.addon_list_mode in {'ADDONS', 'ALL'}:
        user_addons_path = bpy.utils.user_resource('SCRIPTS', path="addons")
        for addon in bpy.context.preferences.addons:
            module_name = addon.module
            if current_addon_id in module_name.lower():
                continue
            addon_path = os.path.join(user_addons_path, module_name)
            module_path = os.path.join(user_addons_path, module_name + ".py")
            if os.path.exists(addon_path) or os.path.exists(module_path):
                display_name = f"{module_name}"
                addon_list.append((module_name, display_name, "", 'PLUGIN', addon_counter))
                addon_counter += 1

    # EXTENSIONS
    if wm.addon_list_mode in {'EXTENSIONS', 'ALL'}:
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
                            display_name = f"{ext_name}"
                            extension_list.append((ext_name, display_name, "", 'LINKED', extension_counter))
                            extension_counter += 1

    # set state
    addon_list_loaded = True


def get_addon_list(self, context):
    """
    获取列表用于EnumProperty
    Get list for EnumProperty
    """
    wm = context.window_manager
    if wm.addon_list_mode == 'ADDONS':
        return addon_list
    elif wm.addon_list_mode == 'EXTENSIONS':
        return extension_list
    else:
        return addon_list + extension_list


def update_addon_list_mode(self, context):
    """
    切换标签页时更新选择
    Update selection when switching tabs
    """
    global last_selected_addon, last_selected_extension, last_selected_all
    if not addon_list_loaded:
        update_addon_list()

    if self.addon_list_mode == 'ADDONS':
        current_list = addon_list
        last_selected = last_selected_addon
    elif self.addon_list_mode == 'EXTENSIONS':
        current_list = extension_list
        last_selected = last_selected_extension
    else:  # ALL mode
        current_list = addon_list + extension_list
        last_selected = last_selected_all

    if last_selected and any(item[0] == last_selected for item in current_list):
        context.window_manager.addon_to_reload = last_selected
    elif current_list:
        context.window_manager.addon_to_reload = current_list[0][0]


def update_addon_selection(self, context):
    """
    当选择改变时更新状态
    Update state when selection changes
    """
    global last_selected_addon, last_selected_extension, last_selected_all
    selected = self.addon_to_reload
    if not selected or selected == 'NONE':
        return
    if self.addon_list_mode == 'ADDONS':
        last_selected_addon = selected
    elif self.addon_list_mode == 'EXTENSIONS':
        last_selected_extension = selected
    else:  # ALL mode
        last_selected_all = selected


class AddonReloader(bpy.types.Panel):
    """
    面板类定义
    Panel class definition
    """
    bl_idname = "addon_reloader"
    bl_label = "Addon Reloader"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Reload'

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        row = layout.row()
        row.prop(wm, "addon_list_mode", expand=True)
        row = layout.row(align=True)
        row.prop(wm, "addon_to_reload", text="")
        row.operator("addonreloader.refresh_list", text="", icon='FILE_REFRESH')
        layout.operator("addonreloader.reload_addon", text="Reload")


class ADDONRELOADER_OT_reload_addon(bpy.types.Operator):
    """
    重新加载插件的操作类
    Operator class for reloading addons
    """
    bl_idname = "addonreloader.reload_addon"
    bl_label = "Reload Addon"
    bl_description = "Disable and re-enable the selected add-on or extension"

    def execute(self, context):
        try:
            addon_name = context.window_manager.addon_to_reload
            if not addon_name:
                self.report({'WARNING'}, "No item selected")
                return {'CANCELLED'}

            if is_user_addon(addon_name):
                self.reload_addon(addon_name)
            else:
                self.reload_extension(addon_name)

            self.report({'INFO'}, f"Reloaded Successfully [ {addon_name} ] √")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Error reloading {addon_name}: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {'CANCELLED'}

    def reload_addon(self, addon_name):
        """
        重新加载插件
        Reload addon
        """
        addon_utils.disable(addon_name, default_set=False)
        addon_utils.enable(addon_name, default_set=False, persistent=True)

    def reload_extension(self, addon_name):
        """
        重新加载扩展及其所有子模块
        Reload extension and all its submodules
        """
        ext_source = get_extension_source(addon_name)
        ext_module = f"bl_ext.{ext_source}.{addon_name}"

        # 禁用扩展 disable extension
        addon_utils.disable(ext_module, default_set=False)

        # 重载所有模块 Reload all modules
        module = sys.modules.get(ext_module)
        if module:
            submodules = [name for name in sys.modules if name.startswith(f"{ext_module}.")]

            # 重新加载所有子模块 Reload all sub modules
            importlib.reload(module)
            for submodule_name in submodules:
                if submodule_name in sys.modules:
                    # print(f"Reloading submodule: {submodule_name}")
                    importlib.reload(sys.modules[submodule_name])

            # 重新加载主模块 reload main modules
            # print(f"Reloading main module: {ext_module}")
            importlib.reload(module)

        # 重新启用扩展 Enable extension
        addon_utils.enable(ext_module, default_set=False, persistent=True)


class ADDONRELOADER_OT_refresh_list(bpy.types.Operator):
    """
    刷新列表的操作类
    Operator class for refreshing the list
    """
    bl_idname = "addonreloader.refresh_list"
    bl_label = "Refresh List"
    bl_description = "Refresh the list of items"

    def execute(self, context):
        update_addon_list()
        self.report({'INFO'}, "List refreshed √")
        return {'FINISHED'}


def register():
    """
    注册插件类和属性
    Register addon classes and properties
    """
    bpy.types.WindowManager.addon_list_mode = EnumProperty(
        name="List Mode",
        description="Select type",
        items=[
            ('ADDONS', 'Add-ons', 'Show add-ons'),
            ('EXTENSIONS', 'Extensions', 'Show extensions'),
            ('ALL', 'All', 'Show all')
        ],
        default='ALL',
        update=update_addon_list_mode
    )

    bpy.types.WindowManager.addon_to_reload = EnumProperty(
        name="",
        description="Select add-on or extensions to reload",
        items=get_addon_list,
        update=update_addon_selection
    )

    bpy.utils.register_class(AddonReloader)
    bpy.utils.register_class(ADDONRELOADER_OT_reload_addon)
    bpy.utils.register_class(ADDONRELOADER_OT_refresh_list)

    update_addon_list()


def unregister():
    """
    注销插件类和属性
    Unregister addon classes and properties
    """
    del bpy.types.WindowManager.addon_to_reload
    del bpy.types.WindowManager.addon_list_mode

    bpy.utils.unregister_class(AddonReloader)
    bpy.utils.unregister_class(ADDONRELOADER_OT_reload_addon)
    bpy.utils.unregister_class(ADDONRELOADER_OT_refresh_list)


if __name__ == "__main__":
    register()
