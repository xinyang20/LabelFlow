#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Label - 快捷图片标注工具 - 应用控制器
"""

from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox
from ui_mainwindow import MainWindow
from data_manager import DataManager
from language_manager import tr


class AppController(QObject):
    """应用程序控制器"""
    
    def __init__(self):
        super().__init__()
        self.main_window = MainWindow()
        self.data_manager = DataManager()
        self.auto_save_timer = QTimer()
        self.current_annotation = ""
        self.auto_save_enabled = True  # 默认开启自动保存
        self.available_labels = []  # 全局可用标签列表

        self.setup_connections()
        self.setup_auto_save()
        
    def setup_connections(self):
        """设置信号连接"""
        # UI信号连接
        self.main_window.directory_selected.connect(self.on_directory_selected)
        self.main_window.save_path_selected.connect(self.on_save_path_selected)
        self.main_window.auto_save_changed.connect(self.on_auto_save_changed)
        self.main_window.next_image.connect(self.on_next_image)
        self.main_window.prev_image.connect(self.on_prev_image)
        self.main_window.annotation_changed.connect(self.on_annotation_changed)
        self.main_window.mode_changed.connect(self.on_mode_changed)
        self.main_window.labels_changed.connect(self.on_labels_changed)

        # 数据管理器信号连接
        self.data_manager.loading_progress.connect(self.on_loading_progress)
        self.data_manager.loading_finished.connect(self.on_loading_finished)
        self.data_manager.hash_calculation_progress.connect(self.on_hash_progress)

        # 窗口关闭事件
        self.main_window.closeEvent = self.closeEvent
        
    def setup_auto_save(self):
        """设置自动保存"""
        self.auto_save_timer.timeout.connect(self.auto_save_annotation)
        self.auto_save_timer.setSingleShot(True)
        
    def show(self):
        """显示主窗口"""
        self.main_window.show()
        
    def on_directory_selected(self, directory: str):
        """处理目录选择"""
        self.main_window.show_loading_progress(True, 0, 100, "正在扫描目录...")
        self.data_manager.set_work_directory(directory)

    def on_save_path_selected(self, path: str):
        """处理保存路径选择"""
        self.data_manager.set_custom_save_path(path)

    def on_auto_save_changed(self, enabled: bool):
        """处理自动保存设置变化"""
        self.auto_save_enabled = enabled
        
    def on_loading_progress(self, current: int, total: int, message: str):
        """处理加载进度"""
        self.main_window.show_loading_progress(True, current, total, message)
        
    def on_loading_finished(self):
        """处理加载完成"""
        self.main_window.show_loading_progress(False)
        self.load_available_labels()  # 加载可用标签
        self.update_ui()
        
    def on_hash_progress(self, current: int, total: int, filename: str):
        """处理哈希计算进度"""
        message = f"正在计算哈希值: {filename} ({current}/{total})"
        self.main_window.show_loading_progress(True, current, total, message)
        
    def on_next_image(self):
        """处理下一张图片"""
        # 检查是否需要保存当前标注
        if not self._handle_save_before_switch():
            return  # 用户取消操作

        # 移动到下一张
        if self.data_manager.move_to_next():
            self.update_ui()
        else:
            # 已经是最后一张
            self.main_window.show_message(tr("tip"), tr("annotation_complete"), "info")
            
    def on_prev_image(self):
        """处理上一张图片"""
        # 检查是否需要保存当前标注
        if not self._handle_save_before_switch():
            return  # 用户取消操作

        # 移动到上一张
        if self.data_manager.move_to_prev():
            self.update_ui()
            
    def on_annotation_changed(self, text: str):
        """处理标注内容变化"""
        self.current_annotation = text
        # 启动自动保存定时器（延迟保存，避免频繁IO）
        self.auto_save_timer.start(1000)  # 1秒后保存
        
    def auto_save_annotation(self):
        """自动保存标注"""
        self.save_current_annotation()
        
    def save_current_annotation(self):
        """保存当前标注"""
        if self.current_annotation is not None:
            self.data_manager.save_annotation(self.current_annotation)

    def _handle_save_before_switch(self):
        """处理切换图片前的保存逻辑

        Returns:
            bool: True表示可以继续切换，False表示用户取消操作
        """
        # 检查当前标注内容是否为空
        current_annotation = self.current_annotation.strip() if self.current_annotation else ""

        if not current_annotation:
            # 没有标注内容，直接切换，不保存
            return True

        if self.auto_save_enabled:
            # 自动保存模式：直接保存
            self.save_current_annotation()
            return True
        else:
            # 手动保存模式：显示确认对话框
            current_image = self.data_manager.get_current_image_info()
            if current_image:
                reply = self.main_window.show_save_confirmation(current_image.filename)

                if reply == QMessageBox.StandardButton.Yes:
                    self.save_current_annotation()
                    return True
                elif reply == QMessageBox.StandardButton.No:
                    return True
                else:  # Cancel
                    return False
            return True
            
    def update_ui(self):
        """更新UI显示"""
        current_image = self.data_manager.get_current_image_info()
        
        if current_image is None:
            # 没有图片
            self.main_window.update_info("", "", 0, 0)
            self.main_window.update_annotation("")
            self.main_window.update_navigation_buttons(False, False)
            return
            
        # 更新图片显示
        if current_image.image_data:
            self.main_window.update_image(current_image.image_data)
        else:
            # 尝试加载图片
            current_image.load_image()
            if current_image.image_data:
                self.main_window.update_image(current_image.image_data)
                
        # 更新文件信息
        current_index, total_count = self.data_manager.get_progress_info()
        hash_value = current_image.hash if current_image.hash else "计算中..."
        self.main_window.update_info(
            current_image.filename,
            hash_value,
            current_index,
            total_count
        )
        
        # 更新标注内容
        self.current_annotation = current_image.annotation

        # 在更新标注前，确保可用标签列表是最新的
        self.load_available_labels()

        self.main_window.update_annotation(current_image.annotation)

        # 如果没有标注内容，重置标签选择状态
        if not current_image.annotation.strip():
            self.main_window.reset_label_selection()
        
        # 更新导航按钮状态
        has_prev = self.data_manager.has_prev()
        has_next = self.data_manager.has_next()
        self.main_window.update_navigation_buttons(has_prev, has_next)
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 检查是否需要保存当前标注
        if not self._handle_save_before_close():
            event.ignore()  # 用户取消关闭
            return

        # 清理资源
        self.data_manager.cleanup()

        event.accept()

    def _handle_save_before_close(self):
        """处理关闭程序前的保存逻辑

        Returns:
            bool: True表示可以关闭程序，False表示用户取消关闭
        """
        # 检查当前标注内容是否为空
        current_annotation = self.current_annotation.strip() if self.current_annotation else ""

        if not current_annotation:
            # 没有标注内容，直接关闭，不保存
            return True

        if self.auto_save_enabled:
            # 自动保存模式：直接保存
            self.save_current_annotation()
            return True
        else:
            # 手动保存模式：显示确认对话框
            current_image = self.data_manager.get_current_image_info()
            if current_image:
                reply = self.main_window.show_save_confirmation(current_image.filename)

                if reply == QMessageBox.StandardButton.Yes:
                    self.save_current_annotation()
                    return True
                elif reply == QMessageBox.StandardButton.No:
                    return True
                else:  # Cancel
                    return False
            return True

    def on_mode_changed(self, mode):
        """处理标注模式变化"""
        # 可以在这里添加模式变化的处理逻辑
        print(f"标注模式已切换为: {mode}")

    def on_labels_changed(self, labels):
        """处理标签列表变化"""
        self.available_labels = labels[:]
        # 保存标签到数据管理器
        self.data_manager.set_available_labels(labels)

    def load_available_labels(self):
        """加载可用标签列表"""
        labels = self.data_manager.get_available_labels()
        self.available_labels = labels
        self.main_window.set_available_labels(labels)
