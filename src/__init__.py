# __init__.py
import bpy

from . import ui, operators, utils


# 属性组
class AddonReloaderPropertyGroup(bpy.types.PropertyGroup):
    addon_state: bpy.props.BoolProperty(
        name="Addon status",
        description="Click to enable/disable addon",
        default=False,
        update=ui.update_toggle_addon_state,
        options={"SKIP_SAVE"},
    )


classes = (
    operators.ADDONRELOADER_OT_reload_addon,
    operators.ADDONRELOADER_OT_refresh_list,
    operators.ADDONRELOADER_OT_dropdown_list,
    operators.ADDONRELOADER_OT_open_addon_folder,
    AddonReloaderPropertyGroup,
)


def register():
    # 获取自己的模块名
    utils.get_my_module_names(__package__)

    # 注册类
    for cls in classes:
        bpy.utils.register_class(cls)

    # 注册属性组
    bpy.types.WindowManager.addonreloader = bpy.props.PointerProperty(
        type=AddonReloaderPropertyGroup
    )

    # 注册顶部菜单
    bpy.types.TOPBAR_HT_upper_bar.append(ui.draw_topbar_menu)

    # 延时获取插件列表
    bpy.app.timers.register(utils.check_blender_ready)


def unregister():
    # 注销顶部菜单
    bpy.types.TOPBAR_HT_upper_bar.remove(ui.draw_topbar_menu)

    # 注销属性组
    del bpy.types.WindowManager.addonreloader

    # 注销类
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
