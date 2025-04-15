from flask import Flask, render_template_string
import yfinance as yf
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# Liste des tickers et noms
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

@app.route("/")
def index():
    now = datetime.now().strftime('%d/%m/%Y %H:%M')
    data = get_data()
    return render_template_string(TEMPLATE, data=data, now=now)

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
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)
