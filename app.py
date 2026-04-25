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

@app.route("/")
def sakums():
    return render_template("pamats.html")
	

@app.route("/pievienot", methods=["POST", "GET"])
def pievienot():
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
            "BND", "AGG", "BNDX", "TLT", "LQD", "VCIT", "BSV"
        ]
    }
    if request.method == "POST":
        symbol = request.form.get("symbol")
        quantity = request.form.get("quantity")

        if not symbol or not quantity:
            return "Trūkst dati"

        quantity = float(quantity)

        if quantity < 0.01:
            return "Minimālais daudzums ir 0.01!"

        conn = sqlite3.connect("investicijas.db")
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute('SELECT ID FROM "Portfeļi" WHERE lietotaja_id = ?', (session["id"],))
        portfelis = c.fetchone()

        if not portfelis:
            c.execute("""
                INSERT INTO "Portfeļi" (lietotaja_id, nosaukums, izveidots, summa)
                VALUES (?, ?, date('now'), ?)
            """, (session["id"], "Mans portfelis", 0))
            portfela_id = c.lastrowid
        else:
            portfela_id = portfelis["ID"]

        c.execute('SELECT ID FROM "Aktivi" WHERE simbols = ?', (symbol,))
        aktivs = c.fetchone()

        if not aktivs:
            c.execute("""
                INSERT INTO "Aktivi" (simbols, nosaukums, aktiva_tips)
                VALUES (?, ?, ?)
            """, (symbol, symbol, "Nav norādīts"))
            aktiva_id = c.lastrowid
        else:
            aktiva_id = aktivs["ID"]

        data = yf.Ticker(symbol).history(period="5d")

        if data.empty:
            conn.close()
            return "Neizdevās iegūt cenu"

        cena = float(data["Close"].iloc[-1])

        c.execute("""
            INSERT INTO "Portfeļa_aktīvi"
            ("portfeļa_id", aktiva_id, daudzums, iegades_cena, iegades_datums)
            VALUES (?, ?, ?, ?, date('now'))
        """, (portfela_id, aktiva_id, quantity, cena))

        conn.commit()
        conn.close()

        

    dati = []

    for kategorija, simboli in instrumenti.items():
        for simbols in simboli:
            data = yf.Ticker(simbols).history(period="5d")

            if not data.empty and len(data) >= 2:
                pedeja_cena = round(float(data["Close"].iloc[-1]), 2)
                iepriekseja_cena = round(float(data["Close"].iloc[-2]), 2)

                izmaina = round(pedeja_cena - iepriekseja_cena, 2)
                proc = round((izmaina / iepriekseja_cena) * 100, 2)

                dati.append({
                    "symbol": simbols,
                    "kategorija": kategorija,
                    "cena": pedeja_cena,
                    "izmaina": izmaina,
                    "proc": proc
                })

    return render_template("pievienot.html", dati=dati)

  


@app.route("/registreties", methods=['GET', 'POST'])
def registreties():
    if request.method == 'POST':
        lietotajs = request.form.get('lietotajs')
        parole = request.form.get('parole')

        hash_parole = generate_password_hash(parole)

        conn = sqlite3.connect("investicijas.db")
        c = conn.cursor()

        c.execute("""
            INSERT INTO Lietotaji (lietotajvards, parole_hash, izveidots)
            VALUES (?, ?, datetime('now'))
        """, (lietotajs, hash_parole))

        conn.commit()
        conn.close()

        return redirect("/pieteikties")

    return render_template("registreties.html")


@app.route("/pieteikties", methods=['GET', 'POST'])# Pieteiksanaas lapa
def login():
    if request.method == 'POST':
        lietotajs = request.form.get('lietotajs')
        parole = request.form.get('parole')

        conn = sqlite3.connect("investicijas.db")
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute("SELECT * FROM Lietotaji WHERE lietotajvards = ?", (lietotajs,))
        atbilde = c.fetchone()

        conn.close()

        if atbilde and check_password_hash(atbilde['parole_hash'], parole):
            session["id"] = atbilde["ID"]
            session["lietotajvards"] = atbilde["lietotajvards"]
            return redirect("/")
        else:
            return "Nepareizs lietotājvārds vai parole!"

    return render_template("login.html")

@app.route("/zinas")  # Lapa finanšu jaunumu lasīšanai, vietne kur uzzināt par jaunāko ekonomikā
def zinas():
    return render_template("zinas.html")
@app.route("/info")  # Lapa informācijas uzziņai, par to, kas vispār ir akcijas, fondi un obligāciju fondi.
def info():
    return render_template("info.html")
@app.route("/apskatit")  
def apskatit():
    conn = sqlite3.connect("investicijas.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT 
            Aktivi.simbols,
            "Portfeļa_aktīvi".daudzums,
            "Portfeļa_aktīvi".iegades_cena,
            "Portfeļa_aktīvi".iegades_datums,
            ROUND("Portfeļa_aktīvi".daudzums * "Portfeļa_aktīvi".iegades_cena, 2) AS jamaksa
        FROM "Portfeļa_aktīvi"
        JOIN Aktivi ON "Portfeļa_aktīvi".aktiva_id = Aktivi.ID
        JOIN "Portfeļi" ON "Portfeļa_aktīvi"."portfeļa_id" = "Portfeļi".ID
        WHERE "Portfeļi".lietotaja_id = ?
    """, (session["id"],))

    pirkumi = c.fetchall()
    conn.close()
    kopejaa_summa = 0
    for p in pirkumi:
        kopejaa_summa += p["jamaksa"]

    return render_template("apkopojums.html",pirkumi=pirkumi,  kopejaa_summa=round(kopejaa_summa, 2))



@app.route("/atslegties")  # Lapa finanšu jaunumu lasīšanai, vietne kur uzzināt par jaunāko ekonomikā
def atslegties():
    session.clear()
    return redirect("/")



if __name__ == "__main__":
	app.run(debug = True)