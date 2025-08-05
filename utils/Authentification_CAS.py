import os
import subprocess
import sys
import json

# Récupérer les identifiants depuis les variables d'environnement
user = os.getenv('CAS_USER')
password = os.getenv('CAS_PASSWORD')

# Effacer les variables d'environnement pour la sécurité
os.environ.pop('CAS_USER', None)
os.environ.pop('CAS_PASSWORD', None)

if not user or not password:
    print("[ERREUR] Les champs 'user' et 'password' sont obligatoires.")
    sys.exit(1)

# Ajouter l’option -w pour récupérer le code HTTP
commande_curl = [
    "curl", "-s", "-o", "-", "-w", "%{http_code}",  # -s = silencieux, -o - = stdout, -w = status
    "-X", "POST",
    "-d", f"user={user}",
    "-d", f"password={password}",
    "--cacert", "./CA/certs/ecc.ca.cert.pem",
    "https://localhost:9000/connexion",
]

try:
    # Exécute la commande et récupère tout en stdout
    result = subprocess.run(
        commande_curl,
        check=True,
        text=True,
        capture_output=True
    )

    # Séparer le corps de la réponse du code HTTP (dernier mot)
    full_output = result.stdout
    http_code = full_output[-3:]
    response_body = full_output[:-3].strip()

    if http_code == "200":
        sys.exit(0)
    else:
        print("[ERREUR] Authentification échouée.")
        sys.exit(1)

except subprocess.CalledProcessError as e:
    print("[ERREUR] La commande a échoué.")
    print("[DÉTAILS] :", e.stderr)
    sys.exit(1)

except Exception as e:
    print(f"[ERREUR] Une exception inattendue s'est produite : {e}")
    sys.exit(1)
