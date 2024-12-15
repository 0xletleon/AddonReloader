# data_manager.py


def singleton(cls):
    """单例模式"""
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class DataManager:
    """数据管理器"""

    def __init__(self):
        # Addon Reloader的模块名
        self.my_addon_names = {"Addon": "", "Extend": ""}

        # 下拉菜单默认值
        self.ddmenu_default_val = [("no_addons", "No Add-ons", "", "PLUGIN", 1)]

        # 上次的选择
        self.last_selected = self.ddmenu_default_val[0]

        # 要显示的插件列表
        self.show_lists = []

        # 插件路径列表
        self.addons_paths = {}


dm = DataManager()
"""数据管理器单例"""
