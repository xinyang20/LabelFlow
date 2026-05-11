#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LabelFlow - 快捷图片标注工具 - 主程序入口
"""

import os
import sys
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from config_manager import config_manager
from logger_manager import logger_manager
from app_controller import AppController


def resolve_resource_path(relative_path: str) -> str:
    """Resolve project resources in both source and frozen builds."""
    if os.path.isabs(relative_path):
        return relative_path

    if getattr(sys, 'frozen', False):
        candidates = [
            os.path.join(getattr(sys, '_MEIPASS', ''), relative_path),
            os.path.join(os.path.dirname(sys.executable), relative_path),
        ]
        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate

        return candidates[-1]

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, relative_path)


def main():
    """主程序入口"""
    # 初始化日志系统
    logger_config = config_manager.get_logging_config()
    logger_manager.setup_logger(logger_config)
    logger_manager.log_app_start()

    # 创建Qt应用
    app = QApplication(sys.argv)

    # 获取应用信息
    app_info = config_manager.get_app_info()
    app.setApplicationName(app_info.get('name', 'LabelFlow'))
    app.setApplicationVersion(app_info.get('version', '0.0.5'))
    icon_path = app_info.get('icon_path')
    if icon_path:
        resolved_icon_path = resolve_resource_path(icon_path)
        if os.path.exists(resolved_icon_path):
            app.setWindowIcon(QIcon(resolved_icon_path))

    # 创建控制器，它会自动创建UI
    controller = AppController()
    controller.show()

    # 运行应用
    exit_code = app.exec()

    # 记录应用退出
    logger_manager.log_app_exit()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
