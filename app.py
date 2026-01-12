from flask import Flask, render_template, request, jsonify
import ml_final
import math
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    results = ml_final.search_tickers(query)
    return jsonify(results)

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    data = request.json
    ticker = data.get('ticker', 'AAPL')
    period = data.get('period', '1y')
    interval = data.get('interval', '1d')
    
    result = ml_final.analyze_stock(ticker, period, interval)
    if "error" in result:
        return jsonify(result), 400
    
    return jsonify(result)

@app.route('/api/profit', methods=['POST'])
def api_profit():
    # Simple profit calculation
    data = request.json
    principal = float(data.get('principal', 0))
    current_price = float(data.get('current_price', 1))
    selling_price = float(data.get('selling_price', 1))
    tax_rate = float(data.get('tax_rate', 15)) # default 15% STCG
    
    if current_price <= 0:
        return jsonify({"error": "Invalid current price"}), 400
        
    num_shares = principal / current_price
    gross_profit = num_shares * (selling_price - current_price)
    tax_amount = max(0, gross_profit * (tax_rate / 100))
    net_profit = gross_profit - tax_amount
    
    return jsonify({
        "num_shares": num_shares,
        "gross_profit": gross_profit,
        "tax_amount": tax_amount,
        "net_profit": net_profit,
        "total_value": principal + net_profit
    })

@app.route('/api/match_pattern', methods=['POST'])
def api_match_pattern():
    data = request.json
    drawn_slope = float(data.get('slope', 0))
    ticker = data.get('ticker', 'AAPL')
    period = data.get('period', '1y')
    
    # We only need the data to calculate the trend
    stock_data = ml_final.get_stock_data(ticker, period=period, interval='1d')
    if stock_data is None:
        return jsonify({"error": "Could not fetch data"}), 400
        
    is_match, trend = ml_final.pattern_match(stock_data, drawn_slope)
    
    return jsonify({
        "is_match": is_match,
        "trend_slope": trend,
        "drawn_slope": drawn_slope
    })

if __name__ == '__main__':
    # Ensure static and templates folders exist
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    app.run(debug=True, port=5000)
