import os

BASE_DIR = os.path.dirname(__file__)

# CSVファイルのパス（services/ 配下に移動した前提）
CSV_FILE = os.path.join(BASE_DIR, "services", "hiraizumi_garbage_dic.csv")

# キャッシュやクイズ挙動の設定
CACHE_TTL_SEC = int(os.environ.get("CACHE_TTL_SEC", "600"))  # 10分
QUIZ_LIMIT     = int(os.environ.get("QUIZ_LIMIT", "100"))
TIME_LIMIT_SEC = int(os.environ.get("TIME_LIMIT_SEC", "60"))

# Flaskセッションキー（本番では環境変数に設定してください）
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")
