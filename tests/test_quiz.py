# tests/test_quiz.py
# quizロジック（セッション管理）のユニットテスト
import importlib


def test_new_game_and_flow(monkeypatch, tmp_csv_utf8):
    # datasetとconfigのCSVを差し替え
    import config

    monkeypatch.setattr(config, "CSV_FILE", str(tmp_csv_utf8))
    import services.dataset as dataset
    import services.quiz as quiz

    importlib.reload(dataset)
    importlib.reload(quiz)

    # 疑似セッションの代わりに dict を使うため、sessionをモンキーパッチ
    class DummySession(dict):
        modified = False

    dummy_session = DummySession()
    quiz.session = dummy_session  # type: ignore

    records = dataset.get_dataset()
    state = quiz.new_game(records, limit=3)
    assert state["index"] == 0
    assert state["score"] == 0
    assert len(state["items"]) == 3

    # 次へ
    q, idx, left = quiz.get_next_question()
    assert q is not None
    assert idx == 0
    assert left > 0

    # 正答と誤答を混ぜて回答
    correct_cat = q["category"]
    res = quiz.answer(correct_cat)
    assert res["result"] is True
    assert res["index"] == 1

    # 不正解回答
    wrong = {"燃やすごみ", "燃やさないごみ", "資源ごみ", "粗大ごみ"} - {correct_cat}
    res2 = quiz.answer(wrong.pop())
    assert res2["index"] == 2

    # 残りまで回答して終了
    _ = quiz.answer(correct_cat)  # 3問目
    summary = quiz.summary()
    assert summary["total"] == 3
    assert 0 <= summary["accuracy"] <= 100
