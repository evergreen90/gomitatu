# tests/test_api.py
# Flask API の結合テスト（/api/quiz/* エンドポイント）
import json


def test_start_next_answer_summary_flow(client):
    # /api/quiz/start
    r = client.post("/api/quiz/start", json={"limit": 5})
    assert r.status_code == 200
    body = r.get_json()
    assert body["ok"] is True
    assert body["count"] <= 5
    assert body["left"] > 0

    # /api/quiz/next
    r = client.get("/api/quiz/next")
    assert r.status_code == 200
    q = r.get_json()
    assert "finished" in q
    assert q["finished"] in (True, False)
    if not q["finished"]:
        assert "item" in q

        # /api/quiz/answer（適当な選択肢を回答）
        r = client.post("/api/quiz/answer", json={"choice": "資源ごみ"})
        assert r.status_code == 200
        ans = r.get_json()
        assert "left" in ans
        assert "index" in ans
        assert "total" in ans

    # /api/quiz/summary
    r = client.get("/api/quiz/summary")
    assert r.status_code == 200
    s = r.get_json()
    assert "score" in s
    assert "total" in s
    assert "accuracy" in s
