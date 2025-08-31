import os
from datetime import timedelta
from flask import Flask, jsonify, render_template, request, send_from_directory

from config import SECRET_KEY, QUIZ_LIMIT
from services.dataset import get_dataset
from services.quiz import new_game, get_next_question, answer as answer_q, summary

# static_folder と template_folder を明示
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = SECRET_KEY
app.permanent_session_lifetime = timedelta(hours=6)

# ---------- Webページ ----------
@app.route("/")
def root():
    # templates/index.html を描画
    return render_template("index.html")

# CSS配信（templates/style.css に置く構成に対応）
@app.route("/style.css")
def style():
    return send_from_directory("templates", "style.css")

# ---------- API: ゲーム開始 ----------
@app.route("/api/quiz/start", methods=["POST"])
def api_quiz_start():
    """
    新しいゲームを開始します。
    body: { "limit": <int> } 省略時は config.QUIZ_LIMIT
    戻り値: { ok, count, left }
    """
    limit = QUIZ_LIMIT
    if request.is_json:
        limit = request.json.get("limit", QUIZ_LIMIT)

    records = get_dataset()         # CSV読み込み＆正規化（services/dataset.py）
    state = new_game(records, limit=limit)  # セッションにゲーム状態を作成（services/quiz.py）
    return jsonify({"ok": True, "count": len(state["items"]), "left": state["time_limit"]})

# ---------- API: 次の問題 ----------
@app.route("/api/quiz/next", methods=["GET"])
def api_quiz_next():
    """
    次の問題（品名）を返します。終了時は finished=True。
    戻り値: { finished, index, left, item? }
    """
    q, idx, left = get_next_question()
    if q is None:
        return jsonify({"finished": True, "index": idx, "left": left})
    return jsonify({"finished": False, "index": idx, "left": left, "item": q["item"]})

# ---------- API: 回答 ----------
@app.route("/api/quiz/answer", methods=["POST"])
def api_quiz_answer():
    """
    回答を受け取り、正解判定して状態更新します。
    body: { "choice": "燃やすごみ" | "燃やさないごみ" | "資源ごみ" | "粗大ごみ" }
    戻り値: { finished?, result?, full?, left, index, total }
    """
    payload = request.json or {}
    choice = payload.get("choice")
    if not choice:
        return jsonify({"error": "choice_required"}), 400
    result = answer_q(choice)
    return jsonify(result)

# ---------- API: サマリ ----------
@app.route("/api/quiz/summary", methods=["GET"])
def api_quiz_summary():
    """
    ゲームのサマリ（正解数・正答率・回答履歴など）を返します。
    戻り値: { score, total, accuracy, answered[], finished, left }
    """
    return jsonify(summary())

# 健康チェック
@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    # 5000が衝突することがあるため、デフォルト8000番
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
