# ui.py
import bpy
from .data_manager import dm


def draw_topbar_menu(self, context) -> None:
    """绘制到顶部菜单栏"""
    # 获取当前区域
    # https://www.cnblogs.com/letleon/p/18991793
    alignment = context.region.alignment

    # 只绘制在右侧
    if alignment == "RIGHT":
        wm = context.window_manager
        layout = self.layout

        # 添加分隔符使其靠右
        layout.separator_spacer()
        # 创建一行
        row = layout.row(align=True)
        # 添加下拉菜单
        row.operator("addonreloader.dropdown_list", text="", icon="DOWNARROW_HLT")

        if dm.last_selected[0] != "no_addons":
            # 状态设置图标
            icon = (
                "SHADING_WIRE" if not wm.addonreloader.addon_state else "SHADING_SOLID"
            )
            # 状态设置
            row.operator("addonreloader.enable_or_disable_addon", text="", icon=icon)
            # 将插件名控制在20个字符以内
            shortened_name = dm.last_selected[1][:20]
            if len(dm.last_selected[1]) > 20:
                shortened_name += "..."
            # 重载按钮
            row.operator("addonreloader.reload_addon", text=shortened_name)
        else:
            # 状态设置
            row.operator(
                "addonreloader.enable_or_disable_addon", text="", icon="RADIOBUT_OFF"
            )
            # 使用动态列表
            row.operator("addonreloader.reload_addon", text=dm.last_selected[1])

        # 打开插件目录按钮
        row.operator("addonreloader.open_addon_folder", text="", icon="FILE_FOLDER")
