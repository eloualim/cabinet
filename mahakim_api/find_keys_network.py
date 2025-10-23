#!/usr/bin/env python3
"""
Extraction des clés Mahakim via interception du trafic réseau
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import json
import re

opts = Options()
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
opts.add_argument('--headless')
opts.add_argument(f'--user-data-dir=/tmp/chrome_mahakim_{int(time.time())}')

# Activer la capture des logs réseau
opts.set_capability('goog:loggingPrefs', {'performance': 'ALL', 'browser': 'ALL'})

driver = webdriver.Chrome(options=opts)

print("🌐 Chargement de Mahakim...")
driver.get('https://www.mahakim.ma/#/suivi/dossier-suivi')

print("⏳ Attente 15 secondes...")
time.sleep(15)

print("🔍 Analyse des logs de performance...")

# Récupérer tous les logs
logs = driver.get_log('performance')

# Chercher les fichiers JS chargés
js_urls = set()
for entry in logs:
    try:
        log = json.loads(entry['message'])
        message = log.get('message', {})
        method = message.get('method', '')
        
        if method == 'Network.responseReceived':
            params = message.get('params', {})
            response = params.get('response', {})
            url = response.get('url', '')
            mime_type = response.get('mimeType', '')
            
            if 'javascript' in mime_type and 'mahakim.ma' in url:
                js_urls.add(url)
    except:
        pass

print(f"\n📦 {len(js_urls)} fichiers JS trouvés")

# Télécharger et analyser chaque fichier JS
import requests

key_found = None
iv_found = None

for url in js_urls:
    print(f"\n🔎 Analyse: {url.split('/')[-1][:50]}")
    
    try:
        r = requests.get(url, timeout=10)
        content = r.text
        
        # Chercher les patterns de clés directement
        # Pattern 1: Chercher des strings base64 de 44 chars (KEY)
        key_pattern = r'"([A-Za-z0-9+/]{43}=)"'
        keys = re.findall(key_pattern, content)
        
        # Pattern 2: Chercher des strings base64 de 24 chars (IV)
        iv_pattern = r'"([A-Za-z0-9+/]{22}==)"'
        ivs = re.findall(iv_pattern, content)
        
        # Valider chaque KEY trouvée
        if keys and not key_found:
            for k in keys:
                try:
                    import base64
                    decoded = base64.b64decode(k)
                    if len(decoded) == 32:  # 256 bits
                        print(f"  ✅ KEY candidate trouvée: {k}")
                        key_found = k
                        break
                except:
                    pass
        
        # Valider chaque IV trouvé
        if ivs and not iv_found:
            for i in ivs:
                try:
                    decoded = base64.b64decode(i)
                    if len(decoded) == 16:  # 128 bits
                        print(f"  ✅ IV candidate trouvé: {i}")
                        iv_found = i
                        break
                except:
                    pass
        
        if key_found and iv_found:
            break
            
    except Exception as e:
        print(f"  ❌ Erreur: {e}")

driver.quit()

print("\n" + "="*60)
print("📊 RÉSULTATS FINAUX")
print("="*60)

if key_found:
    print(f"✅ KEY: {key_found}")
else:
    print("❌ KEY non trouvée")

if iv_found:
    print(f"✅ IV: {iv_found}")
else:
    print("❌ IV non trouvé")

# Test de validation avec les valeurs connues
if key_found == "qKG6nnv7VXVSA4pDotDyWNx8ca5mKxWkn0eL784GxKQ=":
    print("\n🎉 KEY VALIDÉE - Correspond à la clé connue!")

if iv_found == "k3vi7ZFUB8/XSID2AXEwug==":
    print("🎉 IV VALIDÉ - Correspond à l'IV connu!")
