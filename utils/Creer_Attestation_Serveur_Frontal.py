import os
import subprocess
import sys

# --- Récupérer les identifiants depuis les variables d'environnement ---
user = os.getenv('CAS_USER')
password = os.getenv('CAS_PASSWORD')

if not user or not password:
    print("[ERREUR] Les identifiants ne sont pas définis dans les variables d'environnement.")
    sys.exit(1)

# --- Demander les informations utilisateur ---
nom = input("Entrez le NOM : ").strip().replace(" ", "_")
prenom = input("Entrez le Prénom : ").strip().replace(" ", "_")
intitule_certif = input("Entrez l'intitulé de la certification (Par défaut : SECU TIC) : ").strip().replace(" ", "_")

if not intitule_certif:
    intitule_certif = "SECU TIC"

# --- Construction de la commande curl ---
commande_curl = [
    "curl", "-s", "-w", "%{http_code}", "-o", "-",  # Sortie propre : -s = silencieux, -w = HTTP code
    "-X", "POST",
    "-d", f"nom={nom}",
    "-d", f"prenom={prenom}",
    "-d", f"intitule_certif={intitule_certif}",
    "-d", f"user={user}",
    "-d", f"password={password}",
    "--cacert", "./CA/certs/ecc.ca.cert.pem",
    "https://localhost:9000/creation"
]

# --- Exécution de la commande ---
try:
    result = subprocess.run(
        commande_curl,
        check=True,
        text=True,
        capture_output=True
    )

    full_output = result.stdout
    http_code = full_output[-3:]
    response_body = full_output[:-3].strip()

    if http_code == "201":
        print("[OK] Attestation générée avec succès.")
        sys.exit(0)
    elif http_code == "400":
        print("[ERREUR] Champs requis manquants.")
    elif http_code == "408":
        print("[ERREUR] Timeout lors de la création.")
    elif http_code == "500":
        print("[ERREUR] Erreur serveur lors de la génération.")
    else:
        print(f"[ERREUR] Code HTTP inattendu : {http_code}")

    print("[DÉTAILS] :", response_body)
    sys.exit(1)

except subprocess.CalledProcessError as e:
    print("[ERREUR] La commande curl a échoué.")
    print("[DÉTAILS] :", e.stderr.strip())
    sys.exit(1)

except Exception as e:
    print(f"[ERREUR] Exception inattendue : {e}")
    sys.exit(1)