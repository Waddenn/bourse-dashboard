import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Flask, render_template, jsonify
import yfinance as yf
from flask_caching import Cache

# Configuration de l'application Flask
app = Flask(__name__)
app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_HOST'] = 'localhost'
app.config['CACHE_REDIS_PORT'] = 6379
app.config['CACHE_REDIS_DB'] = 0
app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'
app.config['CACHE_DEFAULT_TIMEOUT'] = 60
cache = Cache(app)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TITLES = {
    'KER.PA': 'KERING', 'MC.PA': 'LVMH', 'RMS.PA': 'HERMES',
    'CFR.SW': 'RICHEMONT', 'BRBY.L': 'BURBERRY', 'OR.PA': "L'OREAL",
    'PUM.DE': 'PUMA', 'ADS.DE': 'ADIDAS', 'EN.PA': 'BOUYGUES', '^FCHI': 'CAC 40'
}
FX_PAIRS = {
    'USD/EUR': 'USDEUR=X',
    'USD/JPY': 'USDJPY=X',
    'GBP/EUR': 'GBPEUR=X',
    'EUR/JPY': 'EURJPY=X'
}
INTEREST_RATES = [
    {'label': 'JJ (Ester)', 'value': '2.417'},
    {'label': 'EUR 1 M', 'value': '2.207'},
    {'label': 'EUR 3 M', 'value': '2.263'},
    {'label': 'EUR 6 M', 'value': '2.214'},
    {'label': 'EUR 1 Y', 'value': '2.126'},
]

def fetch_yfinance_info(symbol):
    """Récupère les infos d'un ticker yfinance, gère les erreurs."""
    try:
        return yf.Ticker(symbol).info
    except Exception as e:
        logger.error("Erreur lors de la récupération de %s: %s", symbol, e)
        return None

def build_ticker_row(symbol, name):
    """Construit une ligne de données pour un titre."""
    info = fetch_yfinance_info(symbol)
    if info:
        return {
            'Nom': name,
            'Heure': datetime.now().strftime('%H:%M'),
            'Veille': round(info.get('previousClose', 0), 2),
            'Ouverture': round(info.get('open', 0), 2),
            'Bas': round(info.get('dayLow', 0), 2),
            'Haut': round(info.get('dayHigh', 0), 2),
            'Spot': round(info.get('regularMarketPrice', 0), 2),
            'Volume': f"{info.get('volume', 0):,}".replace(",", " "),
            'Change': f"{round(info.get('regularMarketChangePercent', 0), 2)}%"
        }
    else:
        return {
            'Nom': name, 'Heure': 'ERR',
            'Veille': '-', 'Ouverture': '-', 'Bas': '-', 'Haut': '-',
            'Spot': '-', 'Volume': '-', 'Change': 'Erreur'
        }

def build_fx_row(label, ticker):
    """Construit une ligne de données pour une paire FX."""
    info = fetch_yfinance_info(ticker)
    if info:
        return {
            'pair': label,
            'bid': round(info.get('bid', 0), 4),
            'ask': round(info.get('ask', 0), 4)
        }
    else:
        return {'pair': label, 'bid': '-', 'ask': '-'}

def fetch_parallel(items, builder, max_workers=5, ordered_keys=None):
    """Récupère des données en parallèle avec un builder donné. Si ordered_keys est fourni, retourne les résultats dans cet ordre."""
    results_map = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(builder, *args): key for key, args in items.items()}
        for future in as_completed(futures):
            key = futures[future]
            results_map[key] = future.result()
    if ordered_keys:
        return [results_map[k] for k in ordered_keys if k in results_map]
    return list(results_map.values())

@cache.cached(key_prefix='market_data')
def get_data():
    """Récupère les données de tous les tickers en parallèle, dans l'ordre défini."""
    items = {symbol: (symbol, name) for symbol, name in TITLES.items()}
    ordered_keys = list(TITLES.keys())
    return fetch_parallel(items, build_ticker_row, max_workers=5, ordered_keys=ordered_keys)

@cache.cached(key_prefix='fx_data')
def get_fx_data():
    """Récupère les taux de change en parallèle."""
    items = {label: (label, ticker) for label, ticker in FX_PAIRS.items()}
    return fetch_parallel(items, build_fx_row, max_workers=4)

def get_interest_rates():
    """Retourne la liste des taux d’intérêts prédéfinis."""
    return INTEREST_RATES

@app.route("/api/market_data")
def api_market_data():
    data = get_data()
    return jsonify(data)

@app.route("/api/fx_data")
def api_fx_data():
    fx_rates = get_fx_data()
    return jsonify(fx_rates)

@app.route("/")
def index():
    now = datetime.now().strftime('%d/%m/%Y %H:%M')
    data = get_data()
    fx_rates = get_fx_data()
    rates = get_interest_rates()
    return render_template("index.html", data=data, now=now, fx_rates=fx_rates, rates=rates)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)