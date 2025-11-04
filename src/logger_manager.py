#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LabelFlow - 快捷图片标注工具 - 日志管理模块
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Optional
from datetime import datetime


class LoggerManager:
    """日志管理器 - 统一管理所有日志记录"""

    _instance = None
    _logger: Optional[logging.Logger] = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化日志管理器"""
        if not hasattr(self, '_initialized'):
            self._initialized = True

    def setup_logger(self, config: Dict[str, Any]):
        """初始化日志系统

        Args:
            config: 日志配置字典，包含：
                - enabled: 是否启用日志
                - log_file: 日志文件路径
                - max_size_mb: 日志文件最大大小（MB）
                - backup_count: 备份文件数量
                - level: 日志级别（DEBUG/INFO/WARNING/ERROR）
                - format: 日志格式
        """
        try:
            # 检查是否启用日志
            if not config.get('enabled', True):
                print("日志系统未启用")
                return

            # 创建logger
            self._logger = logging.getLogger('LabelFlow')

            # 清除现有的handlers（避免重复）
            self._logger.handlers.clear()

            # 设置日志级别
            level_name = config.get('level', 'INFO')
            level = getattr(logging, level_name, logging.INFO)
            self._logger.setLevel(level)

            # 获取日志文件路径
            log_file = self._get_log_file_path(config.get('log_file', 'logs/labelflow.log'))

            # 确保日志目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # 创建RotatingFileHandler（日志文件轮转）
            max_bytes = config.get('max_size_mb', 10) * 1024 * 1024  # 转换为字节
            backup_count = config.get('backup_count', 3)

            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)

            # 创建控制台Handler（只在开发环境）
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.WARNING)  # 控制台只显示警告和错误

            # 设置日志格式
            log_format = config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            formatter = logging.Formatter(log_format)
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # 添加handlers
            self._logger.addHandler(file_handler)
            if not getattr(sys, 'frozen', False):  # 只在开发环境添加控制台输出
                self._logger.addHandler(console_handler)

            # 记录初始化成功
            self._logger.info("="* 60)
            self._logger.info("LabelFlow 日志系统初始化成功")
            self._logger.info(f"日志文件: {log_file}")
            self._logger.info(f"日志级别: {level_name}")
            self._logger.info(f"最大大小: {config.get('max_size_mb', 10)}MB")
            self._logger.info(f"备份数量: {backup_count}")
            self._logger.info("=" * 60)

            print(f"日志系统初始化成功: {log_file}")

        except Exception as e:
            print(f"日志系统初始化失败: {e}")
            # 即使日志初始化失败，也不影响主程序运行
            self._logger = None

    def _get_log_file_path(self, relative_path: str) -> str:
        """获取日志文件的绝对路径（兼容PyInstaller打包）

        Args:
            relative_path: 相对路径

        Returns:
            日志文件的绝对路径
        """
        if getattr(sys, 'frozen', False):
            # 打包后的环境 - 日志文件在exe同级目录
            base_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境 - 日志文件在项目根目录
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        return os.path.join(base_dir, relative_path)

    def log_app_start(self):
        """记录应用启动"""
        if self._logger:
            self._logger.info("应用程序启动")

    def log_app_exit(self):
        """记录应用退出"""
        if self._logger:
            self._logger.info("应用程序退出")
            self._logger.info("=" * 60)

    def log_directory_opened(self, directory: str, image_count: int):
        """记录打开工作目录

        Args:
            directory: 目录路径
            image_count: 图片数量
        """
        if self._logger:
            self._logger.info(f"打开工作目录: {directory}, 图片数量: {image_count}")

    def log_image_switch(self, from_image: str, to_image: str, current_index: int, total_count: int):
        """记录图片切换

        Args:
            from_image: 切换前的图片名
            to_image: 切换后的图片名
            current_index: 当前索引
            total_count: 总数量
        """
        if self._logger:
            self._logger.debug(
                f"图片切换: {from_image} -> {to_image} "
                f"({current_index}/{total_count})"
            )

    def log_annotation_save(self, image_name: str, mode: str, content_length: int, labels_count: int):
        """记录标注保存

        Args:
            image_name: 图片名称
            mode: 标注模式（description/label/mixed）
            content_length: 描述内容长度
            labels_count: 标签数量
        """
        if self._logger:
            self._logger.info(
                f"保存标注: {image_name}, "
                f"模式: {mode}, "
                f"描述长度: {content_length}, "
                f"标签数量: {labels_count}"
            )

    def log_label_change(self, operation: str, old_labels: list, new_labels: list):
        """记录标签变化

        Args:
            operation: 操作类型（add/remove/change）
            old_labels: 旧标签列表
            new_labels: 新标签列表
        """
        if self._logger:
            self._logger.debug(
                f"标签变化 [{operation}]: "
                f"{old_labels} -> {new_labels}"
            )

    def log_config_change(self, config_key: str, old_value: Any, new_value: Any):
        """记录配置变更

        Args:
            config_key: 配置项名称
            old_value: 旧值
            new_value: 新值
        """
        if self._logger:
            self._logger.info(
                f"配置变更: {config_key} = {old_value} -> {new_value}"
            )

    def log_mode_change(self, old_mode: str, new_mode: str):
        """记录标注模式切换

        Args:
            old_mode: 旧模式
            new_mode: 新模式
        """
        if self._logger:
            self._logger.info(f"标注模式切换: {old_mode} -> {new_mode}")

    def log_operation(self, operation: str, details: Dict[str, Any]):
        """记录一般操作

        Args:
            operation: 操作名称
            details: 操作详情
        """
        if self._logger:
            details_str = ", ".join([f"{k}={v}" for k, v in details.items()])
            self._logger.info(f"操作: {operation}, 详情: {details_str}")

    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """记录错误

        Args:
            error: 异常对象
            context: 错误上下文信息
        """
        if self._logger:
            context_str = ""
            if context:
                context_str = ", ".join([f"{k}={v}" for k, v in context.items()])

            self._logger.error(
                f"错误: {type(error).__name__}: {str(error)}"
                f"{', 上下文: ' + context_str if context_str else ''}",
                exc_info=True
            )

    def log_warning(self, message: str, details: Dict[str, Any] = None):
        """记录警告

        Args:
            message: 警告消息
            details: 详情
        """
        if self._logger:
            details_str = ""
            if details:
                details_str = ", ".join([f"{k}={v}" for k, v in details.items()])

            self._logger.warning(
                f"{message}{', 详情: ' + details_str if details_str else ''}"
            )

    def log_performance(self, operation: str, duration_ms: float, details: Dict[str, Any] = None):
        """记录性能数据

        Args:
            operation: 操作名称
            duration_ms: 耗时（毫秒）
            details: 详情
        """
        if self._logger:
            details_str = ""
            if details:
                details_str = ", ".join([f"{k}={v}" for k, v in details.items()])

            self._logger.debug(
                f"性能: {operation}, "
                f"耗时: {duration_ms:.2f}ms"
                f"{', 详情: ' + details_str if details_str else ''}"
            )

    def log_undo_redo(self, action: str, command_description: str):
        """记录撤销/重做操作

        Args:
            action: 操作类型（undo/redo）
            command_description: 命令描述
        """
        if self._logger:
            self._logger.info(f"{action.upper()}: {command_description}")


# 创建全局日志管理器实例
logger_manager = LoggerManager()
