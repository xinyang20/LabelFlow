# LabelFlow - 快捷图片标注工具

简体中文 | [English](README_EN.md)

一款轻量级的桌面图片标注工具，支持文字描述和标签标注。

## 核心特性

- **多模式标注**: 文字描述、标签选择、混合模式
- **智能管理**: SHA256图片识别，自动标签缓存
- **断点续标**: 自动恢复标注进度
- **数据保护**: Base64编码备份，防止数据丢失

## 快速开始

### 安装依赖

```bash
# 安装依赖
uv sync
```

### 运行程序

```bash
uv run python src/main.py
```

## 基本使用

1. **Ctrl+O** 打开图片目录
2. 选择标注模式（描述/标签/混合）
3. 输入标注内容
4. **Ctrl+→ / Ctrl+←** 切换图片（自动保存）
5. **Ctrl+Z / Ctrl+Y** 撤销/重做操作

## 常用快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+O | 打开目录 |
| Ctrl+S | 设置保存路径 |
| Ctrl+Z | 撤销 |
| Ctrl+Y | 重做 |
| Ctrl+Return | 快速保存 |
| Ctrl+D | 清空标注 |
| Ctrl+Shift+C | 复制上一张标注 |
| Ctrl+← / Ctrl+→ | 上一张/下一张 |
| Ctrl+0-9 | 快速选择标签（标签模式） |

## 数据格式

每张图片对应一个JSON文件，包含：

```json
{
  "filename": "image.jpg",
  "hash": "sha256_hash",
  "describe": "图片描述",
  "label": ["标签1", "标签2"],
  "base64_data": "..."
}
```

## 配置文件

程序配置保存在 `config.json`，支持自定义：
- 性能参数（内存限制、撤销步数等）
- UI设置（语言、窗口大小等）
- 日志配置（大小、备份数量等）
- 快捷键映射

## 支持的图片格式

JPG/JPEG, PNG, BMP, TIFF/TIF

## 系统要求

- Python 3.8+
- PyQt6
- Pillow
- psutil

## 打包发布

```bash
python build_spec.py
```

生成的可执行文件位于 `dist/LabelFlow.exe`

## 许可证

MIT License

## 项目地址

https://github.com/xinyang20/LabelFlow
