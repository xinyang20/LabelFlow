#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Label - 快捷图片标注工具 - 语言管理模块
"""

import json
from typing import Dict, Optional
from PyQt6.QtCore import QObject, pyqtSignal


class LanguageManager(QObject):
    """语言管理器"""

    # 语言变化信号
    language_changed = pyqtSignal(str)  # 语言代码

    def __init__(self):
        super().__init__()
        self.current_language = "zh_CN"  # 默认中文
        self.translations: Dict[str, Dict[str, str]] = {}
        self.load_built_in_translations()

    def load_built_in_translations(self):
        """加载内置翻译"""
        # 中文翻译（默认）
        self.translations["zh_CN"] = {
            "app_title": "Quick Label - 快捷图片标注工具",
            "file_menu": "文件(&F)",
            "select_directory": "选择工作目录(&O)",
            "set_save_path": "设置标注保存路径(&S)",
            "exit": "退出(&X)",
            "settings_menu": "设置(&S)",
            "auto_save": "自动保存(&A)",
            "language": "语言(&L)",
            "help_menu": "帮助(&H)",
            "about": "关于Quick Label(&A)",
            "filename": "文件名",
            "progress": "进度",
            "annotation_mode": "标注模式",
            "description_mode": "描述模式",
            "label_mode": "标签模式",
            "mixed_mode": "混合模式",
            "annotation_content": "标注内容",
            "new_label": "新标签",
            "available_labels": "可用标签",
            "add": "添加",
            "zoom": "缩放",
            "reset": "重置",
            "prev": "上一张",
            "next": "下一张",
            "ready": "就绪",
            "loading": "正在加载",
            "save_confirmation": "保存确认",
            "save_current_annotation": "是否保存当前图片的标注？",
            "file": "文件",
            "annotation_complete": "全部标注完成！",
            "tip": "提示",
            "select_work_directory": "选择包含图片的工作目录",
            "select_save_directory": "选择标注文件保存目录",
            "save_path_set": "标注文件保存路径已设置为",
            "setting_success": "设置成功",
            "auto_save_enabled": "自动保存已开启",
            "auto_save_disabled": "自动保存已关闭",
            "input_description": "请在此输入图片描述...",
            "input_new_label": "输入新标签...",
            "select_work_directory_to_start": "请选择工作目录以开始标注",
            "cannot_load_image": "无法加载图片",
            "not_selected": "未选择",
            "not_calculated": "未计算"
        }

        # 英文翻译
        self.translations["en_US"] = {
            "app_title": "Quick Label - Image Annotation Tool",
            "file_menu": "&File",
            "select_directory": "&Open Work Directory",
            "set_save_path": "&Set Save Path",
            "exit": "E&xit",
            "settings_menu": "&Settings",
            "auto_save": "&Auto Save",
            "language": "&Language",
            "help_menu": "&Help",
            "about": "&About Quick Label",
            "filename": "Filename",
            "progress": "Progress",
            "annotation_mode": "Annotation Mode",
            "description_mode": "Description Mode",
            "label_mode": "Label Mode",
            "mixed_mode": "Mixed Mode",
            "annotation_content": "Annotation Content",
            "new_label": "New Label",
            "available_labels": "Available Labels",
            "add": "Add",
            "zoom": "Zoom",
            "reset": "Reset",
            "prev": "Previous",
            "next": "Next",
            "ready": "Ready",
            "loading": "Loading",
            "save_confirmation": "Save Confirmation",
            "save_current_annotation": "Save current image annotation?",
            "file": "File",
            "annotation_complete": "All annotations completed!",
            "tip": "Tip",
            "select_work_directory": "Select work directory containing images",
            "select_save_directory": "Select directory to save annotation files",
            "save_path_set": "Annotation save path set to",
            "setting_success": "Setting Successful",
            "auto_save_enabled": "Auto save enabled",
            "auto_save_disabled": "Auto save disabled",
            "input_description": "Please enter image description here...",
            "input_new_label": "Enter new label...",
            "select_work_directory_to_start": "Please select work directory to start annotation",
            "cannot_load_image": "Cannot load image",
            "not_selected": "Not selected",
            "not_calculated": "Not calculated"
        }

        # # Miao翻译
        # self.translations["Miao"] = {
        #     "app_title": "Miao",
        #     "file_menu": "Miao",
        #     "select_directory": "Miao",
        #     "set_save_path": "Miao",
        #     "exit": "Miao",
        #     "settings_menu": "Miao",
        #     "auto_save": "Miao",
        #     "language": "Miao",
        #     "help_menu": "Miao",
        #     "about": "Miao",
        #     "filename": "Miao",
        #     "progress": "Miao",
        #     "annotation_mode": "Miao",
        #     "description_mode": "Miao",
        #     "label_mode": "Miao",
        #     "mixed_mode": "Miao",
        #     "annotation_content": "Miao",
        #     "new_label": "Miao",
        #     "available_labels": "Miao",
        #     "add": "Miao",
        #     "zoom": "Miao",
        #     "reset": "Miao",
        #     "prev": "Miao",
        #     "next": "Miao",
        #     "ready": "Miao",
        #     "loading": "Miao",
        #     "save_confirmation": "Miao",
        #     "save_current_annotation": "Miao",
        #     "file": "Miao",
        #     "annotation_complete": "Miao",
        #     "tip": "Miao",
        #     "select_work_directory": "Miao",
        #     "select_save_directory": "Miao",
        #     "save_path_set": "Miao",
        #     "setting_success": "Miao",
        #     "auto_save_enabled": "Miao",
        #     "auto_save_disabled": "Miao",
        #     "input_description": "Miao",
        #     "input_new_label": "Miao",
        #     "select_work_directory_to_start": "Miao",
        #     "cannot_load_image": "Miao",
        #     "not_selected": "Miao",
        #     "not_calculated": "Miao",
        # }

    def get_available_languages(self) -> Dict[str, str]:
        """获取可用语言列表"""
        return {
            "zh_CN": "中文",
            "en_US": "English"
            # "Miao": "喵喵"
        }

    def set_language(self, language_code: str):
        """设置当前语言"""
        if language_code in self.translations:
            self.current_language = language_code
            self.language_changed.emit(language_code)
            return True
        return False

    def get_current_language(self) -> str:
        """获取当前语言代码"""
        return self.current_language

    def translate(self, key: str, default: Optional[str] = None) -> str:
        """翻译文本"""
        if self.current_language in self.translations:
            translation = self.translations[self.current_language].get(key)
            if translation:
                return translation

        # 如果没有找到翻译，返回默认值或键名
        return default if default is not None else key

    def load_custom_translation(self, language_code: str, file_path: str) -> bool:
        """加载自定义翻译文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                custom_translations = json.load(f)

            if language_code not in self.translations:
                self.translations[language_code] = {}

            # 合并翻译
            self.translations[language_code].update(custom_translations)
            return True
        except Exception as e:
            print(f"加载自定义翻译文件失败: {e}")
            return False

    def export_translation_template(self, file_path: str, language_code: str = "zh_CN") -> bool:
        """导出翻译模板"""
        try:
            if language_code in self.translations:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.translations[language_code], f, 
                             ensure_ascii=False, indent=2)
                return True
        except Exception as e:
            print(f"导出翻译模板失败: {e}")
        return False


# 全局语言管理器实例
language_manager = LanguageManager()


def tr(key: str, default: Optional[str] = None) -> str:
    """全局翻译函数"""
    return language_manager.translate(key, default)
