#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Label - 快捷图片标注工具 - UI界面模块
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QLabel, QTextEdit, QPushButton, QMenuBar, QMenu,
                             QFileDialog, QMessageBox, QProgressBar, QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QAction


class MainWindow(QMainWindow):
    """主窗口类"""
    
    # 定义信号
    directory_selected = pyqtSignal(str)  # 目录选择信号
    next_image = pyqtSignal()  # 下一张图片信号
    prev_image = pyqtSignal()  # 上一张图片信号
    annotation_changed = pyqtSignal(str)  # 标注内容变化信号
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化UI界面"""
        self.setWindowTitle("Quick Label - 快捷图片标注工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局（水平分割器）
        main_layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧：图片显示区域
        self.create_image_area(splitter)
        
        # 右侧：控制面板
        self.create_control_panel(splitter)
        
        # 设置分割器比例
        splitter.setSizes([800, 400])
        
        # 创建状态栏
        self.create_status_bar()
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        
        # 选择目录动作
        select_dir_action = QAction('选择工作目录(&O)', self)
        select_dir_action.setShortcut('Ctrl+O')
        select_dir_action.triggered.connect(self.select_directory)
        file_menu.addAction(select_dir_action)
        
        file_menu.addSeparator()
        
        # 退出动作
        exit_action = QAction('退出(&X)', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
    def create_image_area(self, parent):
        """创建图片显示区域"""
        image_widget = QWidget()
        image_layout = QVBoxLayout(image_widget)
        
        # 图片显示标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px solid #cccccc;
                background-color: #f5f5f5;
                min-height: 400px;
                min-width: 600px;
            }
        """)
        self.image_label.setText("请选择工作目录以开始标注")
        self.image_label.setScaledContents(False)  # 禁用自动缩放内容
        image_layout.addWidget(self.image_label)
        
        parent.addWidget(image_widget)
        
    def create_control_panel(self, parent):
        """创建右侧控制面板"""
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        # 文件信息区域
        info_layout = QVBoxLayout()
        
        # 文件名显示
        self.filename_label = QLabel("文件名: 未选择")
        self.filename_label.setWordWrap(True)
        info_layout.addWidget(self.filename_label)
        
        # 哈希值显示
        self.hash_label = QLabel("SHA256: 未计算")
        self.hash_label.setWordWrap(True)
        self.hash_label.setStyleSheet("font-family: monospace; font-size: 10px;")
        info_layout.addWidget(self.hash_label)
        
        # 进度显示
        self.progress_label = QLabel("进度: 0 / 0")
        info_layout.addWidget(self.progress_label)
        
        control_layout.addLayout(info_layout)
        
        # 标注文本区域
        annotation_label = QLabel("标注内容:")
        control_layout.addWidget(annotation_label)
        
        self.annotation_text = QTextEdit()
        self.annotation_text.setPlaceholderText("请在此输入图片描述...")
        self.annotation_text.textChanged.connect(self.on_annotation_changed)
        control_layout.addWidget(self.annotation_text)
        
        # 导航按钮区域
        button_layout = QHBoxLayout()
        
        self.prev_button = QPushButton("上一张")
        self.prev_button.clicked.connect(self.on_prev_clicked)
        self.prev_button.setEnabled(False)
        button_layout.addWidget(self.prev_button)
        
        self.next_button = QPushButton("下一张")
        self.next_button.clicked.connect(self.on_next_clicked)
        self.next_button.setEnabled(False)
        button_layout.addWidget(self.next_button)
        
        control_layout.addLayout(button_layout)
        
        # 添加弹性空间
        control_layout.addStretch()
        
        parent.addWidget(control_widget)
        
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        self.status_bar.showMessage("就绪")
        
    def select_directory(self):
        """选择工作目录"""
        directory = QFileDialog.getExistingDirectory(
            self, "选择包含图片的工作目录", "")
        if directory:
            self.directory_selected.emit(directory)
            
    def on_prev_clicked(self):
        """上一张按钮点击"""
        self.prev_image.emit()
        
    def on_next_clicked(self):
        """下一张按钮点击"""
        self.next_image.emit()
        
    def on_annotation_changed(self):
        """标注内容变化"""
        text = self.annotation_text.toPlainText()
        self.annotation_changed.emit(text)
        
    def update_image(self, pixmap):
        """更新显示的图片"""
        if pixmap and not pixmap.isNull():
            # 使用固定的最大尺寸来缩放图片，避免影响窗口布局
            max_width = 600
            max_height = 400

            # 缩放图片以适应固定的显示区域
            scaled_pixmap = pixmap.scaled(
                max_width, max_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("无法加载图片")
            
    def update_info(self, filename, hash_value, current_index, total_count):
        """更新文件信息"""
        self.filename_label.setText(f"文件名: {filename}")
        self.hash_label.setText(f"SHA256: {hash_value}")
        self.progress_label.setText(f"进度: {current_index + 1} / {total_count}")
        
    def update_annotation(self, annotation):
        """更新标注内容"""
        # 暂时断开信号连接，避免循环触发
        self.annotation_text.textChanged.disconnect()
        self.annotation_text.setPlainText(annotation)
        self.annotation_text.textChanged.connect(self.on_annotation_changed)
        
    def update_navigation_buttons(self, has_prev, has_next):
        """更新导航按钮状态"""
        self.prev_button.setEnabled(has_prev)
        self.next_button.setEnabled(has_next)
        
    def show_loading_progress(self, visible, current=0, total=0, message=""):
        """显示加载进度"""
        self.progress_bar.setVisible(visible)
        if visible:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            self.status_bar.showMessage(message)
        else:
            self.status_bar.showMessage("就绪")
            
    def show_message(self, title, message, msg_type="info"):
        """显示消息框"""
        if msg_type == "info":
            QMessageBox.information(self, title, message)
        elif msg_type == "warning":
            QMessageBox.warning(self, title, message)
        elif msg_type == "error":
            QMessageBox.critical(self, title, message)
