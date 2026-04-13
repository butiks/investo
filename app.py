from flask import Flask, render_template, request, url_for,redirect,session
import sqlite3
import yfinance as yf
import pandas as pd

from werkzeug.security import generate_password_hash, check_password_hash


# izveido lietotnes objektu
app = Flask(__name__)
app.secret_key = "loti_slepeni_123"
@app.before_request
def gatekeeper():
    # Saraksts ar ceļiem, kuriem var piekļūt bez ielogošanās
    # Jāpārbauda savi funkciju (funkciju, nevis path) nosaukumi!
    publiskie_celi = ['login', 'registreties', 'static']
    
    # Ja lietotājs nav sesijā un mēģina piekļūt ne-publiskam ceļam
    if 'id' not in session and request.endpoint not in publiskie_celi:
        return redirect("/pieteikties")

@app.route("/") # Sākuma lapa
def sakums():
	return render_template("pamats.html")

@app.route("/meklet") # Lapa finanšu instrumentu meklēšanai
def meklet():
	 instrumenti = {
        "Akcijas": [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "BRK-B", "V", "JNJ", 
            "WMT", "MA", "PG", "UNH", "HD", "BAC", "DIS", "ADBE", "NFLX", "PFE"
        ],
        "ETF Fondi": [
            "SPY", "IVV", "VOO", "QQQ", "VTI", "VEA", "IEFA", "VUG", "VTV", "VWO", 
            "IJR", "IWF", "IJH", "IWD", "VXUS", "VIG", "SCHD", "QUAL", "VGT", "XLK"
        ],
        "Obligāciju ETF": [
            "BND", "AGG", "BNDX", "TLT", "LQD", "VCIT", "BSV", "BIV", "VCSH", "TIP", 
            "IEF", "SHY", "MBB", "MUB", "HYG", "JNK", "GOVT", "VGIT", "VMBS", "EMB"
        ]
    }






   # data = yf.download(all_tickers, period="1d", group_by='ticker', threads=True)

@app.route("/registreties") # Reģistrācijas lapa
def registreties():
	return render_template("registreties.html")

@app.route("/pieteikties", methods =['GET', 'POST']) # Pieteikšanās lapa
def login():
	if request.method == 'POST':
		lietotajs = request.form.get('lietotajs')
		parole = request.form.get('parole')

		conn = sqlite3.connect("investicijas.db")
		conn.row_factory = sqlite3.Row
		c = conn.cursor()
		c.execute("SELECT * FROM lietotaji WHERE lietotajvards = ?", (lietotajs,))
		atbilde = c.fetchone()
		conn.close()
		if atbilde and check_password_hash(atbilde['parole'], parole):
			session["id"] = atbilde["id"]
			session["lietotajvards"] = atbilde["lietotajvards"]
			return redirect("/")
		else:
			return "Nepareizi dati!"


	return render_template("login.html")

	

if __name__ == "__main__":
	app.run(debug = True)