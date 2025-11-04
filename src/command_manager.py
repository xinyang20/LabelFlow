#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LabelFlow - 快捷图片标注工具 - 命令管理模块（撤销/重做功能）
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from config_manager import config_manager
from logger_manager import logger_manager


class Command(ABC):
    """命令基类 - 所有可撤销操作的抽象基类"""

    @abstractmethod
    def execute(self):
        """执行命令"""
        pass

    @abstractmethod
    def undo(self):
        """撤销命令"""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """获取命令描述（用于日志和调试）"""
        pass


class TextEditCommand(Command):
    """文字编辑命令"""

    def __init__(self, controller, image_index: int, old_text: str, new_text: str):
        """初始化文字编辑命令

        Args:
            controller: AppController实例
            image_index: 图片索引
            old_text: 旧文本
            new_text: 新文本
        """
        self.controller = controller
        self.image_index = image_index
        self.old_text = old_text
        self.new_text = new_text

    def execute(self):
        """执行：应用新文本"""
        # 跳转到对应图片
        if self.controller.data_manager.current_index != self.image_index:
            self.controller.data_manager.jump_to_index(self.image_index)

        # 更新标注内容
        self.controller.current_annotation = self.new_text
        self.controller.main_window.update_annotation(self.new_text)

    def undo(self):
        """撤销：恢复旧文本"""
        # 跳转到对应图片
        if self.controller.data_manager.current_index != self.image_index:
            self.controller.data_manager.jump_to_index(self.image_index)

        # 恢复标注内容
        self.controller.current_annotation = self.old_text
        self.controller.main_window.update_annotation(self.old_text)

    def get_description(self) -> str:
        """获取命令描述"""
        return f"编辑文本 (图片#{self.image_index})"


class LabelSelectCommand(Command):
    """标签选择命令"""

    def __init__(self, controller, image_index: int, old_labels: list, new_labels: list):
        """初始化标签选择命令

        Args:
            controller: AppController实例
            image_index: 图片索引
            old_labels: 旧标签列表
            new_labels: 新标签列表
        """
        self.controller = controller
        self.image_index = image_index
        self.old_labels = old_labels.copy()
        self.new_labels = new_labels.copy()

    def execute(self):
        """执行：应用新标签"""
        # 跳转到对应图片
        if self.controller.data_manager.current_index != self.image_index:
            self.controller.data_manager.jump_to_index(self.image_index)

        # 更新标签
        self.controller.main_window.selected_labels = self.new_labels.copy()
        self.controller.main_window.update_label_selection(self.new_labels)

    def undo(self):
        """撤销：恢复旧标签"""
        # 跳转到对应图片
        if self.controller.data_manager.current_index != self.image_index:
            self.controller.data_manager.jump_to_index(self.image_index)

        # 恢复标签
        self.controller.main_window.selected_labels = self.old_labels.copy()
        self.controller.main_window.update_label_selection(self.old_labels)

    def get_description(self) -> str:
        """获取命令描述"""
        return f"选择标签 (图片#{self.image_index}): {self.new_labels}"


class ImageSwitchCommand(Command):
    """图片切换命令"""

    def __init__(self, controller, from_index: int, to_index: int):
        """初始化图片切换命令

        Args:
            controller: AppController实例
            from_index: 源图片索引
            to_index: 目标图片索引
        """
        self.controller = controller
        self.from_index = from_index
        self.to_index = to_index

    def execute(self):
        """执行：切换到目标图片"""
        if self.controller.data_manager.jump_to_index(self.to_index):
            self.controller.update_ui()

    def undo(self):
        """撤销：切换回源图片"""
        if self.controller.data_manager.jump_to_index(self.from_index):
            self.controller.update_ui()

    def get_description(self) -> str:
        """获取命令描述"""
        return f"切换图片: #{self.from_index} -> #{self.to_index}"


class CommandManager:
    """命令管理器 - 管理撤销/重做历史"""

    def __init__(self, max_history: Optional[int] = None):
        """初始化命令管理器

        Args:
            max_history: 最大历史记录数，None则从配置读取
        """
        if max_history is None:
            perf_config = config_manager.get_performance_config()
            max_history = perf_config.get('max_undo_steps', 50)

        self.max_history = max_history
        self.undo_stack: List[Command] = []  # 撤销栈
        self.redo_stack: List[Command] = []  # 重做栈

    def execute(self, command: Command):
        """执行命令并添加到历史记录

        Args:
            command: 要执行的命令
        """
        try:
            # 执行命令
            command.execute()

            # 添加到撤销栈
            self.undo_stack.append(command)

            # 清空重做栈（执行新命令后，重做历史失效）
            self.redo_stack.clear()

            # 限制历史记录数量
            if len(self.undo_stack) > self.max_history:
                # 移除最旧的命令
                self.undo_stack.pop(0)

            # 记录日志
            logger_manager.log_operation(
                "执行命令",
                {"command": command.get_description()}
            )

        except Exception as e:
            logger_manager.log_error(e, {
                "operation": "execute_command",
                "command": command.get_description()
            })
            raise

    def add_to_history(self, command: Command):
        """将已执行的命令添加到历史记录（不再执行）

        用于记录已经在UI层完成的操作，如文本编辑、标签选择等。
        这些操作已经生效，只需要记录到历史以支持撤销。

        Args:
            command: 已执行的命令
        """
        try:
            # 添加到撤销栈（不执行）
            self.undo_stack.append(command)

            # 清空重做栈（新操作后，重做历史失效）
            self.redo_stack.clear()

            # 限制历史记录数量
            if len(self.undo_stack) > self.max_history:
                # 移除最旧的命令
                self.undo_stack.pop(0)

            # 记录日志
            logger_manager.log_operation(
                "记录命令",
                {"command": command.get_description()}
            )

        except Exception as e:
            logger_manager.log_error(e, {
                "operation": "add_to_history",
                "command": command.get_description()
            })
            raise

    def undo(self) -> bool:
        """撤销上一个命令

        Returns:
            是否成功撤销
        """
        if not self.can_undo():
            return False

        try:
            # 从撤销栈弹出命令
            command = self.undo_stack.pop()

            # 执行撤销
            command.undo()

            # 添加到重做栈
            self.redo_stack.append(command)

            # 记录日志
            logger_manager.log_undo_redo("undo", command.get_description())

            return True

        except Exception as e:
            logger_manager.log_error(e, {"operation": "undo"})
            # 撤销失败，恢复命令到撤销栈
            if command:
                self.undo_stack.append(command)
            return False

    def redo(self) -> bool:
        """重做上一个被撤销的命令

        Returns:
            是否成功重做
        """
        if not self.can_redo():
            return False

        try:
            # 从重做栈弹出命令
            command = self.redo_stack.pop()

            # 执行重做（即再次执行）
            command.execute()

            # 添加回撤销栈
            self.undo_stack.append(command)

            # 记录日志
            logger_manager.log_undo_redo("redo", command.get_description())

            return True

        except Exception as e:
            logger_manager.log_error(e, {"operation": "redo"})
            # 重做失败，恢复命令到重做栈
            if command:
                self.redo_stack.append(command)
            return False

    def can_undo(self) -> bool:
        """检查是否可以撤销

        Returns:
            是否可以撤销
        """
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """检查是否可以重做

        Returns:
            是否可以重做
        """
        return len(self.redo_stack) > 0

    def clear_history(self):
        """清空所有历史记录"""
        self.undo_stack.clear()
        self.redo_stack.clear()
        logger_manager.log_operation("清空历史记录", {})

    def get_undo_description(self) -> Optional[str]:
        """获取下一个可撤销操作的描述

        Returns:
            操作描述，如果无法撤销则返回None
        """
        if self.can_undo():
            return self.undo_stack[-1].get_description()
        return None

    def get_redo_description(self) -> Optional[str]:
        """获取下一个可重做操作的描述

        Returns:
            操作描述，如果无法重做则返回None
        """
        if self.can_redo():
            return self.redo_stack[-1].get_description()
        return None

    def get_history(self) -> List[str]:
        """获取历史记录列表（用于调试）

        Returns:
            操作描述列表
        """
        return [cmd.get_description() for cmd in self.undo_stack]

    def get_stats(self) -> dict:
        """获取统计信息

        Returns:
            统计信息字典
        """
        return {
            'undo_count': len(self.undo_stack),
            'redo_count': len(self.redo_stack),
            'max_history': self.max_history,
            'can_undo': self.can_undo(),
            'can_redo': self.can_redo()
        }

    def __repr__(self) -> str:
        """字符串表示"""
        stats = self.get_stats()
        return (f"CommandManager(undo={stats['undo_count']}, "
                f"redo={stats['redo_count']}, "
                f"max={stats['max_history']})")
