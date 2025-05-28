from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///baza.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Saldo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wartosc = db.Column(db.Float, nullable=False)

class Produkt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nazwa = db.Column(db.String(100), unique=True, nullable=False)
    ilosc = db.Column(db.Integer, nullable=False)
    cena = db.Column(db.Float, nullable=False)

class Historia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wpis = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()
    if Saldo.query.first() is None:
        db.session.add(Saldo(wartosc=0.0))
        db.session.commit()


@app.route("/", methods=["GET", "POST"])
def main():
    saldo = Saldo.query.first()
    produkty = Produkt.query.all()

    if request.method == "POST":
        action = request.form.get("action")

        try:
            if action == "saldo":
                wartosc = float(request.form.get("wartosc", 0))
                saldo.wartosc += wartosc
                db.session.add(Historia(wpis=f"Zmiana salda: {wartosc} PLN"))

            elif action == "zakup":
                nazwa = request.form.get("nazwa")
                cena = float(request.form.get("cena"))
                ilosc = int(request.form.get("ilosc"))
                koszt = cena * ilosc

                if koszt <= saldo.wartosc:
                    produkt = Produkt.query.filter_by(nazwa=nazwa).first()
                    if produkt:
                        produkt.ilosc += ilosc
                        produkt.cena = cena
                    else:
                        db.session.add(Produkt(nazwa=nazwa, ilosc=ilosc, cena=cena))
                    saldo.wartosc -= koszt
                    db.session.add(Historia(wpis=f"Zakup: {nazwa}, {ilosc} szt. po {cena} PLN"))
                else:
                    db.session.add(Historia(wpis=f"Nieudany zakup: {nazwa}, brak środków"))

            elif action == "sprzedaz":
                nazwa = request.form.get("nazwa")
                ilosc = int(request.form.get("ilosc"))
                produkt = Produkt.query.filter_by(nazwa=nazwa).first()
                if produkt and produkt.ilosc >= ilosc:
                    przychod = produkt.cena * ilosc
                    produkt.ilosc -= ilosc
                    saldo.wartosc += przychod
                    db.session.add(Historia(wpis=f"Sprzedaż: {nazwa}, {ilosc} szt. po {produkt.cena} PLN"))
                    if produkt.ilosc == 0:
                        db.session.delete(produkt)
                else:
                    db.session.add(Historia(wpis=f"Nieudana sprzedaż: {nazwa}"))

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            return f"Błąd: {e}", 500

        return redirect(url_for("main"))

    magazyn = {p.nazwa: {"ilosc": p.ilosc, "cena": p.cena} for p in produkty}
    return render_template("main.html", saldo=saldo.wartosc, magazyn=magazyn)


@app.route("/historia/")
@app.route("/historia/<int:start>/<int:end>/")
def historia(start=0, end=None):
    wpisy = Historia.query.order_by(Historia.id).all()
    if end is None:
        end = len(wpisy)

    if start < 0 or end > len(wpisy) or start >= end:
        error_msg = f"Błędny zakres. Możliwy zakres: 0 - {len(wpisy)}"
        return render_template("historia.html", historia=[], od=start, do=end, error=error_msg)

    return render_template("historia.html", historia=wpisy[start:end], od=start, do=end, error=None)

if __name__ == "__main__":
    app.run(debug=True)