from flask import Flask, render_template, request, redirect, url_for
import os
import ast

app = Flask(__name__)

PLIK_SALDO = "Saldo_konta.txt"
PLIK_MAGAZYN = "Magazyn.txt"
PLIK_HISTORIA = "Przegląd.txt"

def load_saldo():
    if os.path.exists(PLIK_SALDO):
        with open(PLIK_SALDO) as f:
            return float(f.read())
    return 0.0

def save_saldo(saldo):
    with open(PLIK_SALDO, "w") as f:
        f.write(str(saldo))

def load_magazyn():
    if os.path.exists(PLIK_MAGAZYN):
        with open(PLIK_MAGAZYN) as f:
            return ast.literal_eval(f.read())
    return {}

def save_magazyn(magazyn):
    with open(PLIK_MAGAZYN, "w") as f:
        f.write(str(magazyn))

def add_historia(entry):
    with open(PLIK_HISTORIA, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def load_historia():
    if os.path.exists(PLIK_HISTORIA):
        with open(PLIK_HISTORIA, encoding="utf-8") as f:
            return f.readlines()
    return []

@app.route("/", methods=["GET", "POST"])
def index():
    saldo = load_saldo()
    magazyn = load_magazyn()

    if request.method == "POST":
        if "zakup" in request.form:
            nazwa = request.form["nazwa_zakup"]
            cena = float(request.form["cena_zakup"])
            ilosc = int(request.form["ilosc_zakup"])
            koszt = cena * ilosc

            if saldo >= koszt:
                saldo -= koszt
                magazyn[nazwa] = magazyn.get(nazwa, 0) + ilosc
                add_historia(f"Zakup: {nazwa}, {ilosc} szt., {cena} zł/szt.")
            else:
                add_historia(f"Nieudany zakup: {nazwa} – brak środków")
        elif "sprzedaz" in request.form:
            nazwa = request.form["nazwa_sprzedaz"]
            ilosc = int(request.form["ilosc_sprzedaz"])
            if nazwa in magazyn and magazyn[nazwa] >= ilosc:
                magazyn[nazwa] -= ilosc
                saldo += ilosc
                add_historia(f"Sprzedaż: {nazwa}, {ilosc} szt.")
            else:
                add_historia(f"Nieudana sprzedaż: {nazwa} – brak w magazynie")
        elif "saldo" in request.form:
            wartosc = float(request.form["wartosc_saldo"])
            saldo += wartosc
            add_historia(f"Zmiana salda: {wartosc} zł")

        save_saldo(saldo)
        save_magazyn(magazyn)

        return redirect(url_for("index"))

    return render_template("index.html", saldo=saldo, magazyn=magazyn)

@app.route("/historia/")
@app.route("/historia/<int:start>/<int:end>/")
def historia(start=None, end=None):
    entries = load_historia()
    zakres = (0, len(entries) - 1)
    error = None

    if start is not None and end is not None:
        if 0 <= start <= end < len(entries):
            entries = entries[start:end+1]
        else:
            error = f"Nieprawidłowy zakres. Możliwy zakres to 0–{len(entries) - 1}"

    return render_template("historia.html", entries=entries, error=error, zakres=zakres)

if __name__ == "__main__":
    app.run(debug=True)
