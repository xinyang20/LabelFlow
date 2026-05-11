import json

from data_manager import DataManager, ImageInfo


def test_save_annotation_calculates_hash_when_missing(tmp_path):
    image_path = tmp_path / "sample.jpg"
    image_path.write_bytes(b"image-bytes")

    manager = DataManager()
    manager.work_directory = str(tmp_path)
    manager.labels_cache_file = str(tmp_path / "labels_cache.json")
    manager.enable_base64 = False
    manager.images = [ImageInfo(str(image_path))]
    manager.current_index = 0

    assert manager.save_annotation("plain text") is True
    assert manager.images[0].hash

    annotation_path = tmp_path / "sample.json"
    assert annotation_path.exists()
    data = json.loads(annotation_path.read_text(encoding="utf-8"))
    assert data["hash"] == manager.images[0].hash
    assert data["describe"] == "plain text"


def test_rename_all_images_updates_matching_json(tmp_path):
    image_a = tmp_path / "a.jpg"
    image_b = tmp_path / "b.jpg"
    image_a.write_bytes(b"a")
    image_b.write_bytes(b"b")
    (tmp_path / "a.json").write_text(
        json.dumps({"filename": "a.jpg", "hash": "hash-a", "describe": "a"}),
        encoding="utf-8",
    )

    manager = DataManager()
    manager.work_directory = str(tmp_path)

    result = manager.rename_all_images()

    assert result["errors"] == []
    assert result["renamed"] == 3
    assert (tmp_path / "IMG_000000.jpg").exists()
    assert (tmp_path / "IMG_000001.jpg").exists()
    assert (tmp_path / "IMG_000000.json").exists()

    data = json.loads((tmp_path / "IMG_000000.json").read_text(encoding="utf-8"))
    assert data["filename"] == "IMG_000000.jpg"


def test_rename_all_images_aborts_when_json_target_conflicts(tmp_path):
    image_path = tmp_path / "a.jpg"
    image_path.write_bytes(b"a")
    (tmp_path / "a.json").write_text(
        json.dumps({"filename": "a.jpg", "hash": "hash-a"}),
        encoding="utf-8",
    )
    (tmp_path / "IMG_000000.json").write_text(
        json.dumps({"filename": "other.jpg", "hash": "hash-other"}),
        encoding="utf-8",
    )

    manager = DataManager()
    manager.work_directory = str(tmp_path)

    result = manager.rename_all_images()

    assert result["errors"]
    assert image_path.exists()
    assert (tmp_path / "a.json").exists()


def test_rename_all_images_aborts_when_json_filename_mismatches_image(tmp_path):
    image_path = tmp_path / "a.jpg"
    image_path.write_bytes(b"a")
    (tmp_path / "a.json").write_text(
        json.dumps({"filename": "a.png", "hash": "hash-a"}),
        encoding="utf-8",
    )

    manager = DataManager()
    manager.work_directory = str(tmp_path)

    result = manager.rename_all_images()

    assert result["errors"]
    assert any("JSON配对关系不一致" in error for error in result["errors"])
    assert image_path.exists()
    assert (tmp_path / "a.json").exists()
    assert not (tmp_path / "IMG_000000.jpg").exists()
    assert not (tmp_path / "IMG_000000.json").exists()
