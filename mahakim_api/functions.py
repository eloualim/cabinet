import base64
import secrets
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from datetime import datetime

# === Paramètres de chiffrement ===
KEY_B64 = "qKG6nnv7VXVSA4pDotDyWNx8ca5mKxWkn0eL784GxKQ="
IV_B64 = "k3vi7ZFUB8/XSID2AXEwug=="

def chiffrer_parametre(texte: str) -> str:
    """
    Chiffre un texte avec AES-256-CBC et retourne le résultat en base64.
    """
    try:
        key = base64.b64decode(KEY_B64)
        iv = base64.b64decode(IV_B64)
        data = texte.encode("utf-8")
        padded_data = pad(data, AES.block_size)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted).decode("utf-8")
    except Exception as e:
        raise Exception(f"Erreur de chiffrement du texte '{texte}': {e}")

# === Lecture des données depuis l'input n8n ===
# Exemple : items[0].json["Juridiction"], items[0].json["NumeroDossier"]
items_out = []
for item in items:
    juridiction = item.get("json", {}).get("Juridiction", "13")
    numero_dossier = item.get("json", {}).get("NumeroDossier", "202512025555")

    juridiction_chiffree = chiffrer_parametre(juridiction)
    numero_chiffre = chiffrer_parametre(numero_dossier)
    token_csrf = secrets.token_hex(16)

    resultat = {
        "JuridictionOriginale": juridiction,
        "JuridictionChiffree": juridiction_chiffree,
        "NumeroDossierOriginal": numero_dossier,
        "NumeroDossierChiffre": numero_chiffre,
        "TokenCSRF": token_csrf,
        "Timestamp": datetime.now().isoformat()
    }

    items_out.append({"json": resultat})

# === Retour correct pour n8n ===
return items_out


"""
Déchiffrement AES-256-CBC pour n8n (Python)
⚠️ À utiliser dans un node "Code" de n8n avec le langage défini sur "Python"
"""

import base64
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from datetime import datetime

# === Paramètres de chiffrement ===
KEY_B64 = "qKG6nnv7VXVSA4pDotDyWNx8ca5mKxWkn0eL784GxKQ="
IV_B64 = "k3vi7ZFUB8/XSID2AXEwug=="

def dechiffrer_reponse(data_chiffree_b64: str) -> str:
    """
    Déchiffre une chaîne AES-256-CBC encodée en base64
    """
    try:
        key = base64.b64decode(KEY_B64)
        iv = base64.b64decode(IV_B64)
        encrypted_data = base64.b64decode(data_chiffree_b64)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_padded = cipher.decrypt(encrypted_data)
        decrypted = unpad(decrypted_padded, AES.block_size)
        return decrypted.decode("utf-8")
    except Exception as e:
        raise Exception(f"Erreur de déchiffrement : {e}")

# === Lecture depuis l'input n8n ===
items_out = []

for item in items:
    data_chiffree = item.get("json", {}).get("data")

    if not data_chiffree:
        raise Exception("Aucune donnée 'data' trouvée dans l'entrée n8n")

    print("🔐 Déchiffrement en cours...")

    # Déchiffrer les données
    donnees_dechiffrees = dechiffrer_reponse(data_chiffree)

    # Déterminer le type de données
    try:
        donnees_finales = json.loads(donnees_dechiffrees)
        type_data = "json"
        print("✅ Données JSON parsées avec succès")
    except json.JSONDecodeError:
        donnees_finales = donnees_dechiffrees
        type_data = "texte"
        print("ℹ️ Données en format texte brut")

    # Créer l’objet de sortie
    resultat = {
        "succes": True,
        "message": item.get("json", {}).get("message"),
        "typeData": type_data,
        "donneesDechiffrees": donnees_finales,
        "timestamp": datetime.now().isoformat()
    }

    items_out.append({"json": resultat})

# === Retourner correctement pour n8n ===
return items_out



url1 = "https://www.mahakim.ma/middleware/api/SuiviDossiers/CarteDossier?numeroCompletDossier=RN97ClZVqfJQfMCtqMl9tw%3D%3D&idjuridiction=3CKKT7LEoNAQyfMlPlWVSw%3D%3D&csrt=1756232039849415424"
url2 = "https://www.mahakim.ma/middleware/api/SuiviDossiers/ListeDicisions?idDossiers=eEu3Zjkovflg1%2Fic4WIrSg%3D%3D&typeaffaire=XOAk5%2BU5QFVfVcTr8bzpYg%3D%3D&csrt=1756232039849415424"
url3 = "https://www.mahakim.ma/middleware/api/SuiviDossiers/ListeParties?idDoss=eEu3Zjkovflg1%2Fic4WIrSg%3D%3D&typeaffaire=XOAk5%2BU5QFVfVcTr8bzpYg%3D%3D&csrt=1756232039849415424"
url4 = "https://www.mahakim.ma/middleware/api/SuiviDossiers/ListeExpertisesJudiciaire?idDossiers=eEu3Zjkovflg1%2Fic4WIrSg%3D%3D&typeaffaire=XOAk5%2BU5QFVfVcTr8bzpYg%3D%3D&csrt=1756232039849415424"
