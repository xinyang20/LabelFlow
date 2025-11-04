#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LabelFlow - 快捷图片标注工具 - 快捷键管理模块
"""

from typing import Dict, Optional, List
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QWidget
from config_manager import config_manager


class ShortcutManager(QObject):
    """快捷键管理器"""

    # 快捷键触发信号
    shortcut_triggered = pyqtSignal(str)  # 功能名称

    def __init__(self, parent_widget: QWidget):
        super().__init__()
        self.parent_widget = parent_widget
        self.shortcuts: Dict[str, QShortcut] = {}
        self.current_shortcuts = {}

        # 加载快捷键配置
        self.load_shortcuts()

    def load_shortcuts(self):
        """从ConfigManager加载快捷键配置"""
        # 从ConfigManager获取快捷键配置
        self.current_shortcuts = config_manager.get_shortcuts_config().copy()
        print(f"已加载快捷键配置，共 {len(self.current_shortcuts)} 个快捷键")

        # 检查快捷键冲突
        conflicts = self.check_conflicts()
        if conflicts:
            print(f"警告: 发现 {len(conflicts)} 个快捷键冲突:")
            for key, functions in conflicts.items():
                print(f"  {key}: {', '.join(functions)}")

        # 应用快捷键
        self.apply_shortcuts()

    def save_shortcuts(self):
        """保存快捷键配置到ConfigManager"""
        try:
            # 更新config中的快捷键配置
            for function_name, key_sequence in self.current_shortcuts.items():
                config_manager.set(f'shortcuts.{function_name}', key_sequence)

            # 保存配置文件
            config_manager.save_config()
            print("已保存快捷键配置到config.json")
        except Exception as e:
            print(f"保存快捷键配置失败: {e}")
    
    def apply_shortcuts(self):
        """应用快捷键到界面"""
        # 清除现有快捷键
        for shortcut in self.shortcuts.values():
            shortcut.setEnabled(False)
            shortcut.deleteLater()
        self.shortcuts.clear()
        
        # 创建新的快捷键
        for function_name, key_sequence in self.current_shortcuts.items():
            if key_sequence:  # 只有非空的快捷键才创建
                try:
                    shortcut = QShortcut(QKeySequence(key_sequence), self.parent_widget)
                    # 使用partial函数避免lambda闭包问题
                    from functools import partial
                    shortcut.activated.connect(
                        partial(self._emit_shortcut_signal, function_name)
                    )
                    self.shortcuts[function_name] = shortcut
                    print(f"创建快捷键成功: {function_name} -> {key_sequence}")
                except Exception as e:
                    print(f"创建快捷键失败 {function_name}: {key_sequence}, 错误: {e}")

    def _emit_shortcut_signal(self, function_name: str):
        """发射快捷键信号的辅助方法"""
        self.shortcut_triggered.emit(function_name)
    
    def get_shortcut(self, function_name: str) -> Optional[str]:
        """获取指定功能的快捷键"""
        return self.current_shortcuts.get(function_name)
    
    def set_shortcut(self, function_name: str, key_sequence: str):
        """设置指定功能的快捷键"""
        self.current_shortcuts[function_name] = key_sequence
        self.apply_shortcuts()
        self.save_shortcuts()
    
    def get_all_shortcuts(self) -> Dict[str, str]:
        """获取所有快捷键配置"""
        return self.current_shortcuts.copy()
    
    def reset_to_default(self):
        """重置为默认快捷键"""
        self.current_shortcuts = config_manager._get_default_config()['shortcuts'].copy()
        self.apply_shortcuts()
        self.save_shortcuts()

    def check_conflicts(self) -> Dict[str, List[str]]:
        """检查快捷键冲突

        Returns:
            冲突字典，键为快捷键，值为使用该快捷键的功能列表
        """
        conflicts = {}
        key_to_functions = {}

        for function_name, key_sequence in self.current_shortcuts.items():
            if not key_sequence:
                continue

            if key_sequence not in key_to_functions:
                key_to_functions[key_sequence] = []
            key_to_functions[key_sequence].append(function_name)

        # 找出冲突的快捷键（多于1个功能使用）
        for key_sequence, functions in key_to_functions.items():
            if len(functions) > 1:
                conflicts[key_sequence] = functions

        return conflicts

    def validate_shortcut(self, key_sequence: str) -> bool:
        """验证快捷键序列是否有效

        Args:
            key_sequence: 快捷键序列字符串

        Returns:
            是否有效
        """
        try:
            seq = QKeySequence(key_sequence)
            return not seq.isEmpty()
        except Exception:
            return False

    def get_conflicts_for_key(self, key_sequence: str) -> List[str]:
        """获取指定快捷键的冲突列表

        Args:
            key_sequence: 快捷键序列

        Returns:
            使用该快捷键的功能列表
        """
        functions = []
        for function_name, seq in self.current_shortcuts.items():
            if seq == key_sequence:
                functions.append(function_name)
        return functions
