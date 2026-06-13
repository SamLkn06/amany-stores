from flask import Flask, render_template_string, request, redirect, session, send_file
import sqlite3, openpyxl, io, os

app = Flask(__name__)
app.secret_key = "aman2026secret"
DB = os.environ.get("DB_PATH", "boutique.db")
MOT_DE_PASSE = "amany2026"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY, produit TEXT,
        montant INTEGER, telephone TEXT, date TEXT, statut TEXT DEFAULT "livree")''')
    c.execute('''CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY, nom TEXT, prix INTEGER, stock INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS commandes (
        id INTEGER PRIMARY KEY, client TEXT, telephone TEXT,
        produit TEXT, montant INTEGER, statut TEXT DEFAULT "en_attente", date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fournisseurs (
        id INTEGER PRIMARY KEY, nom TEXT, contact TEXT, pays TEXT, note TEXT)''')
    if c.execute("SELECT COUNT(*) FROM produits").fetchone()[0] == 0:
        for nom, prix in [("Tripod", 15000), ("Microphone", 25000),
                          ("Ring Light", 18000), ("Gimbal", 45000)]:
            c.execute("INSERT INTO produits (nom, prix, stock) VALUES (?,?,?)", (nom, prix, 10))
    conn.commit()
    conn.close()

def get_produits():
    conn = sqlite3.connect(DB)
    rows = conn.cursor().execute("SELECT nom, prix FROM produits").fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}

def get_stats():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    nb_ventes = c.execute("SELECT COUNT(*) FROM ventes").fetchone()[0]
    total = c.execute("SELECT COALESCE(SUM(montant),0) FROM ventes").fetchone()[0]
    nb_produits = c.execute("SELECT COUNT(*) FROM produits").fetchone()[0]
    nb_commandes = c.execute("SELECT COUNT(*) FROM commandes WHERE statut='en_attente'").fetchone()[0]
    conn.close()
    return nb_ventes, total, nb_produits, nb_commandes

# ─── LOGO SVG AMAN ───────────────────────────────────────────────
LOGO_SVG = '''<svg width="80" height="90" viewBox="0 0 680 480" xmlns="http://www.w3.org/2000/svg">
<defs>
  <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
    <path d="M2 1L8 5L2 9" fill="none" stroke="#FF6B6B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
  <clipPath id="clipA">
    <polygon points="340,25 182,310 258,310 284,240 396,240 422,310 498,310"/>
  </clipPath>
</defs>
<polygon points="340,25 182,310 258,310 284,240 396,240 422,310 498,310" fill="#0C1B33"/>
<g clip-path="url(#clipA)">
  <g transform="translate(218,28) scale(1.22)">
    <path d="M88,2 C102,0 118,5 130,13 C144,22 152,34 152,48 C152,58 146,66 138,70 C124,66 108,64 92,64 C76,64 60,66 46,70 C38,66 28,56 24,44 C20,30 32,14 52,6 C64,2 76,3 88,2 Z" fill="#06B6D4"/>
    <path d="M138,70 C148,67 160,70 168,78 C176,88 174,102 164,112 C158,118 152,120 148,126 C144,116 140,104 138,92 C136,82 136,74 138,70 Z" fill="#A855F7"/>
    <path d="M24,44 C18,58 12,74 10,90 C8,106 10,122 16,136 C20,144 26,150 24,158 C16,150 8,138 4,124 C0,108 0,90 4,74 C8,60 14,50 24,44 Z" fill="#84CC16"/>
    <path d="M46,70 C60,66 76,64 92,64 C108,64 124,66 138,70 C136,74 136,82 138,92 C140,104 144,116 148,126 C140,130 130,132 120,132 C108,132 96,130 86,126 C72,120 60,110 52,98 C44,86 40,76 46,70 Z" fill="#DC2626"/>
    <path d="M148,126 C152,120 158,118 164,112 C168,120 170,132 166,144 C162,156 154,164 146,170 C140,174 132,176 128,172 C132,162 136,150 138,140 C140,132 144,128 148,126 Z" fill="#F59E0B"/>
    <path d="M24,158 C26,150 20,144 16,136 C24,140 34,144 44,148 C56,152 68,154 80,154 C92,154 104,152 114,148 C122,144 128,138 128,132 C132,140 136,150 138,140 C136,150 132,162 128,172 C120,182 108,190 94,194 C80,198 64,196 52,188 C40,180 30,168 24,158 Z" fill="#2563EB"/>
    <path d="M52,188 C64,196 80,198 94,194 C108,190 120,182 128,172 C122,182 112,192 100,198 C88,204 74,204 62,198 C56,194 52,190 52,188 Z" fill="#2563EB"/>
    <ellipse cx="178" cy="136" rx="8" ry="22" fill="#84CC16" opacity="0.85" transform="rotate(-12,178,136)"/>
    <circle cx="32" cy="102" r="5" fill="#FF2D78"/>
    <circle cx="32" cy="102" r="10" fill="none" stroke="#FF2D78" stroke-width="1.2" opacity="0.45"/>
    <line x1="32" y1="97" x2="120" y2="8" stroke="#FF6B6B" stroke-width="2.5" stroke-linecap="round" marker-end="url(#arr)"/>
  </g>
</g>
<rect x="282" y="235" width="116" height="5" rx="2.5" fill="#06B6D4"/>
</svg>'''

# ─── CSS COMMUN ──────────────────────────────────────────────────
CSS = '''
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box;}
:root{
  --bg:#060D1F;
  --bg2:#0C1829;
  --bg3:#111F35;
  --cyan:#06B6D4;
  --green:#84CC16;
  --red:#DC2626;
  --gold:#F59E0B;
  --purple:#A855F7;
  --blue:#2563EB;
  --text:#E2E8F0;
  --muted:#64748B;
  --border:#1E3A5F;
}
body{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;min-height:100vh;}

/* NAV */
.nav{background:var(--bg2);border-bottom:1px solid var(--border);padding:0 30px;display:flex;align-items:center;justify-content:space-between;height:70px;position:sticky;top:0;z-index:100;}
.nav-brand{display:flex;align-items:center;gap:12px;}
.nav-brand-text{display:flex;flex-direction:column;}
.nav-brand-name{font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:700;color:var(--cyan);letter-spacing:4px;}
.nav-brand-tag{font-size:9px;letter-spacing:3px;color:var(--muted);}
.nav-links{display:flex;gap:6px;}
.nav-link{padding:8px 16px;border-radius:8px;font-size:13px;font-weight:500;text-decoration:none;color:var(--muted);transition:all .2s;}
.nav-link:hover,.nav-link.active{background:var(--bg3);color:var(--text);}
.nav-link.active{border-left:3px solid var(--cyan);padding-left:13px;}
.nav-logout{padding:8px 16px;background:transparent;border:1px solid var(--red);color:var(--red);border-radius:8px;font-size:13px;cursor:pointer;text-decoration:none;}

/* LAYOUT */
.page{max-width:1100px;margin:0 auto;padding:30px 20px;}
.page-title{font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:700;margin-bottom:6px;}
.page-sub{color:var(--muted);font-size:13px;margin-bottom:28px;}

/* STATS */
.stats-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:30px;}
.stat-card{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:22px;position:relative;overflow:hidden;}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;}
.stat-card.cyan::before{background:var(--cyan);}
.stat-card.gold::before{background:var(--gold);}
.stat-card.green::before{background:var(--green);}
.stat-card.purple::before{background:var(--purple);}
.stat-icon{font-size:24px;margin-bottom:10px;}
.stat-val{font-size:28px;font-weight:700;margin-bottom:4px;}
.stat-val.cyan{color:var(--cyan);}
.stat-val.gold{color:var(--gold);}
.stat-val.green{color:var(--green);}
.stat-val.purple{color:var(--purple);}
.stat-lbl{font-size:11px;letter-spacing:2px;color:var(--muted);text-transform:uppercase;}

/* GRID 2 COL */
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px;}

/* CARDS */
.card{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:26px;margin-bottom:20px;}
.card-head{font-size:11px;letter-spacing:3px;color:var(--cyan);text-transform:uppercase;margin-bottom:20px;padding-bottom:12px;border-bottom:1px solid var(--border);}

/* FORMS */
.field{width:100%;padding:13px 15px;margin-bottom:12px;background:var(--bg);border:1px solid var(--border);color:var(--text);border-radius:9px;font-size:14px;font-family:'Inter',sans-serif;outline:none;transition:border .2s;}
.field:focus{border-color:var(--cyan);}
.grid-input{display:grid;grid-template-columns:1fr 1fr;gap:10px;}

/* BUTTONS */
.btn{width:100%;padding:13px;border:none;border-radius:9px;font-size:13px;font-weight:600;letter-spacing:1px;cursor:pointer;text-transform:uppercase;transition:opacity .2s;}
.btn:hover{opacity:.85;}
.btn-red{background:var(--red);color:#fff;}
.btn-cyan{background:var(--cyan);color:#000;}
.btn-gold{background:var(--gold);color:#000;}
.btn-green{background:var(--green);color:#000;}
.btn-sm{width:auto;padding:6px 14px;font-size:11px;}

/* TABLE */
.table-wrap{overflow-x:auto;}
table{width:100%;border-collapse:collapse;}
th{background:var(--bg3);color:var(--muted);padding:12px 14px;font-size:11px;letter-spacing:2px;text-transform:uppercase;text-align:left;border-bottom:1px solid var(--border);}
td{padding:13px 14px;border-bottom:1px solid var(--border);font-size:13px;color:var(--text);}
tr:last-child td{border-bottom:none;}
tr:hover td{background:var(--bg3);}

/* BADGES */
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;}
.badge-green{background:#84CC1622;color:var(--green);border:1px solid #84CC1633;}
.badge-gold{background:#F59E0B22;color:var(--gold);border:1px solid #F59E0B33;}
.badge-red{background:#DC262622;color:var(--red);border:1px solid #DC262633;}

/* TOTAL */
.total-bar{background:var(--bg3);border:1px solid var(--gold);border-radius:10px;padding:16px 22px;display:flex;justify-content:space-between;align-items:center;margin-top:16px;}
.total-bar span:first-child{font-size:12px;letter-spacing:2px;color:var(--muted);}
.total-bar span:last-child{font-size:22px;font-weight:700;color:var(--gold);}

/* ALERT */
.alert{padding:12px 16px;border-radius:8px;margin-bottom:16px;font-size:13px;}
.alert-success{background:#84CC1615;border:1px solid #84CC1640;color:var(--green);}

/* LOGIN */
.login-wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;background:var(--bg);}
.login-box{background:var(--bg2);border:1px solid var(--border);border-radius:18px;padding:48px 40px;width:340px;text-align:center;}
.login-name{font-family:'Space Grotesk',sans-serif;font-size:28px;font-weight:700;color:var(--cyan);letter-spacing:6px;margin:16px 0 4px;}
.login-tag{font-size:10px;letter-spacing:3px;color:var(--muted);margin-bottom:32px;}
.login-error{color:var(--red);font-size:13px;margin-bottom:14px;}

/* FOOTER */
.footer{text-align:center;padding:30px;color:var(--muted);font-size:11px;letter-spacing:3px;}
'''

# ─── TEMPLATES ───────────────────────────────────────────────────
LOGIN = '''<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AMAN — Connexion</title>
<style>{{ css }}</style></head><body>
<div class="login-wrap">
<div class="login-box">
  {{ logo|safe }}
  <div class="login-name">AMAN</div>
  <div class="login-tag">TRUST · SAFETY · QUALITY</div>
  {% if erreur %}<div class="login-error">Mot de passe incorrect</div>{% endif %}
  <form method="POST">
    <input class="field" type="password" name="mdp" placeholder="Mot de passe" required>
    <button class="btn btn-cyan" type="submit">Connexion</button>
  </form>
  <div style="margin-top:20px;font-size:10px;letter-spacing:2px;color:var(--muted)">BÉNIN · AFRIQUE</div>
</div>
</div>
</body></html>'''

DASHBOARD = '''<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AMAN — Dashboard</title>
<style>{{ css }}</style></head><body>

<nav class="nav">
  <div class="nav-brand">
    {{ logo|safe }}
    <div class="nav-brand-text">
      <span class="nav-brand-name">AMAN</span>
      <span class="nav-brand-tag">TRUST · SAFETY · QUALITY</span>
    </div>
  </div>
  <div class="nav-links">
    <a href="/" class="nav-link active">Dashboard</a>
    <a href="/commandes" class="nav-link">Commandes</a>
    <a href="/fournisseurs" class="nav-link">Fournisseurs</a>
    <a href="/catalogue" class="nav-link">Catalogue</a>
  </div>
  <a href="/logout" class="nav-logout">Déconnexion</a>
</nav>

<div class="page">
  <div class="page-title">Dashboard</div>
  <div class="page-sub">Vue d'ensemble — {{ today }}</div>

  <!-- STATS -->
  <div class="stats-grid">
    <div class="stat-card cyan">
      <div class="stat-icon">📦</div>
      <div class="stat-val cyan">{{ nb_ventes }}</div>
      <div class="stat-lbl">Ventes totales</div>
    </div>
    <div class="stat-card gold">
      <div class="stat-icon">💰</div>
      <div class="stat-val gold">{{ "{:,}".format(total) }}</div>
      <div class="stat-lbl">FCFA encaissés</div>
    </div>
    <div class="stat-card green">
      <div class="stat-icon">🛒</div>
      <div class="stat-val green">{{ nb_produits }}</div>
      <div class="stat-lbl">Produits actifs</div>
    </div>
    <div class="stat-card purple">
      <div class="stat-icon">⏳</div>
      <div class="stat-val purple">{{ nb_commandes }}</div>
      <div class="stat-lbl">Commandes en attente</div>
    </div>
  </div>

  <!-- NOUVELLE VENTE + PRODUITS -->
  <div class="grid2">

    <div class="card">
      <div class="card-head">Nouvelle vente</div>
      {% if msg %}<div class="alert alert-success">{{ msg }}</div>{% endif %}
      <form method="POST" action="/vendre">
        <select class="field" name="produit">
          {% for p, prix in produits.items() %}
          <option value="{{ p }}">{{ p }} — {{ "{:,}".format(prix) }} FCFA</option>
          {% endfor %}
        </select>
        <input class="field" name="telephone" placeholder="Numéro client (+229 01...)">
        <button class="btn btn-red" type="submit">Enregistrer la vente</button>
      </form>
    </div>

    <div class="card">
      <div class="card-head">Ajouter un produit</div>
      <form method="POST" action="/produit/ajouter">
        <div class="grid-input">
          <input class="field" name="nom" placeholder="Nom du produit" required>
          <input class="field" name="prix" type="number" placeholder="Prix FCFA" required>
        </div>
        <input class="field" name="stock" type="number" placeholder="Stock initial" value="0">
        <button class="btn btn-cyan" type="submit">+ Ajouter</button>
      </form>
    </div>
  </div>

  <!-- CATALOGUE RÉSUMÉ -->
  <div class="card">
    <div class="card-head">Produits en catalogue</div>
    <div class="table-wrap">
    <table>
      <tr><th>Produit</th><th>Prix</th><th>Action</th></tr>
      {% for p, prix in produits.items() %}
      <tr>
        <td>{{ p }}</td>
        <td><span class="badge badge-gold">{{ "{:,}".format(prix) }} FCFA</span></td>
        <td>
          <form method="POST" action="/produit/supprimer/{{ p }}" style="display:inline">
            <button class="btn btn-sm btn-red" type="submit">Supprimer</button>
          </form>
        </td>
      </tr>
      {% endfor %}
    </table>
    </div>
  </div>

  <!-- HISTORIQUE VENTES -->
  <div class="card">
    <div class="card-head">Historique des ventes</div>
    <a href="/export" style="text-decoration:none">
      <button class="btn btn-gold" style="width:auto;padding:10px 22px;margin-bottom:18px">
        ⬇ Télécharger Excel
      </button>
    </a>
    <div class="table-wrap">
    <table>
      <tr><th>#</th><th>Produit</th><th>Montant</th><th>Téléphone</th><th>Date</th><th>Statut</th><th>Action</th></tr>
      {% for v in ventes %}
      <tr>
        <td>{{ v[0] }}</td>
        <td>{{ v[1] }}</td>
        <td>{{ "{:,}".format(v[2]) }} FCFA</td>
        <td>{{ v[3] }}</td>
        <td>{{ v[4] }}</td>
        <td><span class="badge badge-green">Livrée</span></td>
        <td>
          <form method="POST" action="/supprimer/{{ v[0] }}" style="display:inline">
            <button class="btn btn-sm btn-red" type="submit">✕</button>
          </form>
        </td>
      </tr>
      {% endfor %}
    </table>
    </div>
    <div class="total-bar">
      <span>TOTAL GÉNÉRAL</span>
      <span>{{ "{:,}".format(total) }} FCFA</span>
    </div>
  </div>

</div>
<div class="footer">© 2026 AMAN — COTONOU, BÉNIN · AFRIQUE</div>
</body></html>'''

# ─── ROUTES ──────────────────────────────────────────────────────
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        if request.form['mdp'] == MOT_DE_PASSE:
            session['ok'] = True
            return redirect('/')
        return render_template_string(LOGIN, css=CSS, logo=LOGO_SVG, erreur=True)
    return render_template_string(LOGIN, css=CSS, logo=LOGO_SVG, erreur=False)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def accueil():
    if not session.get('ok'): return redirect('/login')
    conn = sqlite3.connect(DB)
    ventes = conn.cursor().execute("SELECT * FROM ventes ORDER BY id DESC").fetchall()
    conn.close()
    total = sum(v[2] for v in ventes)
    nb_ventes, _, nb_produits, nb_commandes = get_stats()
    from datetime import date
    today = date.today().strftime("%d %B %Y")
    msg = request.args.get('msg','')
    return render_template_string(DASHBOARD, css=CSS, logo=LOGO_SVG,
        ventes=ventes, produits=get_produits(), total=total,
        nb_ventes=nb_ventes, nb_produits=nb_produits, nb_commandes=nb_commandes,
        today=today, msg=msg)

@app.route('/vendre', methods=['POST'])
def vendre():
    if not session.get('ok'): return redirect('/login')
    produit = request.form['produit']
    telephone = request.form.get('telephone','')
    montant = get_produits().get(produit, 0)
    conn = sqlite3.connect(DB)
    conn.cursor().execute(
        "INSERT INTO ventes (produit,montant,telephone,date) VALUES (?,?,?,datetime('now','localtime'))",
        (produit, montant, telephone))
    conn.commit(); conn.close()
    return redirect('/?msg=Vente enregistrée ✓')

@app.route('/supprimer/<int:id>', methods=['POST'])
def supprimer(id):
    if not session.get('ok'): return redirect('/login')
    conn = sqlite3.connect(DB)
    conn.cursor().execute("DELETE FROM ventes WHERE id=?", (id,))
    conn.commit(); conn.close()
    return redirect('/')

@app.route('/produit/ajouter', methods=['POST'])
def produit_ajouter():
    if not session.get('ok'): return redirect('/login')
    nom = request.form['nom'].strip()
    prix = int(request.form['prix'])
    stock = int(request.form.get('stock', 0))
    conn = sqlite3.connect(DB)
    conn.cursor().execute("INSERT INTO produits (nom,prix,stock) VALUES (?,?,?)", (nom,prix,stock))
    conn.commit(); conn.close()
    return redirect('/?msg=Produit ajouté ✓')

@app.route('/produit/supprimer/<nom>', methods=['POST'])
def produit_supprimer(nom):
    if not session.get('ok'): return redirect('/login')
    conn = sqlite3.connect(DB)
    conn.cursor().execute("DELETE FROM produits WHERE nom=?", (nom,))
    conn.commit(); conn.close()
    return redirect('/?msg=Produit supprimé')

@app.route('/commandes')
def commandes():
    if not session.get('ok'): return redirect('/login')
    return redirect('/?msg=Page commandes — bientôt disponible')

@app.route('/fournisseurs')
def fournisseurs():
    if not session.get('ok'): return redirect('/login')
    return redirect('/?msg=Page fournisseurs — bientôt disponible')

@app.route('/catalogue')
def catalogue():
    if not session.get('ok'): return redirect('/login')
    return redirect('/?msg=Page catalogue — bientôt disponible')

@app.route('/export')
def export_excel():
    if not session.get('ok'): return redirect('/login')
    conn = sqlite3.connect(DB)
    ventes = conn.cursor().execute("SELECT * FROM ventes").fetchall()
    conn.close()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ventes AMAN"
    ws.append(["ID","Produit","Montant (FCFA)","Telephone","Date"])
    for v in ventes: ws.append(list(v))
    ws.append([])
    ws.append(["","TOTAL",sum(v[2] for v in ventes),"",""])
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 20
    output = io.BytesIO()
    wb.save(output); output.seek(0)
    return send_file(output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True, download_name='ventes_aman.xlsx')

init_db()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
