import json
from pathlib import Path
import main

CONFIG_FILE = "config.json"

def load_config(config_path: str = CONFIG_FILE) -> dict:
    """
    加载JSON配置文件
    
    Args:
        config_path: 配置文件路径，默认为 config.json
    
    Returns:
        字典类型的配置数据
    
    Raises:
        FileNotFoundError: 如果配置文件不存在
        json.JSONDecodeError: 如果JSON格式无效
    """
    if not Path(config_path).exists():
        raise FileNotFoundError(f"配置文件 {config_path} 不存在")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config


def save_config(config: dict, config_path: str = CONFIG_FILE) -> None:
    """
    保存配置到JSON文件
    
    Args:
        config: 配置字典
        config_path: 配置文件路径，默认为 config.json
    """
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_hotkey(config_path: str = CONFIG_FILE) -> str:
    """
    从配置文件中获取热键
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        热键字符串
    """
    config = load_config(config_path)
    return config.get("hotkey", "enter")


def set_hotkey(new_hotkey: str, config_path: str = CONFIG_FILE) -> None:
    """
    修改配置文件中的热键值
    
    Args:
        new_hotkey: 新的热键值（例如："enter", "space", "ctrl+c"）
        config_path: 配置文件路径
    """
    config = load_config(config_path)
    config["hotkey"] = new_hotkey
    save_config(config, config_path)
    main.HOTKEY = new_hotkey
    print(f"热键已更新为: {new_hotkey}")


def get_config_value(key: str, config_path: str = CONFIG_FILE):
    """
    获取配置文件中的任意值
    
    Args:
        key: 配置键名
        config_path: 配置文件路径
    
    Returns:
        配置值
    """
    config = load_config(config_path)
    return config.get(key)


def set_config_value(key: str, value, config_path: str = CONFIG_FILE) -> None:
    """
    设置配置文件中的任意值
    
    Args:
        key: 配置键名
        value: 配置值
        config_path: 配置文件路径
    """
    config = load_config(config_path)
    config[key] = value
    save_config(config, config_path)
    print(f"配置 '{key}' 已更新为: {value}")
