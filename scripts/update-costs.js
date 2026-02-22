const fs = require('fs');
const path = require('path');

const SESSIONS_DIR = path.join('C:\\Users\\YEHUDA\\.openclaw\\agents\\main\\sessions');
const CRON_DIR = path.join('C:\\Users\\YEHUDA\\.openclaw\\cron\\runs');
const OUTPUT = path.join('C:\\Users\\YEHUDA\\.openclaw\\workspace\\costs.json');

// Category mappings
const CRON_JOB_CATEGORIES = {
  'e1eb3b60-b369-41e4-be2e-fbf5f0844f79': { name: 'Grok Virtual Trader', category: 'מסחר' },
  'b496cdfe-7a7c-4462-b172-7d3fe8dbb758': { name: 'Daily Stock Scanner', category: 'מסחר' },
  'df402cec-2d90-4241-88a0-03e0f451cef9': { name: 'סיכום AI יומי', category: 'סיכום יומי' },
  'aa64c5a7-930c-454b-9fc2-db1d1a54beee': { name: 'Cost Dashboard Update', category: 'תחזוקה' },
  '74a0a646-b83d-441b-bbdc-8a8613dbcdfd': { name: 'Backup MEMORY.md', category: 'תחזוקה' },
};

const MAIN_SESSION_ID = '0b8a66e9-8346-4180-841b-afff6a820b4a';

// Build session->category mapping from cron run logs
// Cron JSONL files contain entries with sessionId and jobId
const sessionCategoryMap = {}; // sessionId -> category

function buildCronSessionMap() {
  try {
    const cronFiles = fs.readdirSync(CRON_DIR).filter(f => f.endsWith('.jsonl'));
    for (const file of cronFiles) {
      const jobId = path.basename(file, '.jsonl');
      const filePath = path.join(CRON_DIR, file);
      try {
        const data = fs.readFileSync(filePath, 'utf8');
        for (const line of data.split('\n')) {
          if (!line.trim()) continue;
          try {
            const obj = JSON.parse(line);
            if (obj.sessionId) {
              const info = CRON_JOB_CATEGORIES[jobId];
              sessionCategoryMap[obj.sessionId] = info ? info.category : 'ג\'ובים אחרים';
            }
          } catch {}
        }
      } catch {}
    }
  } catch {}
  console.log(`Mapped ${Object.keys(sessionCategoryMap).length} cron sessions to categories`);
}

buildCronSessionMap();

function getFileCategory(filePath) {
  const basename = path.basename(filePath, '.jsonl');
  
  // Known main session
  if (basename === MAIN_SESSION_ID) return 'וואטסאפ / צ\'אט ראשי';
  
  // Check cron session map
  if (sessionCategoryMap[basename]) return sessionCategoryMap[basename];
  
  // Check file content for session type hints
  try {
    const firstChunk = fs.readFileSync(filePath, 'utf8').slice(0, 3000);
    for (const line of firstChunk.split('\n')) {
      if (!line.trim()) continue;
      try {
        const obj = JSON.parse(line);
        // Check for message content that indicates main session (has channel info)
        if (obj.type === 'session' && obj.cwd) {
          // Session metadata - no key info, continue
          continue;
        }
        const key = obj.sessionKey || obj.session || '';
        if (key === 'agent:main:main') return 'וואטסאפ / צ\'אט ראשי';
        if (key.includes('subagent')) return 'סאב-אייג\'נטים';
        if (key.includes(':cron:')) {
          for (const [jobId, info] of Object.entries(CRON_JOB_CATEGORIES)) {
            if (key.includes(jobId)) return info.category;
          }
          return 'ג\'ובים אחרים';
        }
      } catch {}
    }
  } catch {}
  
  // Default: subagent (most non-main sessions are subagents)
  return 'סאב-אייג\'נטים';
}

const daily = {};
const byModel = {};
const byCategory = {};
const dailyByCategory = {};

function addToCategory(cat, cost, tokens, calls) {
  if (!byCategory[cat]) byCategory[cat] = { cost: 0, tokens: 0, calls: 0 };
  byCategory[cat].cost += cost;
  byCategory[cat].tokens += tokens;
  byCategory[cat].calls += calls;
}

function addToDailyCategory(date, cat, cost) {
  if (!dailyByCategory[date]) dailyByCategory[date] = {};
  if (!dailyByCategory[date][cat]) dailyByCategory[date][cat] = 0;
  dailyByCategory[date][cat] += cost;
}

function processFile(filePath) {
  let data;
  try { data = fs.readFileSync(filePath, 'utf8'); } catch { return; }
  const lines = data.split('\n');
  const sessionId = path.basename(filePath);
  const category = getFileCategory(filePath);

  for (const line of lines) {
    if (!line.trim()) continue;
    let obj;
    try { obj = JSON.parse(line); } catch { continue; }
    if (obj.type !== 'message') continue;
    const msg = obj.message;
    if (!msg || msg.role !== 'assistant') continue;
    if (!msg.usage || !msg.usage.cost || !msg.usage.cost.total) continue;
    if (msg.model === 'delivery-mirror') continue;

    const cost = msg.usage.cost.total;
    if (!cost || cost <= 0) continue;

    const ts = obj.timestamp || msg.timestamp;
    if (!ts) continue;
    const date = new Date(typeof ts === 'number' ? ts : ts).toISOString().slice(0, 10);
    const model = msg.model || 'unknown';
    const input = msg.usage.input || 0;
    const output = msg.usage.output || 0;
    const cacheRead = msg.usage.cacheRead || 0;
    const cacheWrite = msg.usage.cacheWrite || 0;

    // Daily
    if (!daily[date]) daily[date] = { cost: 0, tokens: 0, inputTokens: 0, outputTokens: 0, cacheReadTokens: 0, cacheWriteTokens: 0, calls: 0, sessions: new Set(), byModel: {} };
    const d = daily[date];
    d.cost += cost;
    d.tokens += input + output;
    d.inputTokens += input;
    d.outputTokens += output;
    d.cacheReadTokens += cacheRead;
    d.cacheWriteTokens += cacheWrite;
    d.calls++;
    d.sessions.add(sessionId);

    if (!d.byModel[model]) d.byModel[model] = { cost: 0, tokens: 0, calls: 0 };
    d.byModel[model].cost += cost;
    d.byModel[model].tokens += input + output;
    d.byModel[model].calls++;

    // By model total
    if (!byModel[model]) byModel[model] = { cost: 0, tokens: 0, calls: 0 };
    byModel[model].cost += cost;
    byModel[model].tokens += input + output;
    byModel[model].calls++;

    // Category
    addToCategory(category, cost, input + output, 1);
    addToDailyCategory(date, category, cost);
  }
}

// Collect all jsonl files
function getJsonlFiles(dir) {
  try {
    return fs.readdirSync(dir).filter(f => f.endsWith('.jsonl')).map(f => path.join(dir, f));
  } catch { return []; }
}

function getJsonlFilesRecursive(dir) {
  const results = [];
  try {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) results.push(...getJsonlFilesRecursive(full));
      else if (entry.name.endsWith('.jsonl')) results.push(full);
    }
  } catch {}
  return results;
}

const files = [...getJsonlFiles(SESSIONS_DIR), ...getJsonlFilesRecursive(CRON_DIR)];
console.log(`Processing ${files.length} files...`);
files.forEach(processFile);

// Build output
const dates = Object.keys(daily).sort();
let totalCost = 0, totalTokens = 0, totalCalls = 0, totalSessions = new Set();

const dailyArr = dates.map(date => {
  const d = daily[date];
  totalCost += d.cost;
  totalTokens += d.tokens;
  totalCalls += d.calls;
  d.sessions.forEach(s => totalSessions.add(s));

  const bm = {};
  for (const [m, v] of Object.entries(d.byModel)) {
    bm[m] = { cost: Math.round(v.cost * 1e6) / 1e6, tokens: v.tokens, calls: v.calls };
  }
  return {
    date,
    cost: Math.round(d.cost * 1e6) / 1e6,
    tokens: d.tokens,
    inputTokens: d.inputTokens,
    outputTokens: d.outputTokens,
    cacheReadTokens: d.cacheReadTokens,
    cacheWriteTokens: d.cacheWriteTokens,
    calls: d.calls,
    sessions: d.sessions.size,
    byModel: bm
  };
});

const bmOut = {};
for (const [m, v] of Object.entries(byModel)) {
  bmOut[m] = { cost: Math.round(v.cost * 1e6) / 1e6, tokens: v.tokens, calls: v.calls };
}

// Build byCategory output
const byCatOut = {};
for (const [cat, v] of Object.entries(byCategory)) {
  byCatOut[cat] = { cost: Math.round(v.cost * 1e6) / 1e6, tokens: v.tokens, calls: v.calls };
}
// Add job names for מסחר
if (byCatOut['מסחר']) {
  byCatOut['מסחר'].jobs = ['Grok Virtual Trader', 'Daily Stock Scanner'];
}

// Build dailyByCategory output
const allCategories = Object.keys(byCategory);
const dailyByCatArr = dates.map(date => {
  const entry = { date };
  for (const cat of allCategories) {
    entry[cat] = Math.round((dailyByCategory[date]?.[cat] || 0) * 1e6) / 1e6;
  }
  return entry;
});

const result = {
  lastUpdated: new Date().toISOString(),
  totalCost: Math.round(totalCost * 1e6) / 1e6,
  totalTokens,
  totalCalls,
  totalSessions: totalSessions.size,
  daysActive: dates.length,
  daily: dailyArr,
  byModel: bmOut,
  byCategory: byCatOut,
  dailyByCategory: dailyByCatArr
};

fs.writeFileSync(OUTPUT, JSON.stringify(result, null, 2));
console.log(`Done! Total cost: $${result.totalCost.toFixed(2)}, ${result.totalCalls} calls, ${result.daysActive} days, ${result.totalSessions} sessions`);
console.log('Categories:', Object.entries(byCatOut).map(([k,v]) => `${k}: $${v.cost.toFixed(2)}`).join(', '));
