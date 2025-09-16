#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LabelFlow - 快捷图片标注工具 - 关于对话框
"""

import os
import sys
import json
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTextEdit, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QDesktopServices
from PyQt6.QtCore import QUrl


class AboutDialog(QDialog):
    """关于对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.app_info = self._load_app_info()
        self.init_ui()

    def _load_app_info(self):
        """从app.info文件加载应用信息"""
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
                    return json.load(f)
            else:
                # 默认信息
                return {
                    "name": "LabelFlow",
                    "version": "1.0.0",
                    "description": "快捷图片标注工具",
                    "author": "xinyang20",
                    "email": "gaoxinyang317@gmail.com",
                    "github": "https://github.com/xinyang20/LabelFlow",
                }
        except Exception as e:
            print(f"加载应用信息失败: {e}")
            # 返回默认信息
            return {
                "name": "LabelFlow",
                "version": "1.0.0",
                "description": "快捷图片标注工具",
                "author": "xinyang20",
                "email": "gaoxinyang317@gmail.com",
                "github": "https://github.com/xinyang20/LabelFlow",
            }

    def init_ui(self):
        """初始化UI界面"""
        self.setWindowTitle("关于 LabelFlow")
        self.setFixedSize(500, 600)
        self.setModal(True)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 标题区域
        self.create_title_section(main_layout)

        # 分隔线
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line1)

        # 软件描述区域
        self.create_description_section(main_layout)

        # 分隔线
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line2)

        # 功能特点区域
        self.create_features_section(main_layout)

        # 分隔线
        line3 = QFrame()
        line3.setFrameShape(QFrame.Shape.HLine)
        line3.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line3)

        # 开发者信息区域
        self.create_developer_section(main_layout)

        # 按钮区域
        self.create_button_section(main_layout)

    def create_title_section(self, parent_layout):
        """创建标题区域"""
        title_layout = QVBoxLayout()

        # 应用名称
        app_name = QLabel(self.app_info.get('name', 'LabelFlow'))
        app_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_name_font = QFont()
        app_name_font.setPointSize(24)
        app_name_font.setBold(True)
        app_name.setFont(app_name_font)
        app_name.setObjectName("aboutAppName")
        title_layout.addWidget(app_name)

        # 副标题
        subtitle = QLabel(self.app_info.get('description', '快捷图片标注工具'))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(14)
        subtitle.setFont(subtitle_font)
        subtitle.setObjectName("aboutSubtitle")
        title_layout.addWidget(subtitle)

        # 版本信息
        version = QLabel(f"版本 {self.app_info.get('version', '1.0.0')}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setObjectName("aboutVersion")
        title_layout.addWidget(version)

        parent_layout.addLayout(title_layout)

    def create_description_section(self, parent_layout):
        """创建软件描述区域"""
        desc_label = QLabel("软件描述")
        desc_label.setProperty("variant", "sectionTitle")
        parent_layout.addWidget(desc_label)

        description = QLabel("一款高效、易用的桌面应用程序，用于对图片进行文字描述标注。")
        description.setWordWrap(True)
        description.setProperty("variant", "bodyText")
        parent_layout.addWidget(description)

    def create_features_section(self, parent_layout):
        """创建功能特点区域"""
        features_label = QLabel("功能特点")
        features_label.setProperty("variant", "sectionTitle")
        parent_layout.addWidget(features_label)

        features_text = """• 智能图片管理：使用SHA256哈希值确保图片与标签的准确对应
• 分片加载策略：支持大量图片的高效处理，自动内存管理
• 实时保存：标注内容自动保存，支持断点续标
• 直观界面：左右布局，图片显示与标注输入分离
• 进度跟踪：实时显示标注进度和文件信息"""

        features = QLabel(features_text)
        features.setWordWrap(True)
        features.setProperty("variant", "bodyText")
        parent_layout.addWidget(features)

    def create_developer_section(self, parent_layout):
        """创建开发者信息区域"""
        dev_label = QLabel("开发者信息")
        dev_label.setProperty("variant", "sectionTitle")
        parent_layout.addWidget(dev_label)

        # 开发者信息布局
        dev_layout = QVBoxLayout()

        # GitHub项目地址
        project_layout = QHBoxLayout()
        project_label = QLabel("项目地址：")
        project_label.setProperty("variant", "mutedLabel")
        project_layout.addWidget(project_label)

        github_url = self.app_info.get(
            "github", "https://github.com/xinyang20/LabelFlow"
        )
        project_link = QLabel(
            f'<a href="{github_url}" style="color: inherit; text-decoration: none;">{github_url}</a>'
        )
        project_link.setOpenExternalLinks(True)
        project_link.setProperty("variant", "link")
        project_layout.addWidget(project_link)
        project_layout.addStretch()

        dev_layout.addLayout(project_layout)

        # 开发者GitHub
        dev_github_layout = QHBoxLayout()
        dev_github_label = QLabel("开发者：")
        dev_github_label.setProperty("variant", "mutedLabel")
        dev_github_layout.addWidget(dev_github_label)

        author = self.app_info.get('author', 'xinyang20')
        author_github_url = f"https://github.com/{author}/"
        dev_github_link = QLabel(
            f'<a href="{author_github_url}" style="color: inherit; text-decoration: none;">{author}</a>'
        )
        dev_github_link.setOpenExternalLinks(True)
        dev_github_link.setProperty("variant", "link")
        dev_github_layout.addWidget(dev_github_link)
        dev_github_layout.addStretch()

        dev_layout.addLayout(dev_github_layout)

        # 联系邮箱
        email_layout = QHBoxLayout()
        email_label = QLabel("联系邮箱：")
        email_label.setProperty("variant", "mutedLabel")
        email_layout.addWidget(email_label)

        email = self.app_info.get('email', 'gaoxinyang317@gmail.com')
        email_link = QLabel(
            f'<a href="mailto:{email}" style="color: inherit; text-decoration: none;">{email}</a>'
        )
        email_link.setOpenExternalLinks(True)
        email_link.setProperty("variant", "link")
        email_layout.addWidget(email_link)
        email_layout.addStretch()

        dev_layout.addLayout(email_layout)

        parent_layout.addLayout(dev_layout)

    def create_button_section(self, parent_layout):
        """创建按钮区域"""
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # 访问GitHub按钮
        github_button = QPushButton("访问GitHub项目")
        github_button.clicked.connect(self.open_github)
        button_layout.addWidget(github_button)

        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.setProperty("buttonRole", "secondary")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        parent_layout.addLayout(button_layout)

    def open_github(self):
        """打开GitHub项目页面"""
        github_url = self.app_info.get(
            "github", "https://github.com/xinyang20/LabelFlow"
        )
        QDesktopServices.openUrl(QUrl(github_url))
