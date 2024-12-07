# ui.py
from typing import Tuple

import addon_utils
import bpy

from .data_manager import dm
from .log import log


# ---- UI Panel ----#


class ADDONRELOADER_PT_popover_panel(bpy.types.Panel):
    """弹出面板类 - Popover Panel Class"""

    bl_idname = "ADDONRELOADER_PT_popover_panel"
    bl_label = "Addon Reloader"
    bl_description = "Addon Reloader"
    bl_space_type = "TOPBAR"
    bl_region_type = "HEADER"

    def draw(self, context) -> None:
        """绘制弹出面板内容 - Draw the popover panel content"""
        log.debug("绘制弹出面板内容 - Draw the popover panel content")

        wm = context.window_manager
        layout = self.layout

        # 标签选择器 - Tab Selector
        row = layout.row()
        row.prop(wm, "addonreloader_addon_tabs", expand=True)

        # 下拉菜单 - Dropdown Menu
        row = layout.row(align=True)

        # 当前选择的标签页和数据 - Current Tab and Data
        current_tab = dm.dm_tabs_index
        current_data = dm.dm_show_lists[current_tab]

        # 判断当前标签页是否有数据 - Check if the current tab has data
        if current_data and len(current_data) > 0:
            log.debug("有数据，使用 addonreloader_ddmenu_list")

            valid_values = {item[0] for item in current_data}
            last_selected = dm.dm_last_selected[current_tab]
            log.debug("last_selected: %s", last_selected)

            # 设置下拉菜单的值 - Set the dropdown menu value
            if last_selected in valid_values:
                # 如果上次选中的值有效，保持选择 - Keep the last selected value
                wm.addonreloader_ddmenu_list = last_selected
            else:
                # 如果上次选中的值无效，选择第一个选项 - Select the first option if the last selected value is invalid
                wm.addonreloader_ddmenu_list = current_data[0][0]
                # 更新最后选择的值 - Update the last selected value
                dm.dm_last_selected[current_tab] = current_data[0][0]

            # 使用动态列表 - Use the dynamic list
            row.prop(wm, "addonreloader_ddmenu_list", text="")
        else:  # 如果没有数据，使用默认选项 - Use the default option if there is no data
            log.debug("列表中没有数据，使用默认选项")
            # 确保选中的插件有效 - Ensure the selected addon is valid
            wm.addonreloader_ddmenu_list = "def_opt"
            # 使用默认列表 - Use the default list
            row.prop(wm, "addonreloader_ddmenu_default_val", text="")

        # 刷新按钮 - Refresh Button
        row.operator("addonreloader.refresh_list", text="", icon="FILE_REFRESH")

        # 新行 - New Row
        row = layout.row()
        # 状态设置图标 - Status Setting Icon
        icon = "RADIOBUT_OFF" if not wm.addonreloader_addon_state else "RADIOBUT_ON"
        # 状态设置 - Status Setting
        row.prop(wm, "addonreloader_addon_state", text="", icon=icon)
        # 重载按钮 - Reload Button
        row.operator("addonreloader.reload_addon", text="Reload")


# ---- Functions ----#


def draw_topbar_menu(self, context) -> None:
    """绘制到顶部菜单栏 - Draw to the top menu bar"""
    layout = self.layout
    layout.separator_spacer()
    layout.popover(panel="ADDONRELOADER_PT_popover_panel", text="Reload", icon="PLUGIN")


def update_tabs_index(self, context):
    """更新插件标签索引 - Update addon tabs index"""
    current_tab = self.addonreloader_addon_tabs
    dm.dm_tabs_index = current_tab
    log.debug("更新插件标签索引 current_tab: %s", current_tab)


def get_ddmenu_default_val(self, context):
    """获取插件标签页默认值 - Get addon tabs default value"""
    res = dm.dm_ddmenu_default_val[dm.dm_tabs_index]
    log.debug("获取插件标签页默认值: %s", res)
    return res


def get_ddmenu_list(self, context) -> Tuple:
    """获取下拉菜单列表 - Get the list for the dropdown menu"""
    current_tab = dm.dm_tabs_index
    this_list = dm.dm_show_lists[current_tab]

    # 如果列表为空则返回默认值 - If the list is empty, return the default value
    if not this_list:
        log.debug("列表为空，返回默认值")
        return dm.dm_ddmenu_default_val[current_tab]

    return this_list


def update_last_selected(self, context):
    """更新插件标签页最后选中的选项 - Update the last selected option for the addon tabs"""
    current_selected = self.addonreloader_ddmenu_list
    dm.dm_last_selected[dm.dm_tabs_index] = current_selected
    log.debug("Current Selected: %s", current_selected)


def update_toggle_state(self, context):
    """启用或禁用插件或扩展 - Enable or disable addon or extension"""
    # 当前状态 - Current state
    current_state = self.addonreloader_addon_state
    log.debug("now state: %s", current_state)

    # 上次选择的插件或扩展 - The last selected addon or extension
    last_selected = dm.dm_last_selected[dm.dm_tabs_index]
    log.debug("Last selected: %s", last_selected)
    if last_selected == "def_opt":
        return

    # 切换插件或扩展的启用状态 - Toggle the enabled state of the addon or extension
    if current_state:
        addon_utils.enable(last_selected, default_set=True)
        log.debug("Enabling addon: %s", last_selected)
    else:
        addon_utils.disable(last_selected, default_set=True)
        log.debug("Disabling addon: %s", last_selected)
