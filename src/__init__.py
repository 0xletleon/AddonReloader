# __init__.py
import bpy

from . import ui, operators, utils

classes = (
    ui.ADDONRELOADER_PT_popover_panel,
    operators.ADDONRELOADER_OT_reload_addon,
    operators.ADDONRELOADER_OT_refresh_list,
)


def register():
    # 获取自己的模块名 - Get my module name
    utils.get_my_module_name(__package__)

    # 注册类 - Register classes
    for cls in classes:
        bpy.utils.register_class(cls)

    # 注册属性 - Register properties
    wm = bpy.types.WindowManager

    # 插件标签值 - Addon tabs value
    wm.addonreloader_addon_tabs = bpy.props.EnumProperty(
        items=[
            ("ADDONS", "Add-ons", "User Add-ons"),
            ("EXTENSIONS", "Extensions", "User Extensions"),
        ],
        default="ADDONS",
        update=ui.update_tabs_index,
        options={"SKIP_SAVE"},
    )

    # 下拉菜单默认值 - Dropdown menu default value
    wm.addonreloader_ddmenu_default_val = bpy.props.EnumProperty(
        name="", items=ui.get_ddmenu_default_val, options={"SKIP_SAVE"}
    )

    # 下拉菜单列表 - Dropdown menu list
    wm.addonreloader_ddmenu_list = bpy.props.EnumProperty(
        name="",
        items=ui.get_ddmenu_list,
        update=ui.update_last_selected,
        options={"SKIP_SAVE"},
    )

    # 选中的插件或扩展状态 - Selected addon or extension status
    wm.addonreloader_addon_state = bpy.props.BoolProperty(
        name="State of the addon or extension",
        description="Click to enable/disable",
        default=True,
        update=ui.update_toggle_state,
        options={"SKIP_SAVE"},
    )

    # 注册顶部菜单 - Register top bar menu
    bpy.types.TOPBAR_HT_upper_bar.append(ui.draw_topbar_menu)

    # 首次获取插件列表 - Get addon list first time
    utils.refresh_addon_list(None, bpy.context)


def unregister():
    # 注销顶部菜单 - Unregister top bar menu
    bpy.types.TOPBAR_HT_upper_bar.remove(ui.draw_topbar_menu)

    # 注销属性 - Unregister properties
    wm = bpy.types.WindowManager
    del wm.addonreloader_addon_tabs
    del wm.addonreloader_ddmenu_default_val
    del wm.addonreloader_ddmenu_list

    # 注销类 - Unregister classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
