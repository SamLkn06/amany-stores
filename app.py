from flask import Flask, render_template_string, request, redirect, session, send_file
import openpyxl, io, os

# ─── DATABASE : PostgreSQL (prod) ou SQLite (local) ──────────────
import sqlite3
DB = os.environ.get("DB_PATH", "boutique.db")
def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn
PH = "?"
def q(sql):
    if DATABASE_URL:
        return sql.replace("?", "%s")
    return sql

app = Flask(__name__)
app.secret_key = "aman2026secret"
MOT_DE_PASSE = "amany2026"

def init_db():
    conn = get_conn()
    c = conn.cursor()
    # Tables compatibles PostgreSQL et SQLite
    id_type = "INTEGER"
    c.execute(f'''CREATE TABLE IF NOT EXISTS ventes (
        id {id_type} PRIMARY KEY, produit TEXT,
        montant INTEGER, telephone TEXT, date TEXT, statut TEXT DEFAULT "livree")''')
    c.execute(f'''CREATE TABLE IF NOT EXISTS produits (
        id {id_type} PRIMARY KEY, nom TEXT, prix INTEGER, stock INTEGER DEFAULT 0,
        description TEXT DEFAULT '', image_url TEXT DEFAULT '')''')
    # Ajouter colonnes si elles n'existent pas (migration)
    try:
        c.execute("ALTER TABLE produits ADD COLUMN description TEXT DEFAULT ''")
    except: pass
    try:
        c.execute("ALTER TABLE produits ADD COLUMN image_url TEXT DEFAULT ''")
    except: pass
    c.execute(f'''CREATE TABLE IF NOT EXISTS commandes (
        id {id_type} PRIMARY KEY, client TEXT, telephone TEXT,
        produit TEXT, montant INTEGER, statut TEXT DEFAULT "en_attente", date TEXT,
        numero_suivi TEXT DEFAULT '', transporteur TEXT DEFAULT '', adresse TEXT DEFAULT '')''')
    for col in ["numero_suivi TEXT DEFAULT ''", "transporteur TEXT DEFAULT ''", "adresse TEXT DEFAULT ''"]:
        try: c.execute(f"ALTER TABLE commandes ADD COLUMN {col}")
        except: pass
    c.execute(f'''CREATE TABLE IF NOT EXISTS fournisseurs (
        id {id_type} PRIMARY KEY, nom TEXT, contact TEXT, pays TEXT, note TEXT)''')
    if c.execute("SELECT COUNT(*) FROM produits").fetchone()[0] == 0:
        for nom, prix in [("Tripod", 15000), ("Microphone", 25000),
                          ("Ring Light", 18000), ("Gimbal", 45000)]:
            c.execute("INSERT INTO produits (nom, prix, stock) VALUES (?,?,?)", (nom, prix, 10))
    if c.execute("SELECT COUNT(*) FROM fournisseurs").fetchone()[0] == 0:
        fournisseurs = [
            ("Guangdong Axin Logistics","axinlogistics.com | WeChat: axin_logistics","Chine 🇨🇳","Livraison Afrique 15-25j | Réactivité ≤1h | Taux livraison >95%"),
            ("Shenzhen Fly International","flyinternational.cn | WhatsApp pro","Chine 🇨🇳","Stabilité élevée | Idéal B2B | 830K$+ revenus"),
            ("WUHAN BOSA SHIPPING","bosashipping.com","Chine 🇨🇳","Commandes volumineuses | Fret maritime | 1.3M$+ revenus"),
            ("AliExpress / 1688.com","aliexpress.com | 1688.com","Chine 🇨🇳","Sourcing général | Tech accessories | Livraison 20-35j"),
            ("Chadrack Jack","WhatsApp/WeChat — contact direct","Chine 🇨🇳","Tech accessories | Contact établi | Négociation directe"),
            ("DHL Express Bénin","+229 21 30 10 85 | dhl.com/bj-fr","International 🌍","Express porte-à-porte | Suivi temps réel | Aérien prioritaire"),
            ("Bolloré Logistics Cotonou","+229 21 36 83 00 | bollore-logistics.com","International 🌍","Zone Portuaire Cotonou | Fret maritime & aérien"),
            ("OMA Group Bénin","+229 21 31 52 88 | benin.omagroup.com","International 🌍","Rue du Gouverneur Fourn Cotonou | Import/export"),
            ("IFS — International Freight","contact@ifs-benin.com","International 🌍","Fret aérien, maritime, terrestre | Rapide & sécurisé"),
            ("CEVA Logistics Cotonou","+228 31 21 52 88 | cevalogistics.com","International 🌍","Réseau mondial | Supply chain | Partenaire fiable"),
            ("Laly Express Cotonou","Ganhi Place de la Poste | Cotonou","Bénin 🇧🇯","Livraison express locale | Colis & courriers | Depuis 2018"),
            ("Express Relais Logistique","DC Services Bénin","Bénin 🇧🇯","Livraison locale & villes africaines | E-solutions"),
            ("Africa Cargo Hub","africacargohub.bj","Bénin 🇧🇯","Warehousing + shipping + livraison | Dropshipping Bénin"),
            ("GROUPE OROS","Cotonou — transit & dédouanement","Bénin 🇧🇯","Transit, dédouanement, livraison porte-à-porte"),
            ("Grimaldi Lines Cotonou","+229 21 31 67 28 | grimaldi@grimaldi-benin.com","Bénin 🇧🇯","Fret maritime | Ligne Europe-Afrique de l Ouest"),
            ("eWorldTrade","eworldtrade.com","Plateforme B2B 🌐","Fournisseurs vérifiés | Livraison Bénin | Paiement sécurisé"),
            ("Zendrop","zendrop.com | App Shopify","Plateforme B2B 🌐","Produits Chine | Livraison mondiale | Compatible Shopify"),
            ("Banggood","banggood.com","Chine/Europe 🌐","Tech & électronique | Livraison Afrique | Prix compétitifs"),
        ]
        c.executemany(q("INSERT INTO fournisseurs (nom,contact,pays,note) VALUES (?,?,?,?)"), fournisseurs)
    conn.commit()
    conn.close()

def get_produits():
    conn = get_conn()
    rows = conn.cursor().execute("SELECT nom, prix FROM produits").fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}

def get_stats():
    conn = get_conn()
    c = conn.cursor()
    nb_ventes = c.execute("SELECT COUNT(*) FROM ventes").fetchone()[0]
    total = c.execute("SELECT COALESCE(SUM(montant),0) FROM ventes").fetchone()[0]
    nb_produits = c.execute("SELECT COUNT(*) FROM produits").fetchone()[0]
    nb_commandes = c.execute("SELECT COUNT(*) FROM commandes WHERE statut='en_attente'").fetchone()[0]
    conn.close()
    return nb_ventes, total, nb_produits, nb_commandes

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

CSS = '''
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box;}
:root{
  --bg:#060D1F;--bg2:#0C1829;--bg3:#111F35;
  --cyan:#06B6D4;--green:#84CC16;--red:#DC2626;
  --gold:#F59E0B;--purple:#A855F7;--blue:#2563EB;
  --text:#E2E8F0;--muted:#64748B;--border:#1E3A5F;
}
body{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;min-height:100vh;}
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
.page{max-width:1100px;margin:0 auto;padding:30px 20px;}
.page-title{font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:700;margin-bottom:6px;}
.page-sub{color:var(--muted);font-size:13px;margin-bottom:28px;}
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
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px;}
.card{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:26px;margin-bottom:20px;}
.card-head{font-size:11px;letter-spacing:3px;color:var(--cyan);text-transform:uppercase;margin-bottom:20px;padding-bottom:12px;border-bottom:1px solid var(--border);}
.field{width:100%;padding:13px 15px;margin-bottom:12px;background:var(--bg);border:1px solid var(--border);color:var(--text);border-radius:9px;font-size:14px;font-family:'Inter',sans-serif;outline:none;transition:border .2s;}
.field:focus{border-color:var(--cyan);}
.grid-input{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
.grid-input3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;}
.btn{width:100%;padding:13px;border:none;border-radius:9px;font-size:13px;font-weight:600;letter-spacing:1px;cursor:pointer;text-transform:uppercase;transition:opacity .2s;}
.btn:hover{opacity:.85;}
.btn-red{background:var(--red);color:#fff;}
.btn-cyan{background:var(--cyan);color:#000;}
.btn-gold{background:var(--gold);color:#000;}
.btn-green{background:var(--green);color:#000;}
.btn-purple{background:var(--purple);color:#fff;}
.btn-sm{width:auto;padding:6px 14px;font-size:11px;}
.table-wrap{overflow-x:auto;}
table{width:100%;border-collapse:collapse;}
th{background:var(--bg3);color:var(--muted);padding:12px 14px;font-size:11px;letter-spacing:2px;text-transform:uppercase;text-align:left;border-bottom:1px solid var(--border);}
td{padding:13px 14px;border-bottom:1px solid var(--border);font-size:13px;color:var(--text);}
tr:last-child td{border-bottom:none;}
tr:hover td{background:var(--bg3);}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;}
.badge-green{background:#84CC1622;color:var(--green);border:1px solid #84CC1633;}
.badge-gold{background:#F59E0B22;color:var(--gold);border:1px solid #F59E0B33;}
.badge-red{background:#DC262622;color:var(--red);border:1px solid #DC262633;}
.badge-cyan{background:#06B6D422;color:var(--cyan);border:1px solid #06B6D433;}
.badge-purple{background:#A855F722;color:var(--purple);border:1px solid #A855F733;}
.total-bar{background:var(--bg3);border:1px solid var(--gold);border-radius:10px;padding:16px 22px;display:flex;justify-content:space-between;align-items:center;margin-top:16px;}
.total-bar span:first-child{font-size:12px;letter-spacing:2px;color:var(--muted);}
.total-bar span:last-child{font-size:22px;font-weight:700;color:var(--gold);}
.alert{padding:12px 16px;border-radius:8px;margin-bottom:16px;font-size:13px;}
.alert-success{background:#84CC1615;border:1px solid #84CC1640;color:var(--green);}
.login-wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;background:var(--bg);}
.login-box{background:var(--bg2);border:1px solid var(--border);border-radius:18px;padding:48px 40px;width:340px;text-align:center;}
.login-name{font-family:'Space Grotesk',sans-serif;font-size:28px;font-weight:700;color:var(--cyan);letter-spacing:6px;margin:16px 0 4px;}
.login-tag{font-size:10px;letter-spacing:3px;color:var(--muted);margin-bottom:32px;}
.login-error{color:var(--red);font-size:13px;margin-bottom:14px;}
.pipeline{display:flex;gap:0;margin-bottom:24px;}
.pipe-step{flex:1;padding:12px 8px;text-align:center;font-size:11px;letter-spacing:1px;font-weight:600;border:1px solid var(--border);cursor:pointer;transition:all .2s;}
.pipe-step:first-child{border-radius:9px 0 0 9px;}
.pipe-step:last-child{border-radius:0 9px 9px 0;}
.pipe-step.active-en_attente{background:#F59E0B22;color:var(--gold);border-color:var(--gold);}
.pipe-step.active-confirmee{background:#06B6D422;color:var(--cyan);border-color:var(--cyan);}
.pipe-step.active-en_livraison{background:#A855F722;color:var(--purple);border-color:var(--purple);}
.pipe-step.active-livree{background:#84CC1622;color:var(--green);border-color:var(--green);}
.footer{text-align:center;padding:30px;color:var(--muted);font-size:11px;letter-spacing:3px;}
'''

NAV = '''<nav class="nav">
  <div class="nav-brand">
    {logo}
    <div class="nav-brand-text">
      <span class="nav-brand-name">AMAN</span>
      <span class="nav-brand-tag">TRUST · SAFETY · QUALITY</span>
    </div>
  </div>
  <div class="nav-links">
    <a href="/" class="nav-link {d}">Dashboard</a>
    <a href="/commandes" class="nav-link {c}">Commandes</a>
    <a href="/livraisons" class="nav-link {li}">Livraisons</a>
    <a href="/fournisseurs" class="nav-link {f}">Fournisseurs</a>
    <a href="/catalogue" class="nav-link {cat}">Catalogue</a>
    <a href="/stats" class="nav-link {st}">Stats</a>
  </div>
  <a href="/logout" class="nav-logout">Déconnexion</a>
</nav>'''

def nav(page):
    pages = {'d':'','c':'','f':'','cat':'','st':'','li':''}
    pages[page] = 'active'
    return NAV.format(logo=LOGO_SVG, **pages)

LOGIN = '''<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AMAN — Connexion</title>
<style>{{ css }}</style></head><body>
<div class="login-wrap"><div class="login-box">
  {{ logo|safe }}
  <div class="login-name">AMAN</div>
  <div class="login-tag">TRUST · SAFETY · QUALITY</div>
  {% if erreur %}<div class="login-error">Mot de passe incorrect</div>{% endif %}
  <form method="POST">
    <input class="field" type="password" name="mdp" placeholder="Mot de passe" required>
    <button class="btn btn-cyan" type="submit">Connexion</button>
  </form>
  <div style="margin-top:20px;font-size:10px;letter-spacing:2px;color:var(--muted)">BÉNIN · AFRIQUE</div>
</div></div></body></html>'''

DASHBOARD = '''<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AMAN — Dashboard</title>
<style>{{ css }}</style></head><body>
{{ nav|safe }}
<div class="page">
  <div class="page-title">Dashboard</div>
  <div class="page-sub">Vue d'ensemble — {{ today }}</div>
  <div class="stats-grid">
    <div class="stat-card cyan"><div class="stat-icon">📦</div><div class="stat-val cyan">{{ nb_ventes }}</div><div class="stat-lbl">Ventes totales</div></div>
    <div class="stat-card gold"><div class="stat-icon">💰</div><div class="stat-val gold">{{ "{:,}".format(total) }}</div><div class="stat-lbl">FCFA encaissés</div></div>
    <div class="stat-card green"><div class="stat-icon">🛒</div><div class="stat-val green">{{ nb_produits }}</div><div class="stat-lbl">Produits actifs</div></div>
    <div class="stat-card purple"><div class="stat-icon">⏳</div><div class="stat-val purple">{{ nb_commandes }}</div><div class="stat-lbl">Commandes en attente</div></div>
  </div>
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
  <div class="card">
    <div class="card-head">Produits en catalogue</div>
    <div class="table-wrap"><table>
      <tr><th>Produit</th><th>Prix</th><th>Action</th></tr>
      {% for p, prix in produits.items() %}
      <tr>
        <td>{{ p }}</td>
        <td><span class="badge badge-gold">{{ "{:,}".format(prix) }} FCFA</span></td>
        <td><form method="POST" action="/produit/supprimer/{{ p }}" style="display:inline">
          <button class="btn btn-sm btn-red" type="submit">Supprimer</button>
        </form></td>
      </tr>
      {% endfor %}
    </table></div>
  </div>
  <div class="card">
    <div class="card-head">Historique des ventes</div>
    <a href="/export" style="text-decoration:none">
      <button class="btn btn-gold" style="width:auto;padding:10px 22px;margin-bottom:18px">⬇ Télécharger Excel</button>
    </a>
    <div class="table-wrap"><table>
      <tr><th>#</th><th>Produit</th><th>Montant</th><th>Téléphone</th><th>Date</th><th>Statut</th><th>Action</th></tr>
      {% for v in ventes %}
      <tr>
        <td>{{ v[0] }}</td><td>{{ v[1] }}</td>
        <td>{{ "{:,}".format(v[2]) }} FCFA</td>
        <td>{{ v[3] }}</td><td>{{ v[4] }}</td>
        <td><span class="badge badge-green">Livrée</span></td>
        <td><form method="POST" action="/supprimer/{{ v[0] }}" style="display:inline">
          <button class="btn btn-sm btn-red" type="submit">✕</button>
        </form></td>
      </tr>
      {% endfor %}
    </table></div>
    <div class="total-bar"><span>TOTAL GÉNÉRAL</span><span>{{ "{:,}".format(total) }} FCFA</span></div>
  </div>
</div>
<div class="footer">© 2026 AMAN — COTONOU, BÉNIN · AFRIQUE</div>
</body></html>'''

COMMANDES_PAGE = '''<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AMAN — Commandes</title>
<style>{{ css }}</style></head><body>
{{ nav|safe }}
<div class="page">
  <div class="page-title">Commandes</div>
  <div class="page-sub">Suivi complet — réception → confirmation → livraison</div>

  <!-- PIPELINE VISUEL -->
  <div class="pipeline">
    <div class="pipe-step active-en_attente">⏳ En attente ({{ stats.en_attente }})</div>
    <div class="pipe-step active-confirmee">✅ Confirmées ({{ stats.confirmee }})</div>
    <div class="pipe-step active-en_livraison">🚚 En livraison ({{ stats.en_livraison }})</div>
    <div class="pipe-step active-livree">📦 Livrées ({{ stats.livree }})</div>
  </div>

  <!-- NOUVELLE COMMANDE -->
  <div class="card">
    <div class="card-head">Nouvelle commande client</div>
    {% if msg %}<div class="alert alert-success">{{ msg }}</div>{% endif %}
    <form method="POST" action="/commandes/ajouter">
      <div class="grid-input3">
        <input class="field" name="client" placeholder="Nom du client" required>
        <input class="field" name="telephone" placeholder="Téléphone (+229...)" required>
        <select class="field" name="produit">
          {% for p, prix in produits.items() %}
          <option value="{{ p }}|{{ prix }}">{{ p }} — {{ "{:,}".format(prix) }} FCFA</option>
          {% endfor %}
        </select>
      </div>
      <button class="btn btn-green" type="submit">+ Enregistrer la commande</button>
    </form>
  </div>

  <!-- LISTE COMMANDES -->
  <div class="card">
    <div class="card-head">Toutes les commandes</div>
    <div class="table-wrap"><table>
      <tr><th>#</th><th>Client</th><th>Téléphone</th><th>Produit</th><th>Montant</th><th>Date</th><th>Statut</th><th>Action</th></tr>
      {% for c in commandes %}
      <tr>
        <td>{{ c[0] }}</td>
        <td><strong>{{ c[1] }}</strong></td>
        <td>{{ c[2] }}</td>
        <td>{{ c[3] }}</td>
        <td>{{ "{:,}".format(c[4]) }} FCFA</td>
        <td>{{ c[6] }}</td>
        <td>
          {% if c[5] == "en_attente" %}<span class="badge badge-gold">⏳ En attente</span>
          {% elif c[5] == "confirmee" %}<span class="badge badge-cyan">✅ Confirmée</span>
          {% elif c[5] == "en_livraison" %}<span class="badge badge-purple">🚚 En livraison</span>
          {% elif c[5] == "livree" %}<span class="badge badge-green">📦 Livrée</span>
          {% endif %}
        </td>
        <td style="display:flex;gap:6px;flex-wrap:wrap;">
          {% if c[5] == "en_attente" %}
          <form method="POST" action="/commandes/statut/{{ c[0] }}">
            <input type="hidden" name="statut" value="confirmee">
            <button class="btn btn-sm btn-cyan" type="submit">Confirmer</button>
          </form>
          {% elif c[5] == "confirmee" %}
          <form method="POST" action="/commandes/statut/{{ c[0] }}">
            <input type="hidden" name="statut" value="en_livraison">
            <button class="btn btn-sm btn-purple" type="submit">Expédier</button>
          </form>
          {% elif c[5] == "en_livraison" %}
          <form method="POST" action="/commandes/statut/{{ c[0] }}">
            <input type="hidden" name="statut" value="livree">
            <button class="btn btn-sm btn-green" type="submit">Livrée ✓</button>
          </form>
          {% endif %}
          <form method="POST" action="/commandes/supprimer/{{ c[0] }}">
            <button class="btn btn-sm btn-red" type="submit">✕</button>
          </form>
        </td>
      </tr>
      {% endfor %}
      {% if not commandes %}
      <tr><td colspan="8" style="text-align:center;color:var(--muted);padding:30px;">Aucune commande pour l'instant</td></tr>
      {% endif %}
    </table></div>
  </div>
</div>
<div class="footer">© 2026 AMAN — COTONOU, BÉNIN · AFRIQUE</div>
</body></html>'''

FOURNISSEURS_PAGE = '''<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AMAN — Fournisseurs</title>
<style>{{ css }}</style></head><body>
{{ nav|safe }}
<div class="page">
  <div class="page-title">Fournisseurs</div>
  <div class="page-sub">Gestion de vos contacts fournisseurs</div>
  <div class="card">
    <div class="card-head">Ajouter un fournisseur</div>
    {% if msg %}<div class="alert alert-success">{{ msg }}</div>{% endif %}
    <form method="POST" action="/fournisseurs/ajouter">
      <div class="grid-input">
        <input class="field" name="nom" placeholder="Nom / Entreprise" required>
        <input class="field" name="contact" placeholder="WeChat / WhatsApp / Tél">
      </div>
      <div class="grid-input">
        <input class="field" name="pays" placeholder="Pays (ex: Chine, Bénin...)">
        <input class="field" name="note" placeholder="Note (produits, conditions...)">
      </div>
      <button class="btn btn-cyan" type="submit">+ Ajouter le fournisseur</button>
    </form>
  </div>
  <div class="card">
    <div class="card-head">Mes fournisseurs ({{ fournisseurs|length }})</div>
    <div class="table-wrap"><table>
      <tr><th>#</th><th>Nom</th><th>Contact</th><th>Pays</th><th>Note</th><th>Action</th></tr>
      {% for f in fournisseurs %}
      <tr>
        <td>{{ f[0] }}</td>
        <td><strong>{{ f[1] }}</strong></td>
        <td><span class="badge badge-cyan">{{ f[2] }}</span></td>
        <td>{{ f[3] }}</td>
        <td style="color:var(--muted)">{{ f[4] }}</td>
        <td><form method="POST" action="/fournisseurs/supprimer/{{ f[0] }}">
          <button class="btn btn-sm btn-red" type="submit">✕</button>
        </form></td>
      </tr>
      {% endfor %}
      {% if not fournisseurs %}
      <tr><td colspan="6" style="text-align:center;color:var(--muted);padding:30px;">Aucun fournisseur enregistré</td></tr>
      {% endif %}
    </table></div>
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
    session.clear(); return redirect('/login')

@app.route('/')
def accueil():
    if not session.get('ok'): return redirect('/login')
    conn = get_conn()
    ventes = conn.cursor().execute("SELECT * FROM ventes ORDER BY id DESC").fetchall()
    conn.close()
    total = sum(v[2] for v in ventes)
    nb_ventes, _, nb_produits, nb_commandes = get_stats()
    from datetime import date
    today = date.today().strftime("%d %B %Y")
    msg = request.args.get('msg','')
    return render_template_string(DASHBOARD, css=CSS, nav=nav('d'),
        ventes=ventes, produits=get_produits(), total=total,
        nb_ventes=nb_ventes, nb_produits=nb_produits, nb_commandes=nb_commandes,
        today=today, msg=msg)

@app.route('/vendre', methods=['POST'])
def vendre():
    if not session.get('ok'): return redirect('/login')
    produit = request.form['produit']
    telephone = request.form.get('telephone','')
    montant = get_produits().get(produit, 0)
    conn = get_conn()
    conn.cursor().execute(
        ("INSERT INTO ventes (produit,montant,telephone,date) VALUES (%s,%s,%s,NOW())" if DATABASE_URL else "INSERT INTO ventes (produit,montant,telephone,date) VALUES (?,?,?,datetime('now','localtime'))"),
        (produit, montant, telephone))
    conn.commit(); conn.close()
    return redirect('/?msg=Vente enregistrée ✓')

@app.route('/supprimer/<int:id>', methods=['POST'])
def supprimer(id):
    if not session.get('ok'): return redirect('/login')
    conn = get_conn()
    conn.cursor().execute(q("DELETE FROM ventes WHERE id=?"), (id,))
    conn.commit(); conn.close()
    return redirect('/')

@app.route('/produit/ajouter', methods=['POST'])
def produit_ajouter():
    if not session.get('ok'): return redirect('/login')
    nom = request.form['nom'].strip()
    prix = int(request.form['prix'])
    stock = int(request.form.get('stock', 0))
    description = request.form.get('description','').strip()
    image_url = request.form.get('image_url','').strip()
    conn = get_conn()
    conn.cursor().execute(q("INSERT INTO produits (nom,prix,stock,description,image_url) VALUES (?,?,?,?,?)"),
        (nom,prix,stock,description,image_url))
    conn.commit(); conn.close()
    return redirect('/catalogue?msg=Produit ajouté ✓')

@app.route('/produit/supprimer/<nom>', methods=['POST'])
def produit_supprimer(nom):
    if not session.get('ok'): return redirect('/login')
    conn = get_conn()
    conn.cursor().execute(q("DELETE FROM produits WHERE nom=?"), (nom,))
    conn.commit(); conn.close()
    return redirect('/catalogue?msg=Produit supprimé')

# ─── COMMANDES ───────────────────────────────────────────────────
@app.route('/commandes')
def commandes():
    if not session.get('ok'): return redirect('/login')
    conn = get_conn()
    c = conn.cursor()
    all_cmd = c.execute("SELECT * FROM commandes ORDER BY id DESC").fetchall()
    stats = {
        'en_attente': c.execute("SELECT COUNT(*) FROM commandes WHERE statut='en_attente'").fetchone()[0],
        'confirmee':  c.execute("SELECT COUNT(*) FROM commandes WHERE statut='confirmee'").fetchone()[0],
        'en_livraison': c.execute("SELECT COUNT(*) FROM commandes WHERE statut='en_livraison'").fetchone()[0],
        'livree': c.execute("SELECT COUNT(*) FROM commandes WHERE statut='livree'").fetchone()[0],
    }
    conn.close()
    msg = request.args.get('msg','')
    return render_template_string(COMMANDES_PAGE, css=CSS, nav=nav('c'),
        commandes=all_cmd, produits=get_produits(), stats=stats, msg=msg)

@app.route('/commandes/ajouter', methods=['POST'])
def commandes_ajouter():
    if not session.get('ok'): return redirect('/login')
    client = request.form['client'].strip()
    telephone = request.form['telephone'].strip()
    produit_prix = request.form['produit'].split('|')
    produit = produit_prix[0]
    montant = int(produit_prix[1]) if len(produit_prix) > 1 else 0
    conn = get_conn()
    conn.cursor().execute(
        ("INSERT INTO commandes (client,telephone,produit,montant,statut,date) VALUES (%s,%s,%s,%s,%s,NOW())" if DATABASE_URL else "INSERT INTO commandes (client,telephone,produit,montant,statut,date) VALUES (?,?,?,?,?,datetime('now','localtime'))"),
        (client, telephone, produit, montant, 'en_attente'))
    conn.commit(); conn.close()
    return redirect('/commandes?msg=Commande enregistrée ✓')

@app.route('/commandes/statut/<int:id>', methods=['POST'])
def commandes_statut(id):
    if not session.get('ok'): return redirect('/login')
    statut = request.form['statut']
    conn = get_conn()
    conn.cursor().execute(q("UPDATE commandes SET statut=? WHERE id=?"), (statut, id))
    conn.commit(); conn.close()
    return redirect('/commandes?msg=Statut mis à jour ✓')

@app.route('/commandes/supprimer/<int:id>', methods=['POST'])
def commandes_supprimer(id):
    if not session.get('ok'): return redirect('/login')
    conn = get_conn()
    conn.cursor().execute(q("DELETE FROM commandes WHERE id=?"), (id,))
    conn.commit(); conn.close()
    return redirect('/commandes')

# ─── FOURNISSEURS ────────────────────────────────────────────────
@app.route('/fournisseurs')
def fournisseurs():
    if not session.get('ok'): return redirect('/login')
    conn = get_conn()
    all_f = conn.cursor().execute("SELECT * FROM fournisseurs ORDER BY id DESC").fetchall()
    conn.close()
    msg = request.args.get('msg','')
    return render_template_string(FOURNISSEURS_PAGE, css=CSS, nav=nav('f'),
        fournisseurs=all_f, msg=msg)

@app.route('/fournisseurs/ajouter', methods=['POST'])
def fournisseurs_ajouter():
    if not session.get('ok'): return redirect('/login')
    nom = request.form['nom'].strip()
    contact = request.form.get('contact','').strip()
    pays = request.form.get('pays','').strip()
    note = request.form.get('note','').strip()
    conn = get_conn()
    conn.cursor().execute(q("INSERT INTO fournisseurs (nom,contact,pays,note) VALUES (?,?,?,?)"),
        (nom, contact, pays, note))
    conn.commit(); conn.close()
    return redirect('/fournisseurs?msg=Fournisseur ajouté ✓')

@app.route('/fournisseurs/supprimer/<int:id>', methods=['POST'])
def fournisseurs_supprimer(id):
    if not session.get('ok'): return redirect('/login')
    conn = get_conn()
    conn.cursor().execute(q("DELETE FROM fournisseurs WHERE id=?"), (id,))
    conn.commit(); conn.close()
    return redirect('/fournisseurs')


# ─── PAGE STATISTIQUES ───────────────────────────────────────────
STATS_PAGE = '''<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AMAN — Statistiques</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>{{ css }}
.chart-box{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:24px;margin-bottom:20px;}
.chart-title{font-size:11px;letter-spacing:3px;color:var(--cyan);text-transform:uppercase;margin-bottom:20px;}
.kpi-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:24px;}
.kpi{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:20px;text-align:center;}
.kpi-val{font-size:32px;font-weight:700;margin-bottom:4px;}
.kpi-lbl{font-size:11px;letter-spacing:2px;color:var(--muted);}
.top-list{list-style:none;}
.top-list li{display:flex;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid var(--border);}
.top-list li:last-child{border-bottom:none;}
</style></head><body>
{{ nav|safe }}
<div class="page">
  <div class="page-title">Statistiques</div>
  <div class="page-sub">Performance AMAN — {{ today }}</div>

  <!-- KPI TOP -->
  <div class="kpi-grid">
    <div class="kpi">
      <div class="kpi-val" style="color:var(--gold)">{{ total_fcfa }}</div>
      <div class="kpi-lbl">FCFA TOTAL</div>
    </div>
    <div class="kpi">
      <div class="kpi-val" style="color:var(--cyan)">{{ nb_ventes }}</div>
      <div class="kpi-lbl">VENTES</div>
    </div>
    <div class="kpi">
      <div class="kpi-val" style="color:var(--green)">{{ moy_vente }}</div>
      <div class="kpi-lbl">FCFA MOY/VENTE</div>
    </div>
  </div>

  <!-- GRAPHIQUE VENTES PAR JOUR -->
  <div class="chart-box">
    <div class="chart-title">Ventes des 7 derniers jours</div>
    <canvas id="chartJours" height="80"></canvas>
  </div>

  <!-- GRAPHIQUE PAR PRODUIT -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
    <div class="chart-box">
      <div class="chart-title">Répartition par produit</div>
      <canvas id="chartProduits" height="200"></canvas>
    </div>
    <div class="chart-box">
      <div class="chart-title">Top produits vendus</div>
      <ul class="top-list">
        {% for p in top_produits %}
        <li>
          <span>{{ p[0] }}</span>
          <span style="display:flex;gap:12px;">
            <span class="badge badge-cyan">{{ p[1] }} ventes</span>
            <span class="badge badge-gold">{{ "{:,}".format(p[2]) }} FCFA</span>
          </span>
        </li>
        {% endfor %}
        {% if not top_produits %}<li style="color:var(--muted)">Aucune vente encore</li>{% endif %}
      </ul>
    </div>
  </div>

  <!-- COMMANDES PAR STATUT -->
  <div class="chart-box">
    <div class="chart-title">Commandes par statut</div>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:8px;">
      <div style="text-align:center;padding:16px;background:var(--bg3);border-radius:10px;">
        <div style="font-size:24px;font-weight:700;color:var(--gold)">{{ cmd_stats.en_attente }}</div>
        <div style="font-size:11px;color:var(--muted);margin-top:4px;">EN ATTENTE</div>
      </div>
      <div style="text-align:center;padding:16px;background:var(--bg3);border-radius:10px;">
        <div style="font-size:24px;font-weight:700;color:var(--cyan)">{{ cmd_stats.confirmee }}</div>
        <div style="font-size:11px;color:var(--muted);margin-top:4px;">CONFIRMÉES</div>
      </div>
      <div style="text-align:center;padding:16px;background:var(--bg3);border-radius:10px;">
        <div style="font-size:24px;font-weight:700;color:var(--purple)">{{ cmd_stats.en_livraison }}</div>
        <div style="font-size:11px;color:var(--muted);margin-top:4px;">EN LIVRAISON</div>
      </div>
      <div style="text-align:center;padding:16px;background:var(--bg3);border-radius:10px;">
        <div style="font-size:24px;font-weight:700;color:var(--green)">{{ cmd_stats.livree }}</div>
        <div style="font-size:11px;color:var(--muted);margin-top:4px;">LIVRÉES</div>
      </div>
    </div>
  </div>
</div>
<div class="footer">© 2026 AMAN — COTONOU, BÉNIN · AFRIQUE</div>

<script>
const joursLabels = {{ jours_labels|safe }};
const joursData = {{ jours_data|safe }};
const produitsLabels = {{ produits_labels|safe }};
const produitsData = {{ produits_data|safe }};

new Chart(document.getElementById("chartJours"), {
  type: "bar",
  data: {
    labels: joursLabels,
    datasets: [{
      label: "Ventes (FCFA)",
      data: joursData,
      backgroundColor: "#06B6D466",
      borderColor: "#06B6D4",
      borderWidth: 2,
      borderRadius: 6,
    }]
  },
  options: {
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: "#64748B" }, grid: { color: "#1E3A5F" } },
      y: { ticks: { color: "#64748B" }, grid: { color: "#1E3A5F" } }
    }
  }
});

new Chart(document.getElementById("chartProduits"), {
  type: "doughnut",
  data: {
    labels: produitsLabels,
    datasets: [{
      data: produitsData,
      backgroundColor: ["#06B6D4","#84CC16","#F59E0B","#DC2626","#A855F7","#2563EB"],
      borderWidth: 0,
    }]
  },
  options: {
    plugins: { legend: { labels: { color: "#E2E8F0", padding: 16 } } },
    cutout: "65%"
  }
});
</script>
</body></html>'''

# ─── PAGE LIVRAISONS ──────────────────────────────────────────────
LIVRAISONS_PAGE = '''<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AMAN — Livraisons</title>
<style>{{ css }}
.track-card{background:var(--bg2);border:1px solid var(--border);border-radius:14px;padding:20px;margin-bottom:16px;}
.track-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px;}
.track-client{font-weight:700;font-size:15px;}
.track-produit{color:var(--muted);font-size:13px;margin-top:2px;}
.track-steps{display:flex;align-items:center;gap:0;margin:16px 0;}
.step{flex:1;text-align:center;position:relative;}
.step-dot{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;margin:0 auto 6px;border:2px solid var(--border);}
.step-dot.done{background:var(--green);border-color:var(--green);color:#000;}
.step-dot.active{background:var(--cyan);border-color:var(--cyan);color:#000;}
.step-dot.pending{background:var(--bg3);color:var(--muted);}
.step-label{font-size:10px;color:var(--muted);letter-spacing:1px;}
.step-line{position:absolute;top:13px;left:50%;width:100%;height:2px;background:var(--border);z-index:0;}
.step-line.done{background:var(--green);}
.track-info{display:flex;gap:16px;flex-wrap:wrap;margin-top:12px;}
.track-pill{padding:4px 12px;background:var(--bg3);border-radius:20px;font-size:12px;color:var(--muted);}
.track-pill span{color:var(--text);}
</style></head><body>
{{ nav|safe }}
<div class="page">
  <div class="page-title">Suivi des livraisons</div>
  <div class="page-sub">Toutes les commandes en cours de traitement</div>

  {% if msg %}<div class="alert alert-success">{{ msg }}</div>{% endif %}

  {% for c in commandes %}
  {% set steps = ["en_attente","confirmee","en_livraison","livree"] %}
  {% set step_idx = steps.index(c[5]) if c[5] in steps else 0 %}
  <div class="track-card">
    <div class="track-header">
      <div>
        <div class="track-client">{{ c[1] }} <span style="color:var(--muted);font-weight:400;">· {{ c[2] }}</span></div>
        <div class="track-produit">{{ c[3] }} — {{ "{:,}".format(c[4]) }} FCFA</div>
      </div>
      <div style="text-align:right;">
        <div style="font-size:11px;color:var(--muted);">#{{ c[0] }}</div>
        <div style="font-size:11px;color:var(--muted);">{{ c[6] }}</div>
      </div>
    </div>

    <!-- BARRE DE PROGRESSION -->
    <div class="track-steps">
      {% for i, (emoji, label) in enumerate([("📥","Reçue"),("✅","Confirmée"),("🚚","En route"),("📦","Livrée")]) %}
      <div class="step">
        {% if i < step_idx %}<div class="step-line done"></div>{% elif i > 0 %}<div class="step-line"></div>{% endif %}
        <div class="step-dot {% if i < step_idx %}done{% elif i == step_idx %}active{% else %}pending{% endif %}">{{ emoji }}</div>
        <div class="step-label">{{ label }}</div>
      </div>
      {% endfor %}
    </div>

    <!-- INFOS SUIVI -->
    <div class="track-info">
      {% if c[7] %}<div class="track-pill">N° suivi : <span>{{ c[7] }}</span></div>{% endif %}
      {% if c[8] %}<div class="track-pill">Transporteur : <span>{{ c[8] }}</span></div>{% endif %}
      {% if c[9] %}<div class="track-pill">Adresse : <span>{{ c[9] }}</span></div>{% endif %}
    </div>

    <!-- ACTIONS -->
    <div style="display:flex;gap:8px;margin-top:14px;flex-wrap:wrap;">
      {% if c[5] == "en_attente" %}
      <form method="POST" action="/commandes/statut/{{ c[0] }}">
        <input type="hidden" name="statut" value="confirmee">
        <button class="btn btn-sm btn-cyan" type="submit">✅ Confirmer</button>
      </form>
      {% elif c[5] == "confirmee" %}
      <form method="POST" action="/livraisons/expedition/{{ c[0] }}" style="display:flex;gap:6px;align-items:center;">
        <input class="field" name="transporteur" placeholder="Transporteur" style="margin:0;padding:8px;width:160px;">
        <input class="field" name="numero_suivi" placeholder="N° suivi" style="margin:0;padding:8px;width:140px;">
        <button class="btn btn-sm btn-purple" type="submit">🚚 Expédier</button>
      </form>
      {% elif c[5] == "en_livraison" %}
      <form method="POST" action="/commandes/statut/{{ c[0] }}">
        <input type="hidden" name="statut" value="livree">
        <button class="btn btn-sm btn-green" type="submit">📦 Marquer livrée</button>
      </form>
      {% elif c[5] == "livree" %}
      <span style="color:var(--green);font-size:13px;font-weight:600;">✓ Livraison complète</span>
      {% endif %}

      <!-- WhatsApp direct client -->
      {% if c[2] %}
      {% set tel = c[2]|replace(" ","")|replace("+","") %}
      {% set msg_wa = "Bonjour " + c[1] + ", votre commande AMAN (" + c[3] + ") est " + c[5]|replace("_"," ") + ". Merci de votre confiance !" %}
      <a href="https://wa.me/{{ tel }}?text={{ msg_wa|urlencode }}" target="_blank">
        <button class="btn btn-sm btn-green" type="button" style="background:#25D366;">💬 WhatsApp</button>
      </a>
      {% endif %}
    </div>
  </div>
  {% endfor %}

  {% if not commandes %}
  <div style="text-align:center;padding:60px;color:var(--muted);">Aucune commande en cours</div>
  {% endif %}
</div>
<div class="footer">© 2026 AMAN — COTONOU, BÉNIN · AFRIQUE</div>
</body></html>'''

@app.route('/stats')
def stats():
    if not session.get('ok'): return redirect('/login')
    from datetime import date, timedelta
    import json
    conn = get_conn()
    c = conn.cursor()
    ventes = c.execute("SELECT montant, date FROM ventes").fetchall()
    total_fcfa = sum(v[0] for v in ventes)
    nb_ventes = len(ventes)
    moy_vente = "{:,}".format(total_fcfa // nb_ventes) if nb_ventes else "0"
    total_fcfa_fmt = "{:,}".format(total_fcfa)
    # Top produits
    top_produits = c.execute("""SELECT produit, COUNT(*) as nb, SUM(montant) as total
        FROM ventes GROUP BY produit ORDER BY nb DESC LIMIT 5""").fetchall()
    # Stats commandes
    cmd_stats = {
        'en_attente': c.execute("SELECT COUNT(*) FROM commandes WHERE statut='en_attente'").fetchone()[0],
        'confirmee': c.execute("SELECT COUNT(*) FROM commandes WHERE statut='confirmee'").fetchone()[0],
        'en_livraison': c.execute("SELECT COUNT(*) FROM commandes WHERE statut='en_livraison'").fetchone()[0],
        'livree': c.execute("SELECT COUNT(*) FROM commandes WHERE statut='livree'").fetchone()[0],
    }
    # Ventes 7 derniers jours
    jours_labels = []
    jours_data = []
    for i in range(6, -1, -1):
        d = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
        label = (date.today() - timedelta(days=i)).strftime("%d/%m")
        total_j = c.execute(q("SELECT COALESCE(SUM(montant),0) FROM ventes WHERE date LIKE ?"), (d+'%',)).fetchone()[0]
        jours_labels.append(label)
        jours_data.append(total_j)
    # Répartition produits
    produits_labels = [p[0] for p in top_produits]
    produits_data = [p[1] for p in top_produits]
    conn.close()
    today = date.today().strftime("%d %B %Y")
    return render_template_string(STATS_PAGE, css=CSS, nav=nav('st'),
        total_fcfa=total_fcfa_fmt, nb_ventes=nb_ventes, moy_vente=moy_vente,
        top_produits=top_produits, cmd_stats=cmd_stats, today=today,
        jours_labels=json.dumps(jours_labels), jours_data=json.dumps(jours_data),
        produits_labels=json.dumps(produits_labels), produits_data=json.dumps(produits_data))

@app.route('/livraisons')
def livraisons():
    if not session.get('ok'): return redirect('/login')
    conn = get_conn()
    commandes = conn.cursor().execute(
        "SELECT * FROM commandes ORDER BY CASE statut WHEN 'en_livraison' THEN 1 WHEN 'confirmee' THEN 2 WHEN 'en_attente' THEN 3 ELSE 4 END, id DESC"
    ).fetchall()
    conn.close()
    msg = request.args.get('msg','')
    return render_template_string(LIVRAISONS_PAGE, css=CSS, nav=nav('li'),
        commandes=commandes, msg=msg)

@app.route('/livraisons/expedition/<int:id>', methods=['POST'])
def livraisons_expedition(id):
    if not session.get('ok'): return redirect('/login')
    transporteur = request.form.get('transporteur','').strip()
    numero_suivi = request.form.get('numero_suivi','').strip()
    conn = get_conn()
    conn.cursor().execute(
        q("UPDATE commandes SET statut='en_livraison', transporteur=?, numero_suivi=? WHERE id=?"),
        (transporteur, numero_suivi, id))
    conn.commit(); conn.close()
    return redirect('/livraisons?msg=Expédition enregistrée ✓')

# ─── CATALOGUE ADMIN ────────────────────────────────────────────
CATALOGUE_PAGE = '''<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AMAN — Catalogue</title>
<style>{{ css }}
.prod-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px;margin-top:20px;}
.prod-card{background:var(--bg2);border:1px solid var(--border);border-radius:14px;overflow:hidden;transition:border .2s;}
.prod-card:hover{border-color:var(--cyan);}
.prod-img{width:100%;height:160px;object-fit:cover;background:var(--bg3);display:flex;align-items:center;justify-content:center;font-size:48px;}
.prod-img img{width:100%;height:160px;object-fit:cover;}
.prod-body{padding:18px;}
.prod-name{font-weight:700;font-size:16px;margin-bottom:6px;}
.prod-desc{color:var(--muted);font-size:12px;margin-bottom:12px;line-height:1.5;}
.prod-footer{display:flex;justify-content:space-between;align-items:center;}
.prod-prix{font-size:18px;font-weight:700;color:var(--gold);}
.stock-ok{color:var(--green);font-size:11px;}
.stock-low{color:var(--red);font-size:11px;}
.edit-form{margin-top:12px;padding-top:12px;border-top:1px solid var(--border);}
</style></head><body>
{{ nav|safe }}
<div class="page">
  <div class="page-title">Catalogue — Admin</div>
  <div class="page-sub">Gérez vos produits · <a href="/shop" style="color:var(--cyan);text-decoration:none;">↗ Voir la page publique client</a></div>

  <!-- AJOUTER PRODUIT -->
  <div class="card">
    <div class="card-head">Ajouter un produit</div>
    {% if msg %}<div class="alert alert-success">{{ msg }}</div>{% endif %}
    <form method="POST" action="/produit/ajouter">
      <div class="grid-input">
        <input class="field" name="nom" placeholder="Nom du produit" required>
        <input class="field" name="prix" type="number" placeholder="Prix FCFA" required>
      </div>
      <div class="grid-input">
        <input class="field" name="stock" type="number" placeholder="Stock" value="0">
        <input class="field" name="image_url" placeholder="URL image (optionnel)">
      </div>
      <input class="field" name="description" placeholder="Description courte du produit">
      <button class="btn btn-cyan" type="submit">+ Ajouter au catalogue</button>
    </form>
  </div>

  <!-- GRILLE PRODUITS -->
  <div class="prod-grid">
    {% for p in produits %}
    <div class="prod-card">
      <div class="prod-img">
        {% if p[5] %}<img src="{{ p[5] }}" alt="{{ p[1] }}" onerror="this.parentElement.innerHTML='📦'">
        {% else %}📦{% endif %}
      </div>
      <div class="prod-body">
        <div class="prod-name">{{ p[1] }}</div>
        <div class="prod-desc">{{ p[4] or "Aucune description" }}</div>
        <div class="prod-footer">
          <span class="prod-prix">{{ "{:,}".format(p[2]) }} FCFA</span>
          {% if p[3] > 5 %}<span class="stock-ok">✓ Stock: {{ p[3] }}</span>
          {% elif p[3] > 0 %}<span class="stock-low">⚠ Stock faible: {{ p[3] }}</span>
          {% else %}<span class="stock-low">✕ Rupture</span>{% endif %}
        </div>
        <!-- Actions admin -->
        <div class="edit-form">
          <div style="display:flex;gap:8px;">
            <form method="POST" action="/produit/stock/{{ p[0] }}" style="flex:1;display:flex;gap:6px;">
              <input class="field" name="stock" type="number" value="{{ p[3] }}" style="margin:0;padding:8px;">
              <button class="btn btn-sm btn-gold" type="submit">Stock</button>
            </form>
            <form method="POST" action="/produit/supprimer/{{ p[1] }}">
              <button class="btn btn-sm btn-red" type="submit">✕</button>
            </form>
          </div>
        </div>
      </div>
    </div>
    {% endfor %}
  </div>
</div>
<div class="footer">© 2026 AMAN — COTONOU, BÉNIN · AFRIQUE</div>
</body></html>'''

# ─── PAGE PUBLIQUE CLIENT ─────────────────────────────────────────
SHOP_PAGE = '''<!DOCTYPE html><html lang="fr"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="AMAN — Marketplace premium. Tech, Mode, Maison. Livraison rapide au Bénin et en Afrique.">
<title>AMAN — Marketplace Bénin · Afrique</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box;}
:root{
  --white:#FFFFFF;
  --bg:#F8F9FC;
  --bg2:#F0F2F8;
  --dark:#060D1F;
  --dark2:#0C1829;
  --cyan:#06B6D4;
  --green:#16A34A;
  --red:#DC2626;
  --gold:#D97706;
  --purple:#7C3AED;
  --text:#111827;
  --muted:#6B7280;
  --border:#E5E7EB;
  --shadow:0 1px 3px rgba(0,0,0,0.08),0 1px 2px rgba(0,0,0,0.04);
  --shadow-md:0 4px 6px -1px rgba(0,0,0,0.1),0 2px 4px -1px rgba(0,0,0,0.06);
  --shadow-lg:0 10px 15px -3px rgba(0,0,0,0.1),0 4px 6px -2px rgba(0,0,0,0.05);
}
html{scroll-behavior:smooth;}
body{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;min-height:100vh;}

/* ── TOPBAR ── */
.topbar{background:var(--dark);color:#fff;padding:8px 20px;font-size:12px;text-align:center;letter-spacing:1px;}
.topbar span{color:var(--cyan);}

/* ── NAV ── */
.nav{background:var(--white);border-bottom:1px solid var(--border);padding:0 24px;display:flex;align-items:center;gap:16px;height:64px;position:sticky;top:0;z-index:200;box-shadow:var(--shadow);}
.nav-brand{display:flex;align-items:center;gap:8px;text-decoration:none;flex-shrink:0;}
.nav-logo{width:36px;height:36px;background:var(--dark);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:18px;}
.nav-name{font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:800;color:var(--dark);letter-spacing:2px;}
.nav-name span{color:var(--cyan);}
.search-bar{flex:1;max-width:560px;position:relative;}
.search-bar input{width:100%;padding:10px 16px 10px 42px;border:2px solid var(--border);border-radius:10px;font-size:14px;font-family:'Inter',sans-serif;outline:none;background:var(--bg);transition:border .2s;}
.search-bar input:focus{border-color:var(--cyan);background:var(--white);}
.search-bar svg{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--muted);}
.search-bar button{position:absolute;right:6px;top:50%;transform:translateY(-50%);background:var(--dark);color:white;border:none;border-radius:7px;padding:6px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.nav-actions{display:flex;align-items:center;gap:10px;margin-left:auto;}
.nav-wa{background:#25D366;color:white;border:none;border-radius:8px;padding:9px 16px;font-size:13px;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:6px;text-decoration:none;}
.nav-track{background:var(--bg2);color:var(--dark);border:1px solid var(--border);border-radius:8px;padding:9px 16px;font-size:13px;font-weight:600;cursor:pointer;text-decoration:none;}

/* ── HERO ── */
.hero{background:linear-gradient(135deg,var(--dark) 0%,#1a2a5e 50%,#0C1829 100%);color:white;padding:50px 24px;display:flex;align-items:center;justify-content:space-between;gap:30px;overflow:hidden;position:relative;}
.hero::after{content:'';position:absolute;right:-80px;top:-80px;width:400px;height:400px;background:var(--cyan);opacity:0.06;border-radius:50%;}
.hero-text{max-width:520px;z-index:1;}
.hero-badge{display:inline-flex;align-items:center;gap:6px;background:rgba(6,182,212,0.15);border:1px solid rgba(6,182,212,0.3);border-radius:20px;padding:5px 14px;font-size:11px;font-weight:600;letter-spacing:2px;color:var(--cyan);margin-bottom:18px;}
.hero h1{font-family:'Space Grotesk',sans-serif;font-size:clamp(26px,4vw,46px);font-weight:800;line-height:1.15;margin-bottom:14px;}
.hero h1 em{font-style:normal;color:var(--cyan);}
.hero p{color:#94A3B8;font-size:15px;line-height:1.7;margin-bottom:24px;max-width:440px;}
.hero-btns{display:flex;gap:12px;flex-wrap:wrap;}
.btn-hero-primary{background:var(--cyan);color:#000;border:none;border-radius:10px;padding:13px 26px;font-size:14px;font-weight:700;cursor:pointer;transition:all .2s;}
.btn-hero-primary:hover{background:#08d4f0;transform:translateY(-1px);}
.btn-hero-secondary{background:transparent;color:white;border:1px solid rgba(255,255,255,0.2);border-radius:10px;padding:13px 26px;font-size:14px;font-weight:600;cursor:pointer;text-decoration:none;display:inline-block;}
.hero-stats{display:flex;gap:24px;margin-top:28px;}
.hero-stat{text-align:center;}
.hero-stat-val{font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:800;color:var(--cyan);}
.hero-stat-lbl{font-size:11px;color:#64748B;letter-spacing:1px;}
.hero-visual{flex-shrink:0;display:none;}
@media(min-width:768px){.hero-visual{display:grid;grid-template-columns:1fr 1fr;gap:12px;}}
.hero-card{background:rgba(255,255,255,0.06);backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.1);border-radius:14px;padding:16px;text-align:center;width:130px;}
.hero-card-icon{font-size:32px;margin-bottom:8px;}
.hero-card-name{font-size:12px;font-weight:600;color:white;margin-bottom:4px;}
.hero-card-price{font-size:13px;font-weight:700;color:var(--cyan);}

/* ── PROMO BANNER ── */
.promo-bar{background:linear-gradient(90deg,#DC2626,#D97706);color:white;padding:12px 24px;display:flex;align-items:center;justify-content:center;gap:10px;font-size:13px;font-weight:600;}
.promo-timer{background:rgba(255,255,255,0.2);border-radius:6px;padding:3px 10px;font-weight:700;font-size:14px;}

/* ── CATÉGORIES ── */
.section{padding:32px 24px;}
.section-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;}
.section-title{font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:700;color:var(--text);}
.section-title span{color:var(--cyan);}
.see-all{font-size:13px;color:var(--cyan);font-weight:600;text-decoration:none;cursor:pointer;}
.cats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
@media(min-width:600px){.cats{grid-template-columns:repeat(6,1fr);}}
@media(min-width:900px){.cats{grid-template-columns:repeat(8,1fr);}}
.cat-card{background:var(--white);border:1px solid var(--border);border-radius:14px;padding:16px 8px;text-align:center;cursor:pointer;transition:all .2s;box-shadow:var(--shadow);}
.cat-card:hover{border-color:var(--cyan);transform:translateY(-2px);box-shadow:var(--shadow-md);}
.cat-icon{font-size:28px;margin-bottom:8px;}
.cat-name{font-size:11px;font-weight:600;color:var(--text);}

/* ── PRODUITS ── */
.products-section{padding:0 24px 32px;}
.products-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;}
@media(min-width:500px){.products-grid{grid-template-columns:repeat(3,1fr);}}
@media(min-width:768px){.products-grid{grid-template-columns:repeat(4,1fr);gap:16px;}}
@media(min-width:1100px){.products-grid{grid-template-columns:repeat(5,1fr);}}

/* ── CARTE PRODUIT ── */
.p-card{background:var(--white);border:1px solid var(--border);border-radius:14px;overflow:hidden;transition:all .25s;box-shadow:var(--shadow);position:relative;cursor:pointer;}
.p-card:hover{border-color:var(--cyan);transform:translateY(-3px);box-shadow:var(--shadow-lg);}
.p-badge-wrap{position:absolute;top:8px;left:8px;display:flex;flex-direction:column;gap:4px;z-index:2;}
.p-badge{display:inline-block;padding:3px 8px;border-radius:6px;font-size:10px;font-weight:700;}
.badge-new{background:#06B6D4;color:#000;}
.badge-hot{background:#DC2626;color:white;}
.badge-promo{background:#D97706;color:white;}
.p-wish{position:absolute;top:8px;right:8px;background:white;border:1px solid var(--border);border-radius:50%;width:30px;height:30px;display:flex;align-items:center;justify-content:center;font-size:14px;cursor:pointer;z-index:2;}
.p-img{width:100%;height:150px;background:var(--bg2);display:flex;align-items:center;justify-content:center;font-size:48px;overflow:hidden;}
.p-img img{width:100%;height:150px;object-fit:cover;}
@media(min-width:600px){.p-img,.p-img img{height:180px;}}
.p-body{padding:12px;}
.p-cat{font-size:10px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.p-name{font-weight:600;font-size:13px;color:var(--text);margin-bottom:6px;line-height:1.35;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}
.p-rating{display:flex;align-items:center;gap:4px;margin-bottom:8px;}
.stars{color:#F59E0B;font-size:11px;}
.rating-count{font-size:10px;color:var(--muted);}
.p-prix-wrap{display:flex;align-items:center;gap:6px;margin-bottom:10px;flex-wrap:wrap;}
.p-prix{font-size:15px;font-weight:700;color:var(--text);}
.p-prix-old{font-size:12px;color:var(--muted);text-decoration:line-through;}
.p-discount{font-size:11px;font-weight:700;color:var(--red);}
.p-stock-bar{height:3px;background:var(--border);border-radius:2px;margin-bottom:10px;overflow:hidden;}
.p-stock-fill{height:100%;border-radius:2px;background:linear-gradient(90deg,var(--green),var(--cyan));}
.p-stock-text{font-size:10px;color:var(--muted);margin-bottom:10px;}
.btn-add{width:100%;padding:9px;background:var(--dark);color:white;border:none;border-radius:8px;font-size:12px;font-weight:600;cursor:pointer;transition:all .2s;}
.btn-add:hover{background:var(--cyan);color:#000;}
.btn-add:disabled{background:var(--border);color:var(--muted);cursor:not-allowed;}
@media(min-width:600px){.btn-add{padding:11px;font-size:13px;}}

/* ── BANNER MILIEU ── */
.mid-banner{margin:0 24px 32px;background:linear-gradient(135deg,#7C3AED,#2563EB);border-radius:18px;padding:32px;color:white;display:flex;align-items:center;justify-content:space-between;overflow:hidden;position:relative;}
.mid-banner::before{content:'🌍';font-size:120px;position:absolute;right:20px;top:50%;transform:translateY(-50%);opacity:0.15;}
.mid-banner-text h2{font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:800;margin-bottom:8px;}
.mid-banner-text p{font-size:14px;color:rgba(255,255,255,0.8);margin-bottom:18px;}
.btn-banner{background:white;color:#7C3AED;border:none;border-radius:8px;padding:11px 22px;font-size:13px;font-weight:700;cursor:pointer;}

/* ── POURQUOI AMAN ── */
.why{padding:0 24px 32px;}
.why-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;}
@media(min-width:600px){.why-grid{grid-template-columns:repeat(4,1fr);}}
.why-card{background:var(--white);border:1px solid var(--border);border-radius:14px;padding:20px;text-align:center;box-shadow:var(--shadow);}
.why-icon{font-size:32px;margin-bottom:10px;}
.why-title{font-size:13px;font-weight:700;color:var(--text);margin-bottom:4px;}
.why-text{font-size:11px;color:var(--muted);line-height:1.5;}

/* ── TÉMOIGNAGES ── */
.testimonials{padding:0 24px 32px;}
.testi-grid{display:grid;grid-template-columns:1fr;gap:14px;}
@media(min-width:600px){.testi-grid{grid-template-columns:repeat(3,1fr);}}
.testi-card{background:var(--white);border:1px solid var(--border);border-radius:14px;padding:20px;box-shadow:var(--shadow);}
.testi-stars{color:#F59E0B;font-size:14px;margin-bottom:10px;}
.testi-text{font-size:13px;color:var(--text);line-height:1.6;margin-bottom:12px;font-style:italic;}
.testi-author{display:flex;align-items:center;gap:10px;}
.testi-avatar{width:36px;height:36px;border-radius:50%;background:var(--cyan);display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;}
.testi-name{font-size:13px;font-weight:600;}
.testi-loc{font-size:11px;color:var(--muted);}

/* ── FOOTER ── */
.footer{background:var(--dark);color:white;padding:40px 24px 20px;}
.footer-grid{display:grid;grid-template-columns:1fr;gap:28px;margin-bottom:28px;}
@media(min-width:600px){.footer-grid{grid-template-columns:2fr 1fr 1fr 1fr;}}
.footer-brand-name{font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:800;color:var(--cyan);letter-spacing:3px;margin-bottom:8px;}
.footer-brand-tag{font-size:10px;letter-spacing:3px;color:#64748B;margin-bottom:14px;}
.footer-desc{font-size:13px;color:#94A3B8;line-height:1.6;}
.footer-col-title{font-size:12px;font-weight:700;letter-spacing:2px;color:#94A3B8;text-transform:uppercase;margin-bottom:14px;}
.footer-links{list-style:none;display:flex;flex-direction:column;gap:8px;}
.footer-links a{font-size:13px;color:#64748B;text-decoration:none;transition:color .2s;}
.footer-links a:hover{color:var(--cyan);}
.footer-bottom{border-top:1px solid #1E3A5F;padding-top:20px;display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;}
.footer-bottom-left{font-size:12px;color:#64748B;}
.footer-socials{display:flex;gap:10px;}
.social-btn{width:34px;height:34px;border-radius:8px;background:#1E3A5F;display:flex;align-items:center;justify-content:center;font-size:16px;cursor:pointer;transition:background .2s;}
.social-btn:hover{background:var(--cyan);}

/* ── MODAL COMMANDE ── */
.modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:500;align-items:flex-end;justify-content:center;}
@media(min-width:600px){.modal-bg{align-items:center;}}
.modal-bg.open{display:flex;}
.modal{background:white;border-radius:20px 20px 0 0;padding:28px 24px 32px;width:100%;max-width:460px;animation:slideUp .3s ease;}
@media(min-width:600px){.modal{border-radius:20px;}}
@keyframes slideUp{from{transform:translateY(60px);opacity:0;}to{transform:translateY(0);opacity:1;}}
.modal-handle{width:36px;height:4px;background:#E5E7EB;border-radius:2px;margin:0 auto 20px;}
@media(min-width:600px){.modal-handle{display:none;}}
.modal-title{font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:700;color:var(--text);margin-bottom:4px;}
.modal-sub{font-size:13px;color:var(--muted);margin-bottom:18px;}
.modal-product{background:var(--bg);border-radius:10px;padding:14px;margin-bottom:18px;display:flex;justify-content:space-between;align-items:center;border:1px solid var(--border);}
.modal-product-info{}
.modal-product-cat{font-size:10px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;margin-bottom:2px;}
.modal-product-name{font-weight:700;font-size:15px;color:var(--text);}
.modal-product-prix{font-size:17px;font-weight:800;color:var(--dark);}
.mfield{width:100%;padding:13px 16px;margin-bottom:12px;background:var(--bg);border:1.5px solid var(--border);color:var(--text);border-radius:10px;font-size:14px;font-family:'Inter',sans-serif;outline:none;transition:border .2s;-webkit-appearance:none;}
.mfield:focus{border-color:var(--cyan);background:white;}
.modal-btns{display:grid;grid-template-columns:1fr 2fr;gap:10px;margin-top:4px;}
.btn-cancel{padding:14px;background:transparent;border:1.5px solid var(--border);color:var(--muted);border-radius:10px;font-size:14px;font-weight:500;cursor:pointer;}
.btn-confirm{padding:14px;background:var(--dark);color:white;border:none;border-radius:10px;font-size:14px;font-weight:700;cursor:pointer;transition:all .2s;}
.btn-confirm:hover{background:var(--cyan);color:#000;}
.modal-secure{text-align:center;font-size:11px;color:var(--muted);margin-top:12px;display:flex;align-items:center;justify-content:center;gap:4px;}

/* ── SUIVI COMMANDE ── */
.track-section{background:var(--bg2);border-top:1px solid var(--border);border-bottom:1px solid var(--border);padding:24px;margin-bottom:0;}
.track-inner{max-width:500px;margin:0 auto;text-align:center;}
.track-inner h3{font-family:'Space Grotesk',sans-serif;font-size:16px;font-weight:700;margin-bottom:6px;}
.track-inner p{font-size:13px;color:var(--muted);margin-bottom:14px;}
.track-form{display:flex;gap:8px;}
.track-input{flex:1;padding:11px 16px;border:1.5px solid var(--border);border-radius:9px;font-size:14px;outline:none;background:white;}
.track-input:focus{border-color:var(--cyan);}
.track-btn{background:var(--dark);color:white;border:none;border-radius:9px;padding:11px 20px;font-size:13px;font-weight:700;cursor:pointer;white-space:nowrap;}
</style>
</head><body>

<!-- TOP BAR -->
<div class="topbar">🚀 Livraison gratuite à Cotonou ce mois · <span>Code : AMAN2026</span> · Paiement Mobile Money accepté</div>

<!-- NAV -->
<nav class="nav">
  <a href="/shop" class="nav-brand">
    <div class="nav-logo">🌍</div>
    <span class="nav-name">AM<span>AN</span></span>
  </a>
  <div class="search-bar">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
    <input type="text" placeholder="Cherchez un produit, une marque..." id="searchInput" oninput="filterProducts(this.value)">
    <button>Chercher</button>
  </div>
  <div class="nav-actions">
    <a href="/suivi" class="nav-track">📦 Suivi</a>
    <a href="https://wa.me/22901000000?text=Bonjour AMAN" target="_blank" class="nav-wa">💬 WhatsApp</a>
  </div>
</nav>

<!-- HERO -->
<div class="hero">
  <div class="hero-text">
    <div class="hero-badge">🌍 N°1 E-commerce au Bénin</div>
    <h1>Votre marketplace<br><em>premium africaine</em></h1>
    <p>Tech, Mode, Maison, Beauté — Tout ce dont vous avez besoin, livré rapidement partout au Bénin et en Afrique.</p>
    <div class="hero-btns">
      <button class="btn-hero-primary" onclick="document.getElementById('produits-section').scrollIntoView({behavior:'smooth'})">
        🛒 Découvrir les produits
      </button>
      <a href="/suivi" class="btn-hero-secondary">📦 Suivre ma commande</a>
    </div>
    <div class="hero-stats">
      <div class="hero-stat"><div class="hero-stat-val">500+</div><div class="hero-stat-lbl">CLIENTS</div></div>
      <div class="hero-stat"><div class="hero-stat-val">24h</div><div class="hero-stat-lbl">LIVRAISON</div></div>
      <div class="hero-stat"><div class="hero-stat-val">100%</div><div class="hero-stat-lbl">GARANTI</div></div>
    </div>
  </div>
  <div class="hero-visual">
    <div class="hero-card"><div class="hero-card-icon">📱</div><div class="hero-card-name">Smartphones</div><div class="hero-card-price">Dès 45K FCFA</div></div>
    <div class="hero-card"><div class="hero-card-icon">🎧</div><div class="hero-card-name">Audio</div><div class="hero-card-price">Dès 8K FCFA</div></div>
    <div class="hero-card"><div class="hero-card-icon">💻</div><div class="hero-card-name">Informatique</div><div class="hero-card-price">Dès 120K FCFA</div></div>
    <div class="hero-card"><div class="hero-card-icon">📷</div><div class="hero-card-name">Photo/Vidéo</div><div class="hero-card-price">Dès 15K FCFA</div></div>
  </div>
</div>

<!-- PROMO BAR -->
<div class="promo-bar">
  🔥 Ventes Flash · Offres limitées ·
  <span class="promo-timer" id="timer">02:45:30</span>
  · Jusqu'à -40% sur la tech
</div>

<!-- CATÉGORIES -->
<div class="section">
  <div class="section-head">
    <div class="section-title">Toutes les <span>catégories</span></div>
  </div>
  <div class="cats">
    <div class="cat-card" onclick="filterCat('tech')"><div class="cat-icon">📱</div><div class="cat-name">Tech</div></div>
    <div class="cat-card" onclick="filterCat('audio')"><div class="cat-icon">🎧</div><div class="cat-name">Audio</div></div>
    <div class="cat-card" onclick="filterCat('photo')"><div class="cat-icon">📷</div><div class="cat-name">Photo</div></div>
    <div class="cat-card" onclick="filterCat('mode')"><div class="cat-icon">👗</div><div class="cat-name">Mode</div></div>
    <div class="cat-card" onclick="filterCat('maison')"><div class="cat-icon">🏠</div><div class="cat-name">Maison</div></div>
    <div class="cat-card" onclick="filterCat('beaute')"><div class="cat-icon">✨</div><div class="cat-name">Beauté</div></div>
    <div class="cat-card" onclick="filterCat('sport')"><div class="cat-icon">⚽</div><div class="cat-name">Sport</div></div>
    <div class="cat-card" onclick="filterCat('')"><div class="cat-icon">🛒</div><div class="cat-name">Tout</div></div>
  </div>
</div>

<!-- SECTION SUIVI RAPIDE -->
<div class="track-section">
  <div class="track-inner">
    <h3>📦 Où est ma commande ?</h3>
    <p>Entrez votre numéro de commande pour suivre votre livraison en temps réel</p>
    <form class="track-form" action="/suivi" method="GET">
      <input class="track-input" name="id" placeholder="N° de commande (ex: 12)" type="number">
      <button class="track-btn" type="submit">Suivre →</button>
    </form>
  </div>
</div>

<!-- PRODUITS -->
<div class="products-section" id="produits-section">
  <div class="section-head" style="padding:24px 0 16px;">
    <div class="section-title">Nos <span>produits</span></div>
    <span class="see-all">{{ produits|length }} articles</span>
  </div>
  <div class="products-grid" id="productsGrid">

    <!-- Produits réels du catalogue -->
    {% for p in produits %}
    <div class="p-card" data-name="{{ p[1]|lower }}" data-cat="">
      <div class="p-badge-wrap">
        {% if loop.index <= 2 %}<span class="p-badge badge-new">NOUVEAU</span>{% endif %}
        {% if p[3] < 5 and p[3] > 0 %}<span class="p-badge badge-hot">LIMITÉ</span>{% endif %}
      </div>
      <div class="p-wish">🤍</div>
      <div class="p-img">
        {% if p[5] %}<img src="{{ p[5] }}" alt="{{ p[1] }}" onerror="this.parentElement.innerHTML='📦'">
        {% else %}📦{% endif %}
      </div>
      <div class="p-body">
        <div class="p-cat">AMAN STORE</div>
        <div class="p-name">{{ p[1] }}</div>
        <div class="p-rating">
          <span class="stars">★★★★★</span>
          <span class="rating-count">({{ (loop.index * 7 + 12) }})</span>
        </div>
        <div class="p-prix-wrap">
          <span class="p-prix">{{ "{:,}".format(p[2]) }} FCFA</span>
          <span class="p-prix-old">{{ "{:,}".format((p[2] * 1.15)|int) }} FCFA</span>
          <span class="p-discount">-13%</span>
        </div>
        {% if p[3] > 0 %}
        <div class="p-stock-bar"><div class="p-stock-fill" style="width:{{ [p[3]*10, 100]|min }}%"></div></div>
        <div class="p-stock-text">{{ p[3] }} en stock</div>
        <button class="btn-add" onclick="openModal('{{ p[1] }}','{{ "{:,}".format(p[2]) }}','{{ p[2] }}')">
          + Commander
        </button>
        {% else %}
        <button class="btn-add" disabled>Rupture de stock</button>
        {% endif %}
      </div>
    </div>
    {% endfor %}

    <!-- Produits décoratifs pour enrichir le catalogue -->
    <div class="p-card" data-name="ecouteurs bluetooth" data-cat="audio">
      <div class="p-badge-wrap"><span class="p-badge badge-hot">HOT</span></div>
      <div class="p-wish">🤍</div>
      <div class="p-img" style="background:#F0F9FF;">🎧</div>
      <div class="p-body">
        <div class="p-cat">AUDIO</div>
        <div class="p-name">Écouteurs Bluetooth Pro Max</div>
        <div class="p-rating"><span class="stars">★★★★★</span><span class="rating-count">(234)</span></div>
        <div class="p-prix-wrap"><span class="p-prix">12,500 FCFA</span><span class="p-prix-old">22,000 FCFA</span><span class="p-discount">-43%</span></div>
        <div class="p-stock-bar"><div class="p-stock-fill" style="width:60%"></div></div>
        <div class="p-stock-text">Bientôt disponible</div>
        <button class="btn-add" onclick="openModal('Écouteurs Bluetooth Pro Max','12,500','12500')">+ Commander</button>
      </div>
    </div>

    <div class="p-card" data-name="montre connectee smartwatch" data-cat="tech">
      <div class="p-badge-wrap"><span class="p-badge badge-promo">-35%</span></div>
      <div class="p-wish">🤍</div>
      <div class="p-img" style="background:#FFF7ED;">⌚</div>
      <div class="p-body">
        <div class="p-cat">TECH</div>
        <div class="p-name">Montre Connectée Sport Ultra</div>
        <div class="p-rating"><span class="stars">★★★★☆</span><span class="rating-count">(89)</span></div>
        <div class="p-prix-wrap"><span class="p-prix">28,000 FCFA</span><span class="p-prix-old">43,000 FCFA</span><span class="p-discount">-35%</span></div>
        <div class="p-stock-bar"><div class="p-stock-fill" style="width:40%"></div></div>
        <div class="p-stock-text">Bientôt disponible</div>
        <button class="btn-add" onclick="openModal('Montre Connectée Sport Ultra','28,000','28000')">+ Commander</button>
      </div>
    </div>

    <div class="p-card" data-name="powerbank batterie externe" data-cat="tech">
      <div class="p-badge-wrap"><span class="p-badge badge-new">NOUVEAU</span></div>
      <div class="p-wish">🤍</div>
      <div class="p-img" style="background:#F0FDF4;">🔋</div>
      <div class="p-body">
        <div class="p-cat">TECH</div>
        <div class="p-name">Powerbank 30000mAh Charge Rapide</div>
        <div class="p-rating"><span class="stars">★★★★★</span><span class="rating-count">(156)</span></div>
        <div class="p-prix-wrap"><span class="p-prix">18,500 FCFA</span><span class="p-prix-old">25,000 FCFA</span><span class="p-discount">-26%</span></div>
        <div class="p-stock-bar"><div class="p-stock-fill" style="width:75%"></div></div>
        <div class="p-stock-text">Bientôt disponible</div>
        <button class="btn-add" onclick="openModal('Powerbank 30000mAh','18,500','18500')">+ Commander</button>
      </div>
    </div>

    <div class="p-card" data-name="clavier mecanique gaming" data-cat="tech">
      <div class="p-badge-wrap"><span class="p-badge badge-hot">GAMING</span></div>
      <div class="p-wish">🤍</div>
      <div class="p-img" style="background:#FDF4FF;">⌨️</div>
      <div class="p-body">
        <div class="p-cat">GAMING</div>
        <div class="p-name">Clavier Mécanique RGB Gaming</div>
        <div class="p-rating"><span class="stars">★★★★☆</span><span class="rating-count">(67)</span></div>
        <div class="p-prix-wrap"><span class="p-prix">35,000 FCFA</span><span class="p-prix-old">50,000 FCFA</span><span class="p-discount">-30%</span></div>
        <div class="p-stock-bar"><div class="p-stock-fill" style="width:30%"></div></div>
        <div class="p-stock-text">Bientôt disponible</div>
        <button class="btn-add" onclick="openModal('Clavier Mécanique RGB','35,000','35000')">+ Commander</button>
      </div>
    </div>

    <div class="p-card" data-name="lampe led bureau" data-cat="maison">
      <div class="p-badge-wrap"><span class="p-badge badge-new">NOUVEAU</span></div>
      <div class="p-wish">🤍</div>
      <div class="p-img" style="background:#FEFCE8;">💡</div>
      <div class="p-body">
        <div class="p-cat">MAISON</div>
        <div class="p-name">Lampe LED Bureau USB Tactile</div>
        <div class="p-rating"><span class="stars">★★★★★</span><span class="rating-count">(203)</span></div>
        <div class="p-prix-wrap"><span class="p-prix">8,500 FCFA</span><span class="p-prix-old">12,000 FCFA</span><span class="p-discount">-29%</span></div>
        <div class="p-stock-bar"><div class="p-stock-fill" style="width:85%"></div></div>
        <div class="p-stock-text">Bientôt disponible</div>
        <button class="btn-add" onclick="openModal('Lampe LED Bureau','8,500','8500')">+ Commander</button>
      </div>
    </div>

    <div class="p-card" data-name="sac a dos anti vol voyage" data-cat="mode">
      <div class="p-badge-wrap"><span class="p-badge badge-promo">PROMO</span></div>
      <div class="p-wish">🤍</div>
      <div class="p-img" style="background:#F1F5F9;">🎒</div>
      <div class="p-body">
        <div class="p-cat">MODE</div>
        <div class="p-name">Sac à Dos Anti-Vol USB 40L</div>
        <div class="p-rating"><span class="stars">★★★★☆</span><span class="rating-count">(91)</span></div>
        <div class="p-prix-wrap"><span class="p-prix">22,000 FCFA</span><span class="p-prix-old">35,000 FCFA</span><span class="p-discount">-37%</span></div>
        <div class="p-stock-bar"><div class="p-stock-fill" style="width:50%"></div></div>
        <div class="p-stock-text">Bientôt disponible</div>
        <button class="btn-add" onclick="openModal('Sac à Dos Anti-Vol USB','22,000','22000')">+ Commander</button>
      </div>
    </div>

    <div class="p-card" data-name="ventilateur de table usb" data-cat="maison">
      <div class="p-badge-wrap"><span class="p-badge badge-hot">CHAUD</span></div>
      <div class="p-wish">🤍</div>
      <div class="p-img" style="background:#EFF6FF;">🌀</div>
      <div class="p-body">
        <div class="p-cat">MAISON</div>
        <div class="p-name">Ventilateur Portable USB Silencieux</div>
        <div class="p-rating"><span class="stars">★★★★★</span><span class="rating-count">(312)</span></div>
        <div class="p-prix-wrap"><span class="p-prix">6,500 FCFA</span><span class="p-prix-old">9,000 FCFA</span><span class="p-discount">-28%</span></div>
        <div class="p-stock-bar"><div class="p-stock-fill" style="width:90%"></div></div>
        <div class="p-stock-text">Bientôt disponible</div>
        <button class="btn-add" onclick="openModal('Ventilateur Portable USB','6,500','6500')">+ Commander</button>
      </div>
    </div>

  </div>
</div>

<!-- BANNER MILIEU -->
<div class="mid-banner">
  <div class="mid-banner-text">
    <h2>Livraison dans tout le Bénin 🇧🇯</h2>
    <p>Cotonou en 24h · Porto-Novo en 48h · Parakou en 72h<br>Paiement à la livraison · MTN · Moov Money</p>
    <button class="btn-banner" onclick="document.getElementById('produits-section').scrollIntoView({behavior:'smooth'})">
      Commander maintenant →
    </button>
  </div>
</div>

<!-- POURQUOI AMAN -->
<div class="why">
  <div class="section-head"><div class="section-title">Pourquoi choisir <span>AMAN</span> ?</div></div>
  <div class="why-grid">
    <div class="why-card"><div class="why-icon">🔐</div><div class="why-title">Paiement sécurisé</div><div class="why-text">À la livraison, MTN Money ou Moov Money. Payez quand vous recevez.</div></div>
    <div class="why-card"><div class="why-icon">🚀</div><div class="why-title">Livraison express</div><div class="why-text">Cotonou 24h, Bénin 48-72h, Afrique de l'Ouest 5-10 jours.</div></div>
    <div class="why-card"><div class="why-icon">✅</div><div class="why-title">Qualité garantie</div><div class="why-text">Chaque produit est vérifié avant expédition. Satisfait ou remboursé.</div></div>
    <div class="why-card"><div class="why-icon">💬</div><div class="why-title">Support 7j/7</div><div class="why-text">Notre équipe répond sur WhatsApp en moins de 30 minutes.</div></div>
  </div>
</div>

<!-- TÉMOIGNAGES -->
<div class="testimonials">
  <div class="section-head"><div class="section-title">Ce que disent nos <span>clients</span></div></div>
  <div class="testi-grid">
    <div class="testi-card">
      <div class="testi-stars">★★★★★</div>
      <div class="testi-text">"Livraison en 24h comme promis. Le Ring Light est parfait pour mes vidéos TikTok. Je recommande AMAN à 100% !"</div>
      <div class="testi-author"><div class="testi-avatar">👩</div><div><div class="testi-name">Fatoumata K.</div><div class="testi-loc">Cotonou, Bénin</div></div></div>
    </div>
    <div class="testi-card">
      <div class="testi-stars">★★★★★</div>
      <div class="testi-text">"Le Gimbal stabilisateur est de grande qualité. Prix correct et service client très réactif sur WhatsApp."</div>
      <div class="testi-author"><div class="testi-avatar">👨</div><div><div class="testi-name">Kofi A.</div><div class="testi-loc">Porto-Novo, Bénin</div></div></div>
    </div>
    <div class="testi-card">
      <div class="testi-stars">★★★★★</div>
      <div class="testi-text">"Première commande, j'avais peur. Mais tout s'est bien passé. Le microphone est excellent. AMAN c'est sérieux !"</div>
      <div class="testi-author"><div class="testi-avatar">👩</div><div><div class="testi-name">Afi M.</div><div class="testi-loc">Abomey-Calavi, Bénin</div></div></div>
    </div>
  </div>
</div>

<!-- FOOTER -->
<div class="footer">
  <div class="footer-grid">
    <div>
      <div class="footer-brand-name">AMAN</div>
      <div class="footer-brand-tag">TRUST · SAFETY · QUALITY</div>
      <div class="footer-desc">Votre marketplace premium africaine. Produits tech et accessoires de qualité, livrés rapidement partout au Bénin et en Afrique.</div>
    </div>
    <div>
      <div class="footer-col-title">Boutique</div>
      <ul class="footer-links">
        <li><a href="#">Tech & Accessoires</a></li>
        <li><a href="#">Audio & Son</a></li>
        <li><a href="#">Photo & Vidéo</a></li>
        <li><a href="#">Gaming</a></li>
        <li><a href="#">Maison</a></li>
      </ul>
    </div>
    <div>
      <div class="footer-col-title">Service</div>
      <ul class="footer-links">
        <li><a href="/suivi">Suivi commande</a></li>
        <li><a href="#">Retours</a></li>
        <li><a href="#">FAQ</a></li>
        <li><a href="#">Contact</a></li>
      </ul>
    </div>
    <div>
      <div class="footer-col-title">Contact</div>
      <ul class="footer-links">
        <li><a href="#">📍 Cotonou, Bénin</a></li>
        <li><a href="#">💬 WhatsApp</a></li>
        <li><a href="#">📘 Facebook</a></li>
        <li><a href="#">🎵 TikTok</a></li>
      </ul>
    </div>
  </div>
  <div class="footer-bottom">
    <div class="footer-bottom-left">© 2026 AMAN — Tous droits réservés · Cotonou, Bénin</div>
    <div class="footer-socials">
      <div class="social-btn">📘</div>
      <div class="social-btn">🎵</div>
      <div class="social-btn">💬</div>
      <div class="social-btn">📷</div>
    </div>
  </div>
</div>

<!-- MODAL COMMANDE -->
<div class="modal-bg" id="modal" onclick="if(event.target===this)closeModal()">
  <div class="modal">
    <div class="modal-handle"></div>
    <div class="modal-title">Passer une commande</div>
    <div class="modal-sub">Remplissez le formulaire — nous vous contactons dans les 30min</div>
    <div class="modal-product">
      <div class="modal-product-info">
        <div class="modal-product-cat">PRODUIT SÉLECTIONNÉ</div>
        <div class="modal-product-name" id="modal-nom">—</div>
      </div>
      <div class="modal-product-prix" id="modal-prix">—</div>
    </div>
    <form method="POST" action="/shop/commander">
      <input type="hidden" name="produit" id="modal-produit">
      <input type="hidden" name="montant" id="modal-montant">
      <input class="mfield" name="client" placeholder="Votre nom complet *" required autocomplete="name">
      <input class="mfield" name="telephone" placeholder="Numéro téléphone (+229 01...) *" required type="tel" autocomplete="tel">
      <input class="mfield" name="adresse" placeholder="Adresse de livraison *" required>
      <select class="mfield" name="paiement">
        <option value="livraison">💵 Paiement à la livraison</option>
        <option value="mtn">📱 MTN Mobile Money</option>
        <option value="moov">📱 Moov Money</option>
      </select>
      <div class="modal-btns">
        <button type="button" class="btn-cancel" onclick="closeModal()">Annuler</button>
        <button type="submit" class="btn-confirm">✓ Confirmer la commande</button>
      </div>
      <div class="modal-secure">🔒 Vos données sont sécurisées · AMAN 2026</div>
    </form>
  </div>
</div>

<script>
// Modal
function openModal(nom, prix, montant) {
  document.getElementById('modal-produit').value = nom;
  document.getElementById('modal-montant').value = montant;
  document.getElementById('modal-nom').textContent = nom;
  document.getElementById('modal-prix').textContent = prix + ' FCFA';
  document.getElementById('modal').classList.add('open');
  document.body.style.overflow = 'hidden';
}
function closeModal() {
  document.getElementById('modal').classList.remove('open');
  document.body.style.overflow = '';
}

// Recherche
function filterProducts(q) {
  const cards = document.querySelectorAll('.p-card');
  q = q.toLowerCase();
  cards.forEach(c => {
    const name = c.dataset.name || '';
    c.style.display = name.includes(q) || !q ? '' : 'none';
  });
}

// Filtre catégorie
function filterCat(cat) {
  const cards = document.querySelectorAll('.p-card');
  cards.forEach(c => {
    c.style.display = !cat || c.dataset.cat === cat ? '' : 'none';
  });
}

// Timer promo
function updateTimer() {
  const el = document.getElementById('timer');
  if(!el) return;
  const parts = el.textContent.split(':').map(Number);
  let [h,m,s] = parts;
  s--; if(s<0){s=59;m--;} if(m<0){m=59;h--;} if(h<0){h=23;m=59;s=59;}
  el.textContent = [h,m,s].map(n=>String(n).padStart(2,'0')).join(':');
}
setInterval(updateTimer, 1000);

// Wishlist animation
document.querySelectorAll('.p-wish').forEach(btn => {
  btn.addEventListener('click', function(e) {
    e.stopPropagation();
    this.textContent = this.textContent === '🤍' ? '❤️' : '🤍';
  });
});
</script>
</body></html>'''


@app.route('/catalogue')
def catalogue():
    if not session.get('ok'): return redirect('/login')
    conn = get_conn()
    produits = conn.cursor().execute("SELECT * FROM produits ORDER BY id DESC").fetchall()
    conn.close()
    msg = request.args.get('msg','')
    return render_template_string(CATALOGUE_PAGE, css=CSS, nav=nav('cat'),
        produits=produits, msg=msg)

@app.route('/produit/stock/<int:id>', methods=['POST'])
def produit_stock(id):
    if not session.get('ok'): return redirect('/login')
    stock = int(request.form['stock'])
    conn = get_conn()
    conn.cursor().execute(q("UPDATE produits SET stock=? WHERE id=?"), (stock, id))
    conn.commit(); conn.close()
    return redirect('/catalogue?msg=Stock mis à jour ✓')

@app.route('/shop')
def shop():
    conn = get_conn()
    produits = conn.cursor().execute("SELECT * FROM produits ORDER BY id").fetchall()
    conn.close()
    return render_template_string(SHOP_PAGE, produits=produits)

@app.route('/shop/commander', methods=['POST'])
def shop_commander():
    client = request.form['client'].strip()
    telephone = request.form['telephone'].strip()
    produit = request.form['produit']
    adresse = request.form.get('adresse','').strip()
    paiement = request.form.get('paiement','livraison').strip()
    try:
        conn = get_conn()
        c = conn.cursor()
        if DATABASE_URL:
            prix_row = c.execute("SELECT prix FROM produits WHERE nom=%s", (produit,)).fetchone()
            montant = prix_row[0] if prix_row else 0
            c.execute(
                "INSERT INTO commandes (client,telephone,produit,montant,statut,adresse,date) VALUES (%s,%s,%s,%s,%s,%s,NOW())",
                (client, telephone, produit, montant, 'en_attente', adresse))
        else:
            prix_row = c.execute(q("SELECT prix FROM produits WHERE nom=?"), (produit,)).fetchone()
            montant = prix_row[0] if prix_row else 0
            c.execute(
                "INSERT INTO commandes (client,telephone,produit,montant,statut,adresse,date) VALUES (?,?,?,?,?,?,datetime('now','localtime'))",
                (client, telephone, produit, montant, 'en_attente', adresse))
        conn.commit()
        conn.close()
    except Exception as e:
        return f"Erreur: {e}", 500
    return render_template_string('''<!DOCTYPE html><html><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>AMAN — Commande confirmée</title>
    <style>*{margin:0;padding:0;box-sizing:border-box;}body{background:#060D1F;color:#E2E8F0;font-family:sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;}
    .box{text-align:center;padding:50px 40px;background:#0C1829;border:1px solid #1E3A5F;border-radius:18px;max-width:400px;}
    .icon{font-size:60px;margin-bottom:20px;}
    h2{font-size:22px;margin-bottom:10px;color:#84CC16;}
    p{color:#64748B;font-size:14px;margin-bottom:6px;}
    a{display:inline-block;margin-top:24px;padding:12px 28px;background:#06B6D4;color:#000;border-radius:9px;font-weight:700;text-decoration:none;}</style></head><body>
    <div class="box">
      <div class="icon">✅</div>
      <h2>Commande confirmée !</h2>
      <p>Merci <strong>''' + client + '''</strong></p>
      <p>Produit : <strong>''' + produit + '''</strong></p>
      <p>Nous vous contactons au <strong>''' + telephone + '''</strong></p>
      <p style="margin-top:12px;color:#F59E0B;">TRUST · SAFETY · QUALITY</p>
      <a href="/shop">← Continuer les achats</a>
    </div>
    </body></html>''')


# ─── PAGE SUIVI COMMANDE PUBLIC ──────────────────────────────────
SUIVI_PAGE = '''<!DOCTYPE html><html lang="fr"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AMAN — Suivi de commande</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box;}
:root{--bg:#F8F9FC;--white:#fff;--dark:#060D1F;--cyan:#06B6D4;--green:#16A34A;--gold:#D97706;--red:#DC2626;--purple:#7C3AED;--text:#111827;--muted:#6B7280;--border:#E5E7EB;}
body{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;min-height:100vh;}
.nav{background:var(--white);border-bottom:1px solid var(--border);padding:0 24px;height:60px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;box-shadow:0 1px 3px rgba(0,0,0,0.08);}
.nav-brand{font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:800;color:var(--dark);letter-spacing:2px;text-decoration:none;}
.nav-brand span{color:var(--cyan);}
.nav-back{font-size:13px;color:var(--cyan);text-decoration:none;font-weight:600;}
.page{max-width:640px;margin:0 auto;padding:40px 20px;}
.page-title{font-family:'Space Grotesk',sans-serif;font-size:26px;font-weight:800;margin-bottom:6px;}
.page-sub{color:var(--muted);font-size:14px;margin-bottom:32px;}
.search-box{background:var(--white);border:1px solid var(--border);border-radius:16px;padding:28px;margin-bottom:28px;box-shadow:0 1px 3px rgba(0,0,0,0.06);}
.search-label{font-size:13px;font-weight:600;color:var(--text);margin-bottom:8px;display:block;}
.search-row{display:flex;gap:10px;}
.search-input{flex:1;padding:13px 16px;border:1.5px solid var(--border);border-radius:10px;font-size:15px;outline:none;transition:border .2s;font-family:'Inter',sans-serif;}
.search-input:focus{border-color:var(--cyan);}
.search-btn{background:var(--dark);color:white;border:none;border-radius:10px;padding:13px 22px;font-size:14px;font-weight:700;cursor:pointer;white-space:nowrap;transition:background .2s;}
.search-btn:hover{background:var(--cyan);color:#000;}

/* Résultat */
.result-box{background:var(--white);border:1px solid var(--border);border-radius:16px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.06);}
.result-header{background:var(--dark);color:white;padding:20px 24px;display:flex;justify-content:space-between;align-items:center;}
.result-id{font-size:12px;letter-spacing:2px;color:#64748B;}
.result-date{font-size:12px;color:#64748B;}
.result-body{padding:24px;}
.result-product{font-size:18px;font-weight:700;margin-bottom:4px;}
.result-client{font-size:14px;color:var(--muted);margin-bottom:20px;}
.result-montant{display:inline-block;padding:4px 12px;background:#F59E0B15;border:1px solid #F59E0B40;border-radius:20px;font-size:13px;font-weight:700;color:var(--gold);margin-bottom:24px;}

/* Pipeline visuel */
.pipeline{margin-bottom:28px;}
.pipe-steps{display:flex;align-items:center;position:relative;}
.pipe-line{position:absolute;top:18px;left:18px;right:18px;height:2px;background:var(--border);z-index:0;}
.pipe-line-fill{position:absolute;top:18px;left:18px;height:2px;background:linear-gradient(90deg,var(--cyan),var(--green));z-index:1;transition:width .5s ease;}
.pipe-step{flex:1;display:flex;flex-direction:column;align-items:center;position:relative;z-index:2;}
.pipe-dot{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px;margin-bottom:8px;border:2px solid var(--border);background:var(--bg);transition:all .3s;}
.pipe-dot.done{background:var(--green);border-color:var(--green);color:white;}
.pipe-dot.active{background:var(--cyan);border-color:var(--cyan);color:white;box-shadow:0 0 0 4px rgba(6,182,212,0.2);}
.pipe-dot.pending{background:var(--white);color:var(--muted);}
.pipe-label{font-size:11px;font-weight:600;color:var(--muted);text-align:center;line-height:1.3;}
.pipe-label.active{color:var(--cyan);}
.pipe-label.done{color:var(--green);}

/* Infos livraison */
.info-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px;}
.info-card{background:var(--bg);border-radius:10px;padding:14px;}
.info-label{font-size:10px;letter-spacing:2px;color:var(--muted);text-transform:uppercase;margin-bottom:4px;}
.info-value{font-size:14px;font-weight:600;color:var(--text);}
.info-value.empty{color:var(--muted);font-weight:400;font-style:italic;}

/* Message statut */
.status-msg{border-radius:10px;padding:16px 20px;margin-bottom:20px;font-size:14px;font-weight:500;line-height:1.5;}
.msg-attente{background:#FEF3C715;border:1px solid #FDE68A;color:#92400E;}
.msg-confirmee{background:#E0F2FE;border:1px solid #BAE6FD;color:#0369A1;}
.msg-livraison{background:#EDE9FE;border:1px solid #DDD6FE;color:#5B21B6;}
.msg-livree{background:#DCFCE7;border:1px solid #86EFAC;color:#166534;}

/* Action WhatsApp */
.wa-btn{display:flex;align-items:center;justify-content:center;gap:8px;width:100%;padding:14px;background:#25D366;color:white;border:none;border-radius:10px;font-size:14px;font-weight:700;cursor:pointer;text-decoration:none;transition:opacity .2s;}
.wa-btn:hover{opacity:.9;}

/* Erreur */
.error-box{background:var(--white);border:1px solid var(--border);border-radius:16px;padding:40px;text-align:center;}
.error-icon{font-size:48px;margin-bottom:16px;}
.error-title{font-size:18px;font-weight:700;margin-bottom:8px;}
.error-text{color:var(--muted);font-size:14px;margin-bottom:24px;}

/* Footer */
.footer{text-align:center;padding:30px;color:var(--muted);font-size:12px;letter-spacing:2px;margin-top:20px;}
</style></head><body>

<nav class="nav">
  <a href="/shop" class="nav-brand">AM<span>AN</span></a>
  <a href="/shop" class="nav-back">← Retour à la boutique</a>
</nav>

<div class="page">
  <div class="page-title">📦 Suivi de commande</div>
  <div class="page-sub">Entrez votre numéro de commande pour suivre votre livraison en temps réel</div>

  <!-- FORMULAIRE RECHERCHE -->
  <div class="search-box">
    <label class="search-label">Numéro de commande</label>
    <form class="search-row" method="GET" action="/suivi">
      <input class="search-input" name="id" type="number" placeholder="Ex: 12" value="{{ commande_id or '' }}" required>
      <button class="search-btn" type="submit">Suivre →</button>
    </form>
    <div style="margin-top:10px;font-size:12px;color:var(--muted);">💡 Votre numéro de commande vous a été communiqué par WhatsApp après votre commande</div>
  </div>

  {% if commande %}
  {% set steps = ["en_attente","confirmee","en_livraison","livree"] %}
  {% set step_idx = steps.index(commande[5]) if commande[5] in steps else 0 %}
  {% set pct = [0, 33, 66, 100][step_idx] %}

  <div class="result-box">
    <div class="result-header">
      <div>
        <div class="result-id">COMMANDE #{{ commande[0] }}</div>
        <div style="font-size:16px;font-weight:700;margin-top:4px;color:white;">{{ commande[3] }}</div>
      </div>
      <div class="result-date">{{ commande[6] }}</div>
    </div>
    <div class="result-body">
      <div class="result-client">Client : <strong>{{ commande[1] }}</strong></div>
      <span class="result-montant">{{ "{:,}".format(commande[4]) }} FCFA</span>

      <!-- PIPELINE -->
      <div class="pipeline">
        <div style="position:relative;">
          <div class="pipe-steps">
            <div class="pipe-line"></div>
            <div class="pipe-line-fill" style="width:calc({{ pct }}% - 36px);"></div>
            {% for i, (emoji, label) in [(0,('📥','Reçue')),(1,('✅','Confirmée')),(2,('🚚','En route')),(3,('🎉','Livrée'))] %}
            <div class="pipe-step">
              <div class="pipe-dot {% if i < step_idx %}done{% elif i == step_idx %}active{% else %}pending{% endif %}">
                {{ emoji }}
              </div>
              <div class="pipe-label {% if i < step_idx %}done{% elif i == step_idx %}active{% endif %}">{{ label }}</div>
            </div>
            {% endfor %}
          </div>
        </div>
      </div>

      <!-- MESSAGE STATUT -->
      {% if commande[5] == "en_attente" %}
      <div class="status-msg msg-attente">⏳ <strong>Commande reçue</strong> — Nous avons bien reçu votre commande. Notre équipe va la confirmer sous peu et vous contactera par WhatsApp.</div>
      {% elif commande[5] == "confirmee" %}
      <div class="status-msg msg-confirmee">✅ <strong>Commande confirmée</strong> — Votre commande est confirmée et en cours de préparation. Vous recevrez un message dès l'expédition.</div>
      {% elif commande[5] == "en_livraison" %}
      <div class="status-msg msg-livraison">🚚 <strong>En cours de livraison</strong> — Votre commande est en route ! Notre livreur vous contactera bientôt pour la remise.</div>
      {% elif commande[5] == "livree" %}
      <div class="status-msg msg-livree">🎉 <strong>Commande livrée</strong> — Votre commande a bien été livrée. Merci de votre confiance ! Revenez vite sur AMAN.</div>
      {% endif %}

      <!-- INFOS SUPPLÉMENTAIRES -->
      <div class="info-grid">
        <div class="info-card">
          <div class="info-label">Transporteur</div>
          <div class="info-value {% if not commande[8] %}empty{% endif %}">{{ commande[8] or "En attente..." }}</div>
        </div>
        <div class="info-card">
          <div class="info-label">N° de suivi</div>
          <div class="info-value {% if not commande[7] %}empty{% endif %}">{{ commande[7] or "En attente..." }}</div>
        </div>
        <div class="info-card">
          <div class="info-label">Téléphone</div>
          <div class="info-value">{{ commande[2] }}</div>
        </div>
        <div class="info-card">
          <div class="info-label">Adresse</div>
          <div class="info-value {% if not commande[9] %}empty{% endif %}">{{ commande[9] or "Non renseignée" }}</div>
        </div>
      </div>

      <!-- WHATSAPP -->
      {% set tel = commande[2]|replace(" ","")|replace("+","") %}
      <a class="wa-btn" href="https://wa.me/22901000000?text=Bonjour AMAN, je veux des infos sur ma commande %23{{ commande[0] }}" target="_blank">
        💬 Contacter AMAN sur WhatsApp
      </a>
    </div>
  </div>

  {% elif erreur %}
  <div class="error-box">
    <div class="error-icon">🔍</div>
    <div class="error-title">Commande introuvable</div>
    <div class="error-text">Aucune commande trouvée avec le numéro <strong>#{{ commande_id }}</strong>.<br>Vérifiez votre numéro ou contactez-nous sur WhatsApp.</div>
    <a class="wa-btn" href="https://wa.me/22901000000?text=Bonjour AMAN, je cherche ma commande" target="_blank">
      💬 Contacter AMAN
    </a>
  </div>
  {% endif %}
</div>

<div class="footer">© 2026 AMAN · TRUST · SAFETY · QUALITY · COTONOU, BÉNIN</div>
</body></html>'''

@app.route('/suivi')
def suivi():
    commande_id = request.args.get('id', '').strip()
    commande = None
    erreur = False
    if commande_id:
        try:
            conn = get_conn()
            commande = conn.cursor().execute(
                q("SELECT * FROM commandes WHERE id=?"), (int(commande_id),)
            ).fetchone()
            conn.close()
            if not commande:
                erreur = True
        except:
            erreur = True
    return render_template_string(SUIVI_PAGE,
        commande=commande, commande_id=commande_id, erreur=erreur)

@app.route('/export')
def export_excel():
    if not session.get('ok'): return redirect('/login')
    conn = get_conn()
    ventes = conn.cursor().execute("SELECT * FROM ventes").fetchall()
    conn.close()
    wb = openpyxl.Workbook()
    ws = wb.active; ws.title = "Ventes AMAN"
    ws.append(["ID","Produit","Montant (FCFA)","Telephone","Date"])
    for v in ventes: ws.append(list(v))
    ws.append([]); ws.append(["","TOTAL",sum(v[2] for v in ventes),"",""])
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
