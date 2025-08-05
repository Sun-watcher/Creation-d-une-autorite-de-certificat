Vous trouverez dans le fichier README.md l'architecture des fichiers présents dans le dossier CA. Parmi eux, le certificat racine de l'AC, ses fichiers de configuration et le certificat de l'application généré par l'AC.

LE MOT DE PASSE D'ACCES A LA CLE PRIVEE DE L'AC EST [NONE], IL EST DONC INEXISTANT POUR PLUS DE SIMPLICITE.

Nous n'avons pas de script pour les requêtes curl, vous pourrez les retrouver très simplement dans utils/Creer_Attestation_ServeurFrontal.py, utils/Verifier_Attestation_Serveur_Frontal.py et Authentification_CAS.py, sous la forme de commandes utilisées par subprocess.

Enfin, vous pourrez trouver dans le dossier commandes/ deux fichiers textes dans lesquels nous avons notés les commandes, majoritairement openssl, que nous utilisées pour générer les fichiers relatifs à l'AC ainsi qu'à l'horodatage (ces dernières étant toujours utilisées à l'intérieur du programme).

------------- TESTS ------------

VOUS TROUVEREZ DEUX ATTESTATIONS A TESTER :

--------------------------------

ATTESTATION VALIDE : 

NOM : BOUTON
Prenom : Baptiste

--------------------------------

ATTESTATION INVALIDE (Non horodatée, entre autres)

NOM : sun
Prenom : sun

--------------------------------

N'HESITEZ PAS A CREER VOTRE PROPRE ATTESTATION AFIN DE VERIFIER PAR VOUS-MEME LE BON FONCTIONNEMENT DE CELLES-CI. 
A NOTER : LES ESPACES SONT DETECTES ET REMPLACES PAR DES "_" LORS DES INPUTS. 

Antoine DE LAVOISIER ==> Antoine DE_LAVOISIER ==> attestation.DE_LAVOISIER_Antoine.png. 

POUR VERIFIER : 

NOM : DE LAVOISIER (sans "_", il sera ajouté !)
Prenom : Antoine

