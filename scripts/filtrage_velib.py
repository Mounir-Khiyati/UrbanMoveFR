import pandas as pd

# 1️⃣ Charger le CSV créé avec pandasUtile.py
df_velib = pd.read_csv("velib_propre.csv")

# 2️⃣ Appliquer les filtres (tout Paris, pas d’arrondissement spécifique)
df_filtre = df_velib[
    (df_velib["numbikesavailable"] >= 1) &   # au moins 1 vélo
    (df_velib["numdocksavailable"] >= 1)     # au moins 1 place libre
]

# 3️⃣ Afficher un aperçu
print(df_filtre.head())
print(f"Nombre de stations après filtrage : {len(df_filtre)}")

# 4️⃣ (optionnel) Sauvegarder dans un nouveau CSV
df_filtre.to_csv("velib_filtre.csv", index=False)
print("✅ Fichier velib_filtre.csv sauvegardé")
