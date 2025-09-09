# Quick Label - Image Annotation Tool V0.0.4

[简体中文](README.md) | English

An efficient and user-friendly desktop application for image annotation with text descriptions and label tagging.

## Features

- **Multi-mode Annotation**: Supports text description, label selection, and hybrid annotation modes
- **Smart Image Management**: Uses SHA256 hash values to ensure accurate correspondence between images and labels
- **Batch Loading Strategy**: Supports efficient processing of large image sets with automatic memory management
- **Flexible Saving Options**: Supports automatic and manual saving modes with customizable save paths
- **Data Backup Protection**: Built-in base64 encoding for images to prevent original image loss
- **Intuitive Interface**: Left-right layout with separate image display and annotation input, supports image scaling and dragging
- **Progress Tracking**: Real-time display of annotation progress and file information
- **Multi-language Support**: Supports Chinese and English interface switching
- **Label Management**: Smart label caching with support for label reuse and quick selection
- **Version Management**: Dynamic version number display for easy version tracking
- **Shortcut Key System**: Comprehensive shortcut key support to improve annotation efficiency
- **Resume Annotation**: Smart recovery of annotation progress, supports continuing after work interruption
- **Image Restoration**: Restore missing image files from JSON files
- **Image Verification**: Automatically verify image integrity and update hash values
- **Batch Rename**: Batch rename image files with unified naming format
- **File Directory Display**: Supports double-click navigation for interval annotation
- **Dangerous Operation Protection**: Confirmation prompts before important operations

## System Requirements

- Windows/macOS/Linux
- Python 3.8+
- PyQt6
- Pillow

## Installation and Running

### Development Environment

1. Clone the project locally

2. Activate virtual environment:

	```bash
	./.venv/Scripts/activate
	```

3. Install dependencies:

	```bash
	uv add PyQt6 Pillow
	```

4. Run the application:

	```bash
	python src/main.py
	```

### Usage Instructions

1. **Select Working Directory**: Click "Open Directory" in the "File" menu to select a folder containing images
2. **Set Save Path** (optional): Click "Set Save Path" in the "File" menu to customize JSON file save location
3. **Configure Annotation Mode**: Select annotation mode in the "Settings" menu:
	- **Description Mode**: Pure text description annotation
	- **Label Mode**: Label selection annotation with Ctrl+0-9 shortcut support
	- **Hybrid Mode**: Supports both text description and label selection
4. **Configure Save Mode**: Switch between automatic/manual save modes in the "Settings" menu
5. **Compatibility Settings**: Enable compatibility mode in the "Settings" menu to support V0.0.2 data format
6. **Language Settings**: Switch between Chinese/English interface in the "Settings" menu
7. **Start Annotation**:
	- Left side displays current image with support for scaling, scrolling, and Ctrl+mouse dragging
	- Right side shows corresponding annotation interface based on selected mode
	- Use "Previous"/"Next" buttons or Ctrl+Left/Right arrow keys to switch images
	- Bottom file directory display supports double-click navigation to specific images
8. **Smart Saving**:
	- Automatic save mode: Automatically saves annotations when switching images
	- Manual save mode: Shows save confirmation dialog before switching images
	- Smart empty content skip: No save operation when there's no annotation content
9. **Resume Annotation**: When reopening the same directory, automatically loads previous annotation progress and available labels, locates to the first unannotated image
10. **Advanced Features**:
	- **Image Restoration**: Automatically restore images from base64 encoding when image files are missing but JSON files exist
	- **Image Verification**: Automatically verify image integrity and recalculate hash values when changes are detected
	- **Batch Rename**: Batch rename image files to IMG_XXXXXX format (dangerous operation, requires confirmation)

## Supported Image Formats

- JPG/JPEG
- PNG
- BMP
- TIFF/TIF

## Shortcut Key System

V0.0.4 provides comprehensive shortcut key support to improve annotation efficiency:

### Global Shortcuts
- **Ctrl+O**: Open working directory
- **Ctrl+S**: Set save path
- **Ctrl+Q**: Exit program
- **Ctrl+A**: Show about page
- **Ctrl+Left**: Previous image
- **Ctrl+Right**: Next image

### Label Mode Shortcuts
- **Ctrl+0-9**: Quick selection of corresponding numbered labels (available only in label mode and hybrid mode)
- Supports up to 10 shortcut labels, assigned according to label cache order
- Press the same shortcut key again to deselect

### Shortcut Configuration
- Shortcut settings are saved in `keys_setting.json` file
- Supports custom shortcut key configuration modification
- Automatically loads shortcut settings on program startup

## Data Format

### Current Version Format (V0.0.4)

Each image corresponds to an independent JSON annotation file with the same filename as the image (with .json extension):

```json
{
  "filename": "IMG_001.jpg",
  "hash": "a1b2c3d4e5f6...",
  "describe": "Detailed description of the image",
  "label": ["Label1", "Label2", "Label3"],
  "file_size": 2048576,
  "base64_data": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

**Field Description:**
- `filename`: Image filename
- `hash`: SHA256 hash value of the image for unique identification and integrity verification
- `describe`: Image description content
- `label`: Label array
- `file_size`: Image file size (bytes)
- `base64_data`: Base64 encoding of the image for image restoration functionality

### Compatibility Support

**V0.0.2 Format Compatibility (requires enabling compatibility mode):**
```json
{
  "filename": "IMG_001.jpg",
  "hash": "a1b2c3d4e5f6...",
  "annotation": "Image description content",
  "file_size": 2048576,
  "base64_data": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

**Note:** V0.0.4 has compatibility mode disabled by default and only supports V0.0.3+ data formats. To support V0.0.2 format, please enable compatibility mode in the "Settings" menu. V0.0.1 format is no longer supported.

## Performance Optimization

- **Batch Loading**: Loads all images when fewer than 100, otherwise loads in batches
- **Memory Management**: Automatically monitors memory usage to avoid exceeding 1GB limit
- **Background Processing**: Hash value and base64 encoding calculations performed in background threads without affecting UI responsiveness
- **Smart Encoding**: Automatically adjusts base64 encoding file size limit based on device memory
- **Empty Content Optimization**: Intelligently skips saving operations for empty annotation content, reducing invalid file generation

## Advanced Features

### Multi-mode Annotation
- **Description Mode**: Focus on text description annotation
- **Label Mode**: Quick label selection and management with Ctrl+0-9 shortcut support
- **Hybrid Mode**: Supports both description and label annotation
- Can dynamically switch annotation modes at runtime

### Smart Label Management
- Automatically caches historical labels for quick reuse
- Extracts labels from existing annotation files
- Supports adding and managing new labels
- Real-time label status synchronization
- Displays shortcut key hints in label mode and hybrid mode

### Enhanced Image Viewing
- Supports image scaling (10%-500%)
- Mouse wheel with Ctrl key for scaling
- Ctrl+mouse drag to move images
- Adaptive display and reset functionality
- Scroll area supports large image browsing
- Adjustable split panel layout

### Resume Annotation Feature
- Automatically detects and recovers previous annotation progress
- Intelligently locates to the first unannotated image
- Maintains annotation mode and available label list
- Supports seamless continuation after work interruption

### Image Management Features
- **Image Restoration**: Automatically restore missing image files from base64 encoding in JSON files
- **Image Verification**: Automatically verify image integrity, detect file changes and update hash values
- **Batch Rename**: Batch rename image files to IMG_XXXXXX format, synchronously update JSON files
- **File Directory Display**: Bottom display of all image files, supports double-click navigation for interval annotation

### Multi-language Interface
- Supports Chinese and English interfaces
- Dynamic language switching at runtime
- Complete interface localization support

### Custom Save Path
- Supports setting custom save path for annotation files
- Defaults to saving in the same directory as image files if not set
- Remains effective until working directory is changed

### Auto-save Mode
- **Enabled**: Automatically saves current annotation when switching images
- **Disabled**: Shows save confirmation dialog before switching images
- Enabled by default, can be toggled in "Settings" menu

### Data Backup Protection
- Automatically generates base64 encoding of images and saves in JSON files
- Can recover images from annotation files when original image files are damaged or lost
- Automatically adjusts encoding file size limit based on device performance (5MB-20MB)

### Security Protection Mechanism
- Confirmation prompts before dangerous operations (batch rename, switching without saving, etc.)
- Double confirmation mechanism to prevent misoperations
- Data integrity protection and verification

### Version Management
- Status bar displays current version number
- Version information read from `src/app.info` file
- Supports dynamic version number management

## Development Architecture

The project uses MVC architecture pattern:

- `src/main.py`: Program entry point
- `src/ui_mainwindow.py`: UI interface layer, includes DraggableImageLabel class
- `src/app_controller.py`: Controller layer, handles business logic
- `src/data_manager.py`: Data model layer, manages image and annotation data
- `src/shortcut_manager.py`: Shortcut key management module
- `src/language_manager.py`: Multi-language support module
- `src/about_dialog.py`: About dialog
- `src/app.info`: Application configuration file
- `keys_setting.json`: Shortcut key configuration file

## Build and Release

Use PyInstaller to package as executable:

```bash
pyinstaller --name QuickLabel --windowed --onefile src/main.py
```

## License

This project is licensed under the MIT License.
