"""
工具函数模块 - 提供通用工具函数
"""
import os
import sys
import logging
import json
import uuid
import socket
import platform
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date

logger = logging.getLogger(__name__)

def generate_id() -> str:
    """生成唯一ID"""
    return str(uuid.uuid4())

def get_hostname() -> str:
    """获取主机名"""
    return socket.gethostname()

def get_ip_address() -> str:
    """获取IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"Failed to get IP address: {e}")
        return "127.0.0.1"

def get_system_info() -> Dict[str, Any]:
    """获取系统信息"""
    info = {
        "hostname": get_hostname(),
        "ip": get_ip_address(),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "python_version": platform.python_version(),
        "architecture": platform.architecture(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count()
    }
    return info

def load_json_file(file_path: str) -> Dict[str, Any]:
    """加载JSON文件"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON file {file_path}: {e}")
        return {}

def save_json_file(file_path: str, data: Dict[str, Any]) -> bool:
    """保存JSON文件"""
    try:
        # 确保目录存在
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to save JSON file {file_path}: {e}")
        return False

def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """合并两个字典，dict2的值会覆盖dict1的值"""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result

class JSONEncoder(json.JSONEncoder):
    """扩展的JSON编码器，支持日期和时间"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

def json_dumps(obj: Any) -> str:
    """将对象转换为JSON字符串"""
    return json.dumps(obj, cls=JSONEncoder, ensure_ascii=False)

def json_loads(s: str) -> Any:
    """将JSON字符串转换为对象"""
    return json.loads(s)

def ensure_dir(directory: str) -> bool:
    """确保目录存在"""
    try:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        return False

def is_port_in_use(port: int) -> bool:
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port: int = 8000, max_port: int = 9000) -> int:
    """查找可用端口"""
    for port in range(start_port, max_port):
        if not is_port_in_use(port):
            return port
    raise RuntimeError(f"No available port found between {start_port} and {max_port}")

def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"