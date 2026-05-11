#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LabelFlow - 快捷图片标注工具 - 配置管理模块
"""

import os
import sys
import json
import shutil
from typing import Any, Dict, Optional


class ConfigManager:
    """配置管理器 - 统一管理所有配置项"""

    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化配置管理器"""
        if not hasattr(self, '_initialized'):
            self.config_path = self._get_config_path()
            self.old_app_info_path = self._get_old_config_path('app.info')
            self.old_keys_setting_path = self._get_old_config_path('keys_setting.json')
            self._initialized = True
            self.load_config()

    def _get_config_path(self) -> str:
        """获取配置文件路径（兼容PyInstaller打包）"""
        if getattr(sys, 'frozen', False):
            # 打包后的环境 - 可写配置文件在exe同级目录
            base_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境 - 配置文件在项目根目录
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        return os.path.join(base_dir, 'config.json')

    def _get_bundled_config_path(self) -> Optional[str]:
        """获取PyInstaller打包资源中的默认配置文件路径。"""
        if not getattr(sys, 'frozen', False):
            return None

        bundled_config = os.path.join(getattr(sys, '_MEIPASS', ''), 'config.json')
        if os.path.exists(bundled_config):
            return bundled_config
        return None

    def _get_old_config_path(self, filename: str) -> str:
        """获取旧配置文件路径"""
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            if filename == 'app.info':
                # app.info在src目录
                base_dir = os.path.dirname(os.path.abspath(__file__))
            else:
                # keys_setting.json在根目录
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        return os.path.join(base_dir, filename)

    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            # 尝试加载新配置文件
            bundled_config_path = self._get_bundled_config_path()
            load_path = self.config_path if os.path.exists(self.config_path) else bundled_config_path

            if load_path and os.path.exists(load_path):
                with open(load_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                    print(f"配置文件加载成功: {load_path}")
            else:
                # 配置文件不存在，尝试从旧配置迁移
                print("配置文件不存在，尝试从旧配置迁移...")
                self._config = self._get_default_config()
                self.migrate_from_old_configs()
                print("配置迁移完成，已保存新配置文件")

            # 验证配置
            self.validate_config()
            if load_path != self.config_path or not os.path.exists(self.config_path):
                self.save_config()
            return self._config

        except Exception as e:
            print(f"加载配置文件失败: {e}")
            # 使用默认配置
            self._config = self._get_default_config()
            return self._config

    def save_config(self) -> bool:
        """保存配置文件"""
        try:
            # 确保配置目录存在
            config_dir = os.path.dirname(self.config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir)

            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)

            print(f"配置文件保存成功: {self.config_path}")
            return True

        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

    def get(self, key_path: str, default: Any = None) -> Any:
        """获取配置项（支持点号路径，如 'app.version'）

        Args:
            key_path: 配置项路径，支持点号分隔
            default: 默认值

        Returns:
            配置项的值，如果不存在则返回默认值
        """
        try:
            keys = key_path.split('.')
            value = self._config

            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default

            return value

        except Exception:
            return default

    def set(self, key_path: str, value: Any) -> bool:
        """设置配置项（支持点号路径）

        Args:
            key_path: 配置项路径，支持点号分隔
            value: 要设置的值

        Returns:
            是否设置成功
        """
        try:
            keys = key_path.split('.')
            config = self._config

            # 导航到倒数第二层
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]

            # 设置最后一层的值
            config[keys[-1]] = value
            return True

        except Exception as e:
            print(f"设置配置项失败: {key_path} = {value}, 错误: {e}")
            return False

    def migrate_from_old_configs(self) -> bool:
        """从旧配置文件迁移数据"""
        try:
            # 1. 从app.info迁移应用信息
            if os.path.exists(self.old_app_info_path):
                print(f"发现旧配置文件: {self.old_app_info_path}")
                with open(self.old_app_info_path, 'r', encoding='utf-8') as f:
                    old_app_info = json.load(f)

                # 迁移应用信息（保留版本号为0.0.5，因为这是新版本）
                if 'name' in old_app_info:
                    self._config['app']['name'] = old_app_info['name']
                if 'description' in old_app_info:
                    self._config['app']['description'] = old_app_info['description']
                if 'author' in old_app_info:
                    self._config['app']['author'] = old_app_info['author']
                if 'email' in old_app_info:
                    self._config['app']['email'] = old_app_info['email']
                if 'github' in old_app_info:
                    self._config['app']['github'] = old_app_info['github']
                if 'license' in old_app_info:
                    self._config['app']['license'] = old_app_info['license']

                print("应用信息迁移完成")

            # 2. 从keys_setting.json迁移快捷键配置
            if os.path.exists(self.old_keys_setting_path):
                print(f"发现旧配置文件: {self.old_keys_setting_path}")
                with open(self.old_keys_setting_path, 'r', encoding='utf-8') as f:
                    old_shortcuts = json.load(f)

                # 迁移快捷键（新快捷键保持默认值）
                for key, value in old_shortcuts.items():
                    if key in self._config['shortcuts']:
                        self._config['shortcuts'][key] = value

                print("快捷键配置迁移完成")

            return True

        except Exception as e:
            print(f"配置迁移失败: {e}")
            return False

    def validate_config(self) -> bool:
        """验证配置有效性"""
        try:
            # 检查必需的配置节
            required_sections = ['app', 'performance', 'ui', 'logging', 'shortcuts']
            for section in required_sections:
                if section not in self._config:
                    print(f"警告: 缺少配置节 '{section}'，使用默认值")
                    self._config[section] = self._get_default_config()[section]

            # 检查必需的应用信息
            required_app_keys = ['name', 'version', 'description']
            for key in required_app_keys:
                if key not in self._config['app']:
                    print(f"警告: 缺少应用信息 '{key}'，使用默认值")
                    self._config['app'][key] = self._get_default_config()['app'][key]

            # 验证数值范围
            if self._config['performance']['max_undo_steps'] < 1:
                self._config['performance']['max_undo_steps'] = 50

            if self._config['logging']['max_size_mb'] < 1:
                self._config['logging']['max_size_mb'] = 10

            return True

        except Exception as e:
            print(f"配置验证失败: {e}")
            return False

    def get_app_info(self) -> Dict[str, str]:
        """获取应用信息"""
        return self._config.get('app', {})

    def get_performance_config(self) -> Dict[str, Any]:
        """获取性能配置"""
        return self._config.get('performance', {})

    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI配置"""
        return self._config.get('ui', {})

    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self._config.get('logging', {})

    def get_shortcuts_config(self) -> Dict[str, str]:
        """获取快捷键配置"""
        return self._config.get('shortcuts', {})

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "app": {
                "name": "LabelFlow",
                "version": "0.0.5",
                "description": "快捷图片标注工具",
                "icon_path": "build_icon.ico",
                "author": "xinyang20",
                "email": "gaoxinyang317@gmail.com",
                "github": "https://github.com/xinyang20/LabelFlow",
                "license": "MIT"
            },
            "performance": {
                "max_memory_mb": 1024,
                "batch_size": 100,
                "min_batch_size": 20,
                "max_undo_steps": 50,
                "enable_base64": True,
                "max_base64_file_size_mb": 10,
                "preload_count": 2,
                "cache_size": 100
            },
            "ui": {
                "language": "zh_CN",
                "window_width": 1200,
                "window_height": 800,
                "theme": "default",
                "default_annotation_mode": "description",
                "auto_save_enabled": True
            },
            "logging": {
                "enabled": True,
                "log_file": "logs/labelflow.log",
                "max_size_mb": 10,
                "backup_count": 3,
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "shortcuts": {
                "Open Directory": "Ctrl+O",
                "Set Save Path": "Ctrl+S",
                "Exit": "Ctrl+Q",
                "About Page": "Ctrl+A",
                "Previous Image": "Ctrl+Left",
                "Next Image": "Ctrl+Right",
                "Quick Save": "Ctrl+Return",
                "Toggle Auto Save": "Ctrl+T",
                "Clear Annotation": "Ctrl+D",
                "Copy From Previous": "Ctrl+Shift+C",
                "Undo": "Ctrl+Z",
                "Redo": "Ctrl+Y",
                "Show Shortcuts Help": "Ctrl+/",
                "Label 0": "Ctrl+0",
                "Label 1": "Ctrl+1",
                "Label 2": "Ctrl+2",
                "Label 3": "Ctrl+3",
                "Label 4": "Ctrl+4",
                "Label 5": "Ctrl+5",
                "Label 6": "Ctrl+6",
                "Label 7": "Ctrl+7",
                "Label 8": "Ctrl+8",
                "Label 9": "Ctrl+9"
            }
        }


# 创建全局配置管理器实例
config_manager = ConfigManager()
