# StockSage — AI-Powered Trading & Sentiment Analysis Platform

> Hi, I'm **[Mathi Sankar M R](https://mathi-sankar.github.io/portfolio)** — I built this AI-powered trading platform to explore the intersection of machine learning, financial sentiment analysis, and predictive algorithms.

🟢 **Live Demo:** [https://algo-trading-a0s5.onrender.com](https://algo-trading-a0s5.onrender.com)

**StockSage** is a full-stack, AI-driven web application designed to provide comprehensive stock market analysis, actionable trading recommendations, and investment estimation tools. By integrating multiple Machine Learning models, heuristic algorithms, and real-time news sentiment analysis, the platform offers a robust, data-driven approach to market forecasting.

The application is built on a **Flask** backend with a modern, responsive **glassmorphism** frontend architecture, prioritizing user experience and data visualization.

---

## 🚀 Key Features

* **Market Explorer**: Real-time ticker search with autocomplete via the Yahoo Finance API, supporting customizable timeframes and charting intervals.
* **Interactive Dashboard**: Clean, dynamic visualizations using Chart.js to track price trends, analyze AI-driven predictive probabilities, and monitor financial health metrics (EPS, P/E, D/E, P/B).
* **Pattern Matching Engine**: An interactive canvas allowing users to draw custom trend lines. The system utilizes Pearson Correlation to statistically compare these user-drawn shapes against the stock's actual price curve.
* **Profit Estimator**: A built-in financial calculator that computes gross profit, configurable tax liabilities, and net returns based on live market pricing.
* **Sentiment Analysis Feed**: Color-coded, real-time financial news aggregator that categorizes headlines into positive, negative, or neutral sentiments.

---

## 🧠 Integrated AI & Mathematical Models

1. **Random Forest Classifier**: Trained on historical index data to predict the probability of upward price movement.
2. **XGBoost Classifier**: Evaluates significant price drop events (>5%) and moving averages (SMA 50, SMA 200) to calculate crash risk probability.
3. **VADER Sentiment Analysis**: A lexicon and rule-based NLP engine that processes recent financial news headlines to gauge market sentiment.
4. **Ant Colony Optimization (ACO)**: A bio-inspired heuristic algorithm that simulates pathfinding to predict stock price trends based on pheromone weighting.
5. **Linear Regression & Pearson Correlation**: Computes the mathematical slope of the stock trend and statistically matches it against user-drawn patterns.

---

## 🛠️ Technology Stack

* **Backend**: Python, Flask
* **Machine Learning & NLP**: scikit-learn, XGBoost, VADER Sentiment
* **Data Sources**: yfinance, Yahoo Finance REST & RSS APIs
* **Frontend**: HTML5, CSS3 (Glassmorphism design system), Vanilla JavaScript
* **Data Visualization**: Chart.js

---

## 📖 How to Use the Software

1. **Market Explorer:** Start by typing a stock symbol (e.g., AAPL for Apple) into the search bar. Select the desired timeframe and interval, then click **Analyze Stock**.
2. **Dashboard Overview:** 
   - **Price Trend:** Review the historical closing prices on the main line chart.
   - **AI Predictors:** Check the probability indicators. High 'Crash Risk' or low 'ML Trend Up' indicates a potential sell, while strong upward indicators suggest a buy.
   - **News Sentiment:** Read through the color-coded news feed to gauge public perception, which is summarized in the sentiment pie chart.
   - **Financial Health:** Ensure the stock passes the fundamental checks (EPS, P/E, D/E, P/B). A 'PASS' means strong company fundamentals.
3. **Drawing & Pattern Matching:** Use the interactive canvas to draw a price movement pattern you expect or recognize. Save the pattern, and then click **Match Stock vs Saved Patterns** to statistically verify if the current stock aligns with your drawn theory.
4. **Profit Estimator:** Enter your initial investment amount, expected selling price, and tax rate. The calculator automatically fetches the current buying price and provides a net profit estimation to help manage risk.

---

## ⚙️ Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Mathi-Sankar/Algo_Trading.git
   cd Algo_Trading
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Access the platform:**
   Navigate to `http://127.0.0.1:5000` in your web browser.

---

*Disclaimer: This project is intended for educational and analytical purposes. It does not constitute financial advice. Always conduct independent research before making investment decisions.*
