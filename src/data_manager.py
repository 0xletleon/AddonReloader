# data_manager.py


def singleton(cls):
    """单例模式装饰器"""
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class DataManager:
    """插件数据管理器"""

    def __init__(self):
        # 当前插件的模块名称
        self.my_addon_names = {"Addon": "", "Extend": ""}

        # 下拉菜单默认值
        self.ddmenu_default_val = [
            ("no_addons", "None", "", "COLORSET_02_VEC", 1)]

        # 上次选择的插件
        self.last_selected = self.ddmenu_default_val[0]

        # 要显示的插件列表
        self.show_lists = []

        # 插件路径映射表
        self.addons_paths = {}


dm = DataManager()
"""数据管理器单例实例"""
