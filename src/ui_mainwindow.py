#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Label - 快捷图片标注工具 - UI界面模块
"""

import os
import sys
import json
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QLabel, QTextEdit, QPushButton, QMenuBar, QMenu,
                             QFileDialog, QMessageBox, QProgressBar, QSplitter,
                             QComboBox, QLineEdit, QCheckBox, QScrollArea, QFrame,
                             QSlider, QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QAction, QWheelEvent
from about_dialog import AboutDialog
from language_manager import language_manager, tr


class MainWindow(QMainWindow):
    """主窗口类"""

    # 定义信号
    directory_selected = pyqtSignal(str)  # 目录选择信号
    save_path_selected = pyqtSignal(str)  # 保存路径选择信号
    auto_save_changed = pyqtSignal(bool)  # 自动保存设置变化信号
    next_image = pyqtSignal()  # 下一张图片信号
    prev_image = pyqtSignal()  # 上一张图片信号
    annotation_changed = pyqtSignal(str)  # 标注内容变化信号
    mode_changed = pyqtSignal(str)  # 标注模式变化信号
    labels_changed = pyqtSignal(list)  # 标签列表变化信号

    def __init__(self):
        super().__init__()
        self.version = self._load_version_info()
        self.auto_save_enabled = True  # 默认开启自动保存
        self.current_mode = "description"  # 当前标注模式：description, label, mixed
        self.available_labels = []  # 可用标签列表
        self.selected_labels = []  # 当前选中的标签
        self.zoom_factor = 100  # 当前缩放比例（百分比）
        self.original_pixmap = None  # 原始图片数据

        # 连接语言变化信号
        language_manager.language_changed.connect(self.on_language_changed)

        self.init_ui()

    def _load_version_info(self):
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
        except Exception as e:
            print(f"加载版本信息失败: {e}")
            return '1.0.0'
        
    def init_ui(self):
        """初始化UI界面"""
        self.setWindowTitle(tr("app_title"))
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
        self.file_menu = menubar.addMenu(tr('file_menu'))

        # 选择目录动作
        self.select_dir_action = QAction(tr('select_directory'), self)
        self.select_dir_action.setShortcut('Ctrl+O')
        self.select_dir_action.triggered.connect(self.select_directory)
        self.file_menu.addAction(self.select_dir_action)

        # 选择保存路径动作
        self.select_save_path_action = QAction(tr('set_save_path'), self)
        self.select_save_path_action.setShortcut('Ctrl+S')
        self.select_save_path_action.triggered.connect(self.select_save_path)
        self.file_menu.addAction(self.select_save_path_action)

        self.file_menu.addSeparator()

        # 退出动作
        self.exit_action = QAction(tr('exit'), self)
        self.exit_action.setShortcut('Ctrl+Q')
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)

        # 设置菜单
        self.settings_menu = menubar.addMenu(tr('settings_menu'))

        # 自动保存选项
        self.auto_save_action = QAction(tr('auto_save'), self)
        self.auto_save_action.setCheckable(True)
        self.auto_save_action.setChecked(self.auto_save_enabled)
        self.auto_save_action.triggered.connect(self.toggle_auto_save)
        self.settings_menu.addAction(self.auto_save_action)

        self.settings_menu.addSeparator()

        # 语言菜单
        self.create_language_menu()

        self.settings_menu.addSeparator()

        # 标注模式菜单
        self.create_mode_menu()

        # 帮助菜单
        self.help_menu = menubar.addMenu(tr('help_menu'))

        # 关于动作
        self.about_action = QAction(tr('about'), self)
        self.about_action.triggered.connect(self.show_about_dialog)
        self.help_menu.addAction(self.about_action)
        
    def create_image_area(self, parent):
        """创建图片显示区域"""
        image_widget = QWidget()
        image_layout = QVBoxLayout(image_widget)

        # 图片显示区域（使用滚动区域支持缩放）
        self.image_scroll = QScrollArea()
        self.image_scroll.setWidgetResizable(True)
        self.image_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
        self.image_label.setText(tr("select_work_directory_to_start"))
        self.image_label.setScaledContents(False)  # 禁用自动缩放内容

        self.image_scroll.setWidget(self.image_label)

        # 安装事件过滤器以处理滚轮缩放
        self.image_scroll.installEventFilter(self)

        image_layout.addWidget(self.image_scroll)

        # 缩放控制区域
        self.create_zoom_controls(image_layout)

        parent.addWidget(image_widget)
        
    def create_control_panel(self, parent):
        """创建右侧控制面板"""
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)

        # 文件信息区域
        info_layout = QVBoxLayout()

        # 文件名显示
        self.filename_label = QLabel(f"{tr('filename')}: {tr('not_selected')}")
        self.filename_label.setWordWrap(True)
        info_layout.addWidget(self.filename_label)

        # 哈希值显示
        self.hash_label = QLabel(f"SHA256: {tr('not_calculated')}")
        self.hash_label.setWordWrap(True)
        self.hash_label.setStyleSheet("font-family: monospace; font-size: 10px;")
        info_layout.addWidget(self.hash_label)

        # 进度显示
        self.progress_label = QLabel(f"{tr('progress')}: 0 / 0")
        info_layout.addWidget(self.progress_label)

        control_layout.addLayout(info_layout)

        # 标注区域
        self.create_annotation_area(control_layout)
        
        # 导航按钮区域
        button_layout = QHBoxLayout()
        
        self.prev_button = QPushButton(tr("prev"))
        self.prev_button.clicked.connect(self.on_prev_clicked)
        self.prev_button.setEnabled(False)
        button_layout.addWidget(self.prev_button)

        self.next_button = QPushButton(tr("next"))
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

        # 版本号标签（左侧永久显示）
        self.version_label = QLabel(f"v{self.version}")
        self.version_label.setStyleSheet("color: #666; font-size: 11px; margin-right: 10px;")
        self.status_bar.addPermanentWidget(self.version_label)

        # 分隔符
        separator = QLabel("|")
        separator.setStyleSheet("color: #ccc; margin: 0 5px;")
        self.status_bar.addPermanentWidget(separator)

        # 进度条（右侧）
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # 设置初始状态消息
        self.status_bar.showMessage(tr("ready"))
        
    def select_directory(self):
        """选择工作目录"""
        directory = QFileDialog.getExistingDirectory(
            self, tr("select_work_directory"), "")
        if directory:
            self.directory_selected.emit(directory)

    def select_save_path(self):
        """选择标注文件保存路径"""
        directory = QFileDialog.getExistingDirectory(
            self, tr("select_save_directory"), "")
        if directory:
            self.save_path_selected.emit(directory)
            self.show_message(tr("setting_success"), f"{tr('save_path_set')}：\n{directory}", "info")

    def toggle_auto_save(self):
        """切换自动保存设置"""
        self.auto_save_enabled = self.auto_save_action.isChecked()
        self.auto_save_changed.emit(self.auto_save_enabled)

        status = tr("auto_save_enabled") if self.auto_save_enabled else tr("auto_save_disabled")
        self.show_message(tr("setting_success"), status, "info")

    def show_save_confirmation(self, filename):
        """显示保存确认对话框"""
        reply = QMessageBox.question(
            self,
            tr("save_confirmation"),
            f"{tr('save_current_annotation')}\n\n{tr('file')}：{filename}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Yes
        )
        return reply

    def show_about_dialog(self):
        """显示关于对话框"""
        about_dialog = AboutDialog(self)
        about_dialog.exec()
            
    def on_prev_clicked(self):
        """上一张按钮点击"""
        self.prev_image.emit()
        
    def on_next_clicked(self):
        """下一张按钮点击"""
        self.next_image.emit()
        
    def on_annotation_changed(self):
        """标注内容变化"""
        # 根据当前模式获取标注数据
        annotation_data = self.get_annotation_data()

        # 发送完整的数据结构（JSON字符串）
        import json
        self.annotation_changed.emit(json.dumps(annotation_data, ensure_ascii=False))
        
    def update_image(self, pixmap):
        """更新显示的图片"""
        if pixmap and not pixmap.isNull():
            # 保存原始图片数据
            self.original_pixmap = pixmap

            # 重置缩放比例为100%
            self.zoom_factor = 100
            self.zoom_slider.setValue(100)
            self.zoom_label.setText("100%")

            # 应用当前缩放
            self.update_image_zoom()
        else:
            self.original_pixmap = None
            self.image_label.setText(tr("cannot_load_image"))
            self.image_label.clear()
            
    def update_info(self, filename, hash_value, current_index, total_count):
        """更新文件信息"""
        self.filename_label.setText(f"{tr('filename')}: {filename}")
        self.hash_label.setText(f"SHA256: {hash_value}")
        self.progress_label.setText(f"{tr('progress')}: {current_index + 1} / {total_count}")
        
    def update_annotation(self, annotation):
        """更新标注内容"""
        # 暂时断开信号连接，避免循环触发
        self.annotation_text.textChanged.disconnect()

        try:
            # 尝试解析为JSON格式
            import json
            if annotation.strip().startswith('{'):
                data = json.loads(annotation)
                self.set_annotation_data(data)
            else:
                # 兼容旧格式（纯字符串）
                self.set_annotation_data(annotation)
        except (json.JSONDecodeError, AttributeError):
            # 如果解析失败，按字符串处理
            self.set_annotation_data(annotation)

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
            self.status_bar.showMessage(tr("ready"))
            
    def show_message(self, title, message, msg_type="info"):
        """显示消息框"""
        if msg_type == "info":
            QMessageBox.information(self, title, message)
        elif msg_type == "warning":
            QMessageBox.warning(self, title, message)
        elif msg_type == "error":
            QMessageBox.critical(self, title, message)



    def create_annotation_area(self, parent_layout):
        """创建标注区域"""
        # 描述模式区域
        self.description_frame = QFrame()
        desc_layout = QVBoxLayout(self.description_frame)

        desc_label = QLabel(f"{tr('annotation_content')}:")
        desc_layout.addWidget(desc_label)

        self.annotation_text = QTextEdit()
        self.annotation_text.setPlaceholderText(tr("input_description"))
        self.annotation_text.textChanged.connect(self.on_annotation_changed)
        desc_layout.addWidget(self.annotation_text)

        parent_layout.addWidget(self.description_frame)

        # 标签模式区域
        self.label_frame = QFrame()
        label_layout = QVBoxLayout(self.label_frame)

        # 新标签输入
        new_label_layout = QHBoxLayout()
        new_label_layout.addWidget(QLabel(f"{tr('new_label')}:"))

        self.new_label_input = QLineEdit()
        self.new_label_input.setPlaceholderText(tr("input_new_label"))
        self.new_label_input.returnPressed.connect(self.add_new_label)
        new_label_layout.addWidget(self.new_label_input)

        add_label_btn = QPushButton(tr("add"))
        add_label_btn.clicked.connect(self.add_new_label)
        new_label_layout.addWidget(add_label_btn)

        label_layout.addLayout(new_label_layout)

        # 标签列表区域
        labels_label = QLabel(f"{tr('available_labels')}:")
        label_layout.addWidget(labels_label)

        # 创建滚动区域用于标签列表
        self.labels_scroll = QScrollArea()
        self.labels_scroll.setWidgetResizable(True)
        self.labels_scroll.setMaximumHeight(200)

        self.labels_widget = QWidget()
        self.labels_layout = QVBoxLayout(self.labels_widget)
        self.labels_scroll.setWidget(self.labels_widget)

        label_layout.addWidget(self.labels_scroll)

        # 初始状态隐藏标签模式
        self.label_frame.setVisible(False)
        parent_layout.addWidget(self.label_frame)



    def add_new_label(self):
        """添加新标签"""
        label_text = self.new_label_input.text().strip()
        if label_text:
            # 将标签添加到当前图片的标签列表
            if label_text not in self.selected_labels:
                self.selected_labels.append(label_text)

            # 将标签添加到全局可用标签列表
            if label_text not in self.available_labels:
                self.available_labels.append(label_text)
                # 发送标签变化信号
                self.labels_changed.emit(self.available_labels)

            self.new_label_input.clear()
            self.update_labels_display()

            # 触发标注内容变化，自动保存
            self.on_annotation_changed()

    def update_labels_display(self):
        """更新标签显示"""
        # 清除现有标签
        for i in reversed(range(self.labels_layout.count())):
            child = self.labels_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        # 添加标签复选框
        for label in self.available_labels:
            checkbox = QCheckBox(label)
            checkbox.setChecked(label in self.selected_labels)
            checkbox.stateChanged.connect(lambda state, l=label: self.on_label_checked(l, state))
            self.labels_layout.addWidget(checkbox)

    def on_label_checked(self, label, state):
        """处理标签选择状态变化"""
        if state == 2:  # 选中
            if label not in self.selected_labels:
                self.selected_labels.append(label)
        else:  # 取消选中
            if label in self.selected_labels:
                self.selected_labels.remove(label)

        # 触发标注内容变化，自动保存
        self.on_annotation_changed()

    def set_available_labels(self, labels):
        """设置可用标签列表"""
        self.available_labels = labels[:]
        self.update_labels_display()

    def set_selected_labels(self, labels):
        """设置选中的标签"""
        self.selected_labels = labels[:]
        self.update_labels_display()

    def reset_label_selection(self):
        """重置标签选择状态（切换图片时使用）"""
        self.selected_labels = []
        self.update_labels_display()

    def get_annotation_data(self):
        """获取当前标注数据"""
        data = {}

        # 新的字段结构 - 直接保存到根级别
        if self.current_mode in ["description", "mixed"]:
            describe_text = self.annotation_text.toPlainText().strip()
            if describe_text:
                data["describe"] = describe_text

        if self.current_mode in ["label", "mixed"]:
            if self.selected_labels:
                data["label"] = self.selected_labels[:]

        # 保持向后兼容的annotation字段 - 简化格式
        if self.current_mode == "description":
            describe_text = self.annotation_text.toPlainText().strip()
            if describe_text:
                data["annotation"] = describe_text
        elif self.current_mode == "label":
            # 对于纯标签模式，annotation字段保存为空字符串或不保存
            if self.selected_labels:
                data["annotation"] = ""  # 标记为已标注但内容在label字段中
        elif self.current_mode == "mixed":
            # 混合模式：annotation字段只保存描述内容
            describe_text = self.annotation_text.toPlainText().strip()
            if describe_text:
                data["annotation"] = describe_text

        return data

    def set_annotation_data(self, data):
        """设置标注数据"""
        # 初始化
        self.annotation_text.setPlainText("")
        self.selected_labels = []

        if isinstance(data, str):
            # 兼容旧格式（纯字符串）
            self.annotation_text.setPlainText(data)
        elif isinstance(data, dict):
            # 优先使用新字段格式
            if "describe" in data:
                self.annotation_text.setPlainText(data["describe"])
            elif "annotation" in data:
                # 向后兼容旧annotation字段
                annotation = data["annotation"]
                if annotation:  # 只有非空时才处理
                    try:
                        # 尝试解析JSON格式的annotation（处理旧的嵌套格式）
                        import json
                        if annotation.strip().startswith('{'):
                            parsed = json.loads(annotation)
                            if "annotation" in parsed:
                                self.annotation_text.setPlainText(parsed["annotation"])
                            if "labels" in parsed:
                                self.selected_labels = parsed["labels"][:]
                        else:
                            self.annotation_text.setPlainText(annotation)
                    except (json.JSONDecodeError, AttributeError):
                        self.annotation_text.setPlainText(annotation)

            # 处理标签字段
            if "label" in data:
                self.selected_labels = data["label"][:]
            elif "labels" in data:
                # 向后兼容旧labels字段
                self.selected_labels = data["labels"][:]

        self.update_labels_display()

    def create_zoom_controls(self, parent_layout):
        """创建缩放控制区域"""
        zoom_frame = QFrame()
        zoom_frame.setFrameStyle(QFrame.Shape.Box)
        zoom_frame.setStyleSheet("QFrame { border: 1px solid #cccccc; border-radius: 3px; padding: 5px; }")
        zoom_layout = QHBoxLayout(zoom_frame)
        zoom_layout.setContentsMargins(5, 5, 5, 5)

        # 缩放标签
        zoom_label = QLabel(f"{tr('zoom')}:")
        zoom_layout.addWidget(zoom_label)

        # 缩小按钮
        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setFixedSize(30, 25)
        zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_layout.addWidget(zoom_out_btn)

        # 缩放滑块
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(10)  # 最小10%
        self.zoom_slider.setMaximum(500)  # 最大500%
        self.zoom_slider.setValue(100)  # 默认100%
        self.zoom_slider.setFixedWidth(150)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        zoom_layout.addWidget(self.zoom_slider)

        # 放大按钮
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedSize(30, 25)
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_layout.addWidget(zoom_in_btn)

        # 缩放比例显示
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(50)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        zoom_layout.addWidget(self.zoom_label)

        # 重置按钮
        reset_btn = QPushButton(tr("reset"))
        reset_btn.setFixedSize(50, 25)
        reset_btn.clicked.connect(self.reset_zoom)
        zoom_layout.addWidget(reset_btn)

        zoom_layout.addStretch()
        parent_layout.addWidget(zoom_frame)

    def zoom_in(self):
        """放大图片"""
        new_value = min(self.zoom_slider.value() + 25, self.zoom_slider.maximum())
        self.zoom_slider.setValue(new_value)

    def zoom_out(self):
        """缩小图片"""
        new_value = max(self.zoom_slider.value() - 25, self.zoom_slider.minimum())
        self.zoom_slider.setValue(new_value)

    def reset_zoom(self):
        """重置缩放"""
        self.zoom_slider.setValue(100)

    def on_zoom_changed(self, value):
        """处理缩放变化"""
        self.zoom_factor = value
        self.zoom_label.setText(f"{value}%")
        self.update_image_zoom()

    def update_image_zoom(self):
        """更新图片缩放显示"""
        if self.original_pixmap and not self.original_pixmap.isNull():
            if self.zoom_factor == 100:
                # 100%时，图片适应显示区域
                scroll_size = self.image_scroll.size()
                # 减去滚动条和边距的空间
                available_width = scroll_size.width() - 20
                available_height = scroll_size.height() - 20

                scaled_pixmap = self.original_pixmap.scaled(
                    available_width, available_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            else:
                # 其他缩放比例，基于100%时的适应大小进行缩放
                scroll_size = self.image_scroll.size()
                available_width = scroll_size.width() - 20
                available_height = scroll_size.height() - 20

                # 先计算100%时的大小
                fit_size = self.original_pixmap.size().scaled(
                    available_width, available_height,
                    Qt.AspectRatioMode.KeepAspectRatio
                )

                # 再根据缩放比例调整
                scale_factor = self.zoom_factor / 100.0
                final_size = fit_size * scale_factor

                scaled_pixmap = self.original_pixmap.scaled(
                    final_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.resize(scaled_pixmap.size())

    def create_language_menu(self):
        """创建语言菜单"""
        self.language_menu = self.settings_menu.addMenu(tr('language'))

        available_languages = language_manager.get_available_languages()
        current_language = language_manager.get_current_language()

        self.language_actions = []
        for lang_code, lang_name in available_languages.items():
            action = QAction(lang_name, self)
            action.setCheckable(True)
            action.setChecked(lang_code == current_language)
            action.triggered.connect(lambda checked, code=lang_code: self.change_language(code))
            self.language_menu.addAction(action)
            self.language_actions.append((action, lang_code))

    def create_mode_menu(self):
        """创建标注模式菜单"""
        self.mode_menu = self.settings_menu.addMenu(tr('annotation_mode'))

        modes = [
            ("description", tr("description_mode")),
            ("label", tr("label_mode")),
            ("mixed", tr("mixed_mode"))
        ]

        self.mode_actions = []
        for mode_code, mode_name in modes:
            action = QAction(mode_name, self)
            action.setCheckable(True)
            action.setChecked(mode_code == self.current_mode)
            action.triggered.connect(lambda checked, code=mode_code: self.change_mode(code))
            self.mode_menu.addAction(action)
            self.mode_actions.append((action, mode_code))

    def change_language(self, language_code: str):
        """切换语言"""
        if language_manager.set_language(language_code):
            # 更新语言菜单选中状态（确保单选）
            for action, code in self.language_actions:
                action.setChecked(code == language_code)

    def change_mode(self, mode_code: str):
        """切换标注模式"""
        self.current_mode = mode_code

        # 更新模式菜单选中状态
        for action, code in self.mode_actions:
            action.setChecked(code == mode_code)

        # 根据模式显示/隐藏相应区域
        if self.current_mode == "description":
            self.description_frame.setVisible(True)
            self.label_frame.setVisible(False)
        elif self.current_mode == "label":
            self.description_frame.setVisible(False)
            self.label_frame.setVisible(True)
        elif self.current_mode == "mixed":
            self.description_frame.setVisible(True)
            self.label_frame.setVisible(True)

        # 发送模式变化信号
        self.mode_changed.emit(self.current_mode)

    def on_language_changed(self, language_code: str):
        """处理语言变化"""
        # 更新窗口标题
        self.setWindowTitle(tr("app_title"))

        # 更新菜单文本
        self.update_menu_texts()

        # 更新界面文本
        self.update_ui_texts()

    def update_menu_texts(self):
        """更新菜单文本"""
        # 更新文件菜单
        self.file_menu.setTitle(tr('file_menu'))
        self.select_dir_action.setText(tr('select_directory'))
        self.select_save_path_action.setText(tr('set_save_path'))
        self.exit_action.setText(tr('exit'))

        # 更新设置菜单
        self.settings_menu.setTitle(tr('settings_menu'))
        self.auto_save_action.setText(tr('auto_save'))

        # 更新语言菜单
        self.language_menu.setTitle(tr('language'))

        # 更新模式菜单
        self.mode_menu.setTitle(tr('annotation_mode'))
        modes = [
            ("description", tr("description_mode")),
            ("label", tr("label_mode")),
            ("mixed", tr("mixed_mode"))
        ]
        for i, (action, mode_code) in enumerate(self.mode_actions):
            if i < len(modes):
                action.setText(modes[i][1])

        # 更新帮助菜单
        self.help_menu.setTitle(tr('help_menu'))
        self.about_action.setText(tr('about'))

    def update_ui_texts(self):
        """更新界面文本"""
        # 更新文件信息标签
        if hasattr(self, 'filename_label'):
            current_text = self.filename_label.text()
            if current_text.startswith("文件名:") or current_text.startswith("Filename:"):
                filename = current_text.split(": ", 1)[1] if ": " in current_text else tr("not_selected")
                self.filename_label.setText(f"{tr('filename')}: {filename}")

        if hasattr(self, 'progress_label'):
            current_text = self.progress_label.text()
            if current_text.startswith("进度:") or current_text.startswith("Progress:"):
                progress = current_text.split(": ", 1)[1] if ": " in current_text else "0 / 0"
                self.progress_label.setText(f"{tr('progress')}: {progress}")



        # 更新其他界面元素
        self.update_annotation_area_texts()
        self.update_zoom_control_texts()
        self.update_navigation_texts()

    def update_annotation_area_texts(self):
        """更新标注区域文本"""
        # 更新标注内容标签
        if hasattr(self, 'description_frame'):
            for child in self.description_frame.findChildren(QLabel):
                text = child.text()
                if ":" in text and (text.startswith("标注内容") or text.startswith("Annotation Content")):
                    child.setText(f"{tr('annotation_content')}:")

        # 更新占位符文本
        if hasattr(self, 'annotation_text'):
            self.annotation_text.setPlaceholderText(tr("input_description"))

        if hasattr(self, 'new_label_input'):
            self.new_label_input.setPlaceholderText(tr("input_new_label"))

        # 更新标签区域文本
        if hasattr(self, 'label_frame'):
            for child in self.label_frame.findChildren(QLabel):
                text = child.text()
                if ":" in text:
                    if text.startswith("新标签") or text.startswith("New Label"):
                        child.setText(f"{tr('new_label')}:")
                    elif text.startswith("可用标签") or text.startswith("Available Labels"):
                        child.setText(f"{tr('available_labels')}:")

        # 更新按钮文本
        if hasattr(self, 'label_frame'):
            for child in self.label_frame.findChildren(QPushButton):
                text = child.text()
                if text in ["添加", "Add"]:
                    child.setText(tr("add"))

    def update_zoom_control_texts(self):
        """更新缩放控制文本"""
        # 查找缩放控制区域的父容器
        for widget in self.findChildren(QFrame):
            # 查找包含缩放控件的框架
            labels = widget.findChildren(QLabel)
            for label in labels:
                text = label.text()
                if ":" in text and (text.startswith("缩放") or text.startswith("Zoom")):
                    label.setText(f"{tr('zoom')}:")

            # 更新重置按钮
            buttons = widget.findChildren(QPushButton)
            for button in buttons:
                text = button.text()
                if text in ["重置", "Reset"]:
                    button.setText(tr("reset"))

    def update_navigation_texts(self):
        """更新导航按钮文本"""
        if hasattr(self, 'prev_button'):
            self.prev_button.setText(tr("prev"))
        if hasattr(self, 'next_button'):
            self.next_button.setText(tr("next"))

    def eventFilter(self, obj, event):
        """事件过滤器，处理Ctrl+滚轮缩放"""
        if obj == self.image_scroll and event.type() == event.Type.Wheel:
            # 检查是否按下Ctrl键
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # 获取滚轮滚动方向
                delta = event.angleDelta().y()

                if delta > 0:
                    # 向上滚动，放大
                    self.zoom_in()
                else:
                    # 向下滚动，缩小
                    self.zoom_out()

                # 阻止事件继续传播
                return True

        # 调用父类的事件过滤器
        return super().eventFilter(obj, event)
