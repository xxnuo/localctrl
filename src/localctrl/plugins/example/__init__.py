"""
示例插件 - 展示插件开发的基本结构和功能
"""
import time
import logging
from typing import Dict, Any, List, Optional
import threading

from ...plugins.base import BasePlugin

logger = logging.getLogger(__name__)

class ExamplePlugin(BasePlugin):
    """示例插件类"""
    
    def __init__(self):
        super().__init__()
        self._name = "Example"
        self._description = "示例插件，展示插件开发的基本结构和功能"
        self._version = "0.1.0"
        self._counter = 0
        self._interval = 5.0  # 默认间隔时间（秒）
        
        # 默认配置
        self._config = {
            "interval": 5.0,
            "message": "Hello from Example Plugin!",
            "enabled_features": ["counter", "logger"]
        }
        
        # 注册UI组件
        self.register_ui_component({
            "type": "card",
            "title": "Example Plugin",
            "content": [
                {
                    "type": "text",
                    "content": "This is an example plugin that demonstrates the plugin system."
                },
                {
                    "type": "counter",
                    "label": "Counter",
                    "value": 0,
                    "update_path": "/api/plugins/{plugin_id}/action",
                    "update_action": "get_counter"
                },
                {
                    "type": "button",
                    "label": "Increment Counter",
                    "action_path": "/api/plugins/{plugin_id}/action",
                    "action_data": {"action": "increment_counter", "params": {}}
                },
                {
                    "type": "input",
                    "label": "Message",
                    "value": self._config["message"],
                    "action_path": "/api/plugins/{plugin_id}/action",
                    "action_data": {"action": "set_message", "params": {"message": ""}}
                }
            ]
        })
        
    def on_initialize(self) -> None:
        """初始化插件"""
        logger.info("Example plugin initializing")
        self._interval = self._config.get("interval", 5.0)
        logger.info(f"Example plugin initialized with interval: {self._interval}s")
        
    def on_cleanup(self) -> None:
        """清理插件资源"""
        logger.info("Example plugin cleaning up")
        # 在这里可以进行资源清理，如关闭文件、连接等
        
    def on_run(self) -> None:
        """插件主运行方法"""
        logger.info("Example plugin starting")
        
        while self.running:
            # 执行插件主要功能
            self._counter += 1
            
            if "logger" in self._config.get("enabled_features", []):
                logger.info(f"Example plugin running: {self._config.get('message', 'Hello')} (count: {self._counter})")
                
            # 等待指定时间
            for _ in range(int(self._interval * 10)):
                if not self.running:
                    break
                time.sleep(0.1)
                
        logger.info("Example plugin stopped")
        
    def on_config_updated(self, config: Dict[str, Any]) -> None:
        """配置更新时调用"""
        logger.info(f"Example plugin config updated: {config}")
        
        # 更新间隔时间
        if "interval" in config:
            self._interval = config["interval"]
            
    # 插件操作方法
    
    def action_get_counter(self) -> Dict[str, Any]:
        """获取计数器值"""
        return {"counter": self._counter}
        
    def action_increment_counter(self) -> Dict[str, Any]:
        """增加计数器值"""
        self._counter += 1
        return {"counter": self._counter}
        
    def action_reset_counter(self) -> Dict[str, Any]:
        """重置计数器"""
        self._counter = 0
        return {"counter": self._counter}
        
    def action_set_message(self, message: str) -> Dict[str, Any]:
        """设置消息"""
        self._config["message"] = message
        return {"message": message}
        
    def action_get_status(self) -> Dict[str, Any]:
        """获取插件状态"""
        return {
            "running": self.running,
            "status": self.status,
            "counter": self._counter,
            "config": self._config
        } 