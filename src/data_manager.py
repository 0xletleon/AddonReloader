# data_manager.py


class DataManager:
    """Addon data manager."""

    def __init__(self):
        # Current addon module names
        self.my_addon_names = {"Addon": "", "Extend": ""}

        # Default dropdown menu value
        self.ddmenu_default_val = [
            ("no_addons", "None", "", "COLORSET_02_VEC", 1)]

        # Last selected addon
        self.last_selected = self.ddmenu_default_val[0]

        # Addon list to display
        self.show_lists = []

        # Addon path mapping
        self.addons_paths = {}

        # Addon enabled-state mapping
        self.enabled_map = {}


# Module-level singleton instance (Python modules load once, naturally singleton)
dm = DataManager()
"""Singleton instance of DataManager."""
