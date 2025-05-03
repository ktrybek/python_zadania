from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

plik_magazyn = 'Magazyn.txt'
plik_saldo = 'Saldo_konta.txt'
plik_przeglad = 'Przegląd.txt'


def save_to_file(plik, zawartosc):
    with open(plik, 'w') as file:
        file.write(str(zawartosc))


def load_magazyn():
    if os.path.exists(plik_magazyn):
        with open(plik_magazyn, 'r') as file:
            return eval(file.read())
    return {}


def load_saldo():
    if os.path.exists(plik_saldo):
        with open(plik_saldo, 'r') as file:
            return float(file.read())
    return 0.0


def append_to_przeglad(entry):
    with open(plik_przeglad, 'a', encoding='utf-8') as file:
        file.write(entry + '\n')


@app.route('/', methods=['GET', 'POST'])
def index():
    magazyn = load_magazyn()
    saldo = load_saldo()

    if request.method == 'POST':
        form_type = request.form['form_type']

        if form_type == 'zakup':
            produkt = request.form['produkt']
            cena = float(request.form['cena'])
            ilosc = int(request.form['ilosc'])
            koszt = cena * ilosc

            if saldo >= koszt:
                magazyn[produkt] = magazyn.get(produkt, {'kwota': 0, 'ilosc': 0})
                magazyn[produkt]['kwota'] += koszt
                magazyn[produkt]['ilosc'] += ilosc
                saldo -= koszt
                append_to_przeglad(f"zakup: {produkt}, {ilosc} szt., {koszt} zł")
            else:
                return "Brak środków na zakup"

        elif form_type == 'sprzedaz':
            produkt = request.form['produkt']
            cena = float(request.form['cena'])
            ilosc = int(request.form['ilosc'])

            if produkt in magazyn and magazyn[produkt]['ilosc'] >= ilosc:
                magazyn[produkt]['ilosc'] -= ilosc
                przychod = cena * ilosc
                magazyn[produkt]['kwota'] -= przychod
                saldo += przychod
                append_to_przeglad(f"sprzedaż: {produkt}, {ilosc} szt., {przychod} zł")
            else:
                return "Brak towaru lub za mała ilość"

        elif form_type == 'saldo':
            wartosc = float(request.form['wartosc'])
            komentarz = request.form['komentarz']
            saldo += wartosc
            append_to_przeglad(f"saldo: {wartosc}, komentarz: {komentarz}")

        save_to_file(plik_magazyn, magazyn)
        save_to_file(plik_saldo, saldo)

        return redirect(url_for('index'))

    return render_template('index.html', magazyn=magazyn, saldo=saldo)


@app.route('/historia/')
@app.route('/historia/<int:line_from>/<int:line_to>/')
def historia(line_from=None, line_to=None):
    if os.path.exists(plik_przeglad):
        with open(plik_przeglad, 'r', encoding='utf-8') as file:
            entries = file.readlines()
            if line_from is not None and line_to is not None:
                entries = entries[line_from - 1:line_to]
    else:
        entries = []
    return render_template('historia.html', entries=entries)


if __name__ == '__main__':
    app.run(debug=True)