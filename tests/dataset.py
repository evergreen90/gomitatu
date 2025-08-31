# tests/test_dataset.py
# dataset層のユニットテスト：エンコーディング、正規化、重複排除など
import importlib


def test_utf8_csv_parsing(monkeypatch, tmp_csv_utf8):
    import config

    monkeypatch.setattr(config, "CSV_FILE", str(tmp_csv_utf8))
    import services.dataset as dataset

    importlib.reload(dataset)

    records = dataset.get_dataset()
    assert len(records) >= 5
    # 代表例の正規化確認
    m = {r["item"]: r for r in records}
    assert m["アイスの棒"]["category"] == "燃やすごみ"
    assert m["空き缶"]["category"] in ("資源ごみ", "資源ごみ")  # リサイクル→資源ごみに正規化
    assert m["フライパン"]["category"] == "燃やさないごみ"
    assert m["ソファー"]["category"] == "粗大ごみ"


def test_cp932_fallback(monkeypatch, tmp_csv_cp932):
    import config

    monkeypatch.setattr(config, "CSV_FILE", str(tmp_csv_cp932))
    import services.dataset as dataset

    importlib.reload(dataset)

    records = dataset.get_dataset()
    assert len(records) >= 5  # cp932でも読めること
    # 代表例の正規化確認
    assert any(r["category"] == "資源ごみ" for r in records)
    assert any(r["category"] == "燃やさないごみ" for r in records)


def test_simplify_category_rules():
    import services.dataset as dataset

    # 否定を先に判定
    assert dataset.simplify_category("燃やせないごみ") == "燃やさないごみ"
    assert dataset.simplify_category("不燃") == "燃やさないごみ"
    assert dataset.simplify_category("燃やせるごみ") == "燃やすごみ"
    assert dataset.simplify_category("リサイクル") == "資源ごみ"
    assert dataset.simplify_category("粗大") == "粗大ごみ"
    assert dataset.simplify_category("未知") == "その他"
