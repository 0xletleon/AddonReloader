import bpy
import os

# 插件元数据
bl_info = {
    "name": "Addon Reloader",
    "author": "letleon ,claude-3-5-sonnet",
    "version": (1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Addon Reloader",
    "description": "Easily reload addons without restarting Blender",
    "warning": "",
    "doc_url": "",
    "category": "Development",
}

# 存储插件列表的全局变量
# Global variable to store the addon list
addon_list = []

class ADDONRELOADER_PT_panel(bpy.types.Panel):
    """定义插件的面板类"""
    """Define the panel class for the addon"""
    bl_idname = "ADDONRELOADER_PT_panel"
    bl_label = "Addon Reloader"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Addon Reloader'

    def draw(self, context):
        """绘制面板的UI元素"""
        """Draw the UI elements of the panel"""
        layout = self.layout
        scene = context.scene

        row = layout.row(align=True)
        row.prop(scene, "addon_to_reload", text="")
        row.operator("addonreloader.refresh_list", text="", icon='FILE_REFRESH')

        layout.operator("addonreloader.reload_addon", text="Reload Addon")

class ADDONRELOADER_OT_reload_addon(bpy.types.Operator):
    """定义重新加载插件的操作类"""
    """Define the operator class for reloading addons"""
    bl_idname = "addonreloader.reload_addon"
    bl_label = "Reload Addon"
    bl_description = "Disable and re-enable the selected addon"

    def execute(self, context):
        """执行重新加载插件的操作"""
        """Execute the addon reloading operation"""
        addon_name = context.scene.addon_to_reload
        if addon_name:
            try:
                bpy.ops.preferences.addon_disable(module=addon_name)
                bpy.ops.preferences.addon_enable(module=addon_name)
                self.report({'INFO'}, f"Addon '{addon_name}' reloaded successfully")
            except Exception as e:
                self.report({'ERROR'}, f"Error reloading addon: {str(e)}")
        else:
            self.report({'WARNING'}, "No addon selected")
        return {'FINISHED'}

class ADDONRELOADER_OT_refresh_list(bpy.types.Operator):
    """定义刷新插件列表的操作类"""
    """Define the operator class for refreshing the addon list"""
    bl_idname = "addonreloader.refresh_list"
    bl_label = "Refresh Addon List"
    bl_description = "Refresh the list of user-installed addons"

    def execute(self, context):
        """执行刷新插件列表的操作"""
        """Execute the addon list refreshing operation"""
        update_addon_list()
        self.report({'INFO'}, "Addon list refreshed")
        return {'FINISHED'}

def get_addon_list(self, context):
    """返回插件列表，用于EnumProperty"""
    """Return the addon list for EnumProperty"""
    global addon_list
    return addon_list

def is_user_addon(module_name):
    """检查插件是否为用户安装的插件"""
    """Check if the addon is user-installed"""
    addon_path = bpy.utils.user_resource('SCRIPTS', path="addons")
    return os.path.exists(os.path.join(addon_path, module_name))

def update_addon_list():
    """更新可重新加载的插件列表"""
    """Update the list of reloadable addons"""
    global addon_list
    current_addon_name = __name__.split('.')[0]
    addon_list = [(addon.module, addon.module, "") for addon in bpy.context.preferences.addons 
                  if is_user_addon(addon.module) and addon.module != current_addon_name]

def register():
    """注册插件的类和属性"""
    """Register the addon's classes and properties"""
    update_addon_list()
    bpy.types.Scene.addon_to_reload = bpy.props.EnumProperty(
        name="",
        description="Select the addon to reload",
        items=get_addon_list
    )
    bpy.utils.register_class(ADDONRELOADER_PT_panel)
    bpy.utils.register_class(ADDONRELOADER_OT_reload_addon)
    bpy.utils.register_class(ADDONRELOADER_OT_refresh_list)

def unregister():
    """注销插件的类和属性"""
    """Unregister the addon's classes and properties"""
    del bpy.types.Scene.addon_to_reload
    bpy.utils.unregister_class(ADDONRELOADER_PT_panel)
    bpy.utils.unregister_class(ADDONRELOADER_OT_reload_addon)
    bpy.utils.unregister_class(ADDONRELOADER_OT_refresh_list)

if __name__ == "__main__":
    register()