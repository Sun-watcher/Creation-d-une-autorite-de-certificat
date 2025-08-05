import subprocess, os, base64, tempfile

RSA_CLE_PRIVEE_SERVEUR = "./CA/private/ecc.serveur.key.pem"
RSA_CLE_PUBLIQUE_SERVEUR = "./CA/private/ecc.serveur.pub.pem"
SIGNATURE_OUT_PATH = "./signatures/"


def sha256(message):
    commande = f'echo -n "{message}" | openssl dgst -sha256 | awk \'{{print $2}}\''

    try:
        result = subprocess.run(commande, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"[ERREUR] Lors du calcul du hash SHA-256 : {e.stderr.decode() if e.stderr else str(e)}")
        return None
    except Exception as e:
        print(f"[ERREUR] Erreur inattendue lors du calcul du hash SHA-256 : {str(e)}")
        return None


def signer_RSA(message, destinataire=f"{SIGNATURE_OUT_PATH}Anonyme"):
    commande = f"echo {message} | openssl dgst -sha256 -sign {RSA_CLE_PRIVEE_SERVEUR} -out {destinataire}.sig"
    try:
        subprocess.run(commande, capture_output=True, shell=True, check=True)
        print(f"Signature générée avec succès : {destinataire}.sig")
    except subprocess.CalledProcessError as e:
        print(f"[ERREUR] Lors de la signature RSA : {e.stderr.decode() if e.stderr else str(e)}")
        print(f"Le fichier de signature était censé être {destinataire}.")
        return None
    except Exception as e:
        print(f"[ERREUR] Erreur inattendue lors de la signature RSA : {str(e)}")
        return None

def verifier_signature(signature, message):
    commande = f"echo '{message}' | openssl dgst -sha256 -verify {RSA_CLE_PUBLIQUE_SERVEUR} -signature {signature}"
    try:
        subprocess.run(commande, capture_output=True, check=True, text=True, shell=True)
        print("Vérification réussie")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERREUR] Erreur de vérification : {e.stderr}")
        return False

def convert_base64(nom_fichier):
    if not os.path.exists(nom_fichier):
        print(f"[ERREUR] Le fichier '{nom_fichier}' n'existe pas.")
        return None

    sortie = f"{nom_fichier}.b64"
    commande = f"base64 {nom_fichier} > {sortie}"

    try:
        subprocess.run(commande, shell=True, check=True, capture_output=True)
        print(f"Conversion en base64 réussie : {sortie}")
        return sortie
    except subprocess.CalledProcessError as e:
        print(f"[ERREUR] Erreur pendant la conversion base64 : {e.stderr.decode() if e.stderr else str(e)}")
        return None
    except Exception as e:
        print(f"[ERREUR] Erreur inattendue pendant la conversion base64 : {e}")
        return None


def lire_fichier(nom_fichier):
    try:
        with open(nom_fichier, "rb") as f:
            contenu = f.read()
        print(f"Contenu lu depuis {nom_fichier}")
        return contenu
    except FileNotFoundError:
        print(f"[ERREUR] Fichier introuvable : {nom_fichier}")
        return None
    except Exception as e:
        print(f"[ERREUR] Erreur lors de la lecture du fichier {nom_fichier} : {e}")
        return None

def decode_base64_vers_binaire(nom_b64, nom_sortie):
    try:
        binaire = base64.b64decode(nom_b64)

        with open(nom_sortie, "wb") as f_out:
            f_out.write(binaire)
        print(f"[OK] Fichier {nom_b64} décodé dans {nom_sortie}")
    except Exception as e:
        print(f"[ERREUR] {e}")