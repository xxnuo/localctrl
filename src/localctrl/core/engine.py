"""
主引擎模块 - 负责控制和管理整个系统
"""
import logging
import importlib
import pkgutil
from typing import Dict, List, Any, Optional, Type
import threading
import time

from ..plugins.base import BasePlugin
from ..config.settings import settings

logger = logging.getLogger(__name__)

class Engine:
    """
    LocalCtrl 主引擎类
    负责管理插件的加载、卸载和执行
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Engine, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.plugins: Dict[str, BasePlugin] = {}
        self.running = False
        self._initialized = True
        self.plugin_threads: Dict[str, threading.Thread] = {}
        logger.info("Engine initialized")
    
    def start(self):
        """启动引擎"""
        if self.running:
            logger.warning("Engine already running")
            return
            
        self.running = True
        logger.info("Engine started")
        
        # 加载所有已配置的插件
        self.load_configured_plugins()
    
    def stop(self):
        """停止引擎"""
        if not self.running:
            logger.warning("Engine not running")
            return
            
        # 停止所有插件
        for plugin_id in list(self.plugins.keys()):
            self.unload_plugin(plugin_id)
            
        self.running = False
        logger.info("Engine stopped")
    
    def load_configured_plugins(self):
        """加载配置中启用的所有插件"""
        for plugin_name in settings.enabled_plugins:
            try:
                self.load_plugin(plugin_name)
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}")
    
    def discover_plugins(self) -> List[str]:
        """发现所有可用的插件"""
        plugin_names = []
        
        # 从插件目录中发现所有插件
        import localctrl.plugins as plugins_pkg
        for _, name, ispkg in pkgutil.iter_modules(plugins_pkg.__path__, plugins_pkg.__name__ + '.'):
            if ispkg and name != 'localctrl.plugins.base':
                plugin_names.append(name.split('.')[-1])
                
        return plugin_names
    
    def load_plugin(self, plugin_name: str) -> bool:
        """
        加载指定的插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 加载是否成功
        """
        if plugin_name in self.plugins:
            logger.warning(f"Plugin {plugin_name} already loaded")
            return False
            
        try:
            # 动态导入插件模块
            module_path = f"localctrl.plugins.{plugin_name}"
            module = importlib.import_module(module_path)
            
            # 查找插件类 (约定插件类名为 Plugin)
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr != BasePlugin:
                    plugin_class = attr
                    break
            
            if not plugin_class:
                logger.error(f"No plugin class found in {module_path}")
                return False
                
            # 实例化插件
            plugin_instance = plugin_class()
            plugin_id = plugin_instance.id
            
            # 初始化插件
            plugin_instance.initialize()
            
            # 存储插件实例
            self.plugins[plugin_id] = plugin_instance
            
            # 如果引擎正在运行，启动插件
            if self.running:
                self._start_plugin_thread(plugin_id)
                
            logger.info(f"Plugin {plugin_id} loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """
        卸载指定的插件
        
        Args:
            plugin_id: 插件ID
            
        Returns:
            bool: 卸载是否成功
        """
        if plugin_id not in self.plugins:
            logger.warning(f"Plugin {plugin_id} not loaded")
            return False
            
        try:
            # 停止插件线程
            if plugin_id in self.plugin_threads:
                self._stop_plugin_thread(plugin_id)
            
            # 调用插件清理方法
            self.plugins[plugin_id].cleanup()
            
            # 移除插件
            del self.plugins[plugin_id]
            
            logger.info(f"Plugin {plugin_id} unloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_id}: {e}")
            return False
    
    def _start_plugin_thread(self, plugin_id: str):
        """启动插件的工作线程"""
        if plugin_id not in self.plugins:
            return
            
        plugin = self.plugins[plugin_id]
        
        # 创建并启动线程
        thread = threading.Thread(
            target=self._plugin_worker,
            args=(plugin_id,),
            name=f"Plugin-{plugin_id}",
            daemon=True
        )
        thread.start()
        
        self.plugin_threads[plugin_id] = thread
        logger.info(f"Started thread for plugin {plugin_id}")
    
    def _stop_plugin_thread(self, plugin_id: str):
        """停止插件的工作线程"""
        if plugin_id not in self.plugin_threads:
            return
            
        # 设置插件停止标志
        self.plugins[plugin_id].running = False
        
        # 等待线程结束
        self.plugin_threads[plugin_id].join(timeout=5.0)
        
        # 移除线程引用
        del self.plugin_threads[plugin_id]
        logger.info(f"Stopped thread for plugin {plugin_id}")
    
    def _plugin_worker(self, plugin_id: str):
        """插件工作线程函数"""
        plugin = self.plugins[plugin_id]
        plugin.running = True
        
        logger.info(f"Plugin {plugin_id} worker started")
        
        try:
            # 调用插件的运行方法
            plugin.run()
        except Exception as e:
            logger.error(f"Error in plugin {plugin_id}: {e}")
        finally:
            plugin.running = False
            logger.info(f"Plugin {plugin_id} worker stopped")
    
    def get_plugin_status(self, plugin_id: str = None) -> Dict[str, Any]:
        """
        获取插件状态
        
        Args:
            plugin_id: 插件ID，如果为None则返回所有插件状态
            
        Returns:
            Dict: 插件状态信息
        """
        if plugin_id:
            if plugin_id not in self.plugins:
                return {"error": f"Plugin {plugin_id} not found"}
            
            plugin = self.plugins[plugin_id]
            return {
                "id": plugin.id,
                "name": plugin.name,
                "description": plugin.description,
                "version": plugin.version,
                "running": plugin.running,
                "status": plugin.status
            }
        else:
            # 返回所有插件状态
            return {
                plugin_id: {
                    "id": plugin.id,
                    "name": plugin.name,
                    "description": plugin.description,
                    "version": plugin.version,
                    "running": plugin.running,
                    "status": plugin.status
                }
                for plugin_id, plugin in self.plugins.items()
            }
    
    def execute_plugin_action(self, plugin_id: str, action: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        执行插件操作
        
        Args:
            plugin_id: 插件ID
            action: 操作名称
            params: 操作参数
            
        Returns:
            Dict: 操作结果
        """
        if plugin_id not in self.plugins:
            return {"error": f"Plugin {plugin_id} not found"}
            
        plugin = self.plugins[plugin_id]
        
        try:
            result = plugin.execute_action(action, params or {})
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Error executing action {action} on plugin {plugin_id}: {e}")
            return {"success": False, "error": str(e)}

# 单例模式获取引擎实例
def get_engine() -> Engine:
    """获取引擎实例"""
    return Engine() 