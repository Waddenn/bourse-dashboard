import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Flask, render_template
import yfinance as yf
from flask_caching import Cache

# Configuration de l'application Flask
app = Flask(__name__)

# Configuration du cache (utilisation de Redis)
app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_HOST'] = 'localhost'
app.config['CACHE_REDIS_PORT'] = 6379
app.config['CACHE_REDIS_DB'] = 0
app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'
app.config['CACHE_DEFAULT_TIMEOUT'] = 60  # cache pendant 60 secondes
cache = Cache(app)

# Configuration de la journalisation
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Dictionnaire des tickers et leurs libellés
TITLES = {
    'KER.PA': 'KERING',
    'MC.PA': 'LVMH',
    'RMS.PA': 'HERMES',
    'CFR.SW': 'RICHEMONT',
    'BRBY.L': 'BURBERRY',
    'OR.PA': "L'OREAL",
    'PUM.DE': 'PUMA',
    'ADS.DE': 'ADIDAS',
    'EN.PA': 'BOUYGUES',
    '^FCHI': 'CAC 40'
}

def fetch_ticker_data(symbol, name):
    """Fonction pour récupérer les données d’un ticker via yfinance."""
    logger.info("Appel à l'API pour le ticker: %s", symbol)
    try:
        info = yf.Ticker(symbol).info
        data = {
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
    except Exception as e:
        logger.error("Erreur lors de la récupération de %s: %s", symbol, e)
        data = {
            'Nom': name,
            'Heure': 'ERR',
            'Veille': '-', 'Ouverture': '-', 'Bas': '-', 'Haut': '-',
            'Spot': '-', 'Volume': '-', 'Change': f'Erreur: {e}'
        }
    return data

@cache.cached(key_prefix='market_data')
def get_data():
    """Récupère les données de tous les tickers en parallèle et renvoie une liste de dictionnaires."""
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_ticker_data, symbol, name): symbol for symbol, name in TITLES.items()}
        for future in as_completed(futures):
            results.append(future.result())
    return results

def fetch_fx_data(label, ticker):
    """Récupère les données de change pour une paire donnée."""
    logger.info("Appel à l'API pour la paire de devises: %s", label)
    try:
        info = yf.Ticker(ticker).info
        return {
            'pair': label,
            'bid': round(info.get('bid', 0), 4),
            'ask': round(info.get('ask', 0), 4)
        }
    except Exception as e:
        logger.error("Erreur lors de la récupération de FX pour %s: %s", label, e)
        return {'pair': label, 'bid': '-', 'ask': '-'}

@cache.cached(key_prefix='fx_data')
def get_fx_data():
    """Récupère les taux de change en parallèle."""
    pairs = {
        'USD/EUR': 'USDEUR=X',
        'USD/JPY': 'USDJPY=X',
        'GBP/EUR': 'GBPEUR=X',
        'EUR/JPY': 'EURJPY=X'
    }
    results = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fetch_fx_data, label, ticker): label for label, ticker in pairs.items()}
        for future in as_completed(futures):
            results.append(future.result())
    return results

def get_interest_rates():
    """Retourne une liste de taux d’intérêts prédéfinis."""
    return [
        {'label': 'JJ (Ester)', 'value': '2.417'},
        {'label': 'EUR 1 M', 'value': '2.207'},
        {'label': 'EUR 3 M', 'value': '2.263'},
        {'label': 'EUR 6 M', 'value': '2.214'},
        {'label': 'EUR 1 Y', 'value': '2.126'},
    ]

@app.route("/")
def index():
    now = datetime.now().strftime('%d/%m/%Y %H:%M')
    data = get_data()
    fx_rates = get_fx_data()
    rates = get_interest_rates()
    return render_template("index.html", data=data, now=now, fx_rates=fx_rates, rates=rates)

# Le point d'entrée de l'application. En production, il est recommandé d’utiliser un serveur WSGI (comme Gunicorn)
if __name__ == "__main__":
    # Pour la production, le debug doit être désactivé
    app.run(host="0.0.0.0", port=5000)
