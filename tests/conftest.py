# tests/conftest.py
# --- ここからが超重要：import より前に、確実に project/ を sys.path に追加 ---
import sys
from pathlib import Path

# このファイルの場所: project/tests/conftest.py
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[1]  # project/
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))  # 先頭に追加

# ここから下はあなたの既存フィクスチャ（前回の内容）でOK
import csv
import pytest


@pytest.fixture
def sample_rows():
    return [
        {"品名": "アイスの棒", "ゴミの種類": "燃やすごみ"},
        {"品名": "空き缶", "ゴミの種類": "リサイクル"},
        {"品名": "フライパン", "ゴミの種類": "燃やせないごみ"},
        {"品名": "古紙", "ゴミの種類": "資源"},
        {"品名": "ソファー", "ゴミの種類": "粗大ごみ"},
    ]


@pytest.fixture
def tmp_csv_utf8(tmp_path, sample_rows):
    p = tmp_path / "tmp_utf8.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["品名", "ゴミの種類"])
        writer.writeheader()
        writer.writerows(sample_rows)
    return p


@pytest.fixture
def tmp_csv_cp932(tmp_path, sample_rows):
    p = tmp_path / "tmp_cp932.csv"
    with p.open("w", encoding="cp932", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["品名", "ゴミの種類"])
        writer.writeheader()
        writer.writerows(sample_rows)
    return p


@pytest.fixture
def app_with_tmp_csv(monkeypatch, tmp_csv_utf8):
    import importlib
    import config

    monkeypatch.setattr(config, "CSV_FILE", str(tmp_csv_utf8))
    import services.dataset as dataset

    importlib.reload(dataset)
    import app as flask_app

    importlib.reload(flask_app)
    flask_app.app.config.update(TESTING=True)
    return flask_app.app


@pytest.fixture
def client(app_with_tmp_csv):
    return app_with_tmp_csv.test_client()

