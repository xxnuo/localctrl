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
