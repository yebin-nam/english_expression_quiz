import os
import glob
import json
import re
import webbrowser
import subprocess


def normalize_expression(text: str) -> str:
    """Normalize typography and unambiguous OCR pronoun forms, not every l."""
    text = text.translate(str.maketrans({c: "'" for c in "‘’ʼ＇`´"}))
    text = re.sub(r"(?<![A-Za-z])[liI](?='(?:m|d|ll|ve)\b)", "I", text)
    text = re.sub(r"(?<![A-Za-z])[li](?=\s|[.!?,;:]|$)", "I", text)
    return re.sub(r"\s+", " ", text).strip()


# 📍 옵시디언 영어공부 폴더 경로
OBSIDIAN_DIR = r"C:\Users\skadp\OneDrive\문서\Obsidian Vault\영어공부\Learning English"
OUTPUT_JS = "./learning_data.js"
QUIZ_HTML = "./index.html"
QUIZ_HTML_ALT = "./quiz.html"

def lesson_sort_key(path):
    name = os.path.splitext(os.path.basename(path))[0].replace("_", " ")
    match = re.search(r"\d+", name)
    if match:
        return (0, -int(match.group()), name[match.end():].strip().casefold(), name.casefold())
    return (1, 0, "", name.casefold())


def update_learning_data():
    all_data = []
    item_id = 1
    
    # 1. 파일 검색
    search_dir = OBSIDIAN_DIR if os.path.exists(OBSIDIAN_DIR) else "."
    if not os.path.exists(OBSIDIAN_DIR):
        print(f"⚠️ 경고: '{OBSIDIAN_DIR}' 폴더를 찾을 수 없어 현재 폴더에서 .md 파일을 검색합니다.")

    md_files = glob.glob(os.path.join(search_dir, "*.md"))
    
    # Lesson number descending; files with the same number use A, B, C order.
    md_files.sort(key=lesson_sort_key)
    print(f"🔄 총 {len(md_files)}개의 마크다운 파일을 파싱하는 중 (번호 큰 순)...")

    for file_path in md_files:
        mtime = os.path.getmtime(file_path)
        unit_name = os.path.basename(file_path).replace(".md", "").replace("_", " ")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"⚠️ {file_path} 읽기 실패: {e}")
            continue
            
        for line in lines:
            line = line.strip()
            if line.startswith("|") and "Expression" not in line and "---" not in line:
                parts = [p.strip() for p in line.split("|")[1:-1]]
                if len(parts) >= 2:
                    expr = parts[0]
                    mean = parts[1]
                    ex = parts[2] if len(parts) >= 3 else ""
                    
                    expr_clean = normalize_expression(re.sub(r"==|\*\*|<br>|~~", "", expr))
                    mean_clean = re.sub(r"==|\*\*|<br>|~~", "", mean).strip()
                    ex_clean = re.sub(r"==|\*\*|<br>|~~", " ", ex).strip()
                    
                    if expr_clean and mean_clean and not re.search(r"@|\baelee\b|\baelly877\b", expr_clean, re.I):
                        has_ex = bool(ex_clean)
                        all_data.append({
                            "id": item_id,
                            "unit": unit_name,
                            "expression": expr_clean,
                            "meaning": mean_clean,
                            "example": ex_clean if has_ex else None,
                            "has_example": has_ex,
                            "last_modified": mtime
                        })
                        item_id += 1

    # JS 스크립트 형태로 저장
    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write("window.expressionsData = " + json.dumps(all_data, ensure_ascii=False, indent=2) + ";")
        
    print(f"✅ 최신화 완료! 총 {len(all_data)}개 표현이 '{OUTPUT_JS}'에 저장되었습니다.")

def create_retro_html():
    html_code = r"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>RETRO ENGLISH QUIZ</title>
  <style>
    @import url('https://cdn.jsdelivr.net/gh/noonnu/noonfonts_2001@1.1/DungGeunMo.woff');
    
    * { box-sizing: border-box; }
    body {
      font-family: 'DungGeunMo', 'Pretendard', 'Malgun Gothic', '맑은 고딕', sans-serif;
      background: #0f172a;
      color: #e2e8f0;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      margin: 0;
      padding: 15px;
    }
    
    .arcade-card {
      background: #1e293b;
      border: 4px solid #475569;
      border-radius: 16px;
      padding: 24px;
      width: 100%;
      max-width: 520px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }

    .top-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #0f172a;
      border: 2px solid #334155;
      padding: 10px 14px;
      border-radius: 8px;
      margin-bottom: 16px;
      font-size: 14px;
    }

    .lives { color: #ef4444; letter-spacing: 2px; }
    .score { color: #f59e0b; font-weight: bold; }

    /* 모드 버튼 */
    .mode-bar { display: flex; gap: 8px; margin-bottom: 14px; }
    .mode-btn {
      flex: 1; padding: 10px; border: 2px solid #475569; border-radius: 8px;
      background: #334155; color: #cbd5e1; font-size: 13px; font-family: inherit;
      cursor: pointer; transition: 0.1s;
    }
    .mode-btn.active { background: #2563eb; color: #ffffff; border-color: #60a5fa; }

    /* 퀴즈 형식 선택 */
    .type-bar { display: flex; gap: 6px; margin-bottom: 14px; }
    .type-btn {
      flex: 1; padding: 8px 4px; border: 2px solid #334155; border-radius: 6px;
      background: #0f172a; color: #94a3b8; font-size: 12px; font-family: inherit;
      cursor: pointer; text-align: center;
    }
    .type-btn.active { background: #0284c7; color: #ffffff; border-color: #38bdf8; }

    /* 파일 선택 아코디언 */
    .file-select-box {
      background: #0f172a; border: 2px solid #334155; border-radius: 8px;
      padding: 10px; margin-bottom: 14px; font-size: 12px;
    }
    .file-list { max-height: 110px; overflow-y: auto; margin-top: 8px; display: flex; flex-direction: column; gap: 4px; }
    .file-item { display: flex; align-items: center; gap: 6px; color: #cbd5e1; }

    /* 세션 문제 수 버튼 */
    .session-bar { display: flex; align-items: center; gap: 6px; margin-bottom: 16px; font-size: 12px; }
    .count-btn {
      padding: 6px 12px; border: 2px solid #334155; border-radius: 6px;
      background: #0f172a; color: #94a3b8; font-family: inherit; cursor: pointer;
    }
    .count-btn.active { background: #d97706; color: #ffffff; border-color: #fbbf24; }

    /* 프로그레스 바 */
    .progress-bg { background: #0f172a; border-radius: 6px; height: 10px; border: 1px solid #334155; margin-bottom: 14px; overflow: hidden; }
    .progress-fill { background: #38bdf8; height: 100%; width: 0%; transition: width 0.2s; }

    /* 문제 영역 */
    .unit-tag { font-size: 11px; color: #38bdf8; background: #0f172a; padding: 4px 8px; border-radius: 4px; border: 1px solid #0284c7; display: inline-block; margin-bottom: 10px; }
    .question-card {
      background: #0f172a; border: 2px solid #334155; padding: 20px; border-radius: 10px;
      font-size: 18px; line-height: 1.6; min-height: 90px; margin-bottom: 16px; word-break: break-all;
    }

    /* 입력 및 버튼 */
    .input-group { display: flex; gap: 8px; margin-bottom: 14px; }
    .quiz-input {
      flex: 1; padding: 12px; border: 2px solid #475569; border-radius: 8px;
      background: #0f172a; color: #ffffff; font-size: 16px; font-family: inherit; outline: none;
    }
    .quiz-input:focus { border-color: #38bdf8; }
    .action-btn {
      padding: 12px 18px; border: 2px solid #2563eb; border-radius: 8px;
      background: #2563eb; color: white; font-family: inherit; font-size: 15px; cursor: pointer;
    }

    /* 힌트 상자 */
    .hint-btn {
      width: 100%; padding: 8px; background: #0f172a; border: 1px dashed #d97706; color: #fbbf24;
      border-radius: 6px; font-family: inherit; font-size: 12px; cursor: pointer; margin-bottom: 12px;
    }
    .hint-box {
      background: #1e1b4b; border: 1px solid #6366f1; padding: 10px; border-radius: 6px;
      color: #a5b4fc; font-size: 15px; letter-spacing: 2px; margin-bottom: 12px; display: none; text-align: center;
    }

    /* 객관식 보기 버튼 */
    .mc-grid { display: flex; flex-direction: column; gap: 8px; margin-bottom: 14px; }
    .mc-btn {
      padding: 12px; border: 2px solid #334155; border-radius: 8px;
      background: #0f172a; color: #e2e8f0; font-family: inherit; font-size: 14px;
      text-align: left; cursor: pointer; transition: 0.1s;
    }
    .mc-btn:hover { border-color: #38bdf8; background: #1e293b; }

    /* 결과 메시지 */
    .result-box { padding: 12px; border-radius: 8px; font-size: 14px; line-height: 1.5; margin-bottom: 14px; display: none; }
    .result-box.correct { background: #064e3b; border: 1px solid #10b981; color: #a7f3d0; }
    .result-box.wrong { background: #7f1d1d; border: 1px solid #ef4444; color: #fecaca; }

    .next-btn {
      width: 100%; padding: 14px; background: #059669; border: 2px solid #10b981; color: white;
      border-radius: 8px; font-family: inherit; font-size: 16px; cursor: pointer; display: none;
    }
    /* Compact default view; settings expand only when needed. */
    body { padding: 12px; align-items: flex-start; }
    .arcade-card { max-width: 640px; padding: 16px; margin: auto; }
    .top-header { margin-bottom: 10px; padding: 8px 12px; }
    .quiz-settings { margin-bottom: 8px; background: #0f172a; border-radius: 8px; }
    .quiz-settings summary { cursor: pointer; padding: 10px; font-size: 13px; }
    #settings-summary { color: #94a3b8; font-size: 12px; }
    .settings-content { padding: 8px 10px 2px; }
    .keyboard-help { margin: 8px 0 10px; color: #94a3b8; font-size: 12px; }
    .question-card { padding: 14px; margin-bottom: 10px; min-height: 70px;
      font-size: 17px; line-height: 1.4; word-break: keep-all; overflow-wrap: anywhere; }
    .input-group, .mc-grid, .result-box, .hint-btn, .hint-box { margin-bottom: 8px; }
    .quiz-input { min-width: 0; width: 100%; }
    .quiz-input, .action-btn, .mc-btn, .next-btn { padding: 10px; }
    .result-box { overflow-wrap: anywhere; }
    .session-bar { flex-wrap: wrap; }
    button:focus-visible, summary:focus-visible { outline: 2px solid #fbbf24; outline-offset: 3px; }
    @media (max-height: 700px) {
      body { padding: 6px; }
      .arcade-card { padding: 10px; }
      .question-card { padding: 10px; font-size: 16px; }
      .top-header, .progress-bg, .unit-tag { margin-bottom: 6px; }
    }
  </style>
  <script src="learning_data.js"></script>
</head>
<body>

<div class="arcade-card">
  <!-- 상단 상태바 -->
  <div class="top-header">
    <div>STAGE <span id="stage-num" style="color:#38bdf8;">1</span></div>
    <div class="score">SCORE <span id="score-val">0</span></div>
    <div class="lives" id="lives-display">❤️❤️❤️</div>
  </div>

  <details class="quiz-settings" id="quiz-settings">
    <summary>⚙️ 학습 설정 · 노트 선택 <span id="settings-summary"></span></summary>
    <div class="settings-content">
  <!-- 모드 선택 -->
  <div class="mode-bar">
    <button class="mode-btn active" id="mode-normal" onclick="setMode('normal')">⚡ 스마트 출제</button>
    <button class="mode-btn" id="mode-wrong" onclick="setMode('wrong')">📕 오답노트 (<span id="wrong-badge">0</span>)</button>
  </div>

  <!-- 퀴즈 형식 선택 -->
  <div class="type-bar">
    <button class="type-btn active" id="type-fill" onclick="setQuizType('fill')">✏️ 빈칸채우기</button>
    <button class="type-btn" id="type-subjective" onclick="setQuizType('subjective')">⌨️ 주관식</button>
    <button class="type-btn" id="type-choice" onclick="setQuizType('choice')">🕹️ 객관식</button>
  </div>

  <!-- 세션 문제 수 -->
  <div class="session-bar">
    <span>문제 세트:</span>
    <button class="count-btn" onclick="setLimit(10)">10개</button>
    <button class="count-btn active" onclick="setLimit(20)">20개</button>
    <button class="count-btn" onclick="setLimit(30)">30개</button>
    <button class="count-btn" onclick="setLimit(999)">MAX(전체)</button>
  </div>

  <!-- 파일 선택 -->
  <div class="file-select-box">
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <strong>📁 출제 노트 선택 (번호 큰 순):</strong>
      <div>
        <button onclick="toggleAllFiles(true)" style="font-size:10px; background:#334155; color:#fff; border:none; border-radius:3px; padding:2px 6px; cursor:pointer;">전체선택</button>
        <button onclick="toggleAllFiles(false)" style="font-size:10px; background:#334155; color:#fff; border:none; border-radius:3px; padding:2px 6px; cursor:pointer;">해제</button>
      </div>
    </div>
    <div class="file-list" id="file-list-container"></div>
  </div>

    </div>
  </details>
  <p class="keyboard-help">Enter: 제출 → 다음 문제 · 객관식: 숫자 1–4</p>

  <!-- 진행률 바 -->
  <div class="progress-bg"><div class="progress-fill" id="progress-bar"></div></div>

  <!-- 퀴즈 영역 -->
  <span class="unit-tag" id="unit-tag">UNIT LOADING</span>
  <div class="question-card" id="question-text">퀴즈 데이터를 준비 중입니다...</div>

  <!-- 주관식 힌트 버튼 & 상자 -->
  <button class="hint-btn" id="hint-btn" onclick="showHint()" style="display:none;">💡 힌트 보기 (첫 글자 & 알파벳 구조)</button>
  <div class="hint-box" id="hint-box"></div>

  <!-- 입력창 (주관식/빈칸) -->
  <div class="input-group" id="input-group">
    <input type="text" class="quiz-input" id="user-input" placeholder="정답 입력..." autocomplete="off">
    <button class="action-btn" id="submit-btn" onclick="submitAnswer()">제출</button>
  </div>

  <!-- 객관식 보기 영역 -->
  <div class="mc-grid" id="mc-container" style="display:none;"></div>

  <!-- 결과 상자 & 다음 버튼 -->
  <div class="result-box" id="result-box" role="status" aria-live="polite"></div>
  <button class="next-btn" id="next-btn" onclick="nextQuestion()">다음 문제 · Enter ➔</button>
</div>

<script>
  let currentMode = 'normal'; // 'normal' | 'wrong'
  let quizType = 'fill';      // 'fill' | 'subjective' | 'choice'
  let sessionLimit = 20;
  let currentQuestion = null;
  
  let score = 0;
  let lives = 3;
  let sessionIndex = 0;
  let sessionQuestions = [];
  let answered = false;

  let wrongList = JSON.parse(localStorage.getItem('quiz_wrong_list') || '[]');
  let selectedUnits = new Set();

  function questionKey(item) {
    // Content stays stable when source files reorder and numeric IDs change.
    return JSON.stringify([
      normalizeAnswer(repairExpression(item.expression)),
      String(item.meaning || '').normalize('NFKC').trim().replace(/\s+/g, ' ')
    ]);
  }

  function uniqueQuestions(items) {
    return [...new Map(items.map(item => [questionKey(item), item])).values()];
  }

  function reconcileWrongList(saved, latest) {
    return uniqueQuestions(saved.map(old => {
      const expression = normalizeAnswer(repairExpression(old.expression));
      const matches = latest.filter(item =>
        normalizeAnswer(repairExpression(item.expression)) === expression);
      // Prefer the original lesson and meaning; allow a corrected meaning.
      return matches.find(item => item.unit === old.unit && questionKey(item) === questionKey(old))
        || matches.find(item => item.unit === old.unit)
        || matches.find(item => questionKey(item) === questionKey(old));
    }).filter(Boolean));
  }

  function saveWrongList() {
    wrongList = uniqueQuestions(wrongList);
    localStorage.setItem('quiz_wrong_list', JSON.stringify(wrongList));
    document.getElementById('wrong-badge').innerText = wrongList.length;
  }

  function compareUnits(a, b) {
    const ma = a.match(/\d+/), mb = b.match(/\d+/);
    if (ma && mb) {
      const byNumber = Number(mb[0]) - Number(ma[0]);
      if (byNumber) return byNumber;
      const suffixA = a.slice(ma.index + ma[0].length).trim();
      const suffixB = b.slice(mb.index + mb[0].length).trim();
      return suffixA.localeCompare(suffixB, 'en', {sensitivity: 'base'}) ||
        a.localeCompare(b, 'en', {sensitivity: 'base'});
    }
    if (ma) return -1;
    if (mb) return 1;
    return a.localeCompare(b, 'en', {sensitivity: 'base'});
  }

  function initFiles() {
    const rawData = window.expressionsData || [];
    const container = document.getElementById('file-list-container');
    container.innerHTML = '';
    
    const unitMap = new Map();
    rawData.forEach(item => {
      if (!unitMap.has(item.unit)) {
        unitMap.set(item.unit, item.last_modified || 0);
      }
    });

    [...unitMap.keys()].sort(compareUnits).forEach(unit => {
      selectedUnits.add(unit);
      const div = document.createElement('div');
      div.className = 'file-item';
      
      div.innerHTML = `<input type="checkbox" checked value="${unit}" onchange="onUnitToggle(this)"> <span>${unit}</span>`;
      container.appendChild(div);
    });

    saveWrongList();
  }

  function toggleAllFiles(status) {
    selectedUnits.clear();
    const cbs = document.querySelectorAll('#file-list-container input[type="checkbox"]');
    cbs.forEach(cb => {
      cb.checked = status;
      if (status) selectedUnits.add(cb.value);
    });
    startSession();
  }

  function onUnitToggle(cb) {
    if (cb.checked) selectedUnits.add(cb.value);
    else selectedUnits.delete(cb.value);
    startSession();
  }

  function setMode(mode) {
    currentMode = mode;
    document.getElementById('mode-normal').classList.toggle('active', mode === 'normal');
    document.getElementById('mode-wrong').classList.toggle('active', mode === 'wrong');
    
    if (mode === 'wrong' && wrongList.length === 0) {
      alert("🎉 저장된 오답이 없습니다! 스마트 출제 모드로 전환합니다.");
      setMode('normal');
      return;
    }
    startSession();
  }

  function setQuizType(type) {
    quizType = type;
    document.getElementById('type-fill').classList.toggle('active', type === 'fill');
    document.getElementById('type-subjective').classList.toggle('active', type === 'subjective');
    document.getElementById('type-choice').classList.toggle('active', type === 'choice');
    startSession();
  }

  function setLimit(num) {
    sessionLimit = num;
    document.querySelectorAll('.session-bar .count-btn').forEach(btn => {
      btn.classList.toggle('active', btn.innerText.includes(num === 999 ? 'MAX' : num));
    });
    startSession();
  }

  function getFilteredPool() {
    let pool = (window.expressionsData || []).filter(item => selectedUnits.has(item.unit));
    if (currentMode === 'wrong') {
      const wrongKeys = new Set(wrongList.map(questionKey));
      pool = pool.filter(item => wrongKeys.has(questionKey(item)));
    }
    return pool;
  }

  function startSession() {
    // Snapshot and shuffle once; never draw a question twice in this session.
    const unique = new Map();
    getFilteredPool().forEach(item => {
      const key = questionKey(item);
      if (!unique.has(key)) unique.set(key, item);
    });
    sessionQuestions = [...unique.values()];
    for (let i = sessionQuestions.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [sessionQuestions[i], sessionQuestions[j]] = [sessionQuestions[j], sessionQuestions[i]];
    }
    if (sessionLimit !== 999) sessionQuestions = sessionQuestions.slice(0, sessionLimit);
    const typeLabel = {fill: '빈칸', subjective: '주관식', choice: '객관식'}[quizType];
    document.getElementById('settings-summary').textContent =
      `· ${selectedUnits.size}개 노트 / ${typeLabel} / ${sessionQuestions.length}문제`;
    sessionIndex = 0;
    score = 0;
    lives = 3;
    document.getElementById('score-val').innerText = score;
    document.getElementById('lives-display').innerText = '❤️❤️❤️';
    document.getElementById('stage-num').innerText = '0';
    document.getElementById('progress-bar').style.width = '0%';
    loadNextQuestion();
  }

  function loadNextQuestion() {
    const pool = getFilteredPool();
    currentQuestion = null;
    answered = false;
    document.getElementById('next-btn').style.display = 'none';
    document.getElementById('result-box').style.display = 'none';
    document.getElementById('hint-box').style.display = 'none';
    document.getElementById('hint-btn').style.display = 'none';

    if (sessionIndex >= sessionQuestions.length) {
      document.getElementById('question-text').innerHTML = sessionQuestions.length
        ? `🎉 세션 완료!<br><br>총 ${sessionQuestions.length}문제를 모두 풀었습니다.<br>최종 SCORE: ${score}`
        : "선택된 파일에 학습 데이터가 없습니다. 노트를 체크해 주세요!";
      document.getElementById('input-group').style.display = 'none';
      document.getElementById('mc-container').style.display = 'none';
      return;
    }

    currentQuestion = sessionQuestions[sessionIndex++];
    document.getElementById('stage-num').innerText = `${sessionIndex} / ${sessionQuestions.length}`;

    document.getElementById('unit-tag').innerText = currentQuestion.unit;

    // 모드별 화면 구성
    if (quizType === 'choice') {
      document.getElementById('input-group').style.display = 'none';
      document.getElementById('mc-container').style.display = 'flex';
      setupMultipleChoice(currentQuestion, pool);
    } else {
      document.getElementById('input-group').style.display = 'flex';
      document.getElementById('mc-container').style.display = 'none';
      
      const inputEl = document.getElementById('user-input');
      inputEl.value = '';
      inputEl.disabled = false;
      document.getElementById('submit-btn').disabled = false;
      inputEl.focus();

      if (quizType === 'fill') {
        setupFillBlank(currentQuestion);
      } else if (quizType === 'subjective') {
        document.getElementById('question-text').innerHTML = `💡 다음 뜻에 알맞은 영어 표현을 적으세요:<br><br>"<strong style="color:#f59e0b;">${currentQuestion.meaning}</strong>"`;
        document.getElementById('hint-btn').style.display = 'block';
      }
    }
  }

  function setupFillBlank(q) {
    const words = q.expression.split(' ');
    if (words.length > 1) {
      const blankIdx = Math.floor(Math.random() * words.length);
      const targetWord = words[blankIdx];
      const maskedWords = words.map((w, idx) => idx === blankIdx ? '____' : w);
      q._targetWord = targetWord;
      document.getElementById('question-text').innerHTML = `💬 빈칸에 들어갈 단어를 채우세요:<br><br>"<strong style="color:#38bdf8; font-size:20px;">${maskedWords.join(' ')}</strong>"<br><br><small style="color:#94a3b8;">뜻: ${q.meaning}</small>`;
    } else {
      q._targetWord = q.expression;
      document.getElementById('question-text').innerHTML = `💬 빈칸에 들어갈 표현을 적으세요:<br><br>"<strong style="color:#38bdf8; font-size:20px;">[   ____   ]</strong>"<br><br><small style="color:#94a3b8;">뜻: ${q.meaning}</small>`;
    }
  }

  function showHint() {
    if (!currentQuestion) return;
    const words = currentQuestion.expression.split(' ');
    const hintStr = words.map(w => {
      if (w.length <= 1) return w;
      return w[0] + ' ' + '_ '.repeat(w.length - 1).trim();
    }).join('   ');
    
    const box = document.getElementById('hint-box');
    box.innerText = `힌트: ${hintStr}`;
    box.style.display = 'block';
  }

  function setupMultipleChoice(q, pool) {
    document.getElementById('question-text').innerHTML = `💡 다음 뜻에 알맞은 영어 표현을 고르세요:<br><br>"<strong style="color:#f59e0b;">${q.meaning}</strong>"`;
    
    let choices = [q.expression];
    let allExpressions = (window.expressionsData || []).map(i => i.expression).filter(e => e !== q.expression);
    
    while (choices.length < 4 && allExpressions.length > 0) {
      const rIdx = Math.floor(Math.random() * allExpressions.length);
      choices.push(allExpressions[rIdx]);
      allExpressions.splice(rIdx, 1);
    }
    
    choices.sort(() => Math.random() - 0.5);

    const container = document.getElementById('mc-container');
    container.innerHTML = '';
    choices.forEach((cText, idx) => {
      const btn = document.createElement('button');
      btn.className = 'mc-btn';
      btn.innerHTML = `<strong>${idx+1}.</strong> ${cText}`;
      btn.onclick = () => evaluateAnswer(cText);
      container.appendChild(btn);
    });
  }

  function submitAnswer() {
    const val = document.getElementById('user-input').value.trim();
    if (!val) return;
    evaluateAnswer(val);
  }

  function normalizeAnswer(value) {
    return String(value).normalize('NFKC')
      .replace(/[‘’ʼ＇`´]/g, "'")
      .trim().replace(/[.。]+$/u, '').trim().replace(/\s+/g, ' ').toLowerCase();
  }

  function repairExpression(value) {
    return String(value).replace(/[‘’ʼ＇`´]/g, "'")
      .replace(/\b[liI](?='(?:m|d|ll|ve)\b)/g, 'I')
      .replace(/\b[li](?=\s|[.!?,;:]|$)/g, 'I');
  }

  function evaluateAnswer(userVal) {
    if (!currentQuestion || answered) return;
    answered = true;
    document.getElementById('quiz-settings').open = false;
    document.getElementById('progress-bar').style.width = `${Math.round(sessionIndex / sessionQuestions.length * 100)}%`;
    const resultBox = document.getElementById('result-box');
    const uVal = normalizeAnswer(userVal);
    
    let isCorrect = false;
    let targetAnswer = currentQuestion.expression;

    if (quizType === 'fill' && currentQuestion._targetWord) {
      const targetW = normalizeAnswer(currentQuestion._targetWord);
      if (uVal === targetW || uVal === normalizeAnswer(currentQuestion.expression)) {
        isCorrect = true;
      }
    } else {
      if (uVal === normalizeAnswer(targetAnswer)) {
        isCorrect = true;
      }
    }

    if (isCorrect) {
      score += 10;
      document.getElementById('score-val').innerText = score;
      resultBox.className = 'result-box correct';

      // ⭐️ 오답노트 모드에서 맞히면 오답노트에서 해당 문제 자동 삭제!
      if (currentMode === 'wrong') {
        wrongList = wrongList.filter(item => questionKey(item) !== questionKey(currentQuestion));
        saveWrongList();
        resultBox.innerHTML = `🎉 정답입니다! (오답노트에서 삭제됨)<br>정답: <strong>${currentQuestion.expression}</strong>`;
      } else {
        resultBox.innerHTML = `🎉 정답입니다!<br>정답: <strong>${currentQuestion.expression}</strong>`;
      }
    } else {
      lives--;
      let hearts = '❤️'.repeat(Math.max(0, lives));
      document.getElementById('lives-display').innerText = hearts || '💀';
      
      resultBox.className = 'result-box wrong';
      resultBox.innerHTML = `❌ 아쉽네요!<br>입력답: ${userVal}<br>정답: <strong>${currentQuestion.expression}</strong>`;
      
      // 오답노트에 추가
      if (!wrongList.some(item => questionKey(item) === questionKey(currentQuestion))) {
        wrongList.push(currentQuestion);
        saveWrongList();
      }
    }

    resultBox.style.display = 'block';
    
    if (quizType !== 'choice') {
      document.getElementById('user-input').disabled = true;
      document.getElementById('submit-btn').disabled = true;
    } else {
      document.querySelectorAll('.mc-btn').forEach(btn => btn.disabled = true);
    }

    document.getElementById('next-btn').style.display = 'block';
    document.getElementById('next-btn').focus({preventScroll: true});
  }

  function nextQuestion() {
    if (!currentQuestion || !answered) return;
    loadNextQuestion();
  }

  function handleQuizKey(event) {
    // Ignore held keys and IME confirmation (e.g. Korean composition).
    if (event.repeat || event.isComposing || event.keyCode === 229 ||
        event.ctrlKey || event.altKey || event.metaKey || event.shiftKey) return;
    const target = event.target;
    if (target && target.closest && target.closest('#quiz-settings')) return;
    if (!currentQuestion) return;
    if (event.key === 'Enter') {
      if (answered) {
        event.preventDefault();
        nextQuestion();
      } else if (quizType !== 'choice' &&
                 (!target || target.id === 'user-input' || target.id === 'submit-btn' ||
                  target === document.body)) {
        event.preventDefault();
        submitAnswer();
      }
    } else if (quizType === 'choice' && !answered && /^[1-4]$/.test(event.key)) {
      const button = document.querySelectorAll('.mc-btn')[Number(event.key) - 1];
      if (button && !button.disabled) {
        event.preventDefault();
        button.click();
      }
    }
  }
  document.addEventListener('keydown', handleQuizKey);

  // Reconcile saved mistakes with regenerated source data; IDs can change.
  const latestData = window.expressionsData || [];
  latestData.forEach(item => { item.expression = repairExpression(item.expression); });
  wrongList = reconcileWrongList(wrongList, latestData);

  // 초기화
  initFiles();
  startSession();
</script>

</body>
</html>
"""
    with open(QUIZ_HTML, "w", encoding="utf-8") as f:
        f.write(html_code)
    with open(QUIZ_HTML_ALT, "w", encoding="utf-8") as f:
        f.write(html_code)
    print("✨ 레트로 테마 'index.html' & 'quiz.html' 생성 완료!")

def sync_to_github():
    print("\n🌐 GitHub repository로 자동 커밋 및 푸시를 진행합니다...")
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Auto-update quiz data from Obsidian"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("🚀 GitHub Pages 업로드 성공! 모바일 웹페이지가 최신화되었습니다.")
    except Exception as e:
        print(f"⚠️ Git 작업 중 안내: {e}")
        print("💡 수동 푸시 필요시 터미널에서 'git pull origin main --rebase' 후 'git push origin main'을 실행해주세요.")

if __name__ == "__main__":
    update_learning_data()
    create_retro_html()
    sync_to_github()
    
    if os.path.exists(QUIZ_HTML):
        webbrowser.open(os.path.abspath(QUIZ_HTML))
