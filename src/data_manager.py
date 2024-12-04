# data_manager.py


def singleton(cls):
    """单例模式 - Singleton Pattern"""
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class DataManager:
    """数据管理器 - Data Manager"""

    def __init__(self):
        # ---- AUX DATA ----#

        # Addon Reloader的模块名 - Module Name of Addon Reloader
        self.dm_my_module_name = {"Addon": "", "Extend": ""}

        # 用户插件路径 - Path of User's Addons
        self.dm_user_addon_path: str = ""

        # 用户扩展路径 - Path of User's Extensions
        self.dm_user_extend_path: str = ""

        # 用户插件扩展路径字典 - Dict of User's Addons and Extensions
        self.dm_user_addon_path_dict = {}

        # ---- TAB AND LISTS ----#

        # 标签索引 - Tabs Index
        self.dm_tabs_index = "ADDONS"

        # 下拉菜单默认值 - Default Value of Dropdown Menu
        self.dm_ddmenu_default_val = {
            "ADDONS": [("def_opt", "None addon", "", "PLUGIN", 1)],
            "EXTENSIONS": [("def_opt", "None exten", "", "LINKED", 1000)]
        }

        # 上次的选择 - Last Selected
        self.dm_last_selected = {"ADDONS": "def_opt", "EXTENSIONS": "def_opt"}

        # 要显示的插件和扩展列表 - Lists of Addons and Extensions to Show
        self.dm_show_lists = {"ADDONS": [], "EXTENSIONS": []}


dm = DataManager()
"""数据管理器单例 - DataManager"""
