# ui.py
import bpy
from typing import Tuple
import addon_utils

from .data_manager import dm
from .log import log
from . import utils


def draw_topbar_menu(self, context) -> None:
    """绘制到顶部菜单栏"""
    wm = context.window_manager
    layout = self.layout

    # 添加分隔符使其靠右
    layout.separator_spacer()
    # 创建一行
    row = layout.row(align=True)
    # 添加下拉菜单
    row.operator("addonreloader.dropdown_list", text="", icon="DOWNARROW_HLT")
    # 刷新按钮
    row.operator("addonreloader.refresh_list", text="", icon="FILE_REFRESH")

    if dm.last_selected[0] != "no_addons":
        # 状态设置图标
        icon = "RADIOBUT_OFF" if not wm.addonreloader.addon_state else "RADIOBUT_ON"
        # 状态设置
        row.prop(wm.addonreloader, "addon_state", text="", icon=icon)
        # 将插件名控制在20个字符以内
        shortened_name = dm.last_selected[1][:20]
        if len(dm.last_selected[1]) > 20:
            shortened_name += "..."
        # 重载按钮
        row.operator("addonreloader.reload_addon", text=shortened_name)
    else:
        # log.debug("!no_addons %s ", dm.last_selected)
        # 状态设置
        row.prop(wm.addonreloader, "addon_state", text="", icon="RADIOBUT_OFF")
        # 使用动态列表
        row.operator("addonreloader.reload_addon", text=dm.last_selected[1])

    # 打开插件目录按钮
    row.operator("addonreloader.open_addon_folder", text="", icon="FILE_FOLDER")


def update_toggle_addon_state(self, context):
    """启用或禁用插件"""
    log.debug("启用或禁用插件")

    # 当前状态
    current_state = self.addon_state
    log.debug("now state: %s", current_state)
    # 上次选择的插件或扩展
    last_selected = dm.last_selected[0]
    log.debug("Last selected: %s", last_selected)

    # 如果没有选择插件则返回
    if last_selected == "no_addons":
        # 使用popup_menu显示警告
        errortext = "Operation failed, please select a plugin"

        def draw(self, context):
            self.layout.label(text=errortext)

        bpy.context.window_manager.popup_menu(draw, title="Warning", icon="ERROR")
        log.error(errortext)
        return

    # 切换插件的启用状态
    try:
        # 获取插件当前状态
        now_addon_state = utils.is_addon_enabled(last_selected)
        if current_state and not now_addon_state:
            addon_utils.enable(last_selected, default_set=True)
            log.info("Enabling addon: %s", last_selected)
        elif not current_state and now_addon_state:
            addon_utils.disable(last_selected, default_set=True)
            log.info("Disabling addon: %s", last_selected)

    except Exception as e:
        log.error("Error toggling addon state: %s ", str(e))
