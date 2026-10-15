# Spécification de l'application de visualisation ABA

## 1. Contexte et objectif

L'application permet d'explorer un framework ABA (Assumption-Based Argumentation) et d'observer, de façon didactique, les arguments, les attaques et certaines propriétés structurelles du framework.

L'utilisateur peut charger un framework, lancer indépendamment les analyses disponibles et consulter leur résultat sans perdre le framework d'origine.

## 2. Utilisateurs visés

L'application s'adresse principalement aux étudiants et enseignants qui souhaitent manipuler des frameworks ABA sans devoir exécuter directement les fonctions Python.

## 3. Périmètre fonctionnel

### 3.1 Importer un framework

Le fichier exemple_aba1.txt est sélectionné par défaut.
L'utilisateur peut charger un framework selon l'une des modalités suivantes :

- choisir l'un des cinq fichiers `exemple_aba1.txt` à `exemple_aba5.txt` fournis avec le projet ;
- sélectionner un fichier texte ABA depuis son appareil ;
- modifier le fichier d'exemple dans un éditeur 

Le contenu importé est analysé et validé avant d'être affiché. Le format attendu est celui accepté par le parseur du projet : déclarations `L` et `A`, contraires `C`, règles, et préférences facultatives `PREF`. Les commentaires commençant par `#` et les lignes vides sont ignorés.

En cas d'échec de lecture ou de validation, l'application affiche un message compréhensible, indique si possible la ligne concernée et conserve le dernier framework correctement chargé. L'import par URL doit signaler les erreurs réseau, les réponses HTTP non valides et les délais d'attente sans bloquer indéfiniment l'interface.

### 3.2 Analyser et transformer

Les quatre actions suivantes sont accessibles après le chargement d'un framework :

1. **Générer les arguments et les attaques**
	- Calculer les arguments à supports minimaux et les attaques associées.
	- Présenter pour chaque argument sa conclusion et son support.
	- Présenter pour chaque attaque l'attaquant, la cible et son type (normale ou inversée).
	- Afficher un résultat vide explicitement lorsqu'aucun argument ou aucune attaque n'est produit.

2. **Tester les propriétés**
	- Indiquer si le framework est atomique et s'il est circulaire.
	- Présenter les deux résultats séparément, avec une valeur lisible (« oui » ou « non »).
	- Une règle est atomique lorsque toutes ses prémisses sont des hypothèses ; la circularité désigne la présence d'un cycle de déduction.

3. **Transformer en framework non circulaire**
	- Proposer une transformation lorsqu'un cycle est détecté.
	- Afficher le framework dérivé et son statut de circularité après transformation.
	- Si le framework est déjà non circulaire, l'indiquer et ne pas produire de transformation inutile.
	- Si la transformation n'est pas applicable, expliquer la raison sans remplacer le framework d'origine.

4. **Transformer en framework atomique**
	- Produire et afficher le framework dérivé selon l'algorithme fourni.
	- Indiquer clairement que le résultat affiché est une transformation et non une modification du framework d'origine.

Chaque action est lancée à la demande. Les transformations ne doivent pas modifier le framework importé ; elles produisent un résultat dérivé. Les opérations suivantes s'appliquent au framework importé, sauf si l'interface permet explicitement à l'utilisateur de sélectionner un résultat dérivé comme nouvelle entrée.

## 4. Interface utilisateur

L'interface présente deux zones de travail côte à côte sur grand écran et l'une sous l'autre sur petit écran :

- **Framework importé** : représentation textuelle lisible des composants du framework chargé (littéraux, hypothèses, contraires, règles et préférences) ;
- **Analyse et résultats** : résultats de la dernière action, avec distinction visible entre une analyse et un framework transformé.

La zone d'import comporte les trois modes d'accès (exemples, fichier, URL). Les quatre actions restent indisponibles tant qu'aucun framework valide n'est chargé. Un indicateur d'activité est présenté pendant les calculs ou l'import réseau ; les erreurs sont affichées près de l'action concernée.

Les listes de résultats doivent être ordonnées de manière stable afin de faciliter la lecture et la comparaison entre deux exécutions. L'application doit rester utilisable au clavier et les libellés des actions doivent être explicites.

## 5. Exigences techniques et déploiement

- Le code métier et l'application sont réalisés en Python, en réutilisant les modules et fonctions présents dans le projet.
- L'application doit pouvoir être lancée depuis un terminal local, avec une commande documentée et des dépendances installables dans un environnement virtuel.
- L'interface est accessible dans un navigateur en local et dans l'environnement de publication retenu.
- La publication sur Back4App est une cible du projet. Avant implémentation, confirmer le produit Back4App visé et sa compatibilité avec l'exécution d'une application Python ; documenter le point d'entrée, la configuration et les éventuelles adaptations nécessaires.
- Les fichiers téléversés et les URL sont traités comme des entrées non fiables : taille maximale, délai réseau et erreurs de parsing doivent être contrôlés. L'application ne doit pas exécuter le contenu importé comme du code.

## 6. Fonctions métier fournies

Les modules du projet fournissent les principales opérations :

- `aba_generator.py` : lecture, validation et représentation d'un framework ABA ;
- `aba_args_attaques.py` : calcul des arguments et des attaques ;
- `aba_conversion.py` : détection de circularité et d'atomicité, transformations associées.

L'interface doit appeler ces fonctions plutôt que réimplémenter les algorithmes. Les erreurs qu'elles lèvent doivent être converties en messages utiles pour l'utilisateur. Les détails d'implémentation et les signatures exactes restent définis par le code source.

## 7. Critères d'acceptation

- Chacun des cinq exemples fournis peut être sélectionné et affiché, ou produit un message d'erreur explicite si son contenu est invalide.
- Un fichier choisi par l'utilisateur et une URL valide peuvent charger un framework conforme au format attendu.
- Un fichier invalide ou une URL inaccessible ne fait pas disparaître le framework précédemment chargé.
- Les quatre actions produisent les résultats attendus par les fonctions métier ; chaque résultat est associé sans ambiguïté au framework analysé.
- Une transformation ne remplace jamais silencieusement les données d'origine.
- L'application peut être lancée localement depuis le terminal et son mode de déploiement Back4App est documenté et vérifié.
- La mise en page reste lisible sur écran étroit ; les états sans framework, chargement, erreur et résultat vide sont traités.

## 8. Points à confirmer avant implémentation

- Le service Back4App exact et les contraintes de déploiement Python associées.
- La limite de taille des fichiers et les domaines autorisés pour l'import par URL.
- La transformation à utiliser pour supprimer les cycles : duplication des littéraux ou remplacement des règles cycliques par des supports minimaux. Les deux approches existent dans le projet et leur choix peut influer sur le résultat affiché.
- Le périmètre de la transformation atomique : le code fourni génère des règles atomiques à partir des arguments et ne calcule pas les attaques dans ce résultat.

