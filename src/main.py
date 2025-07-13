#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Label - 快捷图片标注工具 - 主程序入口
"""

import sys
from PyQt6.QtWidgets import QApplication
from app_controller import AppController


def main():
    """主程序入口"""
    app = QApplication(sys.argv)
    app.setApplicationName("Quick Label")
    app.setApplicationVersion("1.0.0")
    
    # 创建控制器，它会自动创建UI
    controller = AppController()
    controller.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
