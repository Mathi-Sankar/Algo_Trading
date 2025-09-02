// State
let stockData = null;
let charts = {};

// DOM Elements
const searchIn = document.getElementById('stockSearch');
const searchRes = document.getElementById('searchResults');
const selTicker = document.getElementById('selectedTicker');
const analyzeBtn = document.getElementById('analyzeBtn');
const loading = document.getElementById('loadingIndicator');
const dashboard = document.getElementById('dashboard');
const toolsGrid = document.getElementById('toolsGrid');

// Setup Search Autocomplete
let searchTimeout;
searchIn.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    const query = e.target.value;
    if (query.length < 2) {
        searchRes.style.display = 'none';
        return;
    }
    
    searchTimeout = setTimeout(async () => {
        try {
            const res = await fetch(`/api/search?q=${query}`);
            const data = await res.json();
            searchRes.innerHTML = '';
            if (data.length > 0) {
                data.forEach(item => {
                    const li = document.createElement('li');
                    li.textContent = `${item.symbol} - ${item.shortname}`;
                    li.onclick = () => {
                        selTicker.value = item.symbol;
                        searchIn.value = item.symbol;
                        searchRes.style.display = 'none';
                    };
                    searchRes.appendChild(li);
                });
                searchRes.style.display = 'block';
            } else {
                searchRes.style.display = 'none';
            }
        } catch (e) { console.error(e); }
    }, 300);
});

// Hide dropdown on click outside
document.addEventListener('click', (e) => {
    if (!searchIn.contains(e.target) && !searchRes.contains(e.target)) {
        searchRes.style.display = 'none';
    }
});

// Analyze Button
analyzeBtn.addEventListener('click', async () => {
    const ticker = selTicker.value;
    const period = document.getElementById('timePeriod').value;
    const interval = document.getElementById('graphInterval').value;
    
    if (!ticker) return alert('Select a ticker first');
    
    loading.classList.remove('hidden');
    dashboard.classList.add('hidden');
    toolsGrid.classList.add('hidden');
    
    try {
        const res = await fetch('/api/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ ticker, period, interval })
        });
        
        const data = await res.json();
        if (data.error) {
            alert(data.error);
            loading.classList.add('hidden');
            return;
        }
        
        stockData = data;
        populateDashboard(data);
        
        loading.classList.add('hidden');
        dashboard.classList.remove('hidden');
        toolsGrid.classList.remove('hidden');
        
    } catch (e) {
        console.error(e);
        alert('An error occurred');
        loading.classList.add('hidden');
    }
});

// Populate Dashboard
function populateDashboard(data) {
    // Set Profit Predictor current price
    document.getElementById('buyPrice').value = data.financials['Current Price'] || data.graph_data.prices[data.graph_data.prices.length-1].toFixed(2);
    
    // Clear old charts
    Object.values(charts).forEach(c => c.destroy());
    
    // Price Chart
    const ctxPrice = document.getElementById('priceChart').getContext('2d');
    charts.price = new Chart(ctxPrice, {
        type: 'line',
        data: {
            labels: data.graph_data.dates,
            datasets: [{
                label: 'Closing Price',
                data: data.graph_data.prices,
                borderColor: '#00e5ff',
                backgroundColor: 'rgba(0, 229, 255, 0.1)',
                borderWidth: 2,
                fill: true,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: { 
                x: { 
                    display: true,
                    ticks: { maxTicksLimit: 8, maxRotation: 45, minRotation: 45 }
                }, 
                y: { display: true } 
            },
            plugins: { legend: { display: false } }
        }
    });

    // Probabilities Bar Chart
    const ctxProb = document.getElementById('probChart').getContext('2d');
    charts.prob = new Chart(ctxProb, {
        type: 'bar',
        data: {
            labels: ['Crash Risk', 'ML Trend Up', 'ACO Trend Up', 'Sentiment %'],
            datasets: [{
                label: 'Probability %',
                data: [
                    data.probabilities.crash, 
                    data.probabilities.ml_up, 
                    data.probabilities.aco_up, 
                    data.probabilities.sentiment
                ],
                backgroundColor: [
                    'rgba(255, 51, 102, 0.8)', // crash red
                    'rgba(0, 255, 136, 0.8)', // ml up green
                    'rgba(0, 229, 255, 0.8)', // aco up blue
                    'rgba(255, 0, 127, 0.8)'  // sentiment pink
                ]
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: { y: { beginAtZero: true, max: 100 } }
        }
    });

    // Sentiment Pie Chart
    const ctxSent = document.getElementById('sentimentChart').getContext('2d');
    charts.sent = new Chart(ctxSent, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Negative', 'Neutral'],
            datasets: [{
                data: [
                    data.sentiment_stats.positive,
                    data.sentiment_stats.negative,
                    data.sentiment_stats.neutral
                ],
                backgroundColor: ['#00ff88', '#ff3366', '#a0aab5']
            }]
        },
        options: { responsive: true, maintainAspectRatio: false }
    });

    // Financials — detailed breakdown
    const finList = document.getElementById('financialsList');
    finList.innerHTML = '';

    const fin = data.financials;
    const na = 'N/A';

    // Helper to format a number or return N/A
    const fmt = (v) => (typeof v === 'number' && !isNaN(v)) ? v.toFixed(2) : na;

    // Define each metric: label, value, benchmark description, pass condition
    const metrics = [
        {
            label: 'EPS (Earnings Per Share)',
            value: fmt(fin['EPS']),
            benchmark: 'Must be > 0 (profitable)',
            passed: typeof fin['EPS'] === 'number' && fin['EPS'] > 0,
            note: 'Measures profit per share. Positive means the company is earning money.'
        },
        {
            label: 'P/E Ratio (Price-to-Earnings)',
            value: fmt(fin['P/E Ratio']),
            benchmark: `≤ Forward P/E (${fmt(fin['Industry P/E Ratio'])}) — not overvalued`,
            passed: typeof fin['P/E Ratio'] === 'number' && typeof fin['Industry P/E Ratio'] === 'number'
                    && fin['P/E Ratio'] <= fin['Industry P/E Ratio'],
            note: 'How much investors pay per ₹1 of earnings. Lower is generally better.'
        },
        {
            label: 'D/E Ratio (Debt-to-Equity)',
            value: fmt(fin['D/E Ratio']),
            benchmark: 'Must be < 100 (manageable debt)',
            passed: typeof fin['D/E Ratio'] === 'number' && fin['D/E Ratio'] < 100,
            note: 'Shows how much debt the company carries vs. shareholder equity. Lower is safer.'
        },
        {
            label: 'P/B Ratio (Price-to-Book)',
            value: fmt(fin['P/B Ratio']),
            benchmark: 'Must be < 5 (reasonable valuation)',
            passed: typeof fin['P/B Ratio'] === 'number' && fin['P/B Ratio'] < 5,
            note: 'Compares market price to book value. Under 5 suggests fair valuation.'
        }
    ];

    metrics.forEach(m => {
        const icon   = m.passed ? '✔' : '✘';
        const color  = m.passed ? 'var(--positive)' : 'var(--negative)';
        finList.innerHTML += `
            <li style="flex-direction:column; align-items:flex-start; gap:3px; padding: 10px 0;">
                <div style="display:flex; justify-content:space-between; width:100%;">
                    <span style="font-weight:600; color:var(--text-light); font-size:0.88rem;">${m.label}</span>
                    <span style="color:${color}; font-weight:700; font-size:1rem;">${icon} ${m.value}</span>
                </div>
                <div style="font-size:0.77rem; color:var(--text-muted);">Benchmark: ${m.benchmark}</div>
                <div style="font-size:0.75rem; color:var(--text-muted); font-style:italic;">${m.note}</div>
            </li>`;
    });

    // Summary verdict
    const passed = data.financial_eval.passed;
    const score  = data.financial_eval.score;
    finList.innerHTML += `
        <li style="
            justify-content:center;
            margin-top:8px;
            padding:8px;
            border-radius:8px;
            background: ${passed ? 'rgba(0,255,136,0.1)' : 'rgba(255,51,102,0.1)'};
            border: 1px solid ${passed ? 'var(--positive)' : 'var(--negative)'};
            color: ${passed ? 'var(--positive)' : 'var(--negative)'};
            font-weight:700;
            font-size:0.9rem;
            letter-spacing:0.5px;">
            Overall Financial Health: ${passed ? 'PASS' : 'FAIL'} &nbsp;(${score} / 4 checks passed)
        </li>`;

    // News updates
    const nf = document.getElementById('newsFeed');
    nf.innerHTML = '';
    data.news.forEach(n => {
        let sc = n.Sentiment > 0.1 ? 'var(--positive)' : n.Sentiment < -0.1 ? 'var(--negative)' : 'var(--text-muted)';
        nf.innerHTML += `<div class="news-item">
            <span style="color: ${sc}">●</span> [${n.Date}] ${n.Headline}
        </div>`;
    });
}

// Profit Estimator Logic
document.getElementById('calcProfitBtn').addEventListener('click', () => {
    const principal = parseFloat(document.getElementById('principalAmount').value);
    const buy = parseFloat(document.getElementById('buyPrice').value);
    const sell = parseFloat(document.getElementById('sellPrice').value);
    const tax = parseFloat(document.getElementById('taxRate').value);
    
    if(!buy || !sell) return alert("Please ensure Buy and Sell prices are filled.");
    
    fetch('/api/profit', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ principal: principal, current_price: buy, selling_price: sell, tax_rate: tax })
    })
    .then(r => r.json())
    .then(data => {
        if(data.error) return alert(data.error);
        document.getElementById('profitResult').classList.remove('hidden');
        document.getElementById('grossRes').textContent = data.gross_profit.toFixed(2);
        document.getElementById('taxRes').textContent = data.tax_amount.toFixed(2);
        
        const netNode = document.getElementById('netRes');
        netNode.textContent = data.net_profit.toFixed(2);
        
        if(data.net_profit >= 0) {
            netNode.style.color = 'var(--positive)';
            document.getElementById('grossRes').style.color = 'var(--positive)';
        } else {
            netNode.style.color = 'var(--negative)';
            document.getElementById('grossRes').style.color = 'var(--negative)';
        }
    });
});

// Drawing Canvas Logic
const canvas = document.getElementById('drawingCanvas');
const ctx = canvas.getContext('2d');
let isDrawing = false;
let points = []; 

canvas.addEventListener('mousedown', (e) => {
    isDrawing = true;
    const rect = canvas.getBoundingClientRect();
    points.push({x: e.clientX - rect.left, y: e.clientY - rect.top});
});

canvas.addEventListener('mousemove', (e) => {
    if(!isDrawing) return;
    const rect = canvas.getBoundingClientRect();
    points.push({x: e.clientX - rect.left, y: e.clientY - rect.top});
    
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for(let i=1; i<points.length; i++) {
        ctx.lineTo(points[i].x, points[i].y);
    }
    ctx.strokeStyle = '#ff007f';
    ctx.lineWidth = 3;
    ctx.stroke();
});

canvas.addEventListener('mouseup', () => {
    isDrawing = false;
});

document.getElementById('clearCanvasBtn').addEventListener('click', () => {
    ctx.clearRect(0,0,canvas.width,canvas.height);
    points = [];
    document.getElementById('patternResult').classList.add('hidden');
});

// Pearson Correlation JS
function pearsonCorrelation(x, y) {
    if (x.length !== y.length || x.length === 0) return 0;
    const n = x.length;
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0, sumY2 = 0;
    for (let i = 0; i < n; i++) {
        sumX += x[i]; sumY += y[i];
        sumXY += x[i] * y[i];
        sumX2 += x[i] * x[i]; sumY2 += y[i] * y[i];
    }
    const numerator = (n * sumXY) - (sumX * sumY);
    const denominator = Math.sqrt(((n * sumX2) - (sumX * sumX)) * ((n * sumY2) - (sumY * sumY)));
    if (denominator === 0) return 0;
    return numerator / denominator;
}

function resample(arr, targetLen) {
    if(arr.length === 0) return [];
    if(arr.length === 1) return new Array(targetLen).fill(arr[0]);
    const res = [];
    for(let i=0; i<targetLen; i++) {
        const floatIdx = (i / (targetLen - 1)) * (arr.length - 1);
        const idx1 = Math.floor(floatIdx), idx2 = Math.ceil(floatIdx);
        if(idx1 === idx2) res.push(arr[idx1]);
        else res.push(arr[idx1] * (1 - (floatIdx - idx1)) + arr[idx2] * (floatIdx - idx1));
    }
    return res;
}

let savedPatterns = [];

document.getElementById('savePatternBtn').addEventListener('click', () => {
    if(points.length < 2) return alert('Draw a pattern on the canvas first!');
    const name = document.getElementById('patternComment').value || `Pattern ${savedPatterns.length + 1}`;
    // Canvas Y is inverted (0 is top). Subtract from heights so higher peaks = higher values
    const yValues = points.map(p => canvas.height - p.y);
    const normalizedY = resample(yValues, 50);
    savedPatterns.push({ name, data: normalizedY });
    
    document.getElementById('savedPatternsList').innerHTML += `<li>${name}</li>`;
    document.getElementById('patternComment').value = '';
    
    // Clear canvas for next drawing
    ctx.clearRect(0,0,canvas.width,canvas.height);
    points = [];
});

document.getElementById('matchPatternBtn').addEventListener('click', () => {
    if(savedPatterns.length === 0) return alert('Save at least one pattern first!');
    if(!stockData) return alert("Analyze a stock first to match its trend!");
    
    const stockPrices = stockData.graph_data.prices;
    const stockFeatures = resample(stockPrices, 50);
    
    let bestMatch = null;
    let bestScore = -Infinity;
    
    savedPatterns.forEach(pattern => {
        let r = pearsonCorrelation(stockFeatures, pattern.data);
        if(r > bestScore) {
            bestScore = r;
            bestMatch = pattern;
        }
    });
    
    const pres = document.getElementById('patternResult');
    pres.classList.remove('hidden');
    let pct = Math.max(0, Math.round(bestScore * 100)); // cap at 0%
    
    pres.innerHTML = `<strong style="font-size:1.1rem;color:var(--primary)">Matched: ${bestMatch.name}</strong><br>Similarity Match: ${pct >= 0 ? pct : 0}%`;
    pres.style.border = pct > 70 ? '1px solid var(--positive)' : '1px solid var(--text-muted)';
    pres.style.padding = "10px";
    pres.style.marginTop = "10px";
});
