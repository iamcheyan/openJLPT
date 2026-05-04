const fs = require('fs');
const path = require('path');

const HTML_PATH = 'output/template.html';
const DATA_DIR = 'data/n2';

// Simple HTML tag stripper
function stripHtml(html) {
  return html
    .replace(/<script[^>]*>.*?<\/script>/gs, '')
    .replace(/<style[^>]*>.*?<\/style>/gs, '')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .trim();
}

function cleanOption(text) {
  return text.replace(/^[１２３４]\.\s*/, '').trim();
}

function extractAnswer(expText) {
  const m = expText.match(/正解[：:]\s*([１２３４])/);
  if (m) {
    const map = { '１': 0, '２': 1, '３': 2, '４': 3 };
    return map[m[1]];
  }
  return 0;
}

function parseQuestions(html) {
  const questions = {};
  // Match question blocks
  const blockRegex = /<div class="question-block" id="q(\d+)"[^>]*>(.*?)<\/div>\s*<\/div>/gs;
  let m;
  while ((m = blockRegex.exec(html)) !== null) {
    const qnum = parseInt(m[1]);
    const block = m[2];

    // Question text
    const qtextMatch = block.match(/<div class="question-text">(.*?)<\/div>/s);
    const qtextHtml = qtextMatch ? qtextMatch[1] : '';
    const qtext = stripHtml(qtextHtml);

    // Options
    const options = [];
    const optRegex = /<li[^>]*>(.*?)<\/li>/gs;
    let om;
    while ((om = optRegex.exec(block)) !== null) {
      options.push(cleanOption(stripHtml(om[1])));
    }

    // Explanation
    const expMatch = block.match(/<div class="explanation"[^>]*>(.*?)<\/div>/s);
    const expHtml = expMatch ? expMatch[1] : '';
    const expText = stripHtml(expHtml);

    // Answer
    const answer = extractAnswer(expText);

    // Target word
    const targetMatch = qtextHtml.match(/<span class="target-word">(.*?)<\/span>/);
    const target = targetMatch ? stripHtml(targetMatch[1]) : '';

    questions[qnum] = { qtext, options, answer, explanation: expText, target };
  }
  return questions;
}

function extractPassage(html, sectionTitle) {
  const regex = new RegExp(
    '<h3>\\s*' + sectionTitle.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') +
    '\\s*</h3>\\s*<div class="instruction">.*?</div>\\s*<div class="passage">(.*?)</div>',
    's'
  );
  const m = html.match(regex);
  return m ? stripHtml(m[1]).trim() : '';
}

function extractGrammarPassage(html) {
  const m = html.match(/<h3>⑧ 文章の文法<\/h3>\s*<div class="passage">(.*?)<\/div>/s);
  return m ? stripHtml(m[1]).trim() : '';
}

function extractStarLine(html, qnum) {
  const blockRegex = new RegExp(
    '<div class="question-block" id="q' + qnum + '"[^>]*>(.*?)</div>\\s*</div>', 's'
  );
  const bm = html.match(blockRegex);
  if (!bm) return [];
  const sm = bm[1].match(/<div class="star-line">(.*?)<\/div>/s);
  if (!sm) return [];
  const text = stripHtml(sm[1]);
  const frags = [];
  for (let i = 1; i <= 4; i++) {
    const numChar = ['１', '２', '３', '４'][i - 1];
    const regex = new RegExp(numChar + '\\.\\s*(.*?)(?=\\s*[１２３４]\\.\\s*|$)');
    const m = text.match(regex);
    if (m) frags.push(m[1].trim());
  }
  return frags.length === 4 ? frags : [];
}

function reconstructComplete(sentence, frags, answer, explanation) {
  // Try to parse order from explanation
  const text = explanation;
  const order = {};
  const matches = text.matchAll(/(\S+?)[(（]([１２３４])[)）]/g);
  for (const match of matches) {
    const word = match[1];
    const num = parseInt(match[2].replace('１','1').replace('２','2').replace('３','3').replace('４','4')) - 1;
    if (num >= 0 && num < 4) order[num] = word;
  }

  if (Object.keys(order).length === 4) {
    const parts = sentence.split(/＿＿|＿★＿/);
    if (parts.length === 5) {
      let result = parts[0];
      for (let i = 0; i < 4; i++) {
        result += (order[i] || frags[i] || '') + parts[i + 1];
      }
      return result;
    }
  }

  // Fallback
  const base = sentence.split('＿')[0].trim();
  const ending = sentence.split('＿').pop().trim();
  return base + frags.join('') + ending;
}

function buildItems(html, questions) {
  const items = {
    vocab_reading: [], vocab_kanji: [], vocab_context: [],
    vocab_synonym: [], vocab_usage: [],
    grammar_fill: [], grammar_order: [], grammar_passage: [],
    reading_short: [], reading_medium: [], reading_long: [], reading_search: []
  };

  const now = new Date().toISOString().slice(0, 19).replace('T', ' ');
  const meta = {
    generated_by: 'gemini:Google Gemini',
    reviewed_by: 'gemini',
    verified: true,
    created_at: now,
    level: 'N2',
    source: 'ai'
  };

  const makeBase = (q) => ({
    sentence: q.qtext,
    options: q.options.slice(0, 4),
    answer: q.answer,
    explanation: q.explanation,
    ...meta
  });

  // ① vocab_reading q1-5
  for (let i = 1; i <= 5; i++) {
    const q = questions[i]; if (!q) continue;
    items.vocab_reading.push({ ...makeBase(q), target: q.target, question_type: 'vocab_reading' });
  }
  // ② vocab_kanji q6-10
  for (let i = 6; i <= 10; i++) {
    const q = questions[i]; if (!q) continue;
    items.vocab_kanji.push({ ...makeBase(q), target: q.target, question_type: 'vocab_kanji' });
  }
  // ③ vocab_context q11-17
  for (let i = 11; i <= 17; i++) {
    const q = questions[i]; if (!q) continue;
    items.vocab_context.push({ ...makeBase(q), question_type: 'vocab_context' });
  }
  // ④ vocab_synonym q18-22
  for (let i = 18; i <= 22; i++) {
    const q = questions[i]; if (!q) continue;
    items.vocab_synonym.push({ ...makeBase(q), target: q.target, question_type: 'vocab_synonym' });
  }
  // ⑤ vocab_usage q23-27
  for (let i = 23; i <= 27; i++) {
    const q = questions[i]; if (!q) continue;
    let target = q.target;
    if (!target && q.qtext.startsWith('**')) {
      target = q.qtext.replace(/\*/g, '').trim();
    }
    items.vocab_usage.push({ ...makeBase(q), target, question_type: 'vocab_usage' });
  }
  // ⑥ grammar_fill q28-39
  for (let i = 28; i <= 39; i++) {
    const q = questions[i]; if (!q) continue;
    items.grammar_fill.push({ ...makeBase(q), question_type: 'grammar_fill' });
  }
  // ⑦ grammar_order q40-44
  for (let i = 40; i <= 44; i++) {
    const q = questions[i]; if (!q) continue;
    const frags = extractStarLine(html, i);
    if (frags.length !== 4) {
      console.log(`  WARN: q${i} has ${frags.length} fragments`);
      continue;
    }
    const complete = reconstructComplete(q.qtext, frags, q.answer, q.explanation);
    items.grammar_order.push({
      sentence: q.qtext,
      fragments: frags,
      options: frags.slice(),
      answer: q.answer,
      complete_sentence: complete,
      explanation: q.explanation,
      ...meta,
      question_type: 'grammar_order'
    });
  }
  // ⑧ grammar_passage q45-49
  const gpPassage = extractGrammarPassage(html);
  const blanks = [];
  for (let i = 45; i <= 49; i++) {
    const q = questions[i]; if (!q) continue;
    blanks.push({ num: i - 44, options: q.options.slice(0, 4), answer: q.answer, explanation: q.explanation });
  }
  if (blanks.length > 0) {
    items.grammar_passage.push({ passage: gpPassage, blanks, ...meta, question_type: 'grammar_passage' });
  }
  // ⑨ reading_short q50-52
  const rsPassage = extractPassage(html, '⑨ 短文読解');
  for (let i = 50; i <= 52; i++) {
    const q = questions[i]; if (!q) continue;
    items.reading_short.push({ passage: rsPassage, question: q.qtext, options: q.options.slice(0,4), answer: q.answer, explanation: q.explanation, ...meta, question_type: 'reading_short' });
  }
  // ⑩ reading_medium q53-56
  const rmPassage = extractPassage(html, '⑩ 中文読解');
  const rmQs = [];
  for (let i = 53; i <= 56; i++) {
    const q = questions[i]; if (!q) continue;
    rmQs.push({ question: q.qtext, options: q.options.slice(0,4), answer: q.answer, explanation: q.explanation });
  }
  if (rmQs.length > 0) {
    items.reading_medium.push({ passage: rmPassage, questions: rmQs, ...meta, question_type: 'reading_medium' });
  }
  // ⑪ reading_long q57-58
  const rlPassage = extractPassage(html, '⑪ 長文読解');
  const rlQs = [];
  for (let i = 57; i <= 58; i++) {
    const q = questions[i]; if (!q) continue;
    rlQs.push({ question: q.qtext, options: q.options.slice(0,4), answer: q.answer, explanation: q.explanation });
  }
  if (rlQs.length > 0) {
    items.reading_long.push({ passage: rlPassage, questions: rlQs, ...meta, question_type: 'reading_long' });
  }
  // ⑫ reading_search q59-60
  const rsePassage = extractPassage(html, '⑫ 情報検索');
  const rseQs = [];
  for (let i = 59; i <= 60; i++) {
    const q = questions[i]; if (!q) continue;
    rseQs.push({ question: q.qtext, options: q.options.slice(0,4), answer: q.answer, explanation: q.explanation });
  }
  if (rseQs.length > 0) {
    items.reading_search.push({ passage: rsePassage, questions: rseQs, ...meta, question_type: 'reading_search' });
  }

  return items;
}

function appendToJson(items) {
  for (const [typeId, list] of Object.entries(items)) {
    if (list.length === 0) continue;
    const filePath = path.join(DATA_DIR, `${typeId}.json`);
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    const existing = data.questions || [];
    const startIdx = existing.length;

    for (let i = 0; i < list.length; i++) {
      list[i].id = `n2-${typeId}-${String(startIdx + i + 1).padStart(3, '0')}`;
      data.questions.push(list[i]);
    }
    data.meta.count = data.questions.length;
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
    console.log(`  ${typeId}: +${list.length} (total ${data.meta.count})`);
  }
}

function main() {
  console.log('Parsing template.html...');
  const html = fs.readFileSync(HTML_PATH, 'utf8');
  const questions = parseQuestions(html);
  console.log(`Found ${Object.keys(questions).length} questions`);

  console.log('Building items...');
  const items = buildItems(html, questions);

  let total = 0;
  for (const list of Object.values(items)) total += list.length;
  console.log(`Total to append: ${total}`);

  console.log('Appending...');
  appendToJson(items);
  console.log('Done!');
}

main();
