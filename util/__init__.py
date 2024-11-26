# 工具类

import json
import os
from typing import Union, List

# 项目根目录绝对地址
this_project_base_path = None


def _get_project_base_path():
    """获取项目根目录的绝对路径"""
    global this_project_base_path

    if this_project_base_path is None:
        this_project_base_path = _get_project_base_path_by_self(os.path.dirname(__file__), "m3u8ProxyServer.py")

    return this_project_base_path


def _get_project_base_path_by_self(start_path: str, target_file: str) -> str:
    """
    递归查找包含目标文件的项目根目录的绝对路径
    :param start_path: 开始查找的目录路径
    :param target_file: 需要查找的文件名
    :return: 包含目标文件的项目根目录的绝对路径
    """
    # 将路径转换为绝对路径
    start_path = os.path.abspath(start_path)

    # 构建目标文件的完整路径
    target_file_path = os.path.join(start_path, target_file)

    # 如果目标文件存在于当前目录，返回当前目录路径
    if os.path.isfile(target_file_path):
        return start_path

    # 获取父目录路径
    parent_dir = os.path.dirname(start_path)

    # 如果已经到达文件系统的根目录，停止递归
    if start_path == parent_dir:
        raise FileNotFoundError(f"无法在路径 {start_path} 及其父目录中找到文件 {target_file}")

    # 递归查找父目录
    return _get_project_base_path_by_self(parent_dir, target_file)


def get_project_file(*paths: Union[str, List[str]]):
    """
    从项目根目录开始，获取指定文件的绝对路径
    例如：/a/b.txt 调用：get_project_file('a','b.txt')
    """
    base_path = _get_project_base_path()
    return os.path.join(base_path, *paths)


def get_project_file_content(*paths: Union[str, List[str]], encoding='utf-8'):
    """
    从项目根目录开始，从指定文件获取文件内容，并返回字符串
    例如：/a/b.txt 调用：get_project_file_content('a','b.txt')
    """
    with open(get_project_file(*paths), 'r', encoding=encoding) as file:
        content = file.read()
    return content


def get_dict_from_json_file(*paths: Union[str, List[str]]) -> dict:
    """
    从项目根目录开始，从指定文件获取 JSON，并返回字典
    例如：/a/b.txt 调用：load_dict_from_json_file('a','b.txt')
    """
    # 检查文件是否存在
    file_path = get_project_file(*paths)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 打开文件并读取内容
    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            # 将 JSON 转换为字典
            config_dict = json.load(file)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON from {file_path}: {e}")

    # 返回结果
    return config_dict


# 初始化项目根目录地址
_get_project_base_path()
