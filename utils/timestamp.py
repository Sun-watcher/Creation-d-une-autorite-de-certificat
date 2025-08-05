import os
import subprocess
import hashlib
import tempfile
import base64

def completer_concatenation(concatenation):
    longueur_cible = 64
    if len(concatenation) >= longueur_cible:
        return concatenation
    return concatenation.ljust(longueur_cible, '*')

def hasher_et_stocker(concatenation):
    # Chemin du dossier de destination
    dossier_destination = os.path.expanduser("Timestamp/timestamp_hash_and_requests")
    os.makedirs(dossier_destination, exist_ok=True)

    # Chemin du fichier de sortie
    fichier_hash = os.path.join(dossier_destination, f"{concatenation}_hash_sha512.bin")

    try:
        # Utilisation d'OpenSSL pour générer le hash
        process = subprocess.run(
            ["openssl", "dgst", "-sha512", "-binary"],
            input=concatenation.encode(),  # Encodage en bytes
            capture_output=True,
            check=True
        )

        # Écrire le hash dans le fichier
        with open(fichier_hash, "wb") as fichier:  # Ouverture en mode binaire
            fichier.write(process.stdout)

        print(f"[OK] Hash SHA-512 généré et stocké dans : {fichier_hash}")
    except subprocess.CalledProcessError as e:
        print(f"[ERREUR] Erreur lors de l'exécution d'OpenSSL : {e}")
    except Exception as e:
        print(f"[ERREUR] Une erreur inattendue s'est produite lors du hashage : {e}")

def preparer_requete_timestamp(fichier_hash):

    # Vérifier si le fichier d'entrée existe
    if not os.path.exists(fichier_hash):
        print(f"[ERREUR] Le fichier {fichier_hash} n'existe pas.")
        return

    # Chemin du fichier de sortie
    fichier_tsq = fichier_hash.replace("_hash_sha512.bin", ".tsq")

    try:
        # Exécuter la commande OpenSSL pour générer le fichier .tsq
        subprocess.run(
            [
                "openssl", "ts", "-query",
                "-data", fichier_hash,
                "-no_nonce", "-sha512", "-cert",
                "-out", fichier_tsq
            ],
            check=True
        )
        print(f"[OK] Fichier de requête de timestamp généré : {fichier_tsq}")
    except subprocess.CalledProcessError as e:
        print(f"[ERREUR] Erreur lors de l'exécution d'OpenSSL : {e}")
    except Exception as e:
        print(f"[ERREUR] Une erreur inattendue s'est produite pendant la préparation de la requête timestamp: {e}")

def envoyer_requete_timestamp(fichier_tsq):

    # Vérifier si le fichier d'entrée existe
    if not os.path.exists(fichier_tsq):
        print(f"[ERREUR] Le fichier {fichier_tsq} n'existe pas.")
        return

    # Chemin du fichier de sortie
    fichier_tsr = fichier_tsq.replace(".tsq", ".tsr")

    try:
        # Exécuter la commande curl pour envoyer le fichier .tsq
        subprocess.run(
            [
                "curl", "-H", "Content-Type: application/timestamp-query",
                "--data-binary", f"@{fichier_tsq}",
                "https://freetsa.org/tsr", "-o", fichier_tsr
            ],
            check=True
        )
        print(f"[OK] Fichier de réponse TSA généré : {fichier_tsr}")
    except subprocess.CalledProcessError as e:
        print(f"[ERREUR] Erreur lors de l'exécution de curl : {e}")
    except Exception as e:
        print(f"[ERREUR] Une erreur inattendue s'est produite durant l'envoi de la requête timestamp: {e}")

def verifier_requete_timestamp(concatenation_complete, contenu_tsr,
                                fichier_cacert="Timestamp/freetsa_certs/cacert.pem",
                                fichier_tsa_crt="Timestamp/freetsa_certs/tsa.crt"):

    print("[INFO] Vérification du timestamp...")

    try:

        # Décoder le contenu binaire reçu
        contenu_tsr = base64.b64decode(contenu_tsr)

        # 1. Générer le hash SHA-512 de la concaténation (doit être identique à celui utilisé pour créer le .tsq initial)
        digest_path = None
        with tempfile.NamedTemporaryFile(delete=False, suffix="_hash_sha512.bin") as temp_hash:
            digest = hashlib.sha512(concatenation_complete.encode('utf-8')).digest()
            temp_hash.write(digest)
            digest_path = temp_hash.name

        # 2. Recréer un fichier .tsq temporaire à partir du hash
        tsq_path = digest_path.replace("_hash_sha512.bin", ".tsq")
        subprocess.run([
            "openssl", "ts", "-query",
            "-data", digest_path,
            "-no_nonce", "-sha512", "-cert",
            "-out", tsq_path
        ], check=True)

        # 3. Recréer un fichier .tsr temporaire à partir du contenu binaire reçu
        tsr_path = digest_path.replace("_hash_sha512.bin", ".tsr")
        with open(tsr_path, "wb") as f:
            f.write(contenu_tsr)

        # 4. Vérification via OpenSSL
        subprocess.run([
            "openssl", "ts", "-verify",
            "-in", tsr_path,
            "-queryfile", tsq_path,
            "-CAfile", fichier_cacert,
            "-untrusted", fichier_tsa_crt
        ], check=True)

        print("[✅] Vérification du timestamp réussie.")
        return True

    except subprocess.CalledProcessError as e:
        print(f"[❌] Erreur OpenSSL : {e}")
        return False
    except Exception as e:
        print(f"[❌] Erreur inattendue pendant la vérification du timestamp : {e}")
        return False
    finally:
        # Nettoyage des fichiers temporaires si besoin
        for path in [digest_path, tsq_path, tsr_path]:
            if path and os.path.exists(path):
                os.remove(path)

def creer_fichiers_timestamp(concatenation):

    try:
        # Étape 1 : Compléter la concaténation
        concatenation_completee = completer_concatenation(concatenation)

        # Étape 2 : Générer et stocker le hash
        hasher_et_stocker(concatenation_completee)
        fichier_hash = os.path.expanduser(
            f"Timestamp/timestamp_hash_and_requests/{concatenation_completee}_hash_sha512.bin"
        )

        # Étape 3 : Préparer la requête de timestamp
        preparer_requete_timestamp(fichier_hash)
        fichier_tsq = fichier_hash.replace("_hash_sha512.bin", ".tsq")

        # Étape 4 : Envoyer la requête de timestamp
        envoyer_requete_timestamp(fichier_tsq)

        # Étape 5 : Vérifier la requête de timestamp
        fichier_tsr = fichier_tsq.replace(".tsq", ".tsr")

        print("[OK] Fichiers de timestamp créés avec succès.")

        return concatenation_completee, fichier_tsr
    except Exception as e:
        print(f"[ERREUR] Une erreur s'est produite lors de la création des fichiers de timestamp : {e}")

