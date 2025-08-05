from PIL import Image

def vers_8bit(c):
    chaine_binaire = bin(ord(c))[2:]
    return "0" * (8 - len(chaine_binaire)) + chaine_binaire

def modifier_pixel(pixel, bit):
    # on modifie que la composante rouge
    r_val = pixel[0]
    rep_binaire = bin(r_val)[2:]
    rep_bin_mod = rep_binaire[:-1] + bit
    r_val = int(rep_bin_mod, 2)
    return tuple([r_val] + list(pixel[1:]))

def recuperer_bit_pfaible(pixel):
    r_val = pixel[0]
    return bin(r_val)[-1]

def cacher(image, message):
    dimX, dimY = image.size
    im = image.load()
    message_binaire = ''.join([vers_8bit(c) for c in message])
    posx_pixel = 0
    posy_pixel = 0
    for bit in message_binaire:
        im[posx_pixel, posy_pixel] = modifier_pixel(im[posx_pixel, posy_pixel], bit)
        posx_pixel += 1
        if posx_pixel == dimX:
            posx_pixel = 0
            posy_pixel += 1
    assert posy_pixel < dimY

def recuperer(image, taille):
    message = ""
    dimX, dimY = image.size
    im = image.load()
    posx_pixel = 0
    posy_pixel = 0
    for rang_car in range(0, taille):
        rep_binaire = ""
        for rang_bit in range(0, 8):
            rep_binaire += recuperer_bit_pfaible(im[posx_pixel, posy_pixel])
            posx_pixel += 1
            if posx_pixel == dimX:
                posx_pixel = 0
                posy_pixel += 1
        message += chr(int(rep_binaire, 2))
    return message

def main():

    # Valeurs par défaut
    nom_defaut = "image_test.png"
    message_defaut = "Hello world"
    choix_defaut = 1

    # Programme de démonstration
    saisie = input("Entrez l'opération 1) cacher 2) retrouver [%d] " % choix_defaut)
    choix = int(saisie) if saisie else choix_defaut

    if choix == 1:
        saisie = input("Entrez le nom du fichier [%s] " % nom_defaut)
        nom_fichier = saisie or nom_defaut
        saisie = input("Entrez le message [%s] " % message_defaut)
        message_a_traiter = saisie or message_defaut
        print("Longueur message : ", len(message_a_traiter))
        mon_image = Image.open(nom_fichier)
        cacher(mon_image, message_a_traiter)
        mon_image.save("stegano_" + nom_fichier)
    else:
        saisie = input("Entrez le nom du fichier [%s] " % nom_defaut)
        nom_fichier = saisie or nom_defaut
        saisie = input("Entrez la taille du message ")
        message_a_traiter = int(saisie)
        mon_image = Image.open(nom_fichier)
        message_retrouve = recuperer(mon_image, message_a_traiter)
        print(message_retrouve)