import urllib.request
import urllib.parse
import re
import threading
from bottle import route, run, request, response, HTTPError
from utils.generation_graphique import generer_certificat, extraire_QRcode
from utils.crypto import *
from utils.timestamp import *
from utils.steganographie import *

SIGNATURE_DIR_PATH = "./signatures/"
ATTESTATION_DIR_PATH = "./images/attestations/"
SIGNATURE_TEMP_FILE = "./signatures/signature_temp.sig"
IMAGE_TEMP_FILE = "./images/attestations/attestation_a_verifier.png"
TIMESTAMP_LENGTH = 7328
HIDDEN_MESSAGE_LENGTH = 7328 + 64

def authentifier_utilisateur(user, password):
    """Authentifie l'utilisateur auprès du serveur CAS et retourne True si réussi."""
    re_token = re.compile(rb'name="token" value="([^"]+)"')
    try:
        # Récupérer le token CSRF
        request_cas = urllib.request.Request('https://cas.unilim.fr')
        rep = urllib.request.urlopen(request_cas)
        contenu = rep.read()
        resultat = re_token.search(contenu)
        if not resultat:
            print("[ERREUR] Impossible de récupérer le token CSRF.")
            return False
        token = resultat.group(1)

        # Authentification avec les identifiants et le token
        cookieProcessor = urllib.request.HTTPCookieProcessor()
        opener = urllib.request.build_opener(cookieProcessor)
        data = urllib.parse.urlencode({'user': user, 'password': password, 'token': token})
        request_auth = urllib.request.Request('https://cas.unilim.fr', bytes(data, encoding='ascii'))
        opener.open(request_auth)

        # Vérifier si le cookie d'authentification est présent
        cookies = [c for c in cookieProcessor.cookiejar if c.name == 'lemonldap']
        if cookies:
            print("[INFO] Authentification réussie.")
            return True
        else:
            print("[ERREUR] Authentification échouée.")
            return False
    except Exception as e:
        print(f"[ERREUR] Une erreur s'est produite lors de l'authentification : {e}")
        return False

@route('/connexion', method='POST')
def connexion():
    user = request.forms.get('user')
    password = request.forms.get('password')

    if not user or not password:
        response.status = 400
        return "[ERREUR] Les champs 'user' et 'password' sont obligatoires."

    if authentifier_utilisateur(user, password):
        response.status = 200
        return "[OK] Authentification réussie."
    else:
        response.status = 401
        return "[ERREUR] Authentification échouée."

@route('/creation', method='POST')
def creation_attestation():
    contenu_nom = request.forms.get('nom')
    contenu_prenom = request.forms.get('prenom')
    contenu_intitulé_certification = request.forms.get('intitule_certif')

    print("[INFO] Début de la création de l'attestation.")
    print(f"[INFO] Nom : {contenu_nom}, Prénom : {contenu_prenom}, Certification : {contenu_intitulé_certification}")

    # --- Vérification des champs requis ---
    if not contenu_nom or not contenu_prenom or not contenu_intitulé_certification:
        response.status = 400
        response.set_header('Content-Type', 'text/plain')
        response.body = "[ERREUR] Tous les champs (nom, prénom, certification) sont obligatoires."
        return response

    # --- Concaténation des données ---
    concatenation = contenu_nom + contenu_prenom + contenu_intitulé_certification
    print("[INFO] Données concaténées avec succès.")

    try:
        # --- Création des fichiers de timestamp avec timeout ---
        print("[INFO] Création des fichiers de timestamp...")

        def creer_fichiers_timestamp_avec_timeout(concatenation, timeout=10):
            result = {}

            def target():
                try:
                    result['data'] = creer_fichiers_timestamp(concatenation)
                except Exception as e:
                    result['error'] = e

            thread = threading.Thread(target=target)
            thread.start()
            thread.join(timeout)

            if thread.is_alive():
                raise TimeoutError("Timeout lors de la création des fichiers de timestamp.")
            if 'error' in result:
                raise result['error']
            return result['data']

        concatenation_completee, timestamp = creer_fichiers_timestamp_avec_timeout(concatenation, timeout=10)

        with open(timestamp, 'rb') as fichier:
            timestamp_readable = base64.b64encode(fichier.read()).decode('utf-8')

        print("[OK] Fichiers de timestamp créés.")

        # --- Signature des données ---
        print("[INFO] Signature des données...")
        nom_fichier = f"{SIGNATURE_DIR_PATH}{contenu_nom}_{contenu_prenom}"
        signer_RSA(concatenation, nom_fichier)
        convert_base64(nom_fichier + ".sig")
        signature = lire_fichier(nom_fichier + ".sig.b64")
        print("[OK] Données signées avec succès.")

        # --- Génération du certificat ---
        print("[INFO] Génération du certificat...")
        destinataire = f"{contenu_nom}_{contenu_prenom}"
        generer_certificat(destinataire, signature, contenu_intitulé_certification)

        chemin_attestation = f"{ATTESTATION_DIR_PATH}attestation_{contenu_nom}_{contenu_prenom}.png"
        concatenation_et_timestamp = concatenation_completee + timestamp_readable
        print(f"[INFO] Données à cacher : {concatenation_et_timestamp}")

        mon_image = Image.open(chemin_attestation)
        cacher(mon_image, concatenation_et_timestamp)
        mon_image.save(chemin_attestation)
        print("[OK] Certificat généré avec succès.")

        response.status = 201  # Code HTTP pour "Created"
        response.set_header('Content-Type', 'text/plain')
        response.body = "[OK] Certificat généré avec succès."
        return response

    except TimeoutError as e:
        print(f"[ERREUR] {e}")
        response.status = 408  # Request Timeout
        response.set_header('Content-Type', 'text/plain')
        response.body = f"[ERREUR] {e}"
        return response

    except Exception as e:
        print(f"[ERREUR] Une erreur s'est produite : {e}")
        response.status = 500
        response.set_header('Content-Type', 'text/plain')
        response.body = f"[ERREUR] Une erreur s'est produite lors de la création de l'attestation : {e}"
        return response

@route('/verification', method='POST')
def vérification_attestation():
    # Sauvegarde l'image
    contenu_image = request.files.get('image')
    if not contenu_image:
        response.status = 400  # Code d'erreur pour requête invalide
        response.body = "[ERREUR] Aucun fichier image fourni."
        return response

    try:
        contenu_image.save(IMAGE_TEMP_FILE, overwrite=True)
    except Exception as e:
        print(f"[ERREUR] Impossible de sauvegarder l'image : {e}")
        response.status = 500  # Code d'erreur pour erreur serveur
        response.body = "[ERREUR] Impossible de sauvegarder l'image."
        return response

    # Vérification de la stéganographie
    try:
        image = Image.open(IMAGE_TEMP_FILE)
        message_recupere = recuperer(image, HIDDEN_MESSAGE_LENGTH)
    except Exception as e:
        print(f"[ERREUR] Une erreur s'est produite lors de la récupération du message : {e}")
        response.status = 422  # Code d'erreur pour données non traitables
        response.body = "[ERREUR] Une erreur s'est produite lors de la récupération du message."
        return response

    partie1 = message_recupere[:64]
    partie2 = message_recupere[64:64 + 7328]

    print(f"[INFO] Première partie du message : {partie1}")
    print(f"[INFO] Deuxième partie du message : {partie2}")

    # Vérification du timestamp
    try:
        verification_timestamp = verifier_requete_timestamp(partie1, partie2)
    except Exception as e:
        print(f"[ERREUR] Une erreur s'est produite lors de la vérification du timestamp : {e}")
        response.status = 500  # Code d'erreur pour erreur serveur
        response.body = "[ERREUR] Une erreur s'est produite lors de la vérification du timestamp."
        return response

    # Vérification de la signature
    try:
        message = partie1.replace("*", "")
        signature = extraire_QRcode(IMAGE_TEMP_FILE)
        decode_base64_vers_binaire(signature, SIGNATURE_TEMP_FILE)
        verification_signature = verifier_signature(SIGNATURE_TEMP_FILE, message)
    except Exception as e:
        print(f"[ERREUR] Une erreur s'est produite lors de la vérification de la signature : {e}")
        response.status = 500  # Code d'erreur pour erreur serveur
        response.body = "[ERREUR] Une erreur s'est produite lors de la vérification de la signature."
        return response

    # Suppression des fichiers temporaires
    try:
        os.remove(SIGNATURE_TEMP_FILE)
        os.remove(IMAGE_TEMP_FILE)
    except Exception as e:
        print(f"[ERREUR] Impossible de supprimer les fichiers temporaires : {e}")
        response.status = 500  # Code d'erreur pour erreur serveur
        response.body = "[ERREUR] Impossible de supprimer les fichiers temporaires."
        return response

    # Retourne la réponse de la vérification
    response.set_header('Content-type', 'text/plain')

    if verification_signature and verification_timestamp:
        response.status = 200  # Succès
        response.body = "[OK] Vérification réussie."
    else:
        response.status = 403  # Code d'erreur pour accès interdit
        response.body = "[ERREUR] L'attestation est fausse."

    return response
   
@route('/fond', method='GET')
def récupérer_fond():
    response.set_header('Content-type', 'image/png')
    
    # Recupere les données
    contenu_nom = request.query.get('nom')
    contenu_prenom = request.query.get('prenom')

    nom_fichier = f'{ATTESTATION_DIR_PATH}attestation_{contenu_nom}_{contenu_prenom}.png'
    
    if not os.path.exists(nom_fichier):
        return HTTPError(404, f"Fichier {nom_fichier} non trouvé.")

    # Envoie l'attestation
    with open(nom_fichier, 'rb') as descripteur_fichier:
        contenu_fichier = descripteur_fichier.read()
    
    return contenu_fichier




run(host='0.0.0.0', port=8080, debug=True)