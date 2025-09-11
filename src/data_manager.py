#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LabelFlow - 快捷图片标注工具 - 数据管理模块
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
    current_image_annotation_updated = pyqtSignal()  # 当前图片标注数据更新
    
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
        self.available_labels = []  # 可用标签列表
        self.labels_cache_file = ""  # 标签缓存文件
        self.mutex = QMutex()
        self.hash_thread = None
        self.loaded_images_count = 0
        self.batch_size = self.DEFAULT_BATCH_SIZE
        self.custom_save_path = ""  # 自定义保存路径
        self.enable_base64 = True  # 是否启用base64编码
        self.max_base64_file_size_mb = self._detect_optimal_file_size_limit()  # 动态检测文件大小限制
        self.compatibility_mode = False  # 兼容模式（支持V0.0.2格式）
        
    def set_work_directory(self, directory: str):
        """设置工作目录"""
        self.work_directory = directory
        self.labels_file = os.path.join(directory, "labels.json")
        self.labels_cache_file = os.path.join(directory, "labels_cache.json")
        self.load_labels()
        self.load_labels_cache()
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

        # 检查并还原缺失的图像
        self.restore_missing_images()

        # 根据图片数量调整加载策略
        self.adjust_loading_strategy()

        # 开始加载和哈希计算
        self.start_loading()

    def restore_missing_images(self):
        """检查并还原缺失的图像文件"""
        if not self.work_directory:
            return

        restored_count = 0
        existing_image_names = set()

        # 收集现有图片文件名（不含扩展名）
        for image_info in self.images:
            base_name = os.path.splitext(image_info.filename)[0]
            existing_image_names.add(base_name.lower())

        # 扫描JSON文件，查找缺失的图像
        for root, dirs, files in os.walk(self.work_directory):
            for file in files:
                if file.lower().endswith('.json') and file not in ['labels.json', 'labels_cache.json']:
                    json_path = os.path.join(root, file)
                    base_name = os.path.splitext(file)[0]

                    # 检查对应的图像文件是否存在
                    if base_name.lower() not in existing_image_names:
                        try:
                            with open(json_path, 'r', encoding='utf-8') as f:
                                annotation_data = json.load(f)

                            # 检查是否有base64数据和文件名信息
                            if ('base64_data' in annotation_data and
                                annotation_data['base64_data'] and
                                'filename' in annotation_data):

                                original_filename = annotation_data['filename']
                                base64_data = annotation_data['base64_data']

                                # 还原图像文件
                                restored_path = self._restore_image_from_base64(
                                    base64_data, original_filename, root
                                )

                                if restored_path:
                                    # 创建ImageInfo对象并添加到列表
                                    image_info = ImageInfo(restored_path)
                                    self.images.append(image_info)
                                    restored_count += 1
                                    print(f"已还原图像: {original_filename}")

                        except Exception as e:
                            print(f"还原图像失败 {file}: {e}")
                            continue

        if restored_count > 0:
            print(f"共还原了 {restored_count} 张图片")
            # 重新排序图片列表
            self.images.sort(key=lambda x: x.filename.lower())

    def _restore_image_from_base64(self, base64_data: str, filename: str, target_dir: str) -> str:
        """从base64数据还原图像文件

        Args:
            base64_data: base64编码的图像数据
            filename: 原始文件名
            target_dir: 目标目录

        Returns:
            str: 还原后的文件路径，失败时返回None
        """
        try:
            # 解码base64数据
            image_data = base64.b64decode(base64_data)

            # 构建目标文件路径
            target_path = os.path.join(target_dir, filename)

            # 如果文件已存在，跳过
            if os.path.exists(target_path):
                return None

            # 写入文件
            with open(target_path, 'wb') as f:
                f.write(image_data)

            return target_path

        except Exception as e:
            print(f"从base64还原图像失败: {e}")
            return None

    def _check_and_update_annotation_file(self, image_info: 'ImageInfo'):
        """检查并更新标注文件中的SHA256和base64数据

        Args:
            image_info: 图像信息对象
        """
        if not image_info.hash:
            return

        # 构建对应的JSON文件路径
        base_name = os.path.splitext(image_info.filename)[0]
        json_filename = f"{base_name}.json"

        # 在工作目录中查找JSON文件
        json_path = None
        for root, dirs, files in os.walk(self.work_directory):
            if json_filename in files:
                json_path = os.path.join(root, json_filename)
                break

        if not json_path or not os.path.exists(json_path):
            return

        try:
            # 读取现有的标注文件
            with open(json_path, 'r', encoding='utf-8') as f:
                annotation_data = json.load(f)

            # 检查SHA256是否一致
            stored_hash = annotation_data.get('hash', '')
            if stored_hash and stored_hash != image_info.hash:
                print(f"检测到SHA256不一致: {image_info.filename}")
                print(f"  存储的: {stored_hash}")
                print(f"  计算的: {image_info.hash}")

                # 更新SHA256
                annotation_data['hash'] = image_info.hash

                # 重新计算base64编码（如果启用）
                if self.enable_base64:
                    new_base64_data = image_info.calculate_base64(
                        self.enable_base64,
                        self.max_base64_file_size_mb
                    )
                    if new_base64_data:
                        annotation_data['base64_data'] = new_base64_data
                        print(f"  已更新base64编码")

                # 更新文件大小
                annotation_data['file_size'] = image_info.get_file_size()

                # 保存更新后的文件
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(annotation_data, f, ensure_ascii=False, indent=2)

                print(f"  已更新标注文件: {json_filename}")

        except Exception as e:
            print(f"检查标注文件失败 {json_filename}: {e}")

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

            # 检查是否存在对应的标注文件，并验证SHA256
            self._check_and_update_annotation_file(image_info)

            # 从labels_data中加载对应的标注（如果还没有通过文件名关联）
            if hash_value in self.labels_data and not image_info.annotation:
                image_info.annotation = self.labels_data[hash_value]
                print(f"通过哈希关联标注数据: {image_info.filename}")

            # 如果这是当前显示的图片，发送信号更新界面
            if index == self.current_index:
                self.current_image_annotation_updated.emit()
                
    def on_hash_calculation_finished(self):
        """哈希计算全部完成"""
        print("所有图片哈希计算完成")
        # 现在定位到第一张未标注的图片（但不在这里调用，让控制器调用）
        self.loading_finished.emit()
        
    def find_first_unlabeled(self):
        """找到第一张未标注的图片并检测标注模式"""
        import json  # 在方法开始就导入json模块

        detected_mode = None
        first_unlabeled_index = None

        for i, image_info in enumerate(self.images):
            # 检查是否有标注内容（考虑JSON格式的标注）
            has_annotation = False
            if image_info.annotation and image_info.annotation.strip():
                try:
                    # 尝试解析JSON格式的标注
                    if image_info.annotation.strip().startswith('{'):
                        parsed = json.loads(image_info.annotation)
                        # 检查是否有实际的标注内容
                        has_describe = parsed.get('describe', '').strip()
                        has_labels = parsed.get('label', []) or parsed.get('labels', [])
                        has_annotation = bool(has_describe or has_labels)
                    else:
                        # 纯文本格式
                        has_annotation = True
                except (json.JSONDecodeError, AttributeError):
                    # 解析失败，按纯文本处理
                    has_annotation = True

            if not has_annotation:
                if first_unlabeled_index is None:
                    first_unlabeled_index = i
                continue

            # 如果还没有检测到模式，分析当前标注内容来检测模式
            if detected_mode is None:
                detected_mode = self._detect_annotation_mode(image_info.annotation)

        # 设置当前索引
        if first_unlabeled_index is not None:
            self.current_index = first_unlabeled_index
            print(f"定位到第一张未标注的图片: {first_unlabeled_index+1}/{len(self.images)} - {self.images[first_unlabeled_index].filename}")
        else:
            # 如果所有图片都已标注，从第一张开始
            self.current_index = 0
            print("所有图片都已标注，从第一张开始")

        # 返回检测到的模式，供控制器使用
        return detected_mode

    def _detect_annotation_mode(self, annotation_text: str):
        """检测标注模式

        Args:
            annotation_text: 标注文本内容

        Returns:
            str: 检测到的模式 ("description", "label", "mixed", None)
        """
        if not annotation_text.strip():
            return None

        try:
            # 尝试解析为JSON格式
            if annotation_text.strip().startswith('{'):
                data = json.loads(annotation_text)

                has_describe = bool(data.get("describe", "").strip())
                has_label = bool(data.get("label", []))

                # 兼容模式：检查V0.0.2格式
                if self.compatibility_mode and not has_describe and not has_label:
                    # 检查V0.0.2的annotation字段
                    old_annotation = data.get("annotation", "").strip()
                    if old_annotation:
                        # V0.0.2格式，默认为描述模式
                        return "description"

                # 根据新字段格式判断模式
                if has_describe and has_label:
                    return "mixed"
                elif has_label:
                    return "label"
                elif has_describe:
                    return "description"

        except json.JSONDecodeError:
            # 不是JSON格式，按纯文本处理，默认为描述模式
            return "description"

        return None
        
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

    def jump_to_index(self, index: int) -> bool:
        """跳转到指定索引的图片"""
        if 0 <= index < len(self.images):
            self.current_index = index
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

            # 构建基础标注数据
            annotation_data = {
                "filename": image_info.filename,
                "hash": image_info.hash,
                "file_size": image_info.get_file_size(),
                "base64_data": base64_data
            }

            # 解析标注内容并直接保存到根级别字段
            try:
                if image_info.annotation.strip().startswith('{'):
                    parsed_annotation = json.loads(image_info.annotation)

                    # 直接将解析后的字段添加到根级别
                    if 'describe' in parsed_annotation:
                        annotation_data['describe'] = parsed_annotation['describe']

                    if 'label' in parsed_annotation:
                        annotation_data['label'] = parsed_annotation['label']
                        # 将标签添加到可用标签列表
                        for label in parsed_annotation['label']:
                            if label not in self.available_labels:
                                self.available_labels.append(label)
                        self.save_labels_cache()

                    # 兼容模式：保持V0.0.2的annotation字段
                    if self.compatibility_mode and 'annotation' in parsed_annotation:
                        annotation_data['annotation'] = parsed_annotation['annotation']

                    # 兼容模式：处理V0.0.2格式的labels字段
                    if self.compatibility_mode and 'labels' in parsed_annotation and 'label' not in parsed_annotation:
                        annotation_data['label'] = parsed_annotation['labels']
                        # 将标签添加到可用标签列表
                        for label in parsed_annotation['labels']:
                            if label not in self.available_labels:
                                self.available_labels.append(label)
                        self.save_labels_cache()

                else:
                    # 纯文本格式，保存为describe字段
                    if image_info.annotation.strip():
                        annotation_data['annotation'] = image_info.annotation
                        annotation_data['describe'] = image_info.annotation

            except json.JSONDecodeError:
                # 解析失败，按纯文本处理
                if image_info.annotation.strip():
                    annotation_data['annotation'] = image_info.annotation
                    annotation_data['describe'] = image_info.annotation

            # 保存JSON文件
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(annotation_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"保存标注文件失败: {image_info.filename}, 错误: {e}")
            
    def load_labels(self):
        """从文件加载标签数据"""
        self.labels_data.clear()

        # 兼容模式：加载V0.0.2格式的labels.json文件
        if self.compatibility_mode and os.path.exists(self.labels_file):
            try:
                with open(self.labels_file, 'r', encoding='utf-8') as f:
                    self.labels_data = json.load(f)
                print(f"兼容模式：从V0.0.2格式加载了 {len(self.labels_data)} 个标签")
            except Exception as e:
                print(f"加载V0.0.2格式标签文件失败: {e}")

        # 加载V0.0.3+格式的单个JSON文件
        self.load_individual_annotations()

    def load_individual_annotations(self):
        """加载单个标注文件"""
        import json  # 在方法开始就导入json模块

        if not self.work_directory:
            return

        loaded_count = 0
        # 创建文件名到标注数据的映射，用于立即关联
        filename_to_annotation = {}

        # 扫描工作目录及其子目录中的JSON文件
        for root, _, files in os.walk(self.work_directory):
            for file in files:
                if file.lower().endswith('.json') and file != 'labels.json':
                    json_path = os.path.join(root, file)
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            annotation_data = json.load(f)

                        # 检查是否是标注文件格式
                        if 'hash' in annotation_data:
                            hash_value = annotation_data['hash']

                            # 重构标注数据为统一格式
                            reconstructed_data = {}

                            # 优先使用新字段格式（V0.0.3+）
                            if 'describe' in annotation_data and annotation_data['describe']:
                                reconstructed_data['describe'] = annotation_data['describe']

                            if 'label' in annotation_data and annotation_data['label']:
                                reconstructed_data['label'] = annotation_data['label']

                            # 兼容模式：处理V0.0.2格式的annotation字段
                            if self.compatibility_mode and 'annotation' in annotation_data:
                                annotation_content = annotation_data['annotation']
                                if annotation_content:
                                    # V0.0.2格式：annotation字段包含实际标注内容
                                    reconstructed_data['annotation'] = annotation_content
                                    # 如果没有describe字段，将annotation内容作为describe
                                    if 'describe' not in reconstructed_data:
                                        reconstructed_data['describe'] = annotation_content

                            # 如果有新字段，将其转换为JSON字符串保存到labels_data
                            if reconstructed_data:
                                annotation_json = json.dumps(reconstructed_data, ensure_ascii=False)
                                self.labels_data[hash_value] = annotation_json
                                loaded_count += 1

                                # 同时建立文件名到标注数据的映射
                                if 'filename' in annotation_data:
                                    filename_to_annotation[annotation_data['filename']] = annotation_json

                                # 立即提取标签到可用标签列表
                                if 'label' in reconstructed_data:
                                    for label in reconstructed_data['label']:
                                        if label not in self.available_labels:
                                            self.available_labels.append(label)

                    except Exception as e:
                        # 忽略无法解析的JSON文件
                        print(f"解析JSON文件失败 {file}: {e}")
                        continue

        # 立即将标注数据关联到对应的ImageInfo对象
        for image_info in self.images:
            if image_info.filename in filename_to_annotation:
                image_info.annotation = filename_to_annotation[image_info.filename]
                print(f"立即关联标注数据: {image_info.filename}")

        if loaded_count > 0:
            print(f"从新格式加载了 {loaded_count} 个标签")
            # 保存更新后的标签缓存
            self.save_labels_cache()
                
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

    def set_available_labels(self, labels: List[str]):
        """设置可用标签列表"""
        self.available_labels = labels[:]
        self.save_labels_cache()

    def get_available_labels(self) -> List[str]:
        """获取可用标签列表"""
        return self.available_labels[:]

    def load_labels_cache(self):
        """加载标签缓存"""
        if os.path.exists(self.labels_cache_file):
            try:
                with open(self.labels_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.available_labels = cache_data.get('available_labels', [])
                print(f"加载了 {len(self.available_labels)} 个缓存标签")
            except Exception as e:
                print(f"加载标签缓存失败: {e}")
                self.available_labels = []

        # 从现有标注中提取标签
        self.extract_labels_from_annotations()

    def save_labels_cache(self):
        """保存标签缓存"""
        try:
            cache_data = {
                'available_labels': self.available_labels
            }
            with open(self.labels_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存标签缓存失败: {e}")

    def extract_labels_from_annotations(self):
        """从现有标注中提取标签"""
        extracted_labels = set()

        # 扫描工作目录中的JSON文件
        if not self.work_directory:
            return

        for root, dirs, files in os.walk(self.work_directory):
            for file in files:
                if file.lower().endswith('.json') and file not in ['labels.json', 'labels_cache.json']:
                    json_path = os.path.join(root, file)
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            annotation_data = json.load(f)

                        # 检查新字段格式（直接在根级别）
                        if 'label' in annotation_data:
                            extracted_labels.update(annotation_data['label'])

                        # 兼容模式：检查V0.0.2格式的labels字段
                        if self.compatibility_mode and 'labels' in annotation_data:
                            extracted_labels.update(annotation_data['labels'])

                        # 兼容模式：检查V0.0.2的annotation字段中的嵌套格式
                        if self.compatibility_mode and 'annotation' in annotation_data:
                            annotation = annotation_data['annotation']
                            if annotation and annotation.strip().startswith('{'):
                                try:
                                    parsed_annotation = json.loads(annotation)
                                    if 'label' in parsed_annotation:
                                        extracted_labels.update(parsed_annotation['label'])
                                    elif 'labels' in parsed_annotation:
                                        # V0.0.2格式兼容
                                        extracted_labels.update(parsed_annotation['labels'])
                                except json.JSONDecodeError:
                                    pass  # 不是JSON格式，跳过

                    except Exception as e:
                        continue  # 忽略无法解析的文件

        # 合并提取的标签到可用标签列表
        for label in extracted_labels:
            if label not in self.available_labels:
                self.available_labels.append(label)

        if extracted_labels:
            print(f"从现有标注中提取了 {len(extracted_labels)} 个标签")
            self.save_labels_cache()

    def rename_all_images(self) -> int:
        """一键重命名所有图片文件

        Returns:
            int: 重命名的文件数量
        """
        if not self.work_directory:
            return 0

        renamed_count = 0

        # 收集所有需要重命名的文件
        image_files = []
        json_files = []

        # 扫描工作目录
        for root, dirs, files in os.walk(self.work_directory):
            for file in files:
                file_path = os.path.join(root, file)

                # 图片文件
                if any(file.lower().endswith(ext) for ext in self.SUPPORTED_FORMATS):
                    image_files.append(file_path)
                # JSON文件（排除系统文件）
                elif (file.lower().endswith('.json') and
                      file not in ['labels.json', 'labels_cache.json', 'keys_setting.json']):
                    json_files.append(file_path)

        # 按文件名排序，确保重命名顺序一致
        image_files.sort()
        json_files.sort()

        # 创建重命名映射
        rename_map = {}  # 原文件名 -> 新文件名

        # 重命名图片文件
        for i, old_path in enumerate(image_files):
            old_filename = os.path.basename(old_path)
            old_name, ext = os.path.splitext(old_filename)

            # 生成新文件名
            new_filename = f"IMG_{i:06d}{ext}"
            new_path = os.path.join(os.path.dirname(old_path), new_filename)

            try:
                # 如果新文件名与旧文件名相同，跳过
                if old_filename == new_filename:
                    continue

                # 如果目标文件已存在，跳过
                if os.path.exists(new_path):
                    print(f"目标文件已存在，跳过: {new_filename}")
                    continue

                # 重命名文件
                os.rename(old_path, new_path)
                rename_map[old_name] = f"IMG_{i:06d}"
                renamed_count += 1
                print(f"重命名图片: {old_filename} -> {new_filename}")

            except Exception as e:
                print(f"重命名图片失败 {old_filename}: {e}")

        # 重命名对应的JSON文件并更新内容
        for json_path in json_files:
            json_filename = os.path.basename(json_path)
            json_name, _ = os.path.splitext(json_filename)

            # 检查是否有对应的图片被重命名
            if json_name in rename_map:
                new_json_name = rename_map[json_name]
                new_json_filename = f"{new_json_name}.json"
                new_json_path = os.path.join(os.path.dirname(json_path), new_json_filename)

                try:
                    # 读取JSON文件内容
                    with open(json_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)

                    # 更新filename字段
                    if 'filename' in json_data:
                        old_img_filename = json_data['filename']
                        old_img_name, old_img_ext = os.path.splitext(old_img_filename)
                        if old_img_name in rename_map:
                            new_img_filename = f"{rename_map[old_img_name]}{old_img_ext}"
                            json_data['filename'] = new_img_filename

                    # 保存到新文件
                    with open(new_json_path, 'w', encoding='utf-8') as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=2)

                    # 删除旧文件
                    os.remove(json_path)
                    renamed_count += 1
                    print(f"重命名JSON: {json_filename} -> {new_json_filename}")

                except Exception as e:
                    print(f"重命名JSON文件失败 {json_filename}: {e}")

        return renamed_count

    def set_compatibility_mode(self, enabled: bool):
        """设置兼容模式

        Args:
            enabled: 是否启用兼容模式（支持V0.0.2格式）
        """
        self.compatibility_mode = enabled
        print(f"兼容模式设置为: {'启用' if enabled else '禁用'}")
