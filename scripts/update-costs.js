const fs = require('fs');
const path = require('path');

const SESSIONS_DIR = path.join('C:\\Users\\YEHUDA\\.openclaw\\agents\\main\\sessions');
const CRON_DIR = path.join('C:\\Users\\YEHUDA\\.openclaw\\cron\\runs');
const OUTPUT = path.join('C:\\Users\\YEHUDA\\.openclaw\\workspace\\costs.json');

// Category mappings
const CRON_JOB_CATEGORIES = {
  // Trading
  'e1eb3b60-b369-41e4-be2e-fbf5f0844f79': { name: 'Grok Virtual Trader', category: 'Trading' },
  'b496cdfe-7a7c-4462-b172-7d3fe8dbb758': { name: 'Daily Stock Scanner + Grok Trader', category: 'Trading' },
  '42b94b85-a32e-4051-ace2-50d66c354889': { name: 'Grok Trader Monday Open', category: 'Trading' },
  // Maintenance
  'aa64c5a7-930c-454b-9fc2-db1d1a54beee': { name: 'Cost Dashboard Update', category: 'Maintenance' },
  '74a0a646-b83d-441b-bbdc-8a8613dbcdfd': { name: 'Backup MEMORY.md', category: 'Maintenance' },
  '8e0d2072-d8aa-4c0d-bf8e-099a7d19e88b': { name: 'Hourly Hub HTML Backup', category: 'Maintenance' },
  'a7f3c9a1-9418-4a82-a5a5-61e2adf624c3': { name: 'Daily yehudaclaw Backup', category: 'Maintenance' },
  // Daily Summary / News
  'df402cec-2d90-4241-88a0-03e0f451cef9': { name: 'Daily AI Summary', category: 'Daily Summary' },
  '17ee5f68-63c1-4dfe-b54d-c8cda3b31250': { name: 'LinkedIn Daily AI Post', category: 'Daily Summary' },
  '78275da2-d012-4b22-afaa-568a18763be3': { name: 'Daily AI News Summary', category: 'Daily Summary' },
  // Reminders
  '5996c738-544e-4633-9ce0-72703242fb1e': { name: 'Wedding Anniversary Reminder', category: 'Reminders' },
  '74767929-3a2d-49c6-8317-902e71e6d339': { name: 'Nitai Birthday Reminder', category: 'Reminders' },
  '968e059d-dc07-4651-8577-05b3f3c9fb3e': { name: 'Arbel Birthday Reminder', category: 'Reminders' },
  'b59cde1a-e3d0-4cbc-a564-d03579e3e6b2': { name: 'Ilana Birthday Reminder', category: 'Reminders' },
  'b208a785-8b36-40fc-b989-dd217237636b': { name: 'Avior Birthday Reminder', category: 'Reminders' },
  '664db225-fdc5-47e8-bd29-2c4065a4f5a7': { name: 'Ilana Birthday Reminder (alt)', category: 'Reminders' },
  // News / Iran
  '9ec71945-81ab-4389-b61f-d3637dfbed80': { name: 'Iran Dashboard Update', category: 'News' },
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
              sessionCategoryMap[obj.sessionId] = info ? info.category : 'Other Jobs';
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
  if (basename === MAIN_SESSION_ID) return 'WhatsApp / Main Chat';
  
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
        if (key === 'agent:main:main') return 'WhatsApp / Main Chat';
        if (key.includes('subagent')) return 'Sub-Agents';
        if (key.includes(':cron:')) {
          for (const [jobId, info] of Object.entries(CRON_JOB_CATEGORIES)) {
            if (key.includes(jobId)) return info.category;
          }
          return 'Other Jobs';
        }
      } catch {}
    }
  } catch {}
  
  // Default: subagent (most non-main sessions are subagents)
  return 'Sub-Agents';
}

const daily = {};
const byModel = {};
const byCategory = {};
const bySkill = {};
const dailyByCategory = {};

function getSessionSkills(filePath) {
  // Detect ONLY skills that were ACTUALLY ACTIVATED via toolCall/tool_use read of SKILL.md
  // This gives accurate attribution - only sessions where a skill was explicitly used
  try {
    const data = fs.readFileSync(filePath, 'utf8');
    if (!data.includes('SKILL.md')) return [];

    const lines = data.split('\n');
    const skills = new Set();

    for (const line of lines) {
      if (!line.includes('SKILL.md') || !line.trim()) continue;
      let obj;
      try { obj = JSON.parse(line); } catch { continue; }
      const msg = obj.message;
      if (!msg || msg.role !== 'assistant') continue;

      if (Array.isArray(msg.content)) {
        for (const block of msg.content) {
          // Format A: {type: "toolCall", name: "read", arguments: {path: "..."}}
          if (block.type === 'toolCall' && block.name === 'read') {
            const p = (block.arguments && block.arguments.path) ? block.arguments.path : '';
            const m = p.match(/skills[\/\\]+([a-z0-9_-]+)[\/\\]+SKILL\.md/i);
            if (m && m[1].length > 2) skills.add(m[1]);
          }
          // Format B: {type: "tool_use", name: "read", input: {path: "..."}}
          if (block.type === 'tool_use' && block.name === 'read') {
            const p = (block.input && block.input.path) ? block.input.path : '';
            const m = p.match(/skills[\/\\]+([a-z0-9_-]+)[\/\\]+SKILL\.md/i);
            if (m && m[1].length > 2) skills.add(m[1]);
          }
        }
      }
    }

    const blacklist = new Set(['X', 'wacli', 'any1']);
    return [...skills].filter(s => !blacklist.has(s));
  } catch {
    return [];
  }
}


function addToCategory(cat, cost, tokens, calls) {
  if (!byCategory[cat]) byCategory[cat] = { cost: 0, tokens: 0, calls: 0 };
  byCategory[cat].cost += cost;
  byCategory[cat].tokens += tokens;
  byCategory[cat].calls += calls;
}

function addToSkill(skill, cost, tokens, calls) {
  if (!bySkill[skill]) bySkill[skill] = { cost: 0, tokens: 0, calls: 0 };
  bySkill[skill].cost += cost;
  bySkill[skill].tokens += tokens;
  bySkill[skill].calls += calls;
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
  const skills = getSessionSkills(filePath);

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

    // Skills - divide cost equally among all skills in this session
    if (skills.length > 0) {
      const costPerSkill = cost / skills.length;
      const tokensPerSkill = (input + output) / skills.length;
      for (const skill of skills) {
        addToSkill(skill, costPerSkill, tokensPerSkill, 1);
      }
    } else {
      addToSkill('None / General', cost, input + output, 1);
    }
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

const bySkillOut = {};
for (const [skill, v] of Object.entries(bySkill)) {
  bySkillOut[skill] = { cost: Math.round(v.cost * 1e6) / 1e6, tokens: v.tokens, calls: v.calls };
}
// sort by cost desc
const sortedBySkill = Object.fromEntries(
  Object.entries(bySkillOut).sort((a, b) => b[1].cost - a[1].cost)
);

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
  bySkill: sortedBySkill,
  dailyByCategory: dailyByCatArr
};

fs.writeFileSync(OUTPUT, JSON.stringify(result, null, 2));
console.log(`Done! Total cost: $${result.totalCost.toFixed(2)}, ${result.totalCalls} calls, ${result.daysActive} days, ${result.totalSessions} sessions`);
console.log('Categories:', Object.entries(byCatOut).map(([k,v]) => `${k}: $${v.cost.toFixed(2)}`).join(', '));
console.log('Skills:', Object.entries(sortedBySkill).slice(0, 10).map(([k,v]) => `${k}: $${v.cost.toFixed(4)}`).join(', '));
