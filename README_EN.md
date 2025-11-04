# LabelFlow - Image Annotation Tool

[简体中文](README.md) | English

A lightweight desktop application for image annotation with text descriptions and label tagging.

## Core Features

- **Multi-mode Annotation**: Text description, label selection, and hybrid modes
- **Smart Management**: SHA256 image identification, automatic label caching
- **Resume Annotation**: Automatically restore annotation progress
- **Data Protection**: Base64 encoding backup to prevent data loss

## Quick Start

### Install Dependencies

```bash
# Install dependencies
uv sync
```

### Run Application

```bash
uv run python src/main.py
```

## Basic Usage

1. **Ctrl+O** Open image directory
2. Select annotation mode (description/label/hybrid)
3. Enter annotation content
4. **Ctrl+→ / Ctrl+←** Switch images (auto-save)
5. **Ctrl+Z / Ctrl+Y** Undo/Redo operations

## Common Shortcuts

| Shortcut | Function |
|----------|----------|
| Ctrl+O | Open directory |
| Ctrl+S | Set save path |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl+Return | Quick save |
| Ctrl+D | Clear annotation |
| Ctrl+Shift+C | Copy previous annotation |
| Ctrl+← / Ctrl+→ | Previous/Next image |
| Ctrl+0-9 | Quick label selection (label mode) |

## Data Format

Each image corresponds to a JSON file containing:

```json
{
  "filename": "image.jpg",
  "hash": "sha256_hash",
  "describe": "Image description",
  "label": ["Label1", "Label2"],
  "base64_data": "..."
}
```

## Configuration File

Application settings are stored in `config.json`, supporting customization of:
- Performance parameters (memory limit, undo steps, etc.)
- UI settings (language, window size, etc.)
- Logging configuration (size, backup count, etc.)
- Keyboard shortcuts mapping

## Supported Image Formats

JPG/JPEG, PNG, BMP, TIFF/TIF

## System Requirements

- Python 3.8+
- PyQt6
- Pillow
- psutil

## Build Release

```bash
python build_spec.py
```

The executable file will be generated in `dist/LabelFlow.exe`

## License

MIT License

## Project Repository

https://github.com/xinyang20/LabelFlow
