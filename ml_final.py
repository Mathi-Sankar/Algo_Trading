import pandas as pd
import yfinance as yf
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import xgboost as xgb
from datetime import datetime, timedelta
import feedparser
import ssl
import sys
from curl_cffi import requests
sys.modules['requests'] = requests  # Force yfinance to use curl_cffi globally!
import warnings

# Global curl_cffi session to bypass Yahoo Finance IP block on cloud platforms
yf_session = requests.Session(impersonate='chrome110')
import math
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore", category=DeprecationWarning)

from yahooquery import Ticker

def get_stock_data(ticker, period="1y", interval="1d"):
    """
    Fetch stock data using yahooquery.
    """
    try:
        t = Ticker(ticker)
        df = t.history(period=period, interval=interval)
        
        if df.empty:
            return None
            
        if isinstance(df.index, pd.MultiIndex):
            df = df.loc[ticker]
            
        # Capitalize columns to match what the ML pipeline expects
        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        
        df.index = pd.to_datetime(df.index, utc=True).strftime('%Y-%m-%d')
        df.dropna(inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def create_features(data):
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    data['SMA_200'] = data['Close'].rolling(window=200).mean()
    data['Price_Change'] = data['Close'].pct_change()
    data['Market_Crash'] = np.where(data['Price_Change'] < -0.05, 1, 0)
    return data

def train_ml_model(stock_data):
    try:
        stock_data['Price_Change_Direction'] = np.where(stock_data['Price_Change'] > 0, 1, 0)
        X = np.array(range(len(stock_data))).reshape(-1, 1)
        y = stock_data['Price_Change_Direction'].values
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        
        model = RandomForestClassifier(n_estimators=10, max_depth=3, random_state=42)
        model.fit(X_train, y_train)
        return model
    except Exception as e:
        print("Error training ML:", e)
        return None

def calculate_crash_probability(stock_data):
    try:
        stock_data = create_features(stock_data)
        stock_data_clean = stock_data.dropna()

        if len(stock_data_clean) < 10:
            return 50.0 # Default if not enough data

        X = stock_data_clean[['SMA_50', 'SMA_200', 'Price_Change']]
        y = stock_data_clean['Market_Crash']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        model = xgb.XGBClassifier(n_estimators=10, max_depth=3)
        model.fit(X_train, y_train)

        latest_data = pd.DataFrame([stock_data_clean[['SMA_50', 'SMA_200', 'Price_Change']].iloc[-1]])
        predicted_probabilities = model.predict_proba(latest_data)

        crash_probability = predicted_probabilities[0][1] * 100
        return crash_probability
    except Exception as e:
        print(f"Crash probability error: {e}")
        return 0.0

def calculate_aco_probability(stock_data):
    try:
        num_ants = 10
        num_iterations = 3
        pheromone_decay = 0.95
        alpha = 1
        
        recent_data = stock_data.tail(100).reset_index(drop=True)
        if len(recent_data) < 10:
            return 50.0

        pheromone = np.ones(len(recent_data))
        pheromone_scaling_factor = 1e-5

        for iteration in range(num_iterations):
            total_path_score = 0
            for ant in range(num_ants):
                start_point = np.random.randint(0, len(recent_data) - 1)
                current_position = start_point
                path_length = 0
                path_score = 0

                while current_position < len(recent_data) - 1:
                    price_change_factor = np.clip(1 + recent_data['Price_Change'].iloc[current_position], -5, 5)
                    next_move_prob = pheromone[current_position] ** alpha * price_change_factor
                    current_position += np.random.randint(1, 5)
                    path_length += 1
                    path_score += next_move_prob

                    if current_position >= len(recent_data):
                        break
                
                total_path_score += path_score

                for i in range(start_point, min(start_point + path_length, len(recent_data))):
                    pheromone[i] += pheromone_scaling_factor * path_score

            pheromone *= pheromone_decay

        max_pheromone = np.max(pheromone)
        if max_pheromone == 0:
            return 50.0
        aco_probability = pheromone[-1] * 100 / max_pheromone
        return aco_probability
    except Exception as e:
        print(f"ACO error: {e}")
        return 50.0

def get_stock_financial_data(stock_symbol):
    def get_val(section, key):
        try:
            val = section.get(key)
            if val is not None and val != 0 and str(val).lower() != 'nan':
                return float(val)
        except: pass
        return 'N/A'

    # Try yahooquery first
    try:
        t = Ticker(stock_symbol)
        fd = t.financial_data
        sd = t.summary_detail
        dks = t.key_stats
        
        fd_data = fd.get(stock_symbol, {}) if isinstance(fd, dict) else {}
        sd_data = sd.get(stock_symbol, {}) if isinstance(sd, dict) else {}
        dks_data = dks.get(stock_symbol, {}) if isinstance(dks, dict) else {}
        
        if isinstance(fd_data, str): fd_data = {}
        if isinstance(sd_data, str): sd_data = {}
        if isinstance(dks_data, str): dks_data = {}
        
        fin = {
            'EPS': get_val(dks_data, 'trailingEps'),
            'P/E Ratio': get_val(sd_data, 'trailingPE'),
            'Industry P/E Ratio': get_val(sd_data, 'forwardPE'),
            'D/E Ratio': get_val(fd_data, 'debtToEquity'),
            'P/B Ratio': get_val(dks_data, 'priceToBook'),
            'Current Price': get_val(fd_data, 'currentPrice')
        }
    except:
        fin = {'P/E Ratio': 'N/A'}
        
    # If Yahoo failed (Render IP block), fallback to robust scrapers
    if fin.get('P/E Ratio') == 'N/A':
        if stock_symbol.endswith('.NS') or stock_symbol.endswith('.BO'):
            # Indian stock fallback using screener.in
            ticker = stock_symbol[:-3]
            try:
                res = requests.get(f'https://www.screener.in/company/{ticker}/consolidated/', headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                soup = BeautifulSoup(res.text, 'html.parser')
                data = {}
                for li in soup.find_all('li', class_='flex flex-space-between'):
                    name = li.find('span', class_='name').text.strip()
                    val = li.find('span', class_='number').text.strip().replace(',', '')
                    data[name] = float(val) if val else 'N/A'
                
                price = data.get('Current Price', 'N/A')
                pe = data.get('Stock P/E', 'N/A')
                bv = data.get('Book Value', 'N/A')
                
                eps = round(price / pe, 2) if price != 'N/A' and pe != 'N/A' and pe != 0 else 'N/A'
                pb = round(price / bv, 2) if price != 'N/A' and bv != 'N/A' and bv != 0 else 'N/A'
                
                fin.update({'Current Price': price, 'P/E Ratio': pe, 'EPS': eps, 'P/B Ratio': pb})
            except Exception as e:
                print('Screener fallback error:', e)
        else:
            # US stock fallback using finviz.com
            try:
                res = requests.get(f'https://finviz.com/quote.ashx?t={stock_symbol.lower()}', headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                soup = BeautifulSoup(res.text, 'html.parser')
                data = {}
                for tr in soup.find_all('tr', class_='table-dark-row'):
                    tds = tr.find_all('td')
                    for i in range(0, len(tds), 2):
                        if i+1 < len(tds):
                            data[tds[i].text.strip()] = tds[i+1].text.strip()
                            
                try: fin['P/E Ratio'] = float(data.get('P/E', 'N/A'))
                except: pass
                
                try: fin['EPS'] = float(data.get('EPS (ttm)', 'N/A'))
                except: pass
                
                try: fin['D/E Ratio'] = float(data.get('Debt/Eq', 'N/A')) * 100 # Convert to percentage ratio
                except: pass
                
                try: fin['P/B Ratio'] = float(data.get('P/B', 'N/A'))
                except: pass
                
                try: fin['Current Price'] = float(data.get('Price', 'N/A'))
                except: pass
            except Exception as e:
                print('Finviz fallback error:', e)
                
    return fin


def evaluate_financials(financial_data):
    try:
        def get_num(key):
            val = financial_data.get(key, 'N/A')
            if val == 'N/A':
                return None
            try:
                return float(val)
            except:
                return None

        eps           = get_num('EPS')
        pe_ratio      = get_num('P/E Ratio')
        industry_pe   = get_num('Industry P/E Ratio')
        de_ratio      = get_num('D/E Ratio')
        pb_ratio      = get_num('P/B Ratio')

        # A check only passes if the value is actually available (not N/A)
        is_eps_high       = eps is not None and eps > 0
        # P/E only passes if BOTH values exist and P/E is genuinely below forward P/E
        is_pe_ratio_low   = (pe_ratio is not None and industry_pe is not None
                             and pe_ratio <= industry_pe)
        is_de_ratio_low   = de_ratio is not None and de_ratio < 100
        is_pb_ratio_low   = pb_ratio is not None and pb_ratio < 5

        pass_count = sum([is_eps_high, is_pe_ratio_low, is_de_ratio_low, is_pb_ratio_low])
        return {"passed": pass_count >= 2, "score": pass_count}
    except Exception as e:
        return {"passed": False, "score": 0}


analyzer = SentimentIntensityAnalyzer()

def get_sentiment(text):
    sentiment = analyzer.polarity_scores(text)
    return sentiment['compound']

def get_news_data(stock_ticker):
    if not stock_ticker:
        return []
    
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={stock_ticker}&region=US&lang=en-US"
    news = []
    try:
        if hasattr(ssl, '_create_unverified_context'):
            ssl._create_default_https_context = ssl._create_unverified_context
            
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            headline = entry.title
            published = entry.get('published', datetime.today().strftime('%Y-%m-%d'))
            
            news.append({
                "Date": published[:16],
                "Headline": headline,
                "Sentiment": get_sentiment(headline)
            })
        return news
    except Exception as e:
        print(f"Error fetching news for '{stock_ticker}': {e}")
        return []

def analyze_news_sentiment(news_data):
    if not news_data:
        return 50.0, {"positive": 0, "negative": 0, "neutral": 0}
    
    df = pd.DataFrame(news_data)
    average_sentiment_prob = df['Sentiment'].mean()
    # Normalize compound sentiment (-1 to 1) to percentage (0 to 100)
    avg_percentage = ((average_sentiment_prob + 1) / 2) * 100
    
    pos = len(df[df['Sentiment'] > 0.1])
    neg = len(df[df['Sentiment'] < -0.1])
    neu = len(df[(df['Sentiment'] >= -0.1) & (df['Sentiment'] <= 0.1)])
    
    return avg_percentage, {"positive": pos, "negative": neg, "neutral": neu}

def pattern_match(stock_data, drawn_slope):
    """
    Match drawing slope to stock trend over the visible period.
    """
    if stock_data is None or stock_data.empty:
        return False, 0
    
    # Calculate simple linear regression of prices
    prices = stock_data['Close'].values
    if len(prices) < 2: return False, 0
    x = np.arange(len(prices))
    slope, _ = np.polyfit(x, prices, 1)
    
    # Normalize slopes: drawn slope is pixel-based, price slope is price-based.
    # A positive drawn slope usually means going up.
    # Let's map trend direction.
    direction_match = (slope > 0 and drawn_slope > 0) or (slope < 0 and drawn_slope < 0)
    
    abs_slope_compare = abs(slope) > 0.01 # just a basic check if there is a trend
    
    return direction_match, slope

def analyze_stock(ticker, period="1y", interval="1d"):
    data = get_stock_data(ticker, period, interval)
    if data is None:
        return {"error": "Failed to fetch stock data for " + ticker}

    # Prevent JSON nan serialization errors
    def safe_nan(val):
        try:
            if pd.isna(val) or math.isnan(val) or math.isinf(val): return 0.0
            return float(val)
        except:
            return 0.0

    crash_prob = safe_nan(calculate_crash_probability(data))
    
    # ML Upward Probability
    ml_model = train_ml_model(data)
    prob_up = 50.0
    if ml_model is not None:
        try:
            prob_up = ml_model.predict_proba([[len(data)]])[0][1] * 100
        except:
            prob_up = 50.0

    # ACO Probability
    aco_prob = calculate_aco_probability(data)
    if pd.isna(aco_prob): aco_prob = 50.0

    # Financials
    financials = get_stock_financial_data(ticker)
    fin_eval = evaluate_financials(financials)

    # News Sentiment
    news = get_news_data(ticker)
    sentiment_prob, sentiment_stats = analyze_news_sentiment(news)
    if pd.isna(sentiment_prob): sentiment_prob = 50.0

    # Overall recommendation logic matching old app
    if crash_prob > 80:
        recommendation = "Sell the stock (High Crash Risk)."
    elif crash_prob > 50 and prob_up < 75:
        recommendation = "Sell the stock (Moderate Crash Risk)."
    elif sentiment_prob < 40 and prob_up < 55:
        recommendation = "Sell the stock (Negative News Sentiment)."
    elif prob_up >= 55 or aco_prob >= 60:
        recommendation = "Buy the stock!"
        if sentiment_prob > 60:
            recommendation += " (Positive news sentiment)."
    elif 40 <= prob_up < 60 and 40 <= aco_prob < 60:
        recommendation = "Hold the stock."
    else:
        recommendation = "Sell the stock."

    safe_prices = []
    for v in data['Close'].tolist():
        safe_prices.append(safe_nan(v))

    # Format graph data
    graph_data = {
        "dates": [str(d) for d in data.index.tolist()],
        "prices": safe_prices
    }

    # Ensure financials are safe too
    safe_financials = {}
    for k, v in financials.items():
        if isinstance(v, (int, float)):
            safe_financials[k] = safe_nan(v)
        else:
            safe_financials[k] = v

    return {
        "ticker": ticker,
        "recommendation": recommendation,
        "probabilities": {
            "crash": safe_nan(crash_prob),
            "ml_up": safe_nan(prob_up),
            "aco_up": safe_nan(aco_prob),
            "sentiment": safe_nan(sentiment_prob)
        },
        "financials": safe_financials,
        "financial_eval": fin_eval,
        "sentiment_stats": sentiment_stats,
        "graph_data": graph_data,
        "news": news
    }

def search_tickers(query):
    """
    Search for tickers using Yahoo Finance autocomplete API.
    """
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=5"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers)
        data = r.json()
        results = []
        if 'quotes' in data:
            for quote in data['quotes']:
                if 'quoteType' in quote and quote['quoteType'] in ['EQUITY', 'ETF']:
                    results.append({
                        "symbol": quote.get('symbol', ''),
                        "shortname": quote.get('shortname', '')
                    })
        return results
    except Exception as e:
        print("Search error:", e)
        return []