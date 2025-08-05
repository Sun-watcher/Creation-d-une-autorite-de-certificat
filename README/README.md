CA/

├── certs/           # Dossier pour les certificats signés (y compris celui de la CA)

│   └── ecc.ca.cert.pem

├── private/         # Dossier sécurisé pour la clé privée de la CA

│   └── ecc.ca.key.pem

├── requests/        # Dossier pour les CSR (demandes de signature)

│   └── ecc.csr.pem

├── newcerts/        # Dossier pour les certificats émis (certificats signés)

│   └── ecc.serveur.pem

└── ecc.ca.cert.srl  # Fichier pour la numérotation des certificats émis

└──root-ca.cnf  # Fichier de configuration pour OpenSSL

