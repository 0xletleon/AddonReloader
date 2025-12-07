# __init__.py
import bpy

from . import ui, operators, utils


# 插件属性组定义
class AddonReloaderPropertyGroup(bpy.types.PropertyGroup):
    addon_state: bpy.props.BoolProperty(
        name="Addon status",
        description="Status of the addon",
        default=False,
        options={'SKIP_SAVE'},
    )  # type: ignore


# 插件类列表
classes = (
    AddonReloaderPropertyGroup,
    operators.ADDONRELOADER_OT_reload_addon,
    operators.ADDONRELOADER_OT_dropdown_list,
    operators.ADDONRELOADER_OT_refresh_list,
    operators.ADDONRELOADER_OT_open_addon_folder,
    operators.ADDONRELOADER_OT_enable_or_disable_addon,
)


def register():
    """注册插件"""
    # 获取当前插件的模块名称
    utils.get_my_module_names(__package__)

    # 注册所有类
    for cls in classes:
        bpy.utils.register_class(cls)

    # 注册属性组
    bpy.types.WindowManager.addonreloader = bpy.props.PointerProperty(
        type=AddonReloaderPropertyGroup
    )

    # 注册顶部菜单绘制函数
    bpy.types.TOPBAR_HT_upper_bar.append(ui.draw_topbar_menu)

    # 注册Blender启动后刷新插件列表的处理器
    bpy.app.timers.register(utils.check_blender_ready)


def unregister():
    """注销插件"""
    # 注销顶部菜单绘制函数
    bpy.types.TOPBAR_HT_upper_bar.remove(ui.draw_topbar_menu)

    # 注销属性组
    del bpy.types.WindowManager.addonreloader

    # 注销所有类（按相反顺序）
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
