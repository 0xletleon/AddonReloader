# ui.py
from .data_manager import dm


def draw_topbar_menu(self, context) -> None:
    """Draw the addon UI in the top menu bar."""
    # Get current region alignment
    # https://www.cnblogs.com/letleon/p/18991793
    alignment = context.region.alignment

    # Only draw in the right-side region
    if alignment == "RIGHT":
        wm = context.window_manager
        layout = self.layout

        # Create a row layout
        row = layout.row(align=True)

        # Addon selection dropdown
        row.operator("addonreloader.dropdown_list",
                     text="", icon="DOWNARROW_HLT")

        # Reload button
        if dm.last_selected[0] != "no_addons":  # If an addon is selected
            # Set icon based on addon enabled state
            is_enabled = wm.addonreloader.addon_state
            icon = "NODE_SOCKET_SHADER" if is_enabled else "RECORD_ON"

            # Add enable/disable button
            row.operator("addonreloader.enable_or_disable_addon",
                         text="", icon=icon)

            # Truncate addon name to 20 characters
            shortened_name = dm.last_selected[1][:20]
            if len(dm.last_selected[1]) > 20:
                shortened_name += "..."
            # Add reload button
            row.operator("addonreloader.reload_addon", text=shortened_name)
        else:  # No addon selected
            # Disabled-state button
            row.operator(
                "addonreloader.enable_or_disable_addon", text="", icon="COLORSET_02_VEC"
            )
            # Add reload button (shows default text when nothing is selected)
            row.operator("addonreloader.reload_addon",
                         text=dm.last_selected[1])

        # Open addon folder button
        row.operator("addonreloader.open_addon_folder",
                     text="", icon="FILE_FOLDER")
