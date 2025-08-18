#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Label - 快捷图片标注工具 - 主程序入口
"""

import sys
import os
import json
from PyQt6.QtWidgets import QApplication
from app_controller import AppController


def load_app_version():
    """从app.info文件加载版本信息"""
    try:
        # 获取资源文件路径（兼容PyInstaller打包）
        if getattr(sys, 'frozen', False):
            # 打包后的环境
            current_dir = sys._MEIPASS
        else:
            # 开发环境
            current_dir = os.path.dirname(os.path.abspath(__file__))
        app_info_path = os.path.join(current_dir, "app.info")

        if os.path.exists(app_info_path):
            with open(app_info_path, 'r', encoding='utf-8') as f:
                app_info = json.load(f)
                return app_info.get('version', '1.0.0')
        else:
            return '1.0.0'
    except Exception:
        return '1.0.0'


def main():
    """主程序入口"""
    app = QApplication(sys.argv)
    app.setApplicationName("Quick Label")
    app.setApplicationVersion(load_app_version())
    
    # 创建控制器，它会自动创建UI
    controller = AppController()
    controller.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
