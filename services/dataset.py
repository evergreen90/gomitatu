import os, csv, time
from io import StringIO
from typing import List, Dict

from config import CSV_FILE, CACHE_TTL_SEC

_CACHE = {"data": None, "fetched": 0.0}

def _read_csv_text_with_fallback(path: str) -> str:
    """UTF-8優先、だめならcp932で寛容に読む。"""
    for enc in ("utf-8", "utf-8-sig"):
        try:
            with open(path, "r", encoding=enc, errors="strict") as f:
                return f.read()
        except Exception:
            pass
    with open(path, "r", encoding="cp932", errors="ignore") as f:
        return f.read()

def simplify_category(s: str) -> str:
    """自治体ごとの差異を吸収し、5分類に正規化。"""
    s = (s or "").strip()
    if not s:
        return "その他"
    # 否定系は先に判定（「燃やせない」を「燃やす」より優先）
    if "燃やさないごみ" in s or "燃やせない" in s or "不燃" in s:
        return "燃やさないごみ"
    if "燃やすごみ" in s or "燃やせる" in s or "可燃" in s or "燃える" in s:
        return "燃やすごみ"
    if any(x in s for x in ["資源","リサイクル","びん","瓶","缶","ペット","紙","古紙"]):
        return "資源ごみ"
    if any(x in s for x in ["粗大","大型"]):
        return "粗大ごみ"
    return "その他"

def _pick_exact_or_contains(keys, exact_list, contains_list=None):
    """ヘッダ名のゆらぎ対策：完全一致→部分一致の順でキーを拾う。"""
    for k in exact_list:
        if k in keys:
            return k
    if contains_list:
        for k in keys:
            if isinstance(k, str) and any(sub in k for sub in contains_list):
                return k
    return None

def parse_csv_to_records(csv_text: str) -> List[Dict]:
    """CSVテキスト→ {item, category, fullCategory} の配列に変換。"""
    f = StringIO(csv_text)
    reader = csv.DictReader(f)

    if reader.fieldnames:
        reader.fieldnames = [fn.strip() if isinstance(fn, str) else fn for fn in reader.fieldnames]

    out, seen = [], set()
    for row in reader:
        # キーと値をstrip
        row = { (k.strip() if isinstance(k, str) else k): (v.strip() if isinstance(v, str) else v)
                for k, v in row.items() }

        keys = row.keys()
        item_key = _pick_exact_or_contains(
            keys, ["品名","品　名","品  名","品目","ごみ名","名称","item"], ["品"]
        )
        cat_key = _pick_exact_or_contains(
            keys, ["ごみの種類","ゴミの種類","種類","区分","分別","分類","カテゴリ","category"],
            ["種類","区分","分別","分類"]
        )
        if not item_key or not cat_key:
            continue

        item = row.get(item_key) or ""
        full = row.get(cat_key) or ""
        if not item or not full:
            continue

        key = (item, full)
        if key in seen:
            continue  # 重複除去
        seen.add(key)

        out.append({
            "item": item,
            "category": simplify_category(full),
            "fullCategory": full
        })
    return out

def get_dataset() -> List[Dict]:
    """10分キャッシュつきでレコード配列を返す。"""
    now = time.time()
    if _CACHE["data"] is not None and (now - _CACHE["fetched"] < CACHE_TTL_SEC):
        return _CACHE["data"]
    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(f"{CSV_FILE} not found.")
    text = _read_csv_text_with_fallback(CSV_FILE)
    records = parse_csv_to_records(text)
    _CACHE["data"] = records
    _CACHE["fetched"] = now
    return records
