import os
import subprocess
import sys

# --- Configuration de l'encodage UTF-8 ---
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding='utf-8')
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

# --- Récupération des identifiants depuis les variables d'environnement ---
user = os.getenv('CAS_USER')
password = os.getenv('CAS_PASSWORD')

if not user or not password:
    print("[ERREUR] Les identifiants ne sont pas définis dans les variables d'environnement.")
    sys.exit(1)

# --- Saisie du nom et prénom ---
print("Nous allons retrouver votre attestation à l'aide de votre nom et de votre prénom.")

nom = input("Entrez le NOM : ").strip().replace(" ", "_")
prenom = input("Entrez le Prénom : ").strip().replace(" ", "_")
chemin_image = f'images/attestations/attestation_{nom}_{prenom}.png'

# --- Vérification de l'existence du fichier ---
while not os.path.exists(chemin_image):
    print(f"[ERREUR] Aucune attestation trouvée pour {nom}_{prenom}.")
    nom = input("Entrez votre NOM : ").strip()
    prenom = input("Entrez votre PRÉNOM : ").strip()
    chemin_image = f'images/attestations/attestation_{nom}_{prenom}.png'

# --- Construction de la commande curl ---
commande_curl = [
    "curl", "-s", "-w", "%{http_code}", "-o", "-",  # -w pour le code HTTP, -o - pour le body
    "-X", "POST",
    "-F", f"image=@{chemin_image}",
    "--cacert", "./CA/certs/ecc.ca.cert.pem",
    "https://localhost:9000/verification"
]

try:
    result = subprocess.run(
        commande_curl,
        check=True,
        text=True,
        capture_output=True
    )

    # --- Extraction du code HTTP et du corps de la réponse ---
    full_output = result.stdout
    http_code = full_output[-3:]
    response_body = full_output[:-3].strip()

    # --- Interprétation du code HTTP ---
    if http_code == "200":
        print("[ATTESTATION VALIDEE] Vérification de l'attestation réussie. Félicitations !")
        sys.exit(0)
    elif http_code == "403":
        print("[ATTESTATION INVALIDE] Attestation invalide.")
    elif http_code == "400":
        print("[ERREUR] Requête invalide : fichier image manquant ou mal formée.")
    elif http_code == "422":
        print("[ERREUR] Image reçue, mais non traitable (données corrompues ?).")
    elif http_code == "500":
        print("[ATTESTATION INVALIDE] Erreur interne du serveur. Attestation invalide.")
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