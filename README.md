# TP Dynamique connaissance partie 1

#





# appli web 
voir 
# Atelier ABA

Application web Python pour charger et explorer les frameworks ABA fournis dans le projet.

## Lancement local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Ouvrir ensuite <http://127.0.0.1:5000>. Le port local peut être remplacé avec la variable d'environnement `PORT`.

## Tests

```bash
python -m unittest -v test_app
```

## Déploiement Back4App

La cible retenue est **Back4App Containers**, qui construit l'application depuis le `Dockerfile` du dépôt. Connecter le dépôt Git à un nouveau conteneur Back4App et utiliser le port HTTP `8080`. La commande de démarrage lance Gunicorn et respecte la variable `PORT` fournie par la plateforme.

Le déploiement dans un compte Back4App n'a pas été effectué depuis cet environnement. Après création du conteneur, vérifier le build, l'état de santé sur `/healthz` et l'accès HTTP à la page d'accueil.

## Import et limites

Les fichiers et contenus importés sont limités à 64 Ko et doivent être en UTF-8. Les URL sont limitées aux protocoles HTTP(S), aux hôtes résolus sur des adresses publiques, sans redirection, avec un délai de cinq secondes. Le contenu importé est analysé comme du texte ABA et n'est jamais exécuté comme du code.