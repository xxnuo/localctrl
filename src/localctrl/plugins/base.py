"""
插件系统基类 - 所有插件必须继承此类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import uuid
import logging

logger = logging.getLogger(__name__)

class BasePlugin(ABC):
    """
    插件基类
    所有插件必须继承此类并实现所需方法
    """
    
    def __init__(self):
        self._id = str(uuid.uuid4())
        self._name = self.__class__.__name__
        self._description = "Base plugin"
        self._version = "0.1.0"
        self._running = False
        self._status = "initialized"
        self._config: Dict[str, Any] = {}
        self._ui_components: List[Dict[str, Any]] = []
        
    @property
    def id(self) -> str:
        """插件唯一ID"""
        return self._id
        
    @property
    def name(self) -> str:
        """插件名称"""
        return self._name
        
    @property
    def description(self) -> str:
        """插件描述"""
        return self._description
        
    @property
    def version(self) -> str:
        """插件版本"""
        return self._version
        
    @property
    def running(self) -> bool:
        """插件是否正在运行"""
        return self._running
        
    @running.setter
    def running(self, value: bool):
        """设置插件运行状态"""
        self._running = value
        
    @property
    def status(self) -> str:
        """插件状态"""
        return self._status
        
    @status.setter
    def status(self, value: str):
        """设置插件状态"""
        self._status = value
        
    @property
    def config(self) -> Dict[str, Any]:
        """插件配置"""
        return self._config
        
    @property
    def ui_components(self) -> List[Dict[str, Any]]:
        """插件UI组件定义"""
        return self._ui_components
        
    def initialize(self) -> None:
        """
        初始化插件
        在插件加载时调用
        """
        try:
            self._status = "initializing"
            self.on_initialize()
            self._status = "ready"
        except Exception as e:
            self._status = f"initialization failed: {str(e)}"
            logger.error(f"Failed to initialize plugin {self.name}: {e}")
            raise
            
    def cleanup(self) -> None:
        """
        清理插件资源
        在插件卸载时调用
        """
        try:
            self._status = "cleaning up"
            self.on_cleanup()
            self._status = "cleaned up"
        except Exception as e:
            self._status = f"cleanup failed: {str(e)}"
            logger.error(f"Failed to cleanup plugin {self.name}: {e}")
            raise
            
    def run(self) -> None:
        """
        插件主运行方法
        在插件线程中执行
        """
        self._status = "running"
        try:
            self.on_run()
        except Exception as e:
            self._status = f"error: {str(e)}"
            logger.error(f"Error in plugin {self.name}: {e}")
            raise
        finally:
            if self._running:
                self._status = "stopped"
                self._running = False
                
    def execute_action(self, action: str, params: Dict[str, Any] = None) -> Any:
        """
        执行插件操作
        
        Args:
            action: 操作名称
            params: 操作参数
            
        Returns:
            Any: 操作结果
        """
        if not hasattr(self, f"action_{action}"):
            raise ValueError(f"Action {action} not supported by plugin {self.name}")
            
        action_method = getattr(self, f"action_{action}")
        return action_method(**(params or {}))
        
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新插件配置
        
        Args:
            config: 新的配置
        """
        self._config.update(config)
        self.on_config_updated(self._config)
        
    def register_ui_component(self, component: Dict[str, Any]) -> None:
        """
        注册UI组件
        
        Args:
            component: UI组件定义
        """
        self._ui_components.append(component)
        
    # 以下方法需要子类实现
    
    @abstractmethod
    def on_initialize(self) -> None:
        """
        插件初始化时调用
        子类必须实现此方法
        """
        pass
        
    @abstractmethod
    def on_cleanup(self) -> None:
        """
        插件清理时调用
        子类必须实现此方法
        """
        pass
        
    @abstractmethod
    def on_run(self) -> None:
        """
        插件运行时调用
        子类必须实现此方法
        """
        pass
        
    def on_config_updated(self, config: Dict[str, Any]) -> None:
        """
        配置更新时调用
        子类可选实现此方法
        
        Args:
            config: 更新后的配置
        """
        pass 