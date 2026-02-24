const fs = require('fs');
const path = require('path');

const sessionsDir = 'C:\\Users\\YEHUDA\\.openclaw\\agents\\main\\sessions';
const files = fs.readdirSync(sessionsDir).filter(f => f.endsWith('.jsonl'));

const categories = {
  Mindmap: /mindmap|mind.?map|עץ|branch|nodes|circles|עיגולים|ענפים/i,
  Skills: /skill|SKILL\.md|סקיל/i,
  Config: /gateway.?config|whatsapp.?sett|allowlist|קונפיג/i,
  Family: /family|ברכה|אבא|אמא|ילדים|משפחה|מזרחי.?אימפריה/i,
  Coding: /\bgit\b|push|code|html|css|javascript|קוד|github/i,
  Heartbeat: /HEARTBEAT_OK|heartbeat/i,
  System: /gateway connected|gateway disconnected|WhatsApp.*connected|WhatsApp.*disconnected/i,
};

function categorize(text) {
  if (!text) return 'General';
  for (const [cat, re] of Object.entries(categories)) {
    if (re.test(text)) return cat;
  }
  return 'General';
}

function extractText(content) {
  if (typeof content === 'string') return content;
  if (Array.isArray(content)) return content.map(c => c.text || '').join(' ');
  return '';
}

const stats = {};
for (const cat of [...Object.keys(categories), 'General']) {
  stats[cat] = { count: 0, cost: 0 };
}

let totalQuestions = 0;
let totalCost = 0;
let lastUserCategory = 'General';

for (const file of files) {
  const lines = fs.readFileSync(path.join(sessionsDir, file), 'utf8').split('\n');
  lastUserCategory = 'General';
  for (const line of lines) {
    if (!line.trim()) continue;
    let obj;
    try { obj = JSON.parse(line); } catch { continue; }
    
    // Handle nested message structure
    const msg = obj.message || obj;
    const role = msg.role;
    
    if (role === 'user') {
      const text = extractText(msg.content);
      lastUserCategory = categorize(text);
      stats[lastUserCategory].count++;
      totalQuestions++;
    } else if (role === 'assistant') {
      // Cost can be on obj.usage or obj.message.usage or obj.usage
      const usage = obj.usage || msg.usage;
      if (usage && usage.cost) {
        const cost = usage.cost.total || 0;
        stats[lastUserCategory].cost += cost;
        totalCost += cost;
      }
    }
  }
}

let mostExpensive = 'General', mostCommon = 'General';
let maxCost = 0, maxCount = 0;
for (const [cat, s] of Object.entries(stats)) {
  if (s.cost > maxCost) { maxCost = s.cost; mostExpensive = cat; }
  if (s.count > maxCount) { maxCount = s.count; mostCommon = cat; }
}

console.log(JSON.stringify({ stats, totalQuestions, totalCost, mostExpensive, mostCommon }));
