# ui.py
from .data_manager import dm


def draw_topbar_menu(self, context) -> None:
    """在顶部菜单栏绘制插件界面"""
    # 获取当前区域对齐方式
    # https://www.cnblogs.com/letleon/p/18991793
    alignment = context.region.alignment

    # 只在右侧区域绘制
    if alignment == "RIGHT":
        wm = context.window_manager
        layout = self.layout

        # 创建一行布局
        row = layout.row(align=True)

        # 📜 插件选择列表
        row.operator("addonreloader.dropdown_list",
                     text="", icon="DOWNARROW_HLT")

        # ✨ 重新载入按钮
        if dm.last_selected[0] != "no_addons":  # 如果有选择的插件
            # 根据插件启用状态设置图标
            is_enabled = wm.addonreloader.addon_state
            icon = "COLORSET_03_VEC" if is_enabled else "COLORSET_13_VEC"

            # 添加启用/禁用按钮
            row.operator("addonreloader.enable_or_disable_addon",
                         text="", icon=icon)

            # 将插件名称限制在20个字符以内
            shortened_name = dm.last_selected[1][:20]
            if len(dm.last_selected[1]) > 20:
                shortened_name += "..."
            # 添加重载按钮
            row.operator("addonreloader.reload_addon", text=shortened_name)
        else:  # 如果没有选择的插件
            # 禁用状态的按钮
            row.operator(
                "addonreloader.enable_or_disable_addon", text="", icon="COLORSET_13_VEC"
            )
            # 添加重载按钮（无选择时显示默认文本）
            row.operator("addonreloader.reload_addon",
                         text=dm.last_selected[1])

        # 📂 打开插件目录按钮
        row.operator("addonreloader.open_addon_folder",
                     text="", icon="FILE_FOLDER")
