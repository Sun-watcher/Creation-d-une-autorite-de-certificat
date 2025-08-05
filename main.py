import os
import subprocess
import time
import socket
from getpass import getpass 

def verifier_serveur_web(host="127.0.0.1", port=8080, timeout=5):
    """Vérifie si le serveur Web est en écoute sur le port spécifié."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                print("[INFO] Le serveur Web est en écoute sur le port 8080.")
                return True
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(1)
    print("[ERREUR] Le serveur Web n'est pas en écoute sur le port 8080.")
    return False

def lancer_serveur_web():
    print("[INFO] Lancement du serveur Web...")
    try:
        # Lancer WebServer.py
        serveur_web = subprocess.Popen(["python3", "web_server.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if verifier_serveur_web():
            print("[OK] Serveur Web lancé.")
            return serveur_web
        else:
            serveur_web.terminate()
            print("[ERREUR] Impossible de vérifier que le serveur Web est en écoute.")
            return None
    except Exception as e:
        print(f"[ERREUR] Impossible de lancer le serveur Web : {e}")
        return None

def lancer_serveur_frontal():
    print("[INFO] Lancement du serveur frontal avec socat...")
    try:
        # Obtenir le chemin du répertoire courant
        chemin_log = os.path.join(os.getcwd(), "socat_error.log")

        # Ouvrir le fichier log en mode écriture
        with open(chemin_log, "w") as log_file:
            # Lancer la commande socat
            serveur_frontal = subprocess.Popen([
                "socat",
                "openssl-listen:9000,fork,cert=./CA/servBundle/bundle_serveur.pem,cafile=./CA/certs/ecc.ca.cert.pem,verify=0",
                "tcp:127.0.0.1:8080"
            ], stdout=subprocess.PIPE, stderr=log_file)
            time.sleep(1)  # Attendre que le serveur frontal démarre
            print("[OK] Serveur frontal lancé.")
            return serveur_frontal
    except Exception as e:
        print(f"[ERREUR] Impossible de lancer le serveur frontal : {e}")
        return None

def lancer_creation_attestation(user, password):
    print("[INFO] Lancement du script de création d'attestation...")
    try:
        # Passer les identifiants en tant que variables d'environnement
        env = os.environ.copy()
        env["CAS_USER"] = user
        env["CAS_PASSWORD"] = password

        # Lancer Creer_Attestation_Serveur_Frontal.py avec les identifiants
        result = subprocess.run(["python3", "utils/Creer_Attestation_Serveur_Frontal.py"], check=True, env=env)
        if result.returncode != 0:
            print("[ERREUR] La création de l'attestation a échoué.")
            return
    except subprocess.CalledProcessError as e:
        print(f"[ERREUR] Erreur lors de l'exécution du script de création d'attestation : {e}")
    except Exception as e:
        print(f"[ERREUR] Une erreur inattendue s'est produite : {e}")

def lancer_verification_attestation(user, password):
    print("[INFO] Lancement du script de vérification d'attestation...")
    try:
        # Passer les identifiants en tant que variables d'environnement
        env = os.environ.copy()
        env["CAS_USER"] = user
        env["CAS_PASSWORD"] = password

        # Lancer Verifier_Attestation_Serveur_Frontal.py avec les identifiants
        result = subprocess.run(["python3", "utils/Verifier_Attestation_Serveur_Frontal.py"], check=True, env=env)
        if result.returncode != 0:
            print("[ERREUR] La vérification de l'attestation a échoué.")
            return
    except subprocess.CalledProcessError as e:
        print(f"[ERREUR] Erreur lors de l'exécution du script de création d'attestation : {e}")
    except Exception as e:
        print(f"[ERREUR] Une erreur inattendue s'est produite : {e}")

def verification_des_identifiants(user, password):
    print("[INFO] Vérification des identifiants...")
    try:
        # Passer les identifiants en tant que variables d'environnement
        env = os.environ.copy()
        env["CAS_USER"] = user
        env["CAS_PASSWORD"] = password

        # Lancer le script d'authentification
        result = subprocess.run(["python3", "utils/Authentification_CAS.py"], check=True, env=env)
        if result.returncode != 0:
            print("[ERREUR] Authentification échouée.")
            return False
        print("[OK] Authentification réussie.")
        return True
    except subprocess.CalledProcessError as e:
        return False
    except Exception as e:
        print(f"[ERREUR] Une erreur inattendue s'est produite : {e}")
        return False


def main():
    # Étape 1 : Lancer le serveur Web
    serveur_web = lancer_serveur_web()
    if not serveur_web:
        return

    # Étape 2 : Lancer le serveur frontal
    serveur_frontal = lancer_serveur_frontal()
    if not serveur_frontal:
        serveur_web.terminate()
        return

    # Demander les identifiants à l'utilisateur jusqu'à ce qu'ils soient corrects
    while True:
        user = input("Veuillez entrer votre identifiant : ")
        password = getpass("Veuillez entrer votre mot de passe : ")

        # Vérification des identifiants
        if verification_des_identifiants(user, password):
            break
        else:
            print("[ERREUR] Echec de la connexion au serveur CAS. Essayez de vérifier vos identifiants.")

    # Étape 3 : Choix de l'utilisateur
    while True:
        try:
            choix = int(input("Souhaitez-vous créer une attestation [1] ou vérifier une attestation [2] ? "))
            if choix == 1:
                print("[INFO] Création d'attestation sélectionnée.")
                lancer_creation_attestation(user, password)
                break
            elif choix == 2:
                print("[INFO] Vérification d'attestation sélectionnée.")
                lancer_verification_attestation(user, password)
                break
            else:
                print("[ERREUR] Choix invalide. Veuillez sélectionner 1 ou 2.")
        except ValueError:
            print("[ERREUR] Entrée invalide. Veuillez entrer un nombre (1 ou 2).")

    print("[INFO] Merci d'avoir utilisé le service de création et de vérification d'attestation.")

if __name__ == "__main__":
    main()