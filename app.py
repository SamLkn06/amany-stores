from flask import Flask, render_template_string, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "amany2026secret"
DB = r"C:\Users\Auguste LOKONON\boutique.db"
MOT_DE_PASSE = "amany2026"

def init_db():
    conn = sqlite3.connect(DB)
    conn.cursor().execute('''CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY, produit TEXT,
        montant INTEGER, telephone TEXT, date TEXT)''')
    conn.commit()
    conn.close()

PRODUITS = {"Tripod": 15000, "Microphone": 25000,
            "Ring Light": 18000, "Gimbal": 45000}

LOGIN_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>AMANY Stores - Connexion</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0D0D2B;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            font-family: Arial, sans-serif;
        }
        .box {
            background: #1a1a4e;
            border: 1px solid #2ABFBF44;
            border-radius: 15px;
            padding: 40px;
            width: 320px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }
        h2 { color: #fff; margin-bottom: 8px; letter-spacing: 3px; font-size: 24px; }
        h2 span { color: #E8472A; }
        .tagline { color: #2ABFBF; font-size: 11px; letter-spacing: 4px; margin-bottom: 30px; }
        input {
            width: 100%; padding: 13px; margin-bottom: 15px;
            background: #0D0D2B; border: 1px solid #2ABFBF55;
            color: #fff; border-radius: 8px; font-size: 15px;
        }
        button {
            width: 100%; padding: 13px;
            background: linear-gradient(135deg, #E8472A, #c73820);
            color: #fff; border: none; border-radius: 8px;
            font-size: 15px; font-weight: bold; cursor: pointer;
            letter-spacing: 2px;
        }
        .error { color: #E8472A; margin-bottom: 15px; font-size: 14px; }
    </style>
</head>
<body>
<div class="box">
    <h2>AMANY <span>Stores</span></h2>
    <p class="tagline">FAST · SAFE · QUALITY</p>
    {% if erreur %}<p class="error">❌ Mot de passe incorrect</p>{% endif %}
    <form method="POST">
        <input type="password" name="mdp" placeholder="Mot de passe" required>
        <button type="submit">CONNEXION</button>
    </form>
</div>
</body>
</html>
'''

PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>AMANY Stores</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Raleway:wght@300;400;600&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0D0D2B;
            color: #f0f0f0;
            font-family: 'Raleway', Arial, sans-serif;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #0D0D2B 0%, #1a1a4e 100%);
            border-bottom: 3px solid #E8472A;
            padding: 25px 20px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(232,71,42,0.3);
        }
        .logo-area { display: flex; align-items: center; justify-content: center; gap: 15px; }
        .logo-icon {
            width: 60px; height: 60px;
            background: linear-gradient(135deg, #2ABFBF, #E8472A);
            clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
        }
        .header h1 {
            font-family: 'Cinzel', serif;
            color: #ffffff; font-size: 32px; letter-spacing: 4px;
        }
        .header h1 span { color: #E8472A; }
        .tagline { color: #2ABFBF; font-size: 12px; letter-spacing: 5px; margin-top: 8px; text-transform: uppercase; }
        .logout-btn {
            position: absolute; right: 20px; top: 25px;
            background: transparent; border: 1px solid #E8472A;
            color: #E8472A; padding: 8px 16px; border-radius: 6px;
            cursor: pointer; font-size: 12px; letter-spacing: 1px;
            text-decoration: none;
        }
        .stats-bar {
            background: linear-gradient(90deg, #1a1a4e, #0D0D2B);
            border-bottom: 1px solid #2ABFBF33;
            padding: 15px 20px;
            display: flex; justify-content: center; gap: 40px;
        }
        .stat { text-align: center; }
        .stat-number { color: #FFD700; font-size: 22px; font-weight: bold; }
        .stat-label { color: #2ABFBF; font-size: 11px; letter-spacing: 2px; }
        .container { max-width: 850px; margin: 35px auto; padding: 0 20px; }
        .card {
            background: linear-gradient(145deg, #1a1a4e, #141430);
            border: 1px solid #2ABFBF44; border-radius: 15px;
            padding: 30px; margin-bottom: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }
        .card-title {
            color: #2ABFBF; font-size: 14px; letter-spacing: 3px;
            text-transform: uppercase; margin-bottom: 25px;
            padding-bottom: 12px; border-bottom: 1px solid #E8472A44;
        }
        select, input {
            width: 100%; padding: 14px 16px; margin-bottom: 15px;
            background: #0D0D2B; border: 1px solid #2ABFBF55;
            color: #f0f0f0; border-radius: 8px; font-size: 15px;
            font-family: 'Raleway', sans-serif;
        }
        .btn {
            width: 100%; padding: 15px;
            background: linear-gradient(135deg, #E8472A, #c73820);
            color: #ffffff; border: none; border-radius: 8px;
            font-size: 15px; font-weight: 600; letter-spacing: 2px;
            cursor: pointer; text-transform: uppercase;
            box-shadow: 0 4px 15px rgba(232,71,42,0.4);
        }
        table { width: 100%; border-collapse: collapse; }
        th {
            background: linear-gradient(90deg, #E8472A, #c73820);
            color: #fff; padding: 13px; font-size: 12px;
            letter-spacing: 2px; text-transform: uppercase;
        }
        td {
            padding: 12px; border-bottom: 1px solid #2ABFBF22;
            text-align: center; font-size: 14px; color: #ddd;
        }
        tr:hover td { background: #1a1a4e; color: #fff; }
        .btn-delete {
            background: transparent; border: 1px solid #E8472A;
            color: #E8472A; padding: 5px 12px; border-radius: 5px;
            cursor: pointer; font-size: 12px;
        }
        .total-box {
            margin-top: 20px; padding: 15px 20px;
            background: linear-gradient(135deg, #1a1a4e, #0D0D2B);
            border: 1px solid #FFD700; border-radius: 8px;
            display: flex; justify-content: space-between; align-items: center;
        }
        .total-label { color: #2ABFBF; letter-spacing: 2px; font-size: 13px; }
        .total-amount { color: #FFD700; font-size: 22px; font-weight: bold; }
        .footer { text-align: center; padding: 20px; color: #444; font-size: 12px; letter-spacing: 2px; }
    </style>
</head>
<body>
    <div class="header" style="position:relative;">
        <div class="logo-area">
            <div class="logo-icon"></div>
            <div>
                <h1>AMANY <span>Stores</span></h1>
                <p class="tagline">Fast · Safe · Quality</p>
            </div>
        </div>
        <a href="/logout" class="logout-btn">🔒 DÉCONNEXION</a>
    </div>

    <div class="stats-bar">
        <div class="stat">
            <div class="stat-number">{{ventes|length}}</div>
            <div class="stat-label">Ventes</div>
        </div>
        <div class="stat">
            <div class="stat-number">{{total}} FCFA</div>
            <div class="stat-label">Total</div>
        </div>
        <div class="stat">
            <div class="stat-number">{{produits|length}}</div>
            <div class="stat-label">Produits</div>
        </div>
    </div>

    <div class="container">
        <div class="card">
            <p class="card-title">➕ Nouvelle vente</p>
            <form method="POST" action="/vendre">
                <select name="produit">
                    {% for p, prix in produits.items() %}
                    <option value="{{p}}">{{p}} — {{prix}} FCFA</option>
                    {% endfor %}
                </select>
                <input name="telephone" placeholder="Numéro client (+229 01...)">
                <button class="btn" type="submit">Enregistrer la vente</button>
            </form>
        </div>

        <div class="card">
            <p class="card-title">📊 Historique des ventes</p>
            <table>
                <tr>
                    <th>ID</th><th>Produit</th><th>Montant</th>
                    <th>Téléphone</th><th>Date</th><th>Action</th>
                </tr>
                {% for v in ventes %}
                <tr>
                    <td>{{v[0]}}</td><td>{{v[1]}}</td>
                    <td>{{v[2]}} FCFA</td><td>{{v[3]}}</td><td>{{v[4]}}</td>
                    <td>
                        <form method="POST" action="/supprimer/{{v[0]}}">
                            <button class="btn-delete" type="submit">🗑️</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </table>
            <div class="total-box">
                <span class="total-label">TOTAL GÉNÉRAL</span>
                <span class="total-amount">{{total}} FCFA</span>
            </div>
        </div>
    </div>

    <div class="footer">© 2026 AMANY STORES · COTONOU, BÉNIN</div>
</body>
</html>
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['mdp'] == MOT_DE_PASSE:
            session['connecte'] = True
            return redirect('/')
        return render_template_string(LOGIN_PAGE, erreur=True)
    return render_template_string(LOGIN_PAGE, erreur=False)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def accueil():
    if not session.get('connecte'):
        return redirect('/login')
    conn = sqlite3.connect(DB)
    ventes = conn.cursor().execute("SELECT * FROM ventes").fetchall()
    conn.close()
    total = sum(v[2] for v in ventes)
    return render_template_string(PAGE, ventes=ventes, produits=PRODUITS, total=total)

@app.route('/vendre', methods=['POST'])
def vendre():
    if not session.get('connecte'):
        return redirect('/login')
    produit = request.form['produit']
    telephone = request.form['telephone']
    montant = PRODUITS.get(produit, 0)
    conn = sqlite3.connect(DB)
    conn.cursor().execute(
        "INSERT INTO ventes (produit,montant,telephone,date) VALUES (?,?,?,datetime('now'))",
        (produit, montant, telephone))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/supprimer/<int:id>', methods=['POST'])
def supprimer(id):
    if not session.get('connecte'):
        return redirect('/login')
    conn = sqlite3.connect(DB)
    conn.cursor().execute("DELETE FROM ventes WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')

init_db()
if __name__ == '__main__':
    app.run(debug=True)
