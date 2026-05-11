#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LabelFlow - 快捷图片标注工具 - 应用控制器
"""

from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtWidgets import QMessageBox
from ui_mainwindow import MainWindow
from data_manager import DataManager
from language_manager import tr
from config_manager import config_manager
from logger_manager import logger_manager
from command_manager import CommandManager, AnnotationStateCommand, ImageSwitchCommand


class AppController(QObject):
    """应用程序控制器"""

    def __init__(self):
        super().__init__()
        self.main_window = MainWindow()
        self.data_manager = DataManager()
        self.command_manager = CommandManager()  # 命令管理器（撤销/重做）
        self.auto_save_timer = QTimer()
        self.current_annotation = ""
        ui_config = config_manager.get_ui_config()
        self.auto_save_enabled = ui_config.get('auto_save_enabled', True)
        self.main_window.auto_save_enabled = self.auto_save_enabled
        if hasattr(self.main_window, 'auto_save_action'):
            self.main_window.auto_save_action.setChecked(self.auto_save_enabled)
        self.available_labels = []  # 全局可用标签列表
        self._last_mode = 'description'  # 记录上一次的模式

        # 撤销/重做功能：跟踪编辑状态
        self._editing_image_index = None  # 当前正在编辑的图片索引
        self._editing_start_annotation = ""  # 编辑开始时的完整标注状态
        self._suppress_annotation_tracking = False

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
        self.main_window.jump_to_image.connect(self.on_jump_to_image)
        self.main_window.rename_images.connect(self.on_rename_images)
        self.main_window.compatibility_mode_changed.connect(self.on_compatibility_mode_changed)

        # 新增信号连接
        self.main_window.undo.connect(self.undo)
        self.main_window.redo.connect(self.redo)
        self.main_window.quick_save.connect(self.on_quick_save)
        self.main_window.clear_annotation.connect(self.on_clear_annotation)
        self.main_window.copy_from_previous.connect(self.on_copy_from_previous)

        # 数据管理器信号连接
        self.data_manager.loading_progress.connect(self.on_loading_progress)
        self.data_manager.loading_finished.connect(self.on_loading_finished)
        self.data_manager.hash_calculation_progress.connect(self.on_hash_progress)
        self.data_manager.current_image_annotation_updated.connect(self.on_current_image_annotation_updated)

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
        logger_manager.log_operation("选择工作目录", {"directory": directory})
        self.main_window.show_loading_progress(True, 0, 100, "正在扫描目录...")
        self.data_manager.set_work_directory(directory)

    def on_save_path_selected(self, path: str):
        """处理保存路径选择"""
        self.data_manager.set_custom_save_path(path)

    def on_auto_save_changed(self, enabled: bool):
        """处理自动保存设置变化"""
        self.auto_save_enabled = enabled
        if not enabled:
            self.auto_save_timer.stop()

        config_manager.set('ui.auto_save_enabled', enabled)
        config_manager.save_config()
        logger_manager.log_config_change("ui.auto_save_enabled", not enabled, enabled)
        
    def on_loading_progress(self, current: int, total: int, message: str):
        """处理加载进度"""
        self.main_window.show_loading_progress(True, current, total, message)
        
    def on_loading_finished(self):
        """处理加载完成"""
        self.main_window.show_loading_progress(False)

        # 记录目录加载完成
        image_count = len(self.data_manager.images)
        logger_manager.log_directory_opened(self.data_manager.work_directory, image_count)

        # 定位到第一张未标注的图片（暂时取消自动恢复标注模式功能）
        self.data_manager.find_first_unlabeled()
        print("已定位到第一张未标注的图片")

        self.load_available_labels()  # 加载可用标签
        self.update_ui()
        
    def on_hash_progress(self, current: int, total: int, filename: str):
        """处理哈希计算进度"""
        message = f"正在计算哈希值: {filename} ({current}/{total})"
        self.main_window.show_loading_progress(True, current, total, message)

    def on_current_image_annotation_updated(self):
        """处理当前图片标注数据更新"""
        # 当前图片的标注数据已更新，刷新界面显示
        current_image = self.data_manager.get_current_image_info()
        if current_image and current_image.annotation and not self._has_pending_annotation_change():
            print(f"当前图片标注数据已更新: {current_image.filename}")
            self.current_annotation = current_image.annotation
            self.main_window.update_annotation(current_image.annotation)
            self._reset_edit_baseline()
        
    def on_next_image(self):
        """处理下一张图片"""
        # 检查是否需要保存当前标注
        if not self._handle_save_before_switch():
            return  # 用户取消操作

        # 获取当前和目标索引
        old_index = self.data_manager.current_index
        if not self.data_manager.has_next():
            # 已经是最后一张
            self.main_window.show_message(tr("tip"), tr("annotation_complete"), "info")
            return

        new_index = old_index + 1

        # 创建并执行图片切换命令
        command = ImageSwitchCommand(self, old_index, new_index)
        self.command_manager.execute(command)
        self._refresh_undo_redo_state()
            
    def on_prev_image(self):
        """处理上一张图片"""
        # 检查是否需要保存当前标注
        if not self._handle_save_before_switch():
            return  # 用户取消操作

        # 获取当前和目标索引
        old_index = self.data_manager.current_index
        if not self.data_manager.has_prev():
            return

        new_index = old_index - 1

        # 创建并执行图片切换命令
        command = ImageSwitchCommand(self, old_index, new_index)
        self.command_manager.execute(command)
        self._refresh_undo_redo_state()
            
    def on_annotation_changed(self, text: str):
        """处理标注内容变化"""
        if self._suppress_annotation_tracking:
            return

        self.current_annotation = text
        current_image = self.data_manager.get_current_image_info()
        if current_image:
            current_image.annotation = text

        if self.auto_save_enabled:
            # 启动自动保存定时器（延迟保存，避免频繁IO）
            self.auto_save_timer.start(1000)  # 1秒后保存
        else:
            self.auto_save_timer.stop()
        
    def auto_save_annotation(self):
        """自动保存标注"""
        self.save_current_annotation()
        
    def save_current_annotation(self):
        """保存当前标注"""
        if self.current_annotation is not None:
            current_image = self.data_manager.get_current_image_info()
            if current_image:
                # 记录保存操作
                logger_manager.log_annotation_save(
                    current_image.filename,
                    self.main_window.current_mode,
                    len(self.current_annotation) if self.current_annotation else 0,
                    len(self.main_window.selected_labels)
                )
            saved = self.data_manager.save_annotation(self.current_annotation)
            if saved and current_image:
                current_image.saved_annotation = self.current_annotation or ""
            return saved
        return False

    def _handle_save_before_switch(self):
        """处理切换图片前的保存逻辑

        Returns:
            bool: True表示可以继续切换，False表示用户取消操作
        """
        if self.auto_save_enabled:
            # 自动保存模式：提交撤销历史；如仍未持久化则保存
            self._commit_pending_annotation_change()
            if self._has_unsaved_annotation_change():
                self.save_current_annotation()
            return True

        if not self._has_unsaved_annotation_change():
            return True

        # 手动保存模式：显示确认对话框
        current_image = self.data_manager.get_current_image_info()
        if current_image:
            reply = self.main_window.show_save_confirmation(current_image.filename)

            if reply == QMessageBox.StandardButton.Yes:
                self._commit_pending_annotation_change()
                self.save_current_annotation()
                return True
            elif reply == QMessageBox.StandardButton.No:
                self._discard_current_annotation_change()
                return True
            else:  # Cancel
                self._refresh_undo_redo_state()
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
        if not hasattr(current_image, 'saved_annotation'):
            current_image.saved_annotation = current_image.annotation or ""

        # 在更新标注前，确保可用标签列表是最新的
        self.load_available_labels()

        # 更新标注内容到界面
        if current_image.annotation and current_image.annotation.strip():
            print(f"更新标注内容到界面: {current_image.filename} -> {current_image.annotation[:100]}...")
            self.main_window.update_annotation(current_image.annotation)
        else:
            # 如果没有标注内容，清空界面并重置标签选择状态
            print(f"清空标注内容: {current_image.filename}")
            self.main_window.update_annotation("")
            self.main_window.reset_label_selection()
        
        # 更新导航按钮状态
        has_prev = self.data_manager.has_prev()
        has_next = self.data_manager.has_next()
        self.main_window.update_navigation_buttons(has_prev, has_next)

        # 更新文件列表显示
        file_list = [img.filename for img in self.data_manager.images]
        current_index = self.data_manager.current_index
        self.main_window.update_file_list(file_list, current_index)

        self._reset_edit_baseline()

    def _record_text_edit_if_changed(self):
        """兼容旧调用：提交完整标注状态变化。"""
        self._commit_pending_annotation_change()

    def _record_label_change_if_changed(self):
        """兼容旧调用：标签状态已经包含在完整标注状态里。"""
        return

    def _reset_edit_baseline(self):
        """将当前UI状态设为下一次撤销记录的起点。"""
        self._editing_image_index = self.data_manager.current_index
        self._editing_start_annotation = self.current_annotation or ""
        self._refresh_undo_redo_state()

    def _has_pending_annotation_change(self) -> bool:
        """检查当前图片是否有尚未进入撤销历史的编辑。"""
        if self._editing_image_index is None:
            return False
        if self._editing_image_index != self.data_manager.current_index:
            return False
        return (self.current_annotation or "") != (self._editing_start_annotation or "")

    def _has_unsaved_annotation_change(self) -> bool:
        """检查当前图片是否有尚未写入JSON文件的编辑。"""
        current_image = self.data_manager.get_current_image_info()
        if not current_image:
            return False

        saved_annotation = getattr(current_image, 'saved_annotation', current_image.annotation or "")
        return (self.current_annotation or "") != (saved_annotation or "")

    def _commit_pending_annotation_change(self):
        """把当前未入栈编辑记录为完整标注状态命令。"""
        if not self._has_pending_annotation_change():
            self._refresh_undo_redo_state()
            return

        command = AnnotationStateCommand(
            self,
            self._editing_image_index,
            self._editing_start_annotation,
            self.current_annotation,
        )
        self.command_manager.add_to_history(command)
        self._editing_start_annotation = self.current_annotation or ""
        self._refresh_undo_redo_state()

    def _discard_current_annotation_change(self):
        """丢弃当前未保存编辑，并恢复到最近一次已保存标注。"""
        current_image = self.data_manager.get_current_image_info()
        if not current_image:
            self._refresh_undo_redo_state()
            return

        saved_annotation = getattr(current_image, 'saved_annotation', current_image.annotation or "") or ""
        current_image.annotation = saved_annotation
        self.current_annotation = saved_annotation

        self._suppress_annotation_tracking = True
        try:
            self.main_window.update_annotation(saved_annotation)
        finally:
            self._suppress_annotation_tracking = False

        self._editing_image_index = self.data_manager.current_index
        self._editing_start_annotation = saved_annotation
        self._refresh_undo_redo_state()

    def _execute_annotation_change(self, new_annotation: str, description: str):
        """通过命令管理器应用一次完整标注变更。"""
        current_image = self.data_manager.get_current_image_info()
        if not current_image:
            return False

        old_annotation = self.current_annotation or ""
        new_annotation = new_annotation or ""
        if old_annotation == new_annotation:
            self._refresh_undo_redo_state()
            return False

        command = AnnotationStateCommand(
            self,
            self.data_manager.current_index,
            old_annotation,
            new_annotation,
            description,
        )
        self.command_manager.execute(command)
        self._refresh_undo_redo_state()
        return True

    def apply_annotation_state(self, image_index: int, annotation: str, update_baseline: bool = True):
        """将完整标注状态应用到指定图片，并同步UI与持久化状态。"""
        if image_index < 0 or image_index >= len(self.data_manager.images):
            return False

        annotation = annotation or ""
        if self.data_manager.current_index != image_index:
            if not self.data_manager.jump_to_index(image_index):
                return False
            self.update_ui()

        image_info = self.data_manager.images[image_index]
        image_info.annotation = annotation
        self.current_annotation = annotation

        self._suppress_annotation_tracking = True
        try:
            self.main_window.update_annotation(annotation)
        finally:
            self._suppress_annotation_tracking = False

        if self.auto_save_enabled:
            self.save_current_annotation()

        if update_baseline:
            self._editing_image_index = image_index
            self._editing_start_annotation = annotation

        return True

    def _refresh_undo_redo_state(self):
        """刷新撤销/重做菜单状态。"""
        if hasattr(self.main_window, 'update_undo_redo_state'):
            self.main_window.update_undo_redo_state(
                self.command_manager.can_undo() or self._has_pending_annotation_change(),
                self.command_manager.can_redo()
            )

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
        if self.auto_save_enabled:
            # 自动保存模式：提交撤销历史；如仍未持久化则保存
            self._commit_pending_annotation_change()
            if self._has_unsaved_annotation_change():
                self.save_current_annotation()
            return True

        if not self._has_unsaved_annotation_change():
            return True

        # 手动保存模式：显示确认对话框
        current_image = self.data_manager.get_current_image_info()
        if current_image:
            reply = self.main_window.show_save_confirmation(current_image.filename)

            if reply == QMessageBox.StandardButton.Yes:
                self._commit_pending_annotation_change()
                self.save_current_annotation()
                return True
            elif reply == QMessageBox.StandardButton.No:
                self._discard_current_annotation_change()
                return True
            else:  # Cancel
                self._refresh_undo_redo_state()
                return False
        return True

    def on_mode_changed(self, mode):
        """处理标注模式变化"""
        old_mode = getattr(self, '_last_mode', 'description')
        self._last_mode = mode
        logger_manager.log_mode_change(old_mode, mode)
        print(f"标注模式已切换为: {mode}")

    def on_labels_changed(self, labels):
        """处理标签列表变化"""
        self.available_labels = labels[:]
        # 保存标签到数据管理器
        self.data_manager.set_available_labels(labels)

    def on_jump_to_image(self, index: int):
        """处理跳转到指定图片"""
        # 检查是否需要保存当前标注
        if not self._handle_save_before_switch():
            return  # 用户取消操作

        # 获取当前索引
        old_index = self.data_manager.current_index

        # 检查目标索引是否有效
        if index < 0 or index >= len(self.data_manager.images):
            self.main_window.show_message("错误", "无法跳转到指定图片", "warning")
            return

        # 如果是跳转到当前图片，不需要创建命令
        if index == old_index:
            return

        # 创建并执行图片切换命令
        command = ImageSwitchCommand(self, old_index, index)
        self.command_manager.execute(command)
        self._refresh_undo_redo_state()

    def on_rename_images(self):
        """处理一键重命名图片"""
        try:
            # 执行重命名操作
            result = self.data_manager.rename_all_images()
            errors = result.get("errors", [])
            warnings = result.get("warnings", [])
            renamed_count = result.get("renamed", 0)

            if errors:
                message = "\n".join(errors[:5])
                if len(errors) > 5:
                    message += f"\n... 还有 {len(errors) - 5} 个错误"
                self.main_window.show_message("重命名失败", message, "error")
            elif renamed_count > 0:
                warning_text = ""
                if warnings:
                    warning_text = "\n\n警告：\n" + "\n".join(warnings[:3])
                self.main_window.show_message(
                    "重命名完成",
                    f"成功重命名了 {renamed_count} 个文件（包括图片和JSON文件）{warning_text}",
                    "info"
                )
                # 重新扫描目录
                self.data_manager.scan_images()
            else:
                warning_text = "\n".join(warnings) if warnings else "没有找到需要重命名的文件"
                self.main_window.show_message(
                    "重命名结果",
                    warning_text,
                    "info"
                )
        except Exception as e:
            self.main_window.show_message(
                "重命名失败",
                f"重命名过程中发生错误：{str(e)}",
                "error"
            )

    def on_compatibility_mode_changed(self, enabled: bool):
        """处理兼容模式变化"""
        self.data_manager.set_compatibility_mode(enabled)
        print(f"兼容模式已{'开启' if enabled else '关闭'}")

    def load_available_labels(self):
        """加载可用标签列表"""
        labels = self.data_manager.get_available_labels()
        self.available_labels = labels
        self.main_window.set_available_labels(labels)

    def undo(self):
        """撤销操作"""
        self._commit_pending_annotation_change()
        if self.command_manager.undo():
            description = self.command_manager.get_redo_description()
            print(f"撤销成功: {description}")
            logger_manager.log_undo_redo("undo", description or "unknown")

            self._refresh_undo_redo_state()
        else:
            print("无法撤销：没有可撤销的操作")
            self.main_window.show_message("提示", "没有可撤销的操作", "info")

    def redo(self):
        """重做操作"""
        self._commit_pending_annotation_change()
        if self.command_manager.redo():
            description = self.command_manager.get_undo_description()
            print(f"重做成功: {description}")
            logger_manager.log_undo_redo("redo", description or "unknown")

            self._refresh_undo_redo_state()
        else:
            print("无法重做：没有可重做的操作")
            self.main_window.show_message("提示", "没有可重做的操作", "info")

    def on_quick_save(self):
        """快速保存当前标注"""
        self._commit_pending_annotation_change()
        logger_manager.log_operation("快速保存", {})
        self.save_current_annotation()
        print("快速保存完成")

    def on_clear_annotation(self):
        """清空当前标注"""
        self._commit_pending_annotation_change()
        logger_manager.log_operation("清空标注", {})
        self._execute_annotation_change("", "清空标注")
        print("标注已清空")

    def on_copy_from_previous(self):
        """复制上一张图片的标注"""
        self._commit_pending_annotation_change()
        if self.data_manager.current_index > 0:
            # 获取上一张图片的标注
            prev_index = self.data_manager.current_index - 1
            prev_image = self.data_manager.images[prev_index]

            if prev_image.annotation:
                self._execute_annotation_change(prev_image.annotation, "复制上一张标注")

                logger_manager.log_operation(
                    "复制标注",
                    {
                        "from": prev_image.filename,
                        "to": self.data_manager.get_current_image_info().filename
                    }
                )
                print(f"已从 {prev_image.filename} 复制标注")
            else:
                print("上一张图片没有标注内容")
        else:
            print("这是第一张图片，无法复制")
