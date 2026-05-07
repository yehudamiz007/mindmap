const { randomUUID } = require('crypto');

const API_KEY = 'sdgdskldFPLGfjHn1421dgnlxdGTbngdflg6290bRjslfihsjhSDsdgGHH25hjf';
const USER_KEY = 'eyJjaSI6IjYwY2FiYjBiLTU1OTctNDQ4NS04ZjYzLTdlOWUwNTZlMGJiOCIsImVhbiI6IlVucmVnaXN0ZXJlZEFwcGxpY2F0aW9uIiwiZWsiOiJZNWI3dTY4alZjcHRkbVQuUFVDWGouTjJKaGpJcWtrUlg3WXV3MmNWNU1lSTZhelNIZ2lRNHkxd2xYZ1BtVkY0b2VmLjltUllXLUU2Qkd3Q09nMzNENi1kN0toOWMxd2M5QllGdWRtRC4zMF8ifQ__';

function headers() {
  return {
    'x-api-key': API_KEY,
    'x-user-key': USER_KEY,
    'x-request-id': randomUUID(),
    'Content-Type': 'application/json'
  };
}

const message = `\u{1F916} Grok Trader Update

\u274C Closed: AAPL (4.1% - outside core strategy)
\u274C Closed: TSLA (3.8% - outside core strategy)
\u274C Closed: AMZN (2.8% - outside core strategy)
\u274C Closed: PLTR (4.3% - outside core strategy)

\u2705 Bought: MSFT +$1,643 (\u219220%)
\u2705 Bought: AMD +$523 (\u219210%)
\u2705 Bought: GOOGL +$697 (\u219210%)
\u2705 Bought: META +$1,011 (\u219215%)
\u2705 Bought: NVDA +$1,977 (\u219225%)
\u2705 Bought: AVGO +$511 (\u219210%)

\u{1F4CA} Target portfolio: MSFT 20% | AMD 10% | GOOGL 10% | META 15% | NVDA 25% | AVGO 10% | Cash 10%
\u{1F4B0} Equity: ~$10,068 | Unrealized PnL: +$49

Reason: Grok 4 rebalance - removed AAPL/TSLA/AMZN/PLTR (outside core 6-stock strategy), deployed cash into high-conviction large-caps
Time: Mon 27 Apr 2026, 16:36 IST`;

async function sendWA(phone, msg) {
  // Try eToro notification endpoint first
  try {
    const url = 'https://public-api.etoro.com/api/v1/notifications/whatsapp';
    const r = await fetch(url, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({ phone, message: msg })
    });
    console.log('eToro WA response:', r.status, await r.text());
  } catch (e) {
    console.log('eToro WA failed:', e.message);
  }
}

async function main() {
  console.log('Message to send:');
  console.log(message);
  console.log('---');
  await sendWA('+972502446410', message);
}
main().catch(console.error);
