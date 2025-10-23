# API Mahakim

API FastAPI simple pour interroger Mahakim avec chiffrement/déchiffrement AES-256-CBC et cache 24h.

## 🚀 Démarrage rapide

```bash
docker-compose up -d
```

L'API sera disponible sur `http://localhost:8000`

## 📡 Endpoints

### 1. Récupérer un dossier (GET /dossier/{juridiction}/{dossier})
```bash
curl http://localhost:8000/dossier/13/202512028569
```

### 2. Récupérer un dossier (POST /dossier)
```bash
curl -X POST http://localhost:8000/dossier \
  -H "Content-Type: application/json" \
  -d '{
    "id_dossier": "202512028569",
    "id_juridiction": "13"
  }'
```

**Les deux endpoints retournent** les 4 endpoints Mahakim déchiffrés :
- `carte` : Informations générales du dossier
- `decisions` : Liste des décisions
- `parties` : Liste des parties
- `expertises` : Liste des expertises judiciaires

**Cache automatique de 24h** - La 2ème requête sera instantanée.

### 2. Mettre à jour les clés de chiffrement (PUT /keys)
```bash
curl -X PUT http://localhost:8000/keys \
  -H "Content-Type: application/json" \
  -d '{
    "key": "qKG6nnv7VXVSA4pDotDyWNx8ca5mKxWkn0eL784GxKQ=",
    "iv": "k3vi7ZFUB8/XSID2AXEwug=="
  }'
```
⚠️ Le cache est vidé automatiquement après la mise à jour des clés.

### 3. Voir les clés actuelles (GET /keys)
```bash
curl http://localhost:8000/keys
```

### 4. Stats du cache (GET /cache/stats)
```bash
curl http://localhost:8000/cache/stats
```
Retourne le nombre total d'entrées en cache, valides et expirées.

### 5. Vider le cache (DELETE /cache)
```bash
curl -X DELETE http://localhost:8000/cache
```

### 6. Health check (GET /health)
```bash
curl http://localhost:8000/health
```

## 📚 Documentation interactive

Une fois l'API lancée :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

## 🔧 Configuration

Les clés de chiffrement peuvent être définies via variables d'environnement dans `docker-compose.yml` :

```yaml
environment:
  - CRYPTO_KEY=qKG6nnv7VXVSA4pDotDyWNx8ca5mKxWkn0eL784GxKQ=
  - CRYPTO_IV=k3vi7ZFUB8/XSID2AXEwug==
```

## 🎯 Fonctionnalités

✅ **Chiffrement AES-256-CBC** des paramètres de requête  
✅ **Déchiffrement automatique** des réponses Mahakim  
✅ **Cache en mémoire** avec TTL de 24h  
✅ **Mise à jour dynamique** des clés sans redémarrage  
✅ **4 endpoints en 1 requête** (carte, décisions, parties, expertises)  
✅ **Gestion d'erreurs** robuste  
✅ **Health checks** pour Docker

## 📝 Exemple de réponse

```json
{
  "source": "api",
  "data": {
    "carte": {
      "idDossierCivil": 13967222,
      "numeroCompletDossier1Instance": "2025/1202/8569",
      "juridiction1Instance": "المحكمة الابتدائية المدنية بالدار البيضاء",
      ...
    },
    "decisions": [...],
    "parties": [...],
    "expertises": [...],
    "timestamp": "2025-10-16T22:44:57.757015"
  }
}
```

## 🧪 Tests

```bash
python test_api.py
```
