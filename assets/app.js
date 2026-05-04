/**
 * OpenJLPT Unified Logic
 */

const SECTION_CONFIG = { "vocab_reading": {s:1, count:5}, "vocab_kanji": {s:2, count:5}, "vocab_context": {s:3, count:7}, "vocab_synonym": {s:4, count:5}, "vocab_usage": {s:5, count:5}, "grammar_fill": {s:6, count:12}, "grammar_order": {s:7, count:5}, "grammar_passage": {s:8, count:null}, "reading_short": {s:9, count:null}, "reading_medium": {s:10, count:null}, "reading_long": {s:11, count:null}, "reading_search": {s:12, count:null} };
const STORAGE_KEY_PREFIX = 'openjlpt_exam_';
let STORAGE_KEY = '';

let QUESTIONS = window.QUESTIONS || [];
let savedSelectedIndices = [], answered = 0, score = 0, selections = [], results = [], totalQuestions = 0;

function wrapTargetWord(s, t) { if (!t || !s) return s; return s.includes(`《${t}》`) ? s.replace(`《${t}》`, `<span class="target-word">${t}</span>`) : (s.includes(t) ? s.replace(t, `<span class="target-word">${t}</span>`) : s); }
function highlightBlanks(t) { return t ? t.replace(/★/g, '<span class="target-word">★</span>').replace(/（[ 　\d]*）/g, m => `<span class="target-word">${m}</span>`) : t; }
function tryExtractTarget(s, o, a) { if (!s || !o || a===undefined) return s; const w = o[a], st = w.replace(/[するだです]+$/, ''); const cs = [w]; if (st!==w) cs.unshift(st); for (const c of cs) if (s.includes(c)) return s.replace(c, '<span class="target-word">（　）</span>'); return s; }

// --- IndexedDB Cache Manager ---
const DB_NAME = "OpenJLPT_Cache";
const STORE_NAME = "questions";
const dbPromise = new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => req.result.createObjectStore(STORE_NAME);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
});

const DataCache = {
    async get(key) {
        const db = await dbPromise;
        return new Promise(r => {
            const req = db.transaction(STORE_NAME).objectStore(STORE_NAME).get(key);
            req.onsuccess = () => r(req.result);
        });
    },
    async set(key, val) {
        const db = await dbPromise;
        const tx = db.transaction(STORE_NAME, "readwrite");
        tx.objectStore(STORE_NAME).put(val, key);
    },
    async hasData(level) {
        const firstFile = Object.keys(SECTION_CONFIG)[0];
        const data = await this.get(`${level}_${firstFile}`);
        return !!data;
    }
};

async function syncFromCloud() {
    const level = window.CURRENT_LEVEL || 'n2';
    const overlay = document.getElementById('sync-overlay');
    const progress = document.getElementById('sync-progress-bar');
    const logTitle = document.getElementById('sync-log');
    const logDetails = document.getElementById('sync-log-details');
    
    if (overlay) overlay.style.display = 'flex';
    if (logDetails) logDetails.innerHTML = '';
    
    const addLog = (msg, type='') => {
        if (!logDetails) return;
        const line = document.createElement('div');
        line.className = 'sync-log-line ' + type;
        line.textContent = `> ${msg}`;
        logDetails.appendChild(line);
        logDetails.scrollTop = logDetails.scrollHeight;
    };

    addLog(`同期プロセスの開始: LEVEL ${level.toUpperCase()}`);
    addLog(`GitHub リポジトリに接続中...`);
    
    const ids = Object.keys(SECTION_CONFIG);
    let updatedCount = 0;
    
    for (let i = 0; i < ids.length; i++) {
        const id = ids[i];
        addLog(`チェック中: ${id}...`);
        
        try {
            const url = `https://raw.githubusercontent.com/iamcheyan/openJLPT/master/data/${level}/${id}.json`;
            const r = await fetch(url);
            if (r.ok) {
                const json = await r.json();
                const local = await DataCache.get(`${level}_${id}`);
                
                // コンテンツの比較
                if (local && JSON.stringify(local) === JSON.stringify(json)) {
                    addLog(`${id}: 最新の状態です`, 'ok');
                } else {
                    await DataCache.set(`${level}_${id}`, json);
                    addLog(`${id}: データを更新しました`, 'new');
                    updatedCount++;
                }
            }
        } catch (e) { 
            addLog(`${id}: 取得エラー`, 'err');
        }
        
        if (progress) progress.style.width = ((i + 1) / ids.length * 100) + "%";
        await new Promise(res => setTimeout(res, 150)); // E-inkフレンドリーな待機
    }

    if (updatedCount > 0) {
        addLog(`同期完了: ${updatedCount} 個のセクションを更新しました`);
        if (logTitle) logTitle.textContent = "同期完了";
    } else {
        addLog(`すべてのデータはすでに最新の状態です`);
        if (logTitle) logTitle.textContent = "更新なし";
    }
    
    addLog(`アプリケーションを再起動しています...`);
    setTimeout(() => window.location.reload(), 2000);
}

// UI Utilities
function toggleFurigana() { document.body.classList.toggle('hide-furigana', !document.getElementById('furigana-toggle').checked); localStorage.setItem('openjlpt_furigana', document.getElementById('furigana-toggle').checked); }

// Base path for data - can be overridden by the host (e.g., an Android app shell)
window.DATA_ROOT = window.DATA_ROOT || 'data';

async function loadExamData() {
    const level = new URLSearchParams(window.location.search).get('level') || 'n2';
    window.CURRENT_LEVEL = level;
    STORAGE_KEY = STORAGE_KEY_PREFIX + (window.EXAM_MODE === 'full' ? 'full_' : '') + level;
    
    if (document.getElementById('exam-title')) {
        document.getElementById('exam-title').textContent = `JLPT ${level.toUpperCase()} ${window.EXAM_MODE === 'full' ? '(Full)' : ''}`;
    }

    // Check Cache first
    const hasCache = await DataCache.hasData(level);
    if (!hasCache && QUESTIONS.length === 0) {
        // Probe if local data is available (e.g., on a real server)
        console.log("No cache found, probing local files...");
        try {
            const firstFile = Object.keys(SECTION_CONFIG)[0];
            const probe = await fetch(`${window.DATA_ROOT}/${level}/${firstFile}.json`);
            if (!probe.ok) throw new Error();
            console.log("Local files found. Skipping sync prompt.");
        } catch (e) {
            console.log("No local data found. Showing sync prompt.");
            const prompt = document.getElementById('sync-prompt');
            const loading = document.getElementById('loading-overlay');
            if (loading) loading.style.display = 'none';
            if (prompt) prompt.style.display = 'flex';
            return;
        }
    }

    if (QUESTIONS.length > 0) {
        console.log("Using pre-loaded questions.");
        await finishLoading();
        return;
    }

    console.log(`Fetching questions for ${level}...`);
    const all = []; const stats = {};
    const promises = Object.keys(SECTION_CONFIG).map(async id => {
        const cfg = SECTION_CONFIG[id];
        try {
            let r, d;
            // 1. Try Cache
            d = await DataCache.get(`${level}_${id}`);
            if (!d) {
                // 2. Try Local File
                try {
                    r = await fetch(`${window.DATA_ROOT}/${level}/${id}.json`);
                    if (r.ok) d = await r.json();
                } catch(e) {}
            }
            if (!d) return;

            const raw = d.questions || []; const proc = [];
            if (id === "grammar_passage") raw.forEach(it => { const p = highlightBlanks(it.passage || ""); (it.blanks || []).forEach(b => proc.push({ s:cfg.s, pas:p, txt:`（　${b.num}　）`, opts:b.options||[], ans:b.answer||0, exp:b.explanation||"", translation:b.translation })); });
            else if (id.startsWith("reading_")) {
                raw.forEach(it => {
                    const p = it.passage || it.content || "";
                    const qList = it.questions || it.questionList || (it.question ? [it] : []);
                    qList.forEach(q => {
                        const qTxt = q.question || q.text || "";
                        if (qTxt) proc.push({ s:cfg.s, pas:p, txt:qTxt, opts:q.options||[], ans:q.answer||0, exp:q.explanation||"", translation:q.translation || it.translation });
                    });
                });
            }
            else if (id === "grammar_order") raw.forEach(q => { const f = q.fragments || q.options || [], sp = f.map((v, i) => `${['１','２','３','４'][i]}. ${v}`); proc.push({ s:cfg.s, txt:highlightBlanks(q.sentence||""), star:sp.join("　"), opts:f, ans:q.answer||0, exp:q.explanation||"", translation:q.translation }); });
            else raw.forEach(q => { let tx = q.sentence || ""; const t = q.target || "", o = q.options || [], a = q.answer || 0; if (id==="vocab_usage") tx = `<span class="target-word">${t}</span>`; else if (["vocab_reading","vocab_kanji","vocab_synonym"].includes(id)) tx = wrapTargetWord(tx, t); else if (id==="vocab_context") { tx = highlightBlanks(tx); if (!tx.includes('target-word')) tx = tryExtractTarget(tx, o, a); } else if (id==="grammar_fill") tx = highlightBlanks(tx); proc.push({ s:cfg.s, txt:tx, opts:o, ans:a, exp:q.explanation||"", translation:q.translation }); });
            
            if (proc.length > 0) {
                all.push(...proc);
                stats[id] = { s:cfg.s, total:proc.length, name:d.meta?d.meta.name:id };
                document.getElementById(`section-${cfg.s}-wrap`)?.style.setProperty('display', 'block'); 
            } else {
                document.getElementById(`section-${cfg.s}-wrap`)?.style.setProperty('display', 'none');
            }
        } catch(e) { console.error("Error loading " + id, e); }
    });
    await Promise.all(promises); 
    all.sort((a, b) => a.s - b.s);
    window.BANK_STATS = stats; QUESTIONS = all;
    await finishLoading();
}

async function finishLoading() {
    selectExamQuestions(); 
    await buildUI(); 
    initNav(); 
    initLevelSwitcher();
}

function selectExamQuestions() {
    if (!QUESTIONS.length) return;
    const saved = tryLoadState();
    if (saved && saved.selectedIndices?.length) { savedSelectedIndices = saved.selectedIndices; QUESTIONS = savedSelectedIndices.map(i => QUESTIONS[i]).filter(Boolean); return; }
    
    // If Full mode, don't sample
    if (window.EXAM_MODE === 'full') {
        savedSelectedIndices = QUESTIONS.map((_, i) => i);
        saveState();
        return;
    }

    const LIMITS = { 
        "1": 5, "2": 5, "3": 5, "4": 7, "5": 5, "6": 17, "7": 5, "8": 5, "9": 5, "10": 9, "11": 5, "12": 2 
    };
    const byS = {}; QUESTIONS.forEach((q, i) => { if (!byS[q.s]) byS[q.s] = []; byS[q.s].push(i); });
    const sel = [];
    console.log("Section counts in bank:", Object.fromEntries(Object.entries(byS).map(([s, ids]) => [s, ids.length])));
    
    // Explicitly iterate 1-12 to ensure no section is missed
    for (let s = 1; s <= 12; s++) {
        const ids = byS[s]; if (!ids) continue;
        const lim = LIMITS[String(s)];
        if (lim === undefined || lim >= ids.length) {
            sel.push(...ids);
        } else {
            const sh = ids.slice();
            for (let i = sh.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [sh[i], sh[j]] = [sh[j], sh[i]];
            }
            sel.push(...sh.slice(0, lim));
        }
    }
    sel.sort((a,b) => a-b); savedSelectedIndices = sel;
    saveState();
    QUESTIONS = sel.map(i => QUESTIONS[i]);
}

function tryLoadState() { try { return JSON.parse(localStorage.getItem(STORAGE_KEY)); } catch(e) { return null; } }
function saveState() { localStorage.setItem(STORAGE_KEY, JSON.stringify({ selectedIndices: savedSelectedIndices, selections: selections, answered: answered, score: score, timestamp: new Date().toISOString() })); }

function showCustomModal(t, b, acts) {
    document.getElementById('modal-title').innerText = t; document.getElementById('modal-body').innerText = b;
    const el = document.getElementById('modal-actions'); el.innerHTML = '';
    acts.forEach(a => { const btn = document.createElement('button'); btn.className = 'modal-btn ' + (a.primary?'modal-btn-primary':''); btn.innerText = a.label; btn.onclick = () => { document.getElementById('custom-modal').classList.remove('active'); a.onClick?.(); }; el.appendChild(btn); });
    document.getElementById('custom-modal').classList.add('active');
}

function refreshExam() {
    if (answered === 0) { localStorage.removeItem(STORAGE_KEY); location.reload(); return; }
    showCustomModal('更新の確認', '現在の進捗が削除されます。再生成しますか？', [{ label: 'キャンセル' }, { label: '確認', primary: true, onClick: () => { localStorage.removeItem(STORAGE_KEY); location.reload(); } }]);
}

function toggleStatsOverlay() {
    const ov = document.getElementById('stats-overlay'); if (!ov) return;
    if (!ov.classList.contains('open')) {
        const b = document.getElementById('stats-overlay-body'); b.innerHTML = ''; let gt = 0;
        const LBL = { 
            1:'① 漢字の読み方', 2:'② 漢字の表記', 3:'③ 文脈規定', 4:'④ 言い換え・類義', 
            5:'⑤ 用法', 6:'⑥ 文の文法', 7:'⑦ 文の組み立て', 8:'⑧ 文章の文法', 
            9:'⑨ 短文読解', 10:'⑩ 中文読解', 11:'⑪ 長文読解', 12:'⑫ 情報検索' 
        };
        Object.values(BANK_STATS || {}).sort((a,b)=>a.s-b.s).forEach(s => { 
            b.innerHTML += `<div class="stats-row"><span>${LBL[s.s]||s.name}</span><b>${s.total} 問</b></div>`; 
            gt += s.total; 
        });
        b.innerHTML += `<div class="stats-total-row"><span>合計</span><span>${gt} 問</span></div>`;
    }
    ov.classList.toggle('open');
}

function initLevelSwitcher() {
    const level = window.CURRENT_LEVEL || 'n2', levels = ['n1', 'n2', 'n3', 'n4', 'n5'];
    const trig = document.getElementById('level-select-trigger'), opts = document.getElementById('level-options'), wrap = document.getElementById('level-select-wrapper');
    if (!trig) return;
    trig.innerText = level.toUpperCase(); opts.innerHTML = '';
    levels.forEach(lv => { const o = document.createElement('div'); o.className = 'custom-option' + (lv === level ? ' selected' : ''); o.innerText = lv.toUpperCase(); o.onclick = () => { location.href = '?level=' + lv; }; opts.appendChild(o); });
    trig.onclick = (e) => { e.stopPropagation(); wrap.classList.toggle('open'); };
    document.addEventListener('click', () => wrap.classList.remove('open'));
}

let tokenizer = null;
async function initFurigana() {
    if (tokenizer || !window.kuromoji) return tokenizer;
    const ps = ['assets/libs/dict/', 'https://cdn.jsdelivr.net/npm/kuromoji@0.1.2/dict/'];
    for (const p of ps) { try { tokenizer = await new Promise((res, rej) => window.kuromoji.builder({ dicPath: p }).build((e, t) => e ? rej(e) : res(t))); return tokenizer; } catch (e) {} }
    return null;
}
function applyFurigana(h) {
    if (!tokenizer) return h; const ts = [];
    const pr = h.replace(/<rt>[\s\S]*?<\/rt>|<\/?ruby>|<\/?rt>/g, '').replace(/<span class=\"target-word\">[\s\S]*?<\/span>/g, m => { const k = `@@T${ts.length}@@`; ts.push(m); return k; });
    const cv = pr.split(/(<[^>]+>)/g).map(p => { if (!p || p.startsWith('<')) return p; return tokenizer.tokenize(p).map(t => { const s = t.surface_form || '', r = String(t.reading || '').replace(/[ァ-ン]/g, c => String.fromCharCode(c.charCodeAt(0) - 0x60)); return (/[一-龯々]/.test(s) && r && r !== '*' && r !== s) ? `<ruby>${s}<rt>${r}</rt></ruby>` : s; }).join(''); }).join('');
    return cv.replace(/@@T(\d+)@@/g, (_, i) => ts[i]);
}

async function buildUI() {
    await initFurigana(); totalQuestions = QUESTIONS.length; selections = new Array(totalQuestions).fill(null); results = new Array(totalQuestions).fill(null);
    const saved = tryLoadState(); if (saved?.selections) { for (let i = 0; i < Math.min(saved.selections.length, totalQuestions); i++) { if (saved.selections[i] !== null) { selections[i] = saved.selections[i]; results[i] = (selections[i] === QUESTIONS[i].ans); answered++; if (results[i]) score++; } } }
    document.getElementById('total').innerText = totalQuestions; document.getElementById('mobile-total').innerText = totalQuestions;
    QUESTIONS.forEach((q, i) => {
        const c = document.getElementById('section-' + q.s); if (!c) return;
        const b = document.createElement('div'); b.className = 'question-block'; b.id = 'q' + (i + 1);
        let h = ''; if (q.pas && (i === 0 || QUESTIONS[i-1].pas !== q.pas)) h += `<div class="passage">${applyFurigana(q.pas)}</div>`;
        h += `<div class="question-text">${i + 1}. ${applyFurigana(q.txt)}</div>`;
        if (q.star) h += `<div class="star-line">${applyFurigana(q.star)}</div>`;
        h += `<ul class="options">`;
        const opts = Array.isArray(q.opts) ? q.opts : [...(q.star || '').replace(/　/g, ' ').matchAll(/[１２３４1-4]\.\s*([^１２３４1-4]+?)(?=\s*[１２３４1-4]\.|$)/g)].map(m => m[1].trim());
        opts.forEach((o, oi) => { h += `<li onclick="check(${i + 1}, ${oi}, ${q.ans})">${oi + 1}. ${applyFurigana(o)}</li>`; });
        let ex = q.exp || `正解：${q.ans + 1}`; if (q.translation) ex += `<div style="margin-top:12px; padding-top:12px; border-top:2px dashed #000;"><b>【解説】</b><br>${q.translation}</div>`;
        h += `</ul><div class="explanation" id="exp${i + 1}">${ex}</div>`;
        b.innerHTML = h; c.appendChild(b);
    });
    document.getElementById('loading-overlay')?.classList.add('hidden');
}

function check(qN, sel, cor) { if (results[qN-1] !== null) return; results[qN-1] = (sel === cor); selections[qN-1] = sel; answered++; if (results[qN-1]) score++; document.getElementById('progress').innerText = answered; document.getElementById('score').innerText = score; document.getElementById('mobile-progress').innerText = answered; document.getElementById('mobile-score').innerText = score; const b = document.getElementById('q' + qN), ex = document.getElementById('exp' + qN), navA = document.getElementById('nav' + qN), os = b.querySelectorAll('.options li'); if (sel === cor) { os[sel].classList.add('correct'); navA.className = 'done-correct'; } else { os[sel].classList.add('wrong'); os[cor].classList.add('correct'); navA.className = 'done-wrong'; } ex.classList.add('show'); saveState(); }
function toggleSidebar() { if (window.matchMedia('(max-width: 900px)').matches) { document.body.classList.toggle('mobile-nav-open'); return; } document.body.classList.toggle('collapsed'); document.getElementById('toggle-btn').innerText = document.body.classList.contains('collapsed') ? '▶' : '◀'; }
function closeMobileNav() { document.body.classList.remove('mobile-nav-open'); }
function openMobileNav() { document.body.classList.add('mobile-nav-open'); }
function toggleFurigana() { const c = document.getElementById('furigana-toggle').checked; document.body.classList.toggle('show-furigana', c); localStorage.setItem('openjlpt_furigana', c ? '1' : '0'); }
function navigateQuestion(d) { const n = Math.min(totalQuestions, Math.max(1, 1 + d)); document.getElementById('q' + n)?.scrollIntoView({ behavior: 'auto', block: 'start' }); }
function initNav() {
    const n = document.getElementById('nav'); n.innerHTML = '';
    const LBL = { 
        1:'① 漢字の読み方', 2:'② 漢字の表記', 3:'③ 文脈規定', 4:'④ 言い換え・類義', 
        5:'⑤ 用法', 6:'⑥ 文の文法', 7:'⑦ 文の組み立て', 8:'⑧ 文章の文法', 
        9:'⑨ 短文読解', 10:'⑩ 中文読解', 11:'⑪ 長文読解', 12:'⑫ 情報検索' 
    };
    let currentS = -1; let currentGrid = null;
    QUESTIONS.forEach((q, i) => {
        if (q.s !== currentS) {
            currentS = q.s;
            const title = document.createElement('div'); title.className = 'nav-section-title'; title.innerText = LBL[currentS] || 'Section ' + currentS;
            n.appendChild(title);
            currentGrid = document.createElement('div'); currentGrid.className = 'nav-grid';
            n.appendChild(currentGrid);
        }
        const a = document.createElement('a'); a.innerText = i + 1; a.id = 'nav' + (i + 1); a.href = '#q' + (i + 1); a.onclick = closeMobileNav;
        currentGrid.appendChild(a);
        if (selections[i] !== null) a.className = results[i] ? 'done-correct' : 'done-wrong';
    });
}

function triggerManualSync() {
    showCustomModal('データの同期', 'クラウドから最新の問題データを取得します。現在の学習進捗はリセットされますが、よろしいですか？', [
        { label: 'キャンセル' },
        { label: '更新を実行', primary: true, onClick: () => { syncFromCloud(); } }
    ]);
}

// Global Init
window.addEventListener('DOMContentLoaded', () => {
    if (localStorage.getItem('openjlpt_furigana') === '1') { document.body.classList.add('show-furigana'); if(document.getElementById('furigana-toggle')) document.getElementById('furigana-toggle').checked = true; }
    loadExamData();
});
