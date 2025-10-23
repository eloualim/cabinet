#!/usr/bin/env python3
"""
API FastAPI pour Mahakim - Simple et efficace
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import secrets
import json
from datetime import datetime, timedelta
from typing import Dict, Any
import os

app = FastAPI(title="Mahakim API")

# === Cache simple en mémoire ===
cache: Dict[str, Dict[str, Any]] = {}

# === Clés de chiffrement (modifiables dynamiquement) ===
crypto_keys = {
    "key": os.getenv("CRYPTO_KEY", "qKG6nnv7VXVSA4pDotDyWNx8ca5mKxWkn0eL784GxKQ="),
    "iv": os.getenv("CRYPTO_IV", "k3vi7ZFUB8/XSID2AXEwug==")
}

class DossierRequest(BaseModel):
    id_dossier: str
    id_juridiction: str

class KeysUpdate(BaseModel):
    key: str
    iv: str

def encrypt(text: str) -> str:
    """Chiffre un texte avec AES-256-CBC"""
    key = base64.b64decode(crypto_keys["key"])
    iv = base64.b64decode(crypto_keys["iv"])
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(text.encode(), AES.block_size))
    return base64.b64encode(encrypted).decode()

def decrypt(encrypted_b64: str) -> dict:
    """Déchiffre une réponse AES-256-CBC"""
    key = base64.b64decode(crypto_keys["key"])
    iv = base64.b64decode(crypto_keys["iv"])
    encrypted = base64.b64decode(encrypted_b64)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(encrypted), AES.block_size)
    return json.loads(decrypted.decode())

def get_cache(cache_key: str) -> dict | None:
    """Récupère depuis le cache si valide"""
    if cache_key in cache:
        entry = cache[cache_key]
        if datetime.fromisoformat(entry["expires"]) > datetime.now():
            return entry["data"]
        del cache[cache_key]
    return None

def set_cache(cache_key: str, data: dict):
    """Met en cache pour 24h"""
    cache[cache_key] = {
        "data": data,
        "expires": (datetime.now() + timedelta(days=1)).isoformat()
    }

async def fetch_url(url: str, params: dict) -> dict:
    """Fait une requête HTTP et déchiffre la réponse"""
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://www.mahakim.ma/"
    }
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        
        # Essayer de parser le JSON
        try:
            result = response.json()
        except json.JSONDecodeError:
            return {"error": "Réponse non-JSON", "text": response.text[:500]}
        
        # Si la réponse contient des données chiffrées
        if isinstance(result, dict):
            # Essayer avec "data" (Mahakim retourne soit "succes" soit "status")
            encrypted_data = result.get("data")
            if encrypted_data and isinstance(encrypted_data, str):
                try:
                    decrypted = decrypt(encrypted_data)
                    result["data_decrypted"] = decrypted
                    return decrypted
                except Exception as e:
                    result["decrypt_error"] = str(e)
        
        return result

async def process_dossier(juridiction_enc: str, dossier_enc: str, csrf: str) -> dict:
    """Traite un dossier et retourne toutes ses données"""
    base_url = "https://www.mahakim.ma/middleware/api/SuiviDossiers"
    
    # ÉTAPE 1: Récupérer la carte du dossier
    params_carte = {
        "numeroCompletDossier": dossier_enc,
        "idjuridiction": juridiction_enc,
        "csrt": csrf
    }
    
    try:
        carte = await fetch_url(f"{base_url}/CarteDossier", params_carte)
    except Exception as e:
        return {
            "error": "Erreur de récupération",
            "message": f"Impossible de récupérer le dossier: {str(e)}",
            "carte": {}
        }
    
    # Vérifier si le dossier existe et extraire l'ID interne
    if not isinstance(carte, dict) or "error" in carte:
        return {
            "error": "Dossier introuvable",
            "message": "Le numéro de dossier ou la juridiction est invalide",
            "carte": carte if isinstance(carte, dict) else {}
        }
    
    # ÉTAPE 2: Extraire les IDs nécessaires (civil ou pénal)
    # Dossiers civils utilisent "idDossierCivil", pénaux utilisent "id"
    id_dossier_interne = carte.get("idDossierCivil") or carte.get("id")
    
    if not id_dossier_interne:
        return {
            "error": "Dossier introuvable",
            "message": "Impossible d'extraire l'ID du dossier",
            "carte": carte
        }
    
    id_dossier_interne = str(id_dossier_interne)
    type_affaire = carte.get("affaire", "DC")
    
    # Chiffrer les nouveaux paramètres
    id_dossier_enc = encrypt(id_dossier_interne)
    type_affaire_enc = encrypt(type_affaire)
    
    # ÉTAPE 3: Préparer les 3 autres requêtes
    params_decisions = {
        "idDossiers": id_dossier_enc,
        "typeaffaire": type_affaire_enc,
        "csrt": csrf
    }
    
    params_parties = {
        "idDoss": id_dossier_enc,
        "typeaffaire": type_affaire_enc,
        "csrt": csrf
    }
    
    params_expertises = {
        "idDossiers": id_dossier_enc,
        "typeaffaire": type_affaire_enc,
        "csrt": csrf
    }
    
    # Exécuter les 3 autres requêtes
    decisions = await fetch_url(f"{base_url}/ListeDicisions", params_decisions)
    parties = await fetch_url(f"{base_url}/ListeParties", params_parties)
    expertises = await fetch_url(f"{base_url}/ListeExpertisesJudiciaire", params_expertises)
    
    return {
        "carte": carte,
        "decisions": decisions,
        "parties": parties,
        "expertises": expertises,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/dossier/{id_juridiction}/{id_dossier}")
async def get_dossier_get(id_juridiction: str, id_dossier: str):
    """
    Récupère les 4 endpoints Mahakim pour un dossier (GET)
    Cache: 24h
    """
    cache_key = f"{id_juridiction}:{id_dossier}"
    
    # Vérifier le cache
    cached = get_cache(cache_key)
    if cached:
        return {"source": "cache", "data": cached}
    
    # Chiffrer les paramètres
    juridiction_enc = encrypt(id_juridiction)
    dossier_enc = encrypt(id_dossier)
    csrf = secrets.token_hex(16)
    
    base_url = "https://www.mahakim.ma/middleware/api/SuiviDossiers"
    
    try:
        results = await process_dossier(juridiction_enc, dossier_enc, csrf)
        
        # Vérifier si erreur
        if "error" in results:
            return {
                "source": "api",
                "error": results["error"],
                "message": results["message"],
                "data": results.get("carte", {})
            }
        
        # Mettre en cache
        set_cache(cache_key, results)
        
        return {"source": "api", "data": results}
        
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Erreur API Mahakim: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.post("/dossier")
async def get_dossier(req: DossierRequest):
    """
    Récupère les 4 endpoints Mahakim pour un dossier (POST)
    Cache: 24h
    """
    cache_key = f"{req.id_juridiction}:{req.id_dossier}"
    
    # Vérifier le cache
    cached = get_cache(cache_key)
    if cached:
        return {"source": "cache", "data": cached}
    
    # Chiffrer les paramètres
    juridiction_enc = encrypt(req.id_juridiction)
    dossier_enc = encrypt(req.id_dossier)
    csrf = secrets.token_hex(16)
    
    base_url = "https://www.mahakim.ma/middleware/api/SuiviDossiers"
    
    try:
        results = await process_dossier(juridiction_enc, dossier_enc, csrf)
        
        # Vérifier si erreur
        if "error" in results:
            return {
                "source": "api",
                "error": results["error"],
                "message": results["message"],
                "data": results.get("carte", {})
            }
        
        # Mettre en cache
        set_cache(cache_key, results)
        
        return {"source": "api", "data": results}
        
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Erreur API Mahakim: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.put("/keys")
async def update_keys(keys: KeysUpdate):
    """Met à jour les clés de chiffrement dynamiquement"""
    try:
        # Valider les clés
        key = base64.b64decode(keys.key)
        iv = base64.b64decode(keys.iv)
        
        if len(key) != 32:
            raise ValueError("La clé doit faire 32 bytes (256 bits)")
        if len(iv) != 16:
            raise ValueError("L'IV doit faire 16 bytes (128 bits)")
        
        crypto_keys["key"] = keys.key
        crypto_keys["iv"] = keys.iv
        
        # Vider le cache après changement de clés
        cache.clear()
        
        return {"message": "Clés mises à jour avec succès"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Clés invalides: {str(e)}")

@app.get("/keys")
async def get_keys():
    """Récupère les clés actuelles"""
    return crypto_keys

@app.get("/cache/stats")
async def cache_stats():
    """Statistiques du cache"""
    valid = sum(1 for e in cache.values() if datetime.fromisoformat(e["expires"]) > datetime.now())
    return {
        "total": len(cache),
        "valid": valid,
        "expired": len(cache) - valid
    }

@app.delete("/cache")
async def clear_cache():
    """Vide le cache"""
    cache.clear()
    return {"message": "Cache vidé"}

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}
