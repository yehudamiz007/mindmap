const fs = require('fs');
const path = require('path');

const SESSIONS_DIR = path.join('C:\\Users\\YEHUDA\\.openclaw\\agents\\main\\sessions');
const CRON_DIR = path.join('C:\\Users\\YEHUDA\\.openclaw\\cron\\runs');
const OUTPUT = path.join('C:\\Users\\YEHUDA\\.openclaw\\workspace\\costs.json');

const daily = {};      // date -> { cost, tokens, inputTokens, outputTokens, cacheReadTokens, cacheWriteTokens, calls, sessions: Set, byModel: {} }
const byModel = {};    // model -> { cost, tokens, calls }

function processFile(filePath) {
  let data;
  try { data = fs.readFileSync(filePath, 'utf8'); } catch { return; }
  const lines = data.split('\n');
  const sessionId = path.basename(filePath);
  
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
  }
}

// Collect all jsonl files
function getJsonlFiles(dir) {
  try {
    return fs.readdirSync(dir).filter(f => f.endsWith('.jsonl')).map(f => path.join(dir, f));
  } catch { return []; }
}

// Also check subdirectories for cron
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

const result = {
  lastUpdated: new Date().toISOString(),
  totalCost: Math.round(totalCost * 1e6) / 1e6,
  totalTokens,
  totalCalls,
  totalSessions: totalSessions.size,
  daysActive: dates.length,
  daily: dailyArr,
  byModel: bmOut
};

fs.writeFileSync(OUTPUT, JSON.stringify(result, null, 2));
console.log(`Done! Total cost: $${result.totalCost.toFixed(2)}, ${result.totalCalls} calls, ${result.daysActive} days, ${result.totalSessions} sessions`);
