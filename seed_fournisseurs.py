"""
Script à exécuter UNE FOIS sur Render pour pré-remplir les fournisseurs.
Dans le terminal Render shell : python seed_fournisseurs.py
"""
import sqlite3, os

DB = os.environ.get("DB_PATH", "boutique.db")
conn = sqlite3.connect(DB)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS fournisseurs (
    id INTEGER PRIMARY KEY, nom TEXT, contact TEXT, pays TEXT, note TEXT)''')

# Ne pas dupliquer si déjà présents
if c.execute("SELECT COUNT(*) FROM fournisseurs").fetchone()[0] > 0:
    print("Fournisseurs déjà présents — rien à faire.")
    conn.close()
    exit()

fournisseurs = [
    ("Guangdong Axin Logistics","axinlogistics.com | WeChat: axin_logistics","Chine 🇨🇳","Livraison Afrique 15-25j | Réactivité ≤1h | Taux livraison >95%"),
    ("Shenzhen Fly International","flyinternational.cn | WhatsApp pro","Chine 🇨🇳","Stabilité financière élevée | Idéal commandes B2B | 830K$+ revenus"),
    ("WUHAN BOSA SHIPPING","bosashipping.com | contact@bosashipping.com","Chine 🇨🇳","Commandes volumineuses | Capacité logistique 1.3M$+ | Fret maritime"),
    ("AliExpress / 1688.com","aliexpress.com | 1688.com","Chine 🇨🇳","Sourcing général | Tech accessories | Livraison Bénin 20-35j"),
    ("Chadrack Jack","WhatsApp/WeChat — contact direct","Chine 🇨🇳","Fournisseur tech accessories | Contact établi | Négociation directe"),
    ("DHL Express Bénin","+229 21 30 10 85 | dhl.com/bj-fr","International 🌍","Livraison express porte-à-porte | Suivi temps réel | Aérien prioritaire"),
    ("Bolloré Logistics Cotonou","+229 21 36 83 00 | bollore-logistics.com","International 🌍","Zone Portuaire Cotonou | Fret maritime & aérien | Solutions complètes"),
    ("OMA Group Bénin","+229 21 31 52 88 | benin.omagroup.com","International 🌍","3 Rue du Gouverneur Fourn Cotonou | Logistique import/export"),
    ("IFS — International Freight Services","Cotonou — contact@ifs-benin.com","International 🌍","Fret aérien, maritime, terrestre | Bénin & international | Rapide & sécurisé"),
    ("CEVA Logistics Cotonou","+228 31 21 52 88 | cevalogistics.com","International 🌍","Réseau mondial | Solutions supply chain | Partenaire fiable"),
    ("Laly Express Cotonou","Ganhi, Place de la Poste | Cotonou","Bénin 🇧🇯","Livraison express locale | Colis & courriers | Depuis 2018"),
    ("Express Relais Logistique","DC Services Bénin | 2022","Bénin 🇧🇯","Livraison locale & villes africaines | E-solutions | Colis & documents"),
    ("Africa Cargo Hub","africacargohub.bj","Bénin 🇧🇯","Warehousing + shipping + livraison | End-to-end dropshipping Bénin"),
    ("GROUPE OROS","Cotonou — transit & dédouanement","Bénin 🇧🇯","Transit, dédouanement, livraison porte-à-porte | National & international"),
    ("Grimaldi Lines Cotonou","+229 21 31 67 28 | grimaldi@grimaldi-benin.com","Bénin 🇧🇯","Fret maritime | Ligne Europe-Afrique de l'Ouest"),
    ("eWorldTrade","eworldtrade.com","Plateforme B2B 🌐","Fournisseurs vérifiés | Livraison Bénin | Paiement sécurisé"),
    ("Zendrop","zendrop.com | App Shopify","Plateforme B2B 🌐","Produits stockés en Chine | Livraison mondiale | Compatible Shopify"),
    ("Banggood","banggood.com","Chine/Europe 🌐","Tech & électronique | Livraison Afrique | Prix compétitifs"),
]

c.executemany("INSERT INTO fournisseurs (nom,contact,pays,note) VALUES (?,?,?,?)", fournisseurs)
conn.commit()
print(f"✅ {len(fournisseurs)} fournisseurs intégrés avec succès !")
conn.close()
