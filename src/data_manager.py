#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Label - 快捷图片标注工具 - 数据管理模块
"""

import os
import json
import hashlib
import threading
import base64
from typing import List, Dict, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QMutex
from PyQt6.QtGui import QPixmap
from PIL import Image


class ImageInfo:
    """图片信息类"""

    def __init__(self, file_path: str):
        self.path = file_path
        self.filename = os.path.basename(file_path)
        self.hash = None  # SHA256哈希值
        self.annotation = ""  # 标注内容
        self.image_data = None  # QPixmap对象
        self.is_loaded = False  # 是否已加载到内存
        self.base64_data = None  # base64编码数据
        self.base64_calculated = False  # 是否已计算base64
        
    def calculate_hash(self):
        """计算文件的SHA256哈希值"""
        if self.hash is None:
            try:
                with open(self.path, 'rb') as f:
                    file_hash = hashlib.sha256()
                    while chunk := f.read(8192):
                        file_hash.update(chunk)
                    self.hash = file_hash.hexdigest()
            except Exception as e:
                print(f"计算哈希值失败: {self.path}, 错误: {e}")
                self.hash = ""
        return self.hash
        
    def load_image(self):
        """加载图片到内存"""
        if not self.is_loaded:
            try:
                self.image_data = QPixmap(self.path)
                self.is_loaded = True
            except Exception as e:
                print(f"加载图片失败: {self.path}, 错误: {e}")
                self.image_data = None
        return self.image_data
        
    def unload_image(self):
        """从内存中卸载图片"""
        self.image_data = None
        self.is_loaded = False
        
    def get_file_size(self):
        """获取文件大小（字节）"""
        try:
            return os.path.getsize(self.path)
        except:
            return 0

    def calculate_base64(self, enable_base64=True, max_file_size_mb=10):
        """计算文件的base64编码

        Args:
            enable_base64: 是否启用base64编码
            max_file_size_mb: 最大文件大小限制（MB），超过此大小的文件将跳过编码
        """
        if not enable_base64:
            self.base64_data = None
            self.base64_calculated = True
            return None

        if not self.base64_calculated:
            try:
                # 检查文件大小，避免对过大的文件进行base64编码
                file_size = self.get_file_size()
                max_size_bytes = max_file_size_mb * 1024 * 1024

                if file_size > max_size_bytes:
                    print(f"文件过大，跳过base64编码: {self.filename} ({file_size / 1024 / 1024:.1f}MB)")
                    self.base64_data = None
                else:
                    # 分块读取文件以减少内存占用
                    with open(self.path, 'rb') as f:
                        file_data = f.read()
                        self.base64_data = base64.b64encode(file_data).decode('utf-8')

                self.base64_calculated = True
            except Exception as e:
                print(f"计算base64编码失败: {self.path}, 错误: {e}")
                self.base64_data = None
                self.base64_calculated = True
        return self.base64_data


class HashCalculationThread(QThread):
    """哈希计算线程"""
    
    progress_updated = pyqtSignal(int, int, str)  # current, total, filename
    hash_calculated = pyqtSignal(int, str)  # index, hash_value
    finished = pyqtSignal()
    
    def __init__(self, images: List[ImageInfo], start_index: int = 0, enable_base64: bool = True, max_file_size_mb: int = 10):
        super().__init__()
        self.images = images
        self.start_index = start_index
        self.should_stop = False
        self.enable_base64 = enable_base64
        self.max_file_size_mb = max_file_size_mb
        
    def run(self):
        """运行哈希计算"""
        total = len(self.images)
        for i in range(self.start_index, total):
            if self.should_stop:
                break
                
            image_info = self.images[i]
            if image_info.hash is None:
                hash_value = image_info.calculate_hash()
                self.hash_calculated.emit(i, hash_value)

            # 计算base64编码（如果启用）
            if self.enable_base64:
                image_info.calculate_base64(self.enable_base64, self.max_file_size_mb)

            self.progress_updated.emit(i + 1, total, image_info.filename)
            
        self.finished.emit()
        
    def stop(self):
        """停止计算"""
        self.should_stop = True


class DataManager(QObject):
    """数据管理器"""
    
    # 信号定义
    loading_progress = pyqtSignal(int, int, str)  # current, total, message
    loading_finished = pyqtSignal()
    hash_calculation_progress = pyqtSignal(int, int, str)
    
    # 支持的图片格式
    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    
    # 内存管理配置
    MAX_MEMORY_MB = 1024  # 最大内存使用量（MB）
    DEFAULT_BATCH_SIZE = 100  # 默认批次大小
    MIN_BATCH_SIZE = 20  # 最小批次大小
    
    def __init__(self):
        super().__init__()
        self.images: List[ImageInfo] = []
        self.current_index = 0
        self.work_directory = ""
        self.labels_file = ""
        self.labels_data: Dict[str, str] = {}
        self.mutex = QMutex()
        self.hash_thread = None
        self.loaded_images_count = 0
        self.batch_size = self.DEFAULT_BATCH_SIZE
        self.custom_save_path = ""  # 自定义保存路径
        self.enable_base64 = True  # 是否启用base64编码
        self.max_base64_file_size_mb = self._detect_optimal_file_size_limit()  # 动态检测文件大小限制
        
    def set_work_directory(self, directory: str):
        """设置工作目录"""
        self.work_directory = directory
        self.labels_file = os.path.join(directory, "labels.json")
        self.load_labels()
        self.scan_images()

    def set_custom_save_path(self, path: str):
        """设置自定义保存路径"""
        self.custom_save_path = path

    def set_enable_base64(self, enable: bool):
        """设置是否启用base64编码"""
        self.enable_base64 = enable

    def _detect_optimal_file_size_limit(self):
        """检测设备的最优文件大小限制"""
        try:
            import psutil
            # 获取系统内存信息
            memory = psutil.virtual_memory()
            total_memory_gb = memory.total / (1024 ** 3)

            # 根据内存大小动态调整文件大小限制
            if total_memory_gb >= 16:
                return 20  # 16GB+内存：20MB限制
            elif total_memory_gb >= 8:
                return 15  # 8-16GB内存：15MB限制
            elif total_memory_gb >= 4:
                return 10  # 4-8GB内存：10MB限制
            else:
                return 5   # 4GB以下内存：5MB限制
        except ImportError:
            # 如果没有psutil库，使用默认值
            return 10
        except Exception:
            # 检测失败时使用保守值
            return 5
        
    def scan_images(self):
        """扫描目录中的图片文件"""
        self.images.clear()
        self.current_index = 0
        
        if not os.path.exists(self.work_directory):
            return
            
        # 扫描所有支持的图片文件
        image_files = []
        for root, dirs, files in os.walk(self.work_directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in self.SUPPORTED_FORMATS):
                    file_path = os.path.join(root, file)
                    image_files.append(file_path)
                    
        # 按文件名排序
        image_files.sort()
        
        # 创建ImageInfo对象
        for file_path in image_files:
            image_info = ImageInfo(file_path)
            self.images.append(image_info)
            
        print(f"扫描到 {len(self.images)} 张图片")
        
        # 根据图片数量调整加载策略
        self.adjust_loading_strategy()
        
        # 开始加载和哈希计算
        self.start_loading()
        
    def adjust_loading_strategy(self):
        """根据图片数量调整加载策略"""
        total_images = len(self.images)
        
        if total_images < 100:
            # 少于100张，全部加载
            self.batch_size = total_images
        else:
            # 估算内存使用量
            if total_images > 0:
                # 检查前几张图片的大小来估算
                sample_size = min(5, total_images)
                total_size = 0
                for i in range(sample_size):
                    total_size += self.images[i].get_file_size()
                    
                avg_size = total_size / sample_size
                estimated_memory_mb = (avg_size * self.DEFAULT_BATCH_SIZE) / (1024 * 1024)
                
                if estimated_memory_mb > self.MAX_MEMORY_MB:
                    # 调整批次大小
                    self.batch_size = max(
                        self.MIN_BATCH_SIZE,
                        int(self.MAX_MEMORY_MB * 1024 * 1024 / avg_size)
                    )
                else:
                    self.batch_size = self.DEFAULT_BATCH_SIZE
                    
        print(f"批次大小设置为: {self.batch_size}")
        
    def start_loading(self):
        """开始加载图片和计算哈希"""
        if not self.images:
            self.loading_finished.emit()
            return

        # 加载第一批图片
        self.load_batch(0, min(self.batch_size, len(self.images)))

        # 开始哈希计算线程
        self.start_hash_calculation()

        # 注意：不在这里调用find_first_unlabeled，而是在哈希计算完成后调用
        
    def load_batch(self, start_index: int, end_index: int):
        """加载指定范围的图片"""
        for i in range(start_index, min(end_index, len(self.images))):
            image_info = self.images[i]
            if not image_info.is_loaded:
                image_info.load_image()
                self.loaded_images_count += 1
                
            self.loading_progress.emit(i + 1, len(self.images), f"加载图片: {image_info.filename}")
            
    def start_hash_calculation(self):
        """开始哈希计算线程"""
        if self.hash_thread and self.hash_thread.isRunning():
            self.hash_thread.stop()
            self.hash_thread.wait()
            
        self.hash_thread = HashCalculationThread(self.images, 0, self.enable_base64, self.max_base64_file_size_mb)
        self.hash_thread.progress_updated.connect(self.hash_calculation_progress.emit)
        self.hash_thread.hash_calculated.connect(self.on_hash_calculated)
        self.hash_thread.finished.connect(self.on_hash_calculation_finished)
        self.hash_thread.start()
        
    def on_hash_calculated(self, index: int, hash_value: str):
        """哈希计算完成回调"""
        if 0 <= index < len(self.images):
            image_info = self.images[index]
            image_info.hash = hash_value
            
            # 从labels_data中加载对应的标注
            if hash_value in self.labels_data:
                image_info.annotation = self.labels_data[hash_value]
                
    def on_hash_calculation_finished(self):
        """哈希计算全部完成"""
        print("所有图片哈希计算完成")
        # 现在定位到第一张未标注的图片
        self.find_first_unlabeled()
        self.loading_finished.emit()
        
    def find_first_unlabeled(self):
        """找到第一张未标注的图片"""
        for i, image_info in enumerate(self.images):
            # 检查是否有标注内容（从内存中的annotation字段检查）
            if not image_info.annotation.strip():
                self.current_index = i
                print(f"定位到第一张未标注的图片: {i+1}/{len(self.images)} - {image_info.filename}")
                return
        # 如果所有图片都已标注，从第一张开始
        self.current_index = 0
        print("所有图片都已标注，从第一张开始")
        
    def get_current_image_info(self) -> Optional[ImageInfo]:
        """获取当前图片信息"""
        if 0 <= self.current_index < len(self.images):
            return self.images[self.current_index]
        return None
        
    def move_to_next(self) -> bool:
        """移动到下一张图片"""
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.ensure_image_loaded(self.current_index)
            return True
        return False
        
    def move_to_prev(self) -> bool:
        """移动到上一张图片"""
        if self.current_index > 0:
            self.current_index -= 1
            self.ensure_image_loaded(self.current_index)
            return True
        return False
        
    def ensure_image_loaded(self, index: int):
        """确保指定索引的图片已加载"""
        if 0 <= index < len(self.images):
            image_info = self.images[index]
            if not image_info.is_loaded:
                image_info.load_image()
                
    def save_annotation(self, annotation: str):
        """保存当前图片的标注"""
        current_image = self.get_current_image_info()
        if current_image and current_image.hash:
            current_image.annotation = annotation
            self.labels_data[current_image.hash] = annotation
            # 保存单个JSON文件
            self.save_single_annotation(current_image)

    def save_single_annotation(self, image_info: 'ImageInfo'):
        """保存单个图片的标注文件"""
        try:
            # 确定保存路径
            if self.custom_save_path and os.path.exists(self.custom_save_path):
                save_dir = self.custom_save_path
            else:
                save_dir = os.path.dirname(image_info.path)

            # 生成JSON文件名（与图片文件名相同，但扩展名为.json）
            base_name = os.path.splitext(image_info.filename)[0]
            json_filename = f"{base_name}.json"
            json_path = os.path.join(save_dir, json_filename)

            # 计算base64编码（如果启用）
            base64_data = None
            if self.enable_base64:
                base64_data = image_info.calculate_base64(self.enable_base64, self.max_base64_file_size_mb)

            # 构建标注数据
            annotation_data = {
                "filename": image_info.filename,
                "hash": image_info.hash,
                "annotation": image_info.annotation,
                "file_size": image_info.get_file_size(),
                "base64_data": base64_data
            }

            # 保存JSON文件
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(annotation_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"保存标注文件失败: {image_info.filename}, 错误: {e}")
            
    def load_labels(self):
        """从文件加载标签数据"""
        self.labels_data.clear()

        # 首先尝试加载旧格式的labels.json文件（向后兼容）
        if os.path.exists(self.labels_file):
            try:
                with open(self.labels_file, 'r', encoding='utf-8') as f:
                    self.labels_data = json.load(f)
                print(f"从旧格式加载了 {len(self.labels_data)} 个标签")
            except Exception as e:
                print(f"加载旧格式标签文件失败: {e}")

        # 然后尝试加载新格式的单个JSON文件
        self.load_individual_annotations()

    def load_individual_annotations(self):
        """加载单个标注文件"""
        if not self.work_directory:
            return

        loaded_count = 0

        # 扫描工作目录及其子目录中的JSON文件
        for root, dirs, files in os.walk(self.work_directory):
            for file in files:
                if file.lower().endswith('.json') and file != 'labels.json':
                    json_path = os.path.join(root, file)
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            annotation_data = json.load(f)

                        # 检查是否是标注文件格式
                        if 'hash' in annotation_data and 'annotation' in annotation_data:
                            hash_value = annotation_data['hash']
                            annotation = annotation_data['annotation']

                            # 更新labels_data
                            self.labels_data[hash_value] = annotation
                            loaded_count += 1

                    except Exception as e:
                        # 忽略无法解析的JSON文件
                        continue

        if loaded_count > 0:
            print(f"从新格式加载了 {loaded_count} 个标签")
                
    def save_labels(self):
        """保存标签数据到文件"""
        try:
            with open(self.labels_file, 'w', encoding='utf-8') as f:
                json.dump(self.labels_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存标签文件失败: {e}")
            
    def get_progress_info(self) -> tuple:
        """获取进度信息"""
        total = len(self.images)
        current = self.current_index
        return current, total
        
    def has_next(self) -> bool:
        """是否有下一张图片"""
        return self.current_index < len(self.images) - 1
        
    def has_prev(self) -> bool:
        """是否有上一张图片"""
        return self.current_index > 0
        
    def cleanup(self):
        """清理资源"""
        if self.hash_thread and self.hash_thread.isRunning():
            self.hash_thread.stop()
            self.hash_thread.wait()
