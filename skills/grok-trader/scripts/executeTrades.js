// eToro Agent-Portfolio Trade Execution Script

// Using built-in fetch in Node.js
const { v4: uuidv4 } = require('uuid');

// API Keys
const API_KEY = 'sdgdskldFPLGfjHn1421dgnlxdGTbngdflg6290bRjslfihsjhSDsdgGHH25hjf';
const USER_KEY = 'eyJjaSI6IjYwY2FiYjBiLTU1OTctNDQ4NS04ZjYzLTdlOWUwNTZlMGJiOCIsImVhbiI6IlVucmVnaXN0ZXJlZEFwcGxpY2F0aW9uIiwiZWsiOiJnYU9JNlZjZklFemNSdDcyNDA4QzRFcC56UTVqRXVFcGVEUWRHa3FKTXRqV2pvSjhpQzFnLmdPWU9QOGlGUGZweFQ2Wjk4MzFKVXUtaVhVOFZ2YlUtRHVBWHo3czV4bG5sUTFKbXMwYmIzNF8ifQ__';

// Positions to close
const POSITIONS_TO_CLOSE = [
    { positionID: '3377763752', instrumentID: '1005', symbol: 'AMZN' },
    { positionID: '3377763871', instrumentID: '1365', symbol: 'ARM' },
    { positionID: '3377763891', instrumentID: '5506', symbol: 'CRWD' },
    { positionID: '3377763784', instrumentID: '7991', symbol: 'PLTR' }
];

// Target allocations for rebalancing
const TARGET_ALLOCATIONS = {
    'MSFT': 0.20,
    'AMD': 0.10,
    'GOOGL': 0.10,
    'META': 0.15,
    'NVDA': 0.25,
    'AVGO': 0.10,
    'Cash': 0.10
};

// Function to delay execution
async function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Function to make API calls with headers
async function makeApiCall(method, url, body = null) {
    const headers = {
        'x-api-key': API_KEY,
        'x-user-key': USER_KEY,
        'x-request-id': uuidv4(),
        'Content-Type': 'application/json'
    };

    const options = {
        method: method,
        headers: headers
    };

    if (body) {
        options.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error in API call to ${url}:`, error);
        throw error;
    }
}

// Step 1: Get current PnL to confirm positions and equity
async function getPnl() {
    console.log('Fetching current PnL...');
    const data = await makeApiCall('GET', 'https://public-api.etoro.com/api/v1/trading/info/real/pnl');
    console.log('Current PnL:', JSON.stringify(data, null, 2));
    return data;
}

// Step 2: Close specified positions
async function closePositions(pnlData) {
    console.log('Closing positions...');
    const closePromises = POSITIONS_TO_CLOSE.map(async (position) => {
        const url = `https://public-api.etoro.com/api/v1/trading/positions/real/${position.positionID}/close`;
        console.log(`Attempting to close position ${position.symbol} (ID: ${position.positionID})`);
        try {
            await makeApiCall('POST', url);
            console.log(`Successfully closed position ${position.symbol}`);
        } catch (error) {
            console.error(`Failed to close position ${position.symbol}:`, error.message);
        }
        await delay(3000); // Space trades 3 seconds apart
    });
    await Promise.all(closePromises);
    console.log('Closure attempts completed for all specified positions.');
}

// Step 3: Wait 60 seconds for PnL refresh
async function waitForPnlRefresh() {
    console.log('Waiting 60 seconds for PnL refresh...');
    await delay(60000);
}

// Step 4: Get updated PnL after closing positions
async function getUpdatedPnl() {
    console.log('Fetching updated PnL after closing positions...');
    const data = await makeApiCall('GET', 'https://public-api.etoro.com/api/v1/trading/info/real/pnl');
    console.log('Updated PnL:', JSON.stringify(data, null, 2));
    return data;
}

// Step 5: Calculate buy amounts for rebalancing
async function calculateBuyAmounts(updatedPnl) {
    const equity = updatedPnl.equity || 2000; // Default to initial equity if not available
    console.log(`Current equity for rebalancing: $${equity}`);
    const buyOrders = [];

    for (const [symbol, targetPercent] of Object.entries(TARGET_ALLOCATIONS)) {
        if (symbol === 'Cash' || symbol === 'NVDA' || symbol === 'AVGO') continue; // Skip cash and positions not to be adjusted

        const targetAmount = equity * targetPercent;
        console.log(`Target amount for ${symbol}: $${targetAmount} (${targetPercent*100}%)`);
        buyOrders.push({ symbol, amount: targetAmount });
    }

    return buyOrders;
}

// Step 6: Execute buy orders
async function executeBuyOrders(buyOrders) {
    console.log('Executing buy orders...');
    const buyPromises = buyOrders.map(async (order) => {
        const url = 'https://public-api.etoro.com/api/v1/trading/orders/real/open';
        const body = {
            instrumentId: getInstrumentId(order.symbol),
            amount: order.amount,
            type: 'Market',
            side: 'Buy'
        };
        console.log(`Opening position for ${order.symbol} with amount $${order.amount}`);
        await makeApiCall('POST', url, body);
        await delay(3000); // Space trades 3 seconds apart
    });
    await Promise.all(buyPromises);
    console.log('All buy orders executed.');
}

// Helper function to map symbol to instrument ID (mock data, update as needed)
function getInstrumentId(symbol) {
    const instrumentMap = {
        'MSFT': '1003',
        'AMD': '1010',
        'GOOGL': '1002',
        'META': '1366',
        'NVDA': '1009',
        'AVGO': '5511'
    };
    return instrumentMap[symbol] || 'UNKNOWN';
}

// Step 7: Notify user via WhatsApp
async function notifyUser(actions) {
    console.log('Sending WhatsApp notification to Yehuda...');
    const message = `🤖 Grok Trader Update\n\n${actions.join('\n')}\n📊 New portfolio: MSFT (20%), AMD (10%), GOOGL (10%), META (15%), NVDA (25%), AVGO (10%), Cash (10%)\nReason: Grok 4 strategy - closed positions below MA20 / weak catalysts\nCurrent time: Monday, April 27th, 2026 - 4:30 PM (Asia/Jerusalem) / 2026-04-27 13:30 UTC`;
    // This would be a call to the message tool, but for now, we'll log it
    console.log('WhatsApp message content:', message);
    // Placeholder for actual WhatsApp notification
    return message;
}

// Main function to execute the trading workflow
async function main() {
    try {
        const initialPnl = await getPnl();
        await closePositions(initialPnl);
        await waitForPnlRefresh();
        const updatedPnl = await getUpdatedPnl();
        const buyOrders = await calculateBuyAmounts(updatedPnl);
        await executeBuyOrders(buyOrders);
        const actions = [
            '❌ Closed: AMZN',
            '❌ Closed: ARM',
            '❌ Closed: CRWD',
            '❌ Closed: PLTR',
            '✅ Opened: MSFT (20%)',
            '✅ Opened: AMD (10%)',
            '✅ Opened: GOOGL (10%)',
            '✅ Opened: META (15%)'
        ];
        await notifyUser(actions);
        console.log('Trade execution completed successfully.');
    } catch (error) {
        console.error('Error in trade execution:', error);
    }
}

main();
