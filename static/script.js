// static/script.js
// ------------------------------------------------------------
// フロント最小ロジック（DOM更新 + API呼び出し）
//  - startGame(): サーバにゲーム開始を要求し、タイマー表示を開始
//  - showQuestion(): 次の問題を取得して表示
//  - answer(choice): 回答を送信して判定結果を表示
//  - endGame(): サマリを取得・表示
// ------------------------------------------------------------
let timerHandle; // 画面表示用タイマー

function updateTimerDisplay(left) {
  const t = document.getElementById('timer');
  if (!t) return;
  t.innerText = `残り時間: ${left}秒`;
}

async function startGame() {
  // 画面の初期化（既存構造に合わせる）
  const startBtn = document.querySelector('button.start');
  if (startBtn) startBtn.style.display = 'none';
  const game = document.getElementById('game');
  if (game) game.style.display = 'block';
  const title = document.getElementById('title');
  if (title) title.style.display = 'none';
  const intro = document.getElementById('intro');
  if (intro) intro.style.display = 'none';
  const note = document.querySelector('.note');
  if (note) note.style.display = 'none';

  // サーバ側でゲーム開始
  const res = await fetch('/api/quiz/start', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({limit: 100})
  });
  const json = await res.json();
  if (!json.ok) {
    alert('開始に失敗しました');
    return;
  }

  // タイマー（表示のみ。実際の制限はサーバ側でもチェック）
  clearInterval(timerHandle);
  let left = json.left;
  updateTimerDisplay(left);
  timerHandle = setInterval(async () => {
    left -= 1;
    if (left <= 0) {
      clearInterval(timerHandle);
      await endGame(); // 0秒でサマリ表示へ
    } else {
      updateTimerDisplay(left);
    }
  }, 1000);

  // 最初の問題へ
  await showQuestion();
}

async function showQuestion() {
  const res = await fetch('/api/quiz/next');
  const json = await res.json();
  if (json.finished) {
    await endGame();
    return;
  }
  const qEl = document.getElementById('question');
  if (qEl) qEl.innerText = `「${json.item}」はどのごみ？`;

  const resultDiv = document.getElementById('result');
  if (resultDiv) {
    resultDiv.innerText = '\u00a0';
    resultDiv.classList.remove('correct', 'incorrect');
  }
  document.querySelectorAll('.choices button').forEach(btn => btn.disabled = false);
}

async function answer(choice) {
  document.querySelectorAll('.choices button').forEach(btn => btn.disabled = true);

  const res = await fetch('/api/quiz/answer', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({choice})
  });
  const json = await res.json();
  if (json.finished) {
    await endGame();
    return;
  }

  const resultDiv = document.getElementById('result');
  if (!resultDiv) return;
  if (json.result === true) {
    resultDiv.innerText = `✨正解！「${json.full}」です✨`;
    resultDiv.classList.add('correct');
  } else if (json.result === false) {
    resultDiv.innerText = `❌不正解。正しくは「${json.full}」です。`;
    resultDiv.classList.add('incorrect');
  }

  setTimeout(showQuestion, 500);
}

async function endGame() {
  const res = await fetch('/api/quiz/summary');
  const json = await res.json();

  clearInterval(timerHandle);
  const total = json.total || 0;
  const score = json.score || 0;
  const accuracy = json.accuracy || 0;

  let summaryHTML = `
    <h2>ゲーム終了！</h2>
    <p>解答数：${total} 問 ／ 正解数：${score} 問 ／ 正解率：${accuracy}%</p>
    <button class="back-btn" onclick="location.reload()">スタート画面に戻る</button>
    <button class="share-btn" onclick="shareResult(${score}, ${total}, ${accuracy})">結果をSNSでシェア</button>
    <div class="summary">
    <table>
      <tr><th>#</th><th>品名</th><th>あなたの回答</th><th>正解（詳細）</th><th>結果</th></tr>
  `;

  (json.answered || []).forEach((entry, i) => {
    summaryHTML += `
      <tr>
        <td>${i + 1}</td>
        <td>${entry.item}</td>
        <td>${entry.user}</td>
        <td>${entry.full}</td>
        <td>${entry.result ? '〇' : '×'}</td>
      </tr>
    `;
  });

  summaryHTML += '</table></div>';
  const game = document.getElementById('game');
  if (game) game.innerHTML = summaryHTML;
}

// 共有（地域に依存しない文言）
function shareResult(score, total, accuracy) {
  const text = `ごみ分別クイズ\n正解数：${score}/${total}問（正解率：${accuracy}%）\n#ごみ分別クイズ`;
  const url = location.href;
  const tweet = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`;
  window.open(tweet, '_blank');
}
