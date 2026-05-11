from PyQt6.QtWidgets import QCheckBox, QMessageBox


class DummyImage:
    def __init__(self, filename, annotation=""):
        self.filename = filename
        self.annotation = annotation
        self.hash = "hash-" + filename
        self.image_data = None
        self.is_loaded = False
        self.path = filename
        self.saved_annotation = annotation

    def load_image(self):
        self.is_loaded = True
        return None

    def get_file_size(self):
        return 0

    def calculate_base64(self, enable_base64=True, max_file_size_mb=10):
        return None


def _patch_ui_config(monkeypatch, auto_save=False):
    from config_manager import config_manager

    monkeypatch.setattr(
        config_manager,
        "get_ui_config",
        lambda: {
            "auto_save_enabled": auto_save,
            "default_annotation_mode": "description",
            "window_width": 1200,
            "window_height": 800,
        },
    )
    return config_manager


def _make_manual_switch_controller(monkeypatch, reply):
    _patch_ui_config(monkeypatch, auto_save=False)

    from app_controller import AppController

    controller = AppController()
    first = DummyImage("one.jpg", '{"describe":"saved"}')
    second = DummyImage("two.jpg", '{"describe":"target"}')
    controller.data_manager.images = [first, second]
    controller.data_manager.current_index = 0
    controller.update_ui()

    save_calls = []
    monkeypatch.setattr(controller.main_window, "show_save_confirmation", lambda filename: reply)
    monkeypatch.setattr(
        controller.data_manager,
        "save_annotation",
        lambda annotation: save_calls.append(annotation) or True,
    )
    return controller, first, second, save_calls


def test_controller_uses_configured_auto_save_initial_state(monkeypatch, qapp):
    config_manager = _patch_ui_config(monkeypatch, auto_save=False)
    saved = {}
    monkeypatch.setattr(config_manager, "set", lambda key, value: saved.setdefault(key, value) or True)
    monkeypatch.setattr(config_manager, "save_config", lambda: True)

    from app_controller import AppController

    controller = AppController()

    assert controller.auto_save_enabled is False
    assert controller.main_window.auto_save_action.isChecked() is False

    controller.on_auto_save_changed(True)
    assert saved["ui.auto_save_enabled"] is True

    controller.main_window.close()
    controller.data_manager.cleanup()


def test_undo_commits_current_edit_before_reverting(monkeypatch, qapp):
    _patch_ui_config(monkeypatch, auto_save=False)

    from app_controller import AppController

    controller = AppController()
    image = DummyImage("one.jpg", '{"describe":"old"}')
    controller.data_manager.images = [image]
    controller.data_manager.current_index = 0
    controller.update_ui()

    controller.on_annotation_changed('{"describe":"new"}')
    controller.undo()

    assert controller.current_annotation == '{"describe":"old"}'
    assert image.annotation == '{"describe":"old"}'
    assert controller.command_manager.can_redo() is True

    controller.main_window.close()
    controller.data_manager.cleanup()


def test_clear_and_copy_previous_are_undoable(monkeypatch, qapp):
    _patch_ui_config(monkeypatch, auto_save=False)

    from app_controller import AppController

    controller = AppController()
    first = DummyImage("one.jpg", '{"describe":"source"}')
    second = DummyImage("two.jpg", '{"describe":"target"}')
    controller.data_manager.images = [first, second]
    controller.data_manager.current_index = 1
    controller.update_ui()

    controller.on_clear_annotation()
    assert controller.current_annotation == ""
    controller.undo()
    assert controller.current_annotation == '{"describe":"target"}'

    controller.on_copy_from_previous()
    assert controller.current_annotation == '{"describe":"source"}'
    controller.undo()
    assert controller.current_annotation == '{"describe":"target"}'

    controller.main_window.close()
    controller.data_manager.cleanup()


def test_manual_switch_no_discards_unsaved_edit_without_annotation_history(monkeypatch, qapp):
    controller, first, second, save_calls = _make_manual_switch_controller(
        monkeypatch,
        QMessageBox.StandardButton.No,
    )

    controller.on_annotation_changed('{"describe":"draft"}')
    controller.on_next_image()

    assert controller.data_manager.current_index == 1
    assert first.annotation == '{"describe":"saved"}'
    assert first.saved_annotation == '{"describe":"saved"}'
    assert save_calls == []
    assert controller.command_manager.get_history() == ["切换图片: #0 -> #1"]

    controller.main_window.close()
    controller.data_manager.cleanup()


def test_manual_switch_cancel_keeps_edit_without_history(monkeypatch, qapp):
    controller, first, second, save_calls = _make_manual_switch_controller(
        monkeypatch,
        QMessageBox.StandardButton.Cancel,
    )

    controller.on_annotation_changed('{"describe":"draft"}')
    controller.on_next_image()

    assert controller.data_manager.current_index == 0
    assert controller.current_annotation == '{"describe":"draft"}'
    assert first.annotation == '{"describe":"draft"}'
    assert first.saved_annotation == '{"describe":"saved"}'
    assert save_calls == []
    assert controller.command_manager.get_history() == []

    controller.main_window.close()
    controller.data_manager.cleanup()


def test_manual_switch_yes_saves_and_records_annotation_history(monkeypatch, qapp):
    controller, first, second, save_calls = _make_manual_switch_controller(
        monkeypatch,
        QMessageBox.StandardButton.Yes,
    )

    controller.on_annotation_changed('{"describe":"draft"}')
    controller.on_next_image()

    assert controller.data_manager.current_index == 1
    assert first.annotation == '{"describe":"draft"}'
    assert first.saved_annotation == '{"describe":"draft"}'
    assert save_calls == ['{"describe":"draft"}']
    assert controller.command_manager.get_history() == [
        "编辑标注 (图片#0)",
        "切换图片: #0 -> #1",
    ]

    controller.main_window.close()
    controller.data_manager.cleanup()


def test_auto_save_switch_records_pending_edit_when_already_saved(monkeypatch, qapp):
    _patch_ui_config(monkeypatch, auto_save=True)

    from app_controller import AppController

    controller = AppController()
    first = DummyImage("one.jpg", '{"describe":"saved"}')
    second = DummyImage("two.jpg", '{"describe":"target"}')
    controller.data_manager.images = [first, second]
    controller.data_manager.current_index = 0
    controller.update_ui()

    save_calls = []
    monkeypatch.setattr(
        controller.data_manager,
        "save_annotation",
        lambda annotation: save_calls.append(annotation) or True,
    )

    controller.on_annotation_changed('{"describe":"draft"}')
    first.saved_annotation = '{"describe":"draft"}'
    controller.on_next_image()

    assert controller.data_manager.current_index == 1
    assert save_calls == []
    assert controller.command_manager.get_history() == [
        "编辑标注 (图片#0)",
        "切换图片: #0 -> #1",
    ]

    controller.main_window.close()
    controller.data_manager.cleanup()


def test_manual_close_no_discards_unsaved_edit_without_annotation_history(monkeypatch, qapp):
    controller, first, second, save_calls = _make_manual_switch_controller(
        monkeypatch,
        QMessageBox.StandardButton.No,
    )

    controller.on_annotation_changed('{"describe":"draft"}')
    assert controller._handle_save_before_close() is True

    assert first.annotation == '{"describe":"saved"}'
    assert first.saved_annotation == '{"describe":"saved"}'
    assert save_calls == []
    assert controller.command_manager.get_history() == []

    controller.main_window.close()
    controller.data_manager.cleanup()


def test_label_selection_refreshes_without_label_checkbox_cache(qapp):
    from ui_mainwindow import MainWindow

    window = MainWindow()
    window.current_mode = "label"
    window.set_available_labels(["cat", "dog"])

    window.update_label_selection(["dog"])
    checked = [box.text() for box in window.findChildren(QCheckBox) if box.isChecked()]
    assert checked == ["dog"]

    window.reset_label_selection()
    checked = [box.text() for box in window.findChildren(QCheckBox) if box.isChecked()]
    assert checked == []

    window.close()
