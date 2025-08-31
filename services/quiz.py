# services/quiz.py
# ------------------------------------------------------------
# クイズのゲーム状態（セッション）管理・判定ロジック
#  - new_game(): 新規ゲーム作成（問題シャッフル・制限時間設定）
#  - get_next_question(): 次の問題と残り時間
#  - answer(): 回答判定＆状態更新
#  - summary(): スコアと回答一覧
# Flaskのセッションに辞書を保存します。
# ------------------------------------------------------------
import random, time
from typing import Dict, List, Any, Tuple
from flask import session
from config import QUIZ_LIMIT, TIME_LIMIT_SEC

# セッションキー名を一元管理
SESS_KEY = "quiz_state"

def _now() -> float:
    return time.time()

def new_game(records: List[Dict], limit: int = QUIZ_LIMIT) -> Dict[str, Any]:
    """ゲーム開始：問題リスト、進行、スコア、開始時刻などをセッションに保存。"""
    items = records[:]
    random.shuffle(items)
    if limit > 0:
        items = items[:limit]

    state = {
        "started_at": _now(),
        "time_limit": TIME_LIMIT_SEC,
        "index": 0,
        "score": 0,
        "answered": [],  # {item, correct, full, user, result}
        "items": items,  # [{item, category, fullCategory}]
        "finished": False
    }
    session[SESS_KEY] = state
    session.modified = True
    return state

def _get_state() -> Dict[str, Any]:
    return session.get(SESS_KEY)

def time_left() -> int:
    st = _get_state()
    if not st:
        return 0
    elapsed = int(_now() - st["started_at"])
    left = max(0, st["time_limit"] - elapsed)
    return left

def get_next_question() -> Tuple[Dict, int, int]:
    """次の問題を返す。戻り値: (question, index, remaining_time)。終了時は (None, idx, left)。"""
    st = _get_state()
    if not st:
        return None, 0, 0
    if st["finished"]:
        return None, st["index"], 0

    left = time_left()
    if left <= 0:
        st["finished"] = True
        session[SESS_KEY] = st
        return None, st["index"], 0

    idx = st["index"]
    if idx >= len(st["items"]):
        st["finished"] = True
        session[SESS_KEY] = st
        return None, idx, left

    q = st["items"][idx]
    return q, idx, left

def answer(choice: str) -> Dict[str, Any]:
    """解答を受け取り、正解判定し、状態を更新。"""
    st = _get_state()
    if not st:
        return {"error": "no_game"}

    left = time_left()
    if left <= 0:
        st["finished"] = True
        session[SESS_KEY] = st
        return {"finished": True, "left": 0}

    idx = st["index"]
    if idx >= len(st["items"]):
        st["finished"] = True
        session[SESS_KEY] = st
        return {"finished": True, "left": left}

    current = st["items"][idx]
    correct = current["category"]
    full = current.get("fullCategory") or correct
    is_correct = (choice == correct)

    if is_correct:
        st["score"] += 1

    st["answered"].append({
        "item": current["item"], "correct": correct, "full": full,
        "user": choice, "result": is_correct
    })
    st["index"] += 1

    session[SESS_KEY] = st
    return {
        "result": is_correct,
        "full": full,
        "left": left,
        "index": st["index"],
        "total": len(st["items"])
    }

def summary() -> Dict[str, Any]:
    """ゲームのサマリ（スコア・正答率・回答履歴・残り時間など）を返す。"""
    st = _get_state()
    if not st:
        return {"error": "no_game"}
    total = len(st["answered"])
    acc = int(round((st["score"]/total)*100)) if total else 0
    return {
        "score": st["score"],
        "total": total,
        "accuracy": acc,
        "answered": st["answered"],
        "finished": st.get("finished", False),
        "left": time_left()
    }
