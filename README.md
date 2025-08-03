# LocalCtrl

An open-source remote control service with plugin support.

## 项目概述

LocalCtrl 是一个基于 Python 的开源远程控制系统，具有以下特点：

- 后端使用 Python + FastAPI + SQLite 构建
- 插件化架构，支持动态加载/卸载插件
- 每个插件作为独立的 Worker 运行，不影响主控制引擎
- 提供完整的 REST API 接口
- 支持用户认证和权限管理
- 前端使用 React + Tailwind CSS + shadcn/ui 实现网络控制后台

## 系统架构

### 后端架构

- **核心引擎**：负责管理插件的加载、卸载和执行
- **插件系统**：提供插件基类和接口，支持动态加载和卸载
- **API 接口**：使用 FastAPI 提供 RESTful API
- **数据存储**：使用 SQLite 存储系统配置、用户信息和插件数据
- **配置管理**：管理系统和插件配置

### 目录结构

```
src/
├── localctrl/
│   ├── api/             # API 接口
│   │   ├── app.py       # FastAPI 应用
│   │   ├── auth.py      # 认证相关 API
│   │   ├── plugins.py   # 插件相关 API
│   │   ├── system.py    # 系统相关 API
│   │   └── users.py     # 用户相关 API
│   ├── config/          # 配置管理
│   │   └── settings.py  # 系统配置
│   ├── core/            # 核心功能
│   │   └── engine.py    # 主引擎
│   ├── models/          # 数据模型
│   │   └── database.py  # 数据库模型
│   ├── plugins/         # 插件系统
│   │   ├── base.py      # 插件基类
│   │   └── example/     # 示例插件
│   └── utils/           # 工具函数
├── main.py              # 主程序入口
└── __init__.py
```

## 安装和使用

### 依赖项

- Python 3.9+
- FastAPI
- SQLAlchemy
- Pydantic
- Uvicorn
- 其他依赖项见 `setup.py`

### 安装

1. 克隆仓库

```bash
git clone https://github.com/yourusername/localctrl.git
cd localctrl
```

2. 安装依赖

```bash
pip install -e .
```

### 运行

```bash
# 默认配置运行
python src/main.py

# 指定配置文件
python src/main.py --config /path/to/config.json

# 调试模式
python src/main.py --debug

# 指定主机和端口
python src/main.py --host 0.0.0.0 --port 8888
```

## API 接口

系统提供以下 API 接口：

- **认证相关**：`/api/auth/*`
  - 登录、注册、API 密钥管理

- **插件相关**：`/api/plugins/*`
  - 获取插件列表、加载/卸载插件、执行插件操作

- **用户相关**：`/api/users/*`
  - 用户管理、权限控制

- **系统相关**：`/api/system/*`
  - 系统信息、状态、配置、日志、备份

## 插件开发

开发插件需要继承 `BasePlugin` 类并实现必要的方法：

```python
from localctrl.plugins.base import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self._name = "MyPlugin"
        self._description = "My custom plugin"
        self._version = "0.1.0"
        
    def on_initialize(self) -> None:
        # 初始化插件
        pass
        
    def on_cleanup(self) -> None:
        # 清理资源
        pass
        
    def on_run(self) -> None:
        # 插件主运行逻辑
        while self.running:
            # 执行任务
            pass
```

请参考 `src/localctrl/plugins/example/__init__.py` 了解更多插件开发示例。

## 配置

系统配置存储在 `~/.localctrl/config.json` 中，可以通过 API 或直接编辑文件进行修改。

主要配置项包括：

- 服务器设置（主机、端口）
- 数据库设置
- 日志设置
- 插件设置

## 许可证

MIT License