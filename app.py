from flask import Flask, render_template_string, request, redirect, session, send_file
import sqlite3
import openpyxl
import io

app = Flask(__name__)
app.secret_key = "amany2026secret"
DB = r"C:\Users\Auguste LOKONON\boutique.db"
MOT_DE_PASSE = "amany2026"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY, produit TEXT,
        montant INTEGER, telephone TEXT, date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY, nom TEXT, prix INTEGER)''')
    if c.execute("SELECT COUNT(*) FROM produits").fetchone()[0] == 0:
        for nom, prix in [("Tripod", 15000), ("Microphone", 25000),
                          ("Ring Light", 18000), ("Gimbal", 45000)]:
            c.execute("INSERT INTO produits (nom, prix) VALUES (?,?)", (nom, prix))
    conn.commit()
    conn.close()

def get_produits():
    conn = sqlite3.connect(DB)
    rows = conn.cursor().execute("SELECT nom, prix FROM produits").fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}

LOGIN_PAGE = '''<!DOCTYPE html><html><head><title>AMANY Stores</title>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#0D0D2B; display:flex; justify-content:center; align-items:center; min-height:100vh; font-family:Arial,sans-serif; }
.box { background:#1a1a4e; border:1px solid #2ABFBF44; border-radius:15px; padding:40px; width:320px; text-align:center; }
h2 { color:#fff; margin-bottom:8px; letter-spacing:3px; font-size:24px; }
h2 span { color:#E8472A; }
.tagline { color:#2ABFBF; font-size:11px; letter-spacing:4px; margin-bottom:30px; }
input { width:100%; padding:13px; margin-bottom:15px; background:#0D0D2B; border:1px solid #2ABFBF55; color:#fff; border-radius:8px; font-size:15px; }
button { width:100%; padding:13px; background:linear-gradient(135deg,#E8472A,#c73820); color:#fff; border:none; border-radius:8px; font-size:15px; font-weight:bold; cursor:pointer; letter-spacing:2px; }
.error { color:#E8472A; margin-bottom:15px; font-size:14px; }
</style></head><body>
<div class="box">
<h2>AMANY <span>Stores</span></h2>
<p class="tagline">FAST - SAFE - QUALITY</p>
{% if erreur %}<p class="error">Mot de passe incorrect</p>{% endif %}
<form method="POST">
<input type="password" name="mdp" placeholder="Mot de passe" required>
<button type="submit">CONNEXION</button>
</form></div></body></html>'''

PAGE = '''<!DOCTYPE html><html><head>
<title>AMANY Stores</title>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Raleway:wght@300;400;600&display=swap');
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#0D0D2B; color:#f0f0f0; font-family:'Raleway',Arial,sans-serif; min-height:100vh; }
.header { background:linear-gradient(135deg,#0D0D2B,#1a1a4e); border-bottom:3px solid #E8472A; padding:25px 20px; text-align:center; position:relative; }
.logo-area { display:flex; align-items:center; justify-content:center; gap:15px; }
.logo-icon { width:60px; height:60px; background:linear-gradient(135deg,#2ABFBF,#E8472A); clip-path:polygon(50% 0%,0% 100%,100% 100%); }
.header h1 { font-family:'Cinzel',serif; color:#fff; font-size:32px; letter-spacing:4px; }
.header h1 span { color:#E8472A; }
.tagline { color:#2ABFBF; font-size:12px; letter-spacing:5px; margin-top:8px; }
.logout-btn { position:absolute; right:20px; top:30px; background:transparent; border:1px solid #E8472A; color:#E8472A; padding:8px 16px; border-radius:6px; font-size:12px; text-decoration:none; }
.stats-bar { background:linear-gradient(90deg,#1a1a4e,#0D0D2B); border-bottom:1px solid #2ABFBF33; padding:15px 20px; display:flex; justify-content:center; gap:40px; }
.stat { text-align:center; }
.stat-number { color:#FFD700; font-size:22px; font-weight:bold; }
.stat-label { color:#2ABFBF; font-size:11px; letter-spacing:2px; }
.container { max-width:850px; margin:35px auto; padding:0 20px; }
.card { background:linear-gradient(145deg,#1a1a4e,#141430); border:1px solid #2ABFBF44; border-radius:15px; padding:30px; margin-bottom:25px; box-shadow:0 8px 32px rgba(0,0,0,0.4); }
.card-title { color:#2ABFBF; font-size:14px; letter-spacing:3px; text-transform:uppercase; margin-bottom:25px; padding-bottom:12px; border-bottom:1px solid #E8472A44; }
select, input { width:100%; padding:14px 16px; margin-bottom:15px; background:#0D0D2B; border:1px solid #2ABFBF55; color:#f0f0f0; border-radius:8px; font-size:15px; font-family:'Raleway',sans-serif; }
.btn { width:100%; padding:15px; background:linear-gradient(135deg,#E8472A,#c73820); color:#fff; border:none; border-radius:8px; font-size:15px; font-weight:600; letter-spacing:2px; cursor:pointer; text-transform:uppercase; margin-bottom:10px; }
.btn-cyan { background:linear-gradient(135deg,#2ABFBF,#1a9999); }
.btn-gold { background:linear-gradient(135deg,#FFD700,#e6c200); color:#0D0D2B; }
table { width:100%; border-collapse:collapse; }
th { background:linear-gradient(90deg,#E8472A,#c73820); color:#fff; padding:13px; font-size:12px; letter-spacing:2px; text-transform:uppercase; }
td { padding:12px; border-bottom:1px solid #2ABFBF22; text-align:center; font-size:14px; color:#ddd; }
tr:hover td { background:#1a1a4e; }
.btn-del { background:transparent; border:1px solid #E8472A; color:#E8472A; padding:5px 12px; border-radius:5px; cursor:pointer; font-size:12px; }
.total-box { margin-top:20px; padding:15px 20px; background:linear-gradient(135deg,#1a1a4e,#0D0D2B); border:1px solid #FFD700; border-radius:8px; display:flex; justify-content:space-between; align-items:center; }
.total-label { color:#2ABFBF; letter-spacing:2px; font-size:13px; }
.total-amount { color:#FFD700; font-size:22px; font-weight:bold; }
.grid2 { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
.success { color:#2ABFBF; margin-bottom:15px; font-size:14px; }
.footer { text-align:center; padding:20px; color:#444; font-size:12px; letter-spacing:2px; }
</style></head><body>

<div class="header">
<div class="logo-area">
<div class="logo-icon"></div>
<div><h1>AMANY <span>Stores</span></h1><p class="tagline">Fast - Safe - Quality</p></div>
</div>
<a href="/logout" class="logout-btn">Deconnexion</a>
</div>

<div class="stats-bar">
<div class="stat"><div class="stat-number">{{ventes|length}}</div><div class="stat-label">Ventes</div></div>
<div class="stat"><div class="stat-number">{{total}} FCFA</div><div class="stat-label">Total</div></div>
<div class="stat"><div class="stat-number">{{produits|length}}</div><div class="stat-label">Produits</div></div>
</div>

<div class="container">

<div class="card">
<p class="card-title">Nouvelle vente</p>
<form method="POST" action="/vendre">
<select name="produit">
{% for p, prix in produits.items() %}
<option value="{{p}}">{{p}} - {{prix}} FCFA</option>
{% endfor %}
</select>
<input name="telephone" placeholder="Numero client (+229 01...)">
<button class="btn" type="submit">Enregistrer la vente</button>
</form>
</div>

<div class="card">
<p class="card-title">Gestion des produits</p>
{% if msg %}<p class="success">{{msg}}</p>{% endif %}
<form method="POST" action="/produit/ajouter">
<div class="grid2">
<input name="nom" placeholder="Nom du produit" required>
<input name="prix" type="number" placeholder="Prix FCFA" required>
</div>
<button class="btn btn-cyan" type="submit">+ Ajouter un produit</button>
</form>
<table style="margin-top:15px">
<tr><th>Produit</th><th>Prix</th><th>Supprimer</th></tr>
{% for p, prix in produits.items() %}
<tr>
<td>{{p}}</td><td>{{prix}} FCFA</td>
<td>
<form method="POST" action="/produit/supprimer/{{p}}" style="display:inline">
<button class="btn-del" type="submit">Supprimer</button>
</form>
</td>
</tr>
{% endfor %}
</table>
</div>

<div class="card">
<p class="card-title">Historique des ventes</p>
<a href="/export" style="text-decoration:none">
<button class="btn btn-gold" style="margin-bottom:20px">Telecharger Excel</button>
</a>
<table>
<tr><th>ID</th><th>Produit</th><th>Montant</th><th>Telephone</th><th>Date</th><th>Action</th></tr>
{% for v in ventes %}
<tr>
<td>{{v[0]}}</td><td>{{v[1]}}</td><td>{{v[2]}} FCFA</td><td>{{v[3]}}</td><td>{{v[4]}}</td>
<td>
<form method="POST" action="/supprimer/{{v[0]}}">
<button class="btn-del" type="submit">X</button>
</form>
</td>
</tr>
{% endfor %}
</table>
<div class="total-box">
<span class="total-label">TOTAL GENERAL</span>
<span class="total-amount">{{total}} FCFA</span>
</div>
</div>

</div>
<div class="footer">2026 AMANY STORES - COTONOU, BENIN</div>
</body></html>'''

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
    msg = request.args.get('msg', '')
    return render_template_string(PAGE, ventes=ventes, produits=get_produits(), total=total, msg=msg)

@app.route('/vendre', methods=['POST'])
def vendre():
    if not session.get('connecte'):
        return redirect('/login')
    produit = request.form['produit']
    telephone = request.form['telephone']
    montant = get_produits().get(produit, 0)
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

@app.route('/produit/ajouter', methods=['POST'])
def produit_ajouter():
    if not session.get('connecte'):
        return redirect('/login')
    nom = request.form['nom'].strip()
    prix = int(request.form['prix'])
    conn = sqlite3.connect(DB)
    conn.cursor().execute("INSERT INTO produits (nom, prix) VALUES (?,?)", (nom, prix))
    conn.commit()
    conn.close()
    return redirect('/?msg=Produit ajoute avec succes')

@app.route('/produit/supprimer/<nom>', methods=['POST'])
def produit_supprimer(nom):
    if not session.get('connecte'):
        return redirect('/login')
    conn = sqlite3.connect(DB)
    conn.cursor().execute("DELETE FROM produits WHERE nom=?", (nom,))
    conn.commit()
    conn.close()
    return redirect('/?msg=Produit supprime')

@app.route('/export')
def export_excel():
    if not session.get('connecte'):
        return redirect('/login')
    conn = sqlite3.connect(DB)
    ventes = conn.cursor().execute("SELECT * FROM ventes").fetchall()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ventes AMANY"

    # En-têtes
    ws.append(["ID", "Produit", "Montant (FCFA)", "Telephone", "Date"])

    # Données
    for v in ventes:
        ws.append(list(v))

    # Total
    ws.append([])
    ws.append(["", "TOTAL", sum(v[2] for v in ventes), "", ""])

    # Largeur colonnes
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 20

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(output,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True,
                     download_name='ventes_amany.xlsx')

init_db()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(__import__('os').environ.get('PORT', 5000)))
