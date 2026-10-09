# Framework ABA

Application web pour charger un framework ABA au format texte, calculer ses arguments et ses attaques, puis afficher sa conversion non circulaire et atomique.

## Lancer localement

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Ouvrir `http://localhost:5000`. Le framework d'exemple est préchargé ; un fichier `.txt` UTF-8 peut aussi être importé. La taille maximale d'envoi est de 64 Ko.

## Déployer sur Back4App Containers

`application_aba.py` est l'interface Tkinter pour ordinateur ; elle reste disponible dans le dépôt, mais Back4App lance la version web définie dans `app.py`, qui réutilise `aba_gen_nico.py` et `exemple_aba.txt`.

1. Pousser le contenu de `IA_AT_TP` dans un dépôt GitHub.
2. Dans Back4App Containers, créer un conteneur et connecter le dépôt.
3. Utiliser `IA_AT_TP` comme répertoire de construction s'il s'agit d'un sous-dossier du dépôt. Le fichier de construction est `Dockerfile`.
4. Déployer la branche souhaitée. L'application écoute sur la variable `PORT` fournie par la plateforme, avec `5000` comme valeur par défaut.
5. Ouvrir l'URL du conteneur une fois la construction terminée.

Aucune base de données ni variable secrète n'est nécessaire. `WEB_CONCURRENCY` permet d'ajuster le nombre de workers Gunicorn (2 par défaut).
