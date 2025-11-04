#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LabelFlow - 快捷图片标注工具 - 标注缓存模块
"""

from typing import Dict, Optional, Any
from collections import OrderedDict
from config_manager import config_manager


class AnnotationCache:
    """标注数据缓存 - 使用LRU (Least Recently Used) 淘汰策略"""

    def __init__(self, max_size: Optional[int] = None):
        """初始化缓存

        Args:
            max_size: 最大缓存数量，None则从配置读取
        """
        if max_size is None:
            perf_config = config_manager.get_performance_config()
            max_size = perf_config.get('cache_size', 100)

        self.max_size = max_size
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.hits = 0  # 缓存命中次数
        self.misses = 0  # 缓存未命中次数

    def get(self, key: str) -> Optional[Any]:
        """获取缓存的标注数据

        Args:
            key: 缓存键（通常是图片哈希值）

        Returns:
            缓存的标注数据，如果不存在则返回None
        """
        if key in self.cache:
            # 缓存命中，将该项移到末尾（最近使用）
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        else:
            # 缓存未命中
            self.misses += 1
            return None

    def set(self, key: str, value: Any):
        """设置缓存数据

        Args:
            key: 缓存键（通常是图片哈希值）
            value: 标注数据
        """
        if key in self.cache:
            # 已存在，更新并移到末尾
            self.cache.move_to_end(key)
        else:
            # 新增
            if len(self.cache) >= self.max_size:
                # 缓存已满，删除最久未使用的项（第一个）
                self.evict_lru()

        self.cache[key] = value

    def remove(self, key: str) -> bool:
        """从缓存中移除指定项

        Args:
            key: 缓存键

        Returns:
            是否成功移除
        """
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self):
        """清空所有缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def evict_lru(self):
        """淘汰最久未使用的缓存项"""
        if self.cache:
            # popitem(last=False) 移除第一个（最久未使用）
            evicted_key, evicted_value = self.cache.popitem(last=False)
            return evicted_key, evicted_value
        return None, None

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息

        Returns:
            包含缓存统计数据的字典
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.2f}%",
            'total_requests': total_requests
        }

    def contains(self, key: str) -> bool:
        """检查缓存中是否包含指定键

        Args:
            key: 缓存键

        Returns:
            是否包含
        """
        return key in self.cache

    def size(self) -> int:
        """获取当前缓存大小

        Returns:
            缓存中的项数
        """
        return len(self.cache)

    def is_full(self) -> bool:
        """检查缓存是否已满

        Returns:
            是否已满
        """
        return len(self.cache) >= self.max_size

    def get_keys(self) -> list:
        """获取所有缓存键列表（按最近使用顺序）

        Returns:
            缓存键列表
        """
        return list(self.cache.keys())

    def reset_stats(self):
        """重置统计信息（不清空缓存内容）"""
        self.hits = 0
        self.misses = 0

    def preload_batch(self, keys_and_values: Dict[str, Any]):
        """批量预加载数据到缓存

        Args:
            keys_and_values: 键值对字典
        """
        for key, value in keys_and_values.items():
            self.set(key, value)

    def get_hit_rate(self) -> float:
        """获取缓存命中率

        Returns:
            命中率（0-100）
        """
        total_requests = self.hits + self.misses
        if total_requests == 0:
            return 0.0
        return (self.hits / total_requests) * 100

    def __len__(self) -> int:
        """返回缓存大小"""
        return len(self.cache)

    def __contains__(self, key: str) -> bool:
        """支持 'in' 操作符"""
        return key in self.cache

    def __repr__(self) -> str:
        """字符串表示"""
        stats = self.get_stats()
        return (f"AnnotationCache(size={stats['size']}/{stats['max_size']}, "
                f"hit_rate={stats['hit_rate']}, "
                f"hits={stats['hits']}, misses={stats['misses']})")
