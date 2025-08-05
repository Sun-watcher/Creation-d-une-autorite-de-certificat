import subprocess, qrcode, zbarlight, os
from PIL import Image, UnidentifiedImageError

IMAGE_PATH = "images/"
COMBINAISONS_PATH = IMAGE_PATH + "combinaison/"
ATTESTATIONS_PATH = IMAGE_PATH + "attestations/"
QRCODE_PATH = IMAGE_PATH + "qrcode/"
TEXTE_PATH = IMAGE_PATH + "texte/"

def generer_texte(destinataire="Anonyme", intitule="Attestation de réussite"):
    try:
        chemin_texte = f"{TEXTE_PATH}texte_{destinataire}.png"

        # Texte formaté avec retour à la ligne manuel + caption (auto wrap)
        texte = f"Attestation de réussite\n\nDélivrée à : {destinataire}\n\n{intitule}"

        # Commande avec spécification de la police et encodage UTF-8
        commande = [
            "convert",
            "-size", "1000x600",
            "-background", "transparent",
            "-fill", "black",
            "-gravity", "center",
            "-pointsize", "48",
            "-font", "DejaVu-Sans",  # Police compatible avec les accents
            f"caption:{texte}",
            chemin_texte
        ]

        subprocess.run(commande, check=True)
        print(f"[OK] Image texte générée avec succès : {chemin_texte}")

    except subprocess.CalledProcessError as e:
        print(f"[ERREUR] Lors de la génération du texte : {e}")


def generer_QRcode(destinataire="Anonyme", signature="https://p-fb.net/"):
    try:
        # Creation du QRcode
        nom_fichier = f"qrcode_{destinataire}.png"
        qr = qrcode.make(signature)
        qr.save(QRCODE_PATH + nom_fichier, scale=2)
        print("Génération du QRcode réussie")

        # Redimensionner le QRcode
        qr_image = Image.open(f"{QRCODE_PATH}qrcode_{destinataire}.png")
        qr_image = qr_image.resize((85, 85))
        qr_image.save(f"{QRCODE_PATH}qrcode_{destinataire}.png")
        print("QR code redimensionné avec succès")
    except Exception as e:
        print(f"[ERREUR] Lors de la génération/redimension du QRcode : {e}")

def combinaison_images(destinataire="Anonyme"):
    chemin_texte = f'"{TEXTE_PATH}texte_{destinataire}.png"'
    chemin_fond = f'"{IMAGE_PATH}fond_attestation.png"'
    chemin_combinaison = f'"{COMBINAISONS_PATH}combinaison_{destinataire}.png"'
    chemin_qrcode = f'"{QRCODE_PATH}qrcode_{destinataire}.png"'
    chemin_attestation = f'"{ATTESTATIONS_PATH}attestation_{destinataire}.png"'

    commande_combinaison_1 = f"composite -gravity center {chemin_texte} {chemin_fond} {chemin_combinaison}"
    commande_combinaison_2 = f"composite -geometry +1480+992 {chemin_qrcode} {chemin_combinaison} {chemin_attestation}"

    try:
        subprocess.run(commande_combinaison_1, shell=True, check=True)
        print(f"Première combinaison réussie. Image enregistrée à : {chemin_combinaison}")
        subprocess.run(commande_combinaison_2, shell=True, check=True)
        print(f"Deuxième combinaison réussie. Attestation finale enregistrée à : {chemin_attestation}")
    except subprocess.CalledProcessError as e:
        print(f"[ERREUR] Lors de la combinaison des images : {e}")

def generer_certificat(destinataire="Anonyme", signature="https://p-fb.net/", intitule="Attestation de réussite"):
    generer_QRcode(destinataire, signature)
    generer_texte(destinataire, intitule)
    combinaison_images(destinataire)

def extraire_QRcode(attestation_path):
    try:
        if not os.path.exists(attestation_path):
            raise FileNotFoundError(f"[ERREUR] Fichier non trouvé : {attestation_path}")

        # Récupère la partie du QRcode
        attestation = Image.open(attestation_path)
        attestation.load()
        qrImage = attestation.crop((1418, 934, 1418 + 210, 934 + 210))

        # Convertit et scanne
        qrImage = qrImage.convert('L')
        qrImage.load()
        data = zbarlight.scan_codes(['qrcode'], qrImage)

        if data:
            print("QR Code détecté :", data[0])
        else:
            print("[ERREUR] Aucun QR code détecté.")
        return data[0]

    except FileNotFoundError as e:
        print(e)

    except UnidentifiedImageError:
        print(f"[ERREUR] Le fichier '{attestation_path}' n'est pas une image valide.")

    except Exception as e:
        print(f"[ERREUR] Erreur inattendue lors de l'extraction du QR code : {e}")

    return None
