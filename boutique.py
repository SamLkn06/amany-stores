import re
import sqlite3

class BoutiqueBenin:
    
    def __init__(self):
        self.produits = ["Tripod", "Microphone", "Ring Light", "Gimbal"]
        self.prix = [15000, 25000, 18000, 45000]
        self.creer_base_donnees()
    
    def creer_base_donnees(self):
        conn = sqlite3.connect("boutique.db")
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY,
                produit TEXT,
                montant INTEGER,
                telephone TEXT,
                date TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def valider_telephone(self, numero):
        numero = numero.replace(" ", "")
        pattern = r'^(\+229|00229)?01[0-9]{8}$'
        return bool(re.match(pattern, numero))
    
    def afficher_catalogue(self):
        print("\n--- Catalogue Tech Shop Bénin ---")
        for i in range(len(self.produits)):
            print(f"{i+1}. {self.produits[i]} → {self.prix[i]} FCFA")
    
    def faire_vente(self):
        telephone = input("\nNuméro client : ")
        if not self.valider_telephone(telephone):
            print("❌ Numéro invalide !")
            return
        produit = input("Produit : ")
        if produit.title() in self.produits:
            index = self.produits.index(produit.title())
            montant = self.prix[index]
            conn = sqlite3.connect("boutique.db")
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ventes (produit, montant, telephone, date)
                VALUES (?, ?, ?, datetime('now'))
            ''', (produit.title(), montant, telephone))
            conn.commit()
            conn.close()
            print(f"✅ Vente confirmée ! {produit.title()} → {montant} FCFA")
        else:
            print("❌ Produit non trouvé !")
    
    def afficher_historique(self):
        conn = sqlite3.connect("boutique.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ventes")
        ventes = cursor.fetchall()
        conn.close()
        print("\n--- Historique des ventes ---")
        if not ventes:
            print("Aucune vente enregistrée.")
        for v in ventes:
            print(f"#{v[0]} | {v[1]} | {v[2]} FCFA | {v[3]} | {v[4]}")
    
    def menu(self):
        while True:
            print("\n=============================")
            print("   AMANY STORES - COTONOU")
            print("=============================")
            print("1 - Voir le catalogue")
            print("2 - Faire une vente")
            print("3 - Voir l'historique")
            print("4 - Quitter")
            choix = input("\nVotre choix : ")
            
            if choix == "1":
                self.afficher_catalogue()
            elif choix == "2":
                self.faire_vente()
            elif choix == "3":
                self.afficher_historique()
            elif choix == "4":
                print("\nAu revoir ! 👋")
                break
            else:
                print("❌ Choix invalide !")

# Lancement
boutique = BoutiqueBenin()
boutique.menu()