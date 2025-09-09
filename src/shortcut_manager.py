#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Label - 快捷图片标注工具 - 快捷键管理模块
"""

import os
import sys
import json
from typing import Dict, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QWidget


class ShortcutManager(QObject):
    """快捷键管理器"""
    
    # 快捷键触发信号
    shortcut_triggered = pyqtSignal(str)  # 功能名称
    
    def __init__(self, parent_widget: QWidget):
        super().__init__()
        self.parent_widget = parent_widget
        self.shortcuts: Dict[str, QShortcut] = {}
        self.config_file = self._get_config_file_path()
        self.default_shortcuts = self._get_default_shortcuts()
        self.current_shortcuts = {}
        
        # 加载快捷键配置
        self.load_shortcuts()
        
    def _get_config_file_path(self) -> str:
        """获取配置文件路径"""
        # 获取程序目录
        if getattr(sys, 'frozen', False):
            # 打包后的环境
            app_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        return os.path.join(app_dir, "keys_setting.json")
    
    def _get_default_shortcuts(self) -> Dict[str, str]:
        """获取默认快捷键配置"""
        return {
            "Open Directory": "Ctrl+O",
            "Set Save Path": "Ctrl+S", 
            "Exit": "Ctrl+Q",
            "About Page": "Ctrl+A",
            "Previous Image": "Ctrl+Left",
            "Next Image": "Ctrl+Right",
            "Label 0": "Ctrl+0",
            "Label 1": "Ctrl+1",
            "Label 2": "Ctrl+2",
            "Label 3": "Ctrl+3",
            "Label 4": "Ctrl+4",
            "Label 5": "Ctrl+5",
            "Label 6": "Ctrl+6",
            "Label 7": "Ctrl+7",
            "Label 8": "Ctrl+8",
            "Label 9": "Ctrl+9"
        }
    
    def load_shortcuts(self):
        """加载快捷键配置"""
        # 先使用默认配置
        self.current_shortcuts = self.default_shortcuts.copy()
        
        # 尝试从文件加载
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_shortcuts = json.load(f)
                    # 更新配置（保留默认值，只覆盖文件中存在的）
                    self.current_shortcuts.update(file_shortcuts)
                print(f"已加载快捷键配置: {self.config_file}")
            except Exception as e:
                print(f"加载快捷键配置失败: {e}")
        else:
            # 创建默认配置文件
            self.save_shortcuts()
            
        # 应用快捷键
        self.apply_shortcuts()
    
    def save_shortcuts(self):
        """保存快捷键配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_shortcuts, f, ensure_ascii=False, indent=2)
            print(f"已保存快捷键配置: {self.config_file}")
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
        self.current_shortcuts = self.default_shortcuts.copy()
        self.apply_shortcuts()
        self.save_shortcuts()
