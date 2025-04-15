from flask import Flask, render_template_string 
import yfinance as yf
import pandas as pd
from datetime import datetime

app = Flask(__name__)

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

def get_data():
    rows = []
    for symbol, name in TITLES.items():
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
            data = {
                'Nom': name,
                'Heure': 'ERR',
                'Veille': '-', 'Ouverture': '-', 'Bas': '-', 'Haut': '-',
                'Spot': '-', 'Volume': '-', 'Change': f'Erreur: {e}'
            }
        rows.append(data)
    return rows

def get_fx_data():
    pairs = {
        'USD/EUR': 'USDEUR=X',
        'USD/JPY': 'USDJPY=X',
        'GBP/EUR': 'GBPEUR=X',
        'EUR/JPY': 'EURJPY=X'
    }
    data = []
    for label, ticker in pairs.items():
        try:
            info = yf.Ticker(ticker).info
            data.append({
                'pair': label,
                'bid': round(info.get('bid', 0), 4),
                'ask': round(info.get('ask', 0), 4)
            })
        except:
            data.append({'pair': label, 'bid': '-', 'ask': '-'})
    return data

def get_interest_rates():
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
    return render_template_string(TEMPLATE, data=data, now=now,
                              fx_rates=get_fx_data(), rates=get_interest_rates())


TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Bourse</title>
  <meta http-equiv="refresh" content="60">
  <style>
    body { font-family: Arial, sans-serif; padding: 20px; }
    h1 { margin-bottom: 0; }
    table { border-collapse: collapse; width: 100%; margin-top: 10px; }
    th, td { border: 1px solid #000; padding: 8px; text-align: center; }
    th { background: #eee; }
    td.red { color: red; }
    .header { margin-bottom: 10px; }
    .tables-container { display: flex; justify-content: space-between; margin-top: 30px; }
    .table-wrapper { width: 48%; }
  </style>
</head>
<body>
  <div class="header">
    <h1>Bourse</h1>
    <p><strong>DATE :</strong> {{ now.split(' ')[0] }}<br>
       <strong>Heure :</strong> {{ now }}</p>
  </div>
  <table>
    <thead>
      <tr>
        <th>TITRE</th>
        <th>Veille</th>
        <th>Ouverture</th>
        <th>+ Bas</th>
        <th>+ Haut</th>
        <th>Spot</th>
        <th>Volume</th>
        <th>% Veille</th>
      </tr>
    </thead>
    <tbody>
      {% for row in data %}
        <tr>
          <td>
            {{ row.Nom }}<br><small>{{ row.Heure }}</small>
          </td>
          <td>{{ row.Veille }}</td>
          <td>{{ row.Ouverture }}</td>
          <td>{{ row.Bas }}</td>
          <td>{{ row.Haut }}</td>
          <td>{{ row.Spot }}</td>
          <td>{{ row.Volume }}</td>
          <td class="{{ 'red' if '-' in row.Change else '' }}">{{ row.Change }}</td>
        </tr>
      {% endfor %}
    </tbody>
  </table>
  <div class="tables-container">
    <div class="table-wrapper">
      <h3>Taux de Change</h3>
      <table>
        <thead>
          <tr><th>Devise</th><th>Cours Bid</th><th>Cours Ask</th></tr>
        </thead>
        <tbody>
          {% for fx in fx_rates %}
          <tr>
            <td>{{ fx.pair }}</td>
            <td>{{ fx.bid }}</td>
            <td>{{ fx.ask }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    <div class="table-wrapper">
      <h3>Taux d’intérêt</h3>
      <table>
        <thead>
          <tr><th>Échéance</th><th>EUR</th></tr>
        </thead>
        <tbody>
          {% for rate in rates %}
          <tr>
            <td>{{ rate.label }}</td>
            <td>{{ rate.value }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)
