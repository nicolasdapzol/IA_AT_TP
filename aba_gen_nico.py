import os
import shutil
import subprocess
from dataclasses import dataclass
from itertools import product
import re


@dataclass(frozen=True)
# définition de la classe Rule
class Rule:
    """ 
    regle : avec un nom , un head (conclusion) et un body (premisses)
    exemple :
    pour [r1]: a <- b,c
        Rule(name="r1", head="a", body=("b", "c"))
    pour [r3]: r <- b,c
        Rule(name="r3", head="r", body=("b", "c"))
    
    """

    name: str
    head: str
    body: tuple[str, ...] = ()


@dataclass(frozen=True)


# définition de la classe Argument 
class Argument:
    """ un argument a un support  et une conclusion  et un nom"""
    """ exemple :
    Argument(conclusion="a", support=frozenset({"a"}), name="arg_a")
    Argument(conclusion="b", support=frozenset({"b"}), premisses=(Argument(conclusion="a", support=frozenset({"a"}), name="arg_a"),), name="arg_b")
    """
    
    conclusion: str
    support: frozenset[str]
    name: str 
    def __repr__(self):
        support_str = ", ".join(sorted(self.support)) if self.support else "∅"
        return f"{self.name}: {self.conclusion} <- [{support_str}]"
        # a quoi servent les premisses : elles permettent de représenter les arguments qui dépendent d'autres arguments. 
    #premisses: tuple["Argument", ...] = ()
    
    """rule: str | None = None
    
    @property
    def literals(self) -> frozenset[str]:
        
        return frozenset({self.conclusion}).union(
            *(premise.literals for premise in self.premisses)
        )
        """


@dataclass(frozen=True)
class Attack:
    """Indices dans createArguments(); witness conserve la preuve du contraire."""

    attacker: int
    target: int
    kind: str
    assumption: str
    witness: int


    
    


class ABA_generator:
    """
    un ABA framework comporte les elements suivants :
    L : ensemble de litteraux (définis par une liste)    
    R : ensemble de regles (définis par des instances de la classe Rule)
    A : ensemble d'assumptions (définis par une liste)
    C : dictionnaire des contraires (clé = contraire, valeur = hypothèse)
    PREF : ensemble de preferences (définis par des paires (a, b) signifiant a > b)
    
    (L, R, A, C, PREF) 
    
    """

    def __init__(self, literals=(), assumptions=(), contraries=None,
                 rules=(), preferences=()):
        self.setLiterals(literals)
        self.setAssumptions(assumptions)
        self.setContraries(contraries or {})
        self.setRules(rules)
        self.setPreferences(preferences)

    def setLiterals(self, literals):
        # définit la liste des littéraux , le set permet d'éviter les doublons
        self._literals = set(literals)

    def getLiterals(self):
        return set(self._literals)

    def setAssumptions(self, assumptions):
        # définit la liste des assumptions , le set permet d'éviter les doublons
        #self._assumptions = set(assumptions)
        self._assumptions = assumptions

    def getAssumptions(self):
        return set(self._assumptions)

    def setContraries(self, contraries):
        """Stocke les contraires sous la forme {contraire: hypothèse}."""
        self._contraries = dict(contraries)

    def getContraries(self):
        return dict(self._contraries)

    def setRules(self, rules):
        """Accepte des objets Rule ou des triplets (nom, conclusion, corps)."""
        self._rules = [
                    rule if isinstance(rule, Rule)
                    else Rule(rule[0], rule[1], tuple(rule[2]))
                    for rule in rules
                ]

    def getRules(self):
        return list(self._rules)

    def setPreferences(self, preferences):
        self._preferences = {tuple(pair) for pair in preferences}

    def getPreferences(self):
        return set(self._preferences)

    def createArguments(self):
        """ y a surement plus simple ! 
        construit les arguments ( il nous faut une classe argument !) puis on applique l'algo
        vu en CM (enfin on tente !)
        1. pour chaque assumptions , on construit l'argument {a} |- a.
        2. pour chaque regle, 
         on construit un nouvel argument dont la conclusion est celle de la règle 
         et dont le support est l'ensemble des littéraux du corps de la règle.
        

        
        2. Pour chaque regle, on combine les preuves de toutes ses premisses.
        3. Leur support est l'union des assumptions utilisees.
        4. On repete jusqu'a ce qu'aucun arbre nouveau ne soit produit.

        Une conclusion deja presente dans une branche interdirait un arbre
        non circulaire : cette combinaison est exclue. Les faits sont obtenus
        grace au produit cartesien vide, qui fournit une combinaison vide.
        L'enumeration est finie, mais peut etre exponentielle.
        """
#        self.validate()
        #   pour chaque assumptions , on construit l'argument {a} |- a.
        print("définition des arguments pour les assumptions")
        arguments = []
        for assumption in sorted(self._assumptions):
            arguments.append(Argument(conclusion=assumption, support=frozenset({assumption}), name=assumption))
        
        print("Arguments après définition des assumptions :", arguments)
        
        #   pour chaque regle, on construit un argument dont la conclusion est celle de la règle
        #for rule in self._rules:
        #    support = frozenset(rule.body)
        #    argument = Argument(rule.head, support, rule.name)
        #    arguments.append(argument)
        # là on a construit les arguments de base pour chaque assumption et chaque règle
        #print("Arguments après définition des règles :", arguments)
        
        
        # maintenant on va combiner les arguments pour générer de nouveaux arguments selon les règles
        # on va utiliser un ensemble arguments_connus pour garder une trace des arguments déjà connus
        # arguments_connus contiendra tous les arguments déjà générés, pour éviter les doublons
        #print("Arguments initiaux :", arguments)
        arguments_connus = set(arguments)
        
        # on crée un dictionnaire by_conclusion pour accéder rapidement aux arguments par leur conclusion
        # by_conclusion = {literal: [] for literal in self._literals}
        # print("Dictionnaire by_conclusion initial :", by_conclusion)
        
        #for argument in arguments:
        #    by_conclusion[argument.conclusion].append(argument)
        #print("Dictionnaire by_conclusion après ajout des arguments initiaux :", by_conclusion)
            
        while True:
            
            # pour chaque règle, on regarde si on peut combiner des arguments existants pour générer un nouvel argument
            # pour cela , pour chaque littéral dans le corps de la règle, 
            # on récupère les arguments connus qui ont cette conclusion            
            # puis on combine ces arguments pour générer un nouvel argument si possible
            print("Nouvelle itération de la boucle de génération d'arguments")
            
            chgt_ = False
            for rule in self._rules:
                les_litteraux = rule.body
                new_regle = True
                supports_des_premisses = []

                for literal in les_litteraux:
                    arguments_avec_conclusion = [
                        arg for arg in arguments_connus if arg.conclusion == literal
                    ]
                    if not arguments_avec_conclusion:
                        new_regle = False
                        break
                    supports_des_premisses.extend(
                        arg.support for arg in arguments_avec_conclusion
                    )

                if new_regle:
                    print("Règle applicable :", rule)
                    support_total = (
                        frozenset().union(*supports_des_premisses)
                        if supports_des_premisses
                        else frozenset()
                    )
                    print("Support total calculé :", support_total)
                    new_argument = Argument(rule.head, support_total, rule.name)
                    print("Nouvel argument généré :", new_argument)
                    if new_argument not in arguments_connus:
                        arguments_connus.add(new_argument)
                        print("Nouvel argument ajouté :", new_argument)
                        chgt_ = True

            #print("Arguments après ajout des nouvelles combinaisons :", arguments_connus)
            #print("Dictionnaire by_conclusion après ajout des nouvelles combinaisons :", by_conclusion)
            if not chgt_:
                break
        print("Boucle terminée.")
        self.arguments=arguments_connus
        
        # trier les arguments connus par nom avant de les afficher
        arguments_connus = sorted(arguments_connus, key=lambda arg: arg.name)
        # ajouter un retour à la ligne entre chaque argument de argurments_connus
        print("Arguments finaux :")
        for arg in arguments_connus:
            print(arg)
            
    def createAttacks(self):
        """Calcule les attaques entre les arguments.

        Un argument avec conclusion a attaque tout argument dont le support contient
        le contraire de a. En ABA+, si a est préférée à un élément b, l'attaque
        peut être inversée.
        """
        liste_attaques = []
        liste_contraires = self.getContraries()
        preferences = self.getPreferences()
        print('____________ debut recherche attaque ____________')
        print('Contraires :', liste_contraires)

        for arg in self.arguments:
            contraire = liste_contraires.get(arg.conclusion)
            if contraire is None:
                continue

            for cible in self.arguments:
                if cible == arg:
                    continue

                if contraire in cible.support:
                    attaque_inversee = any(
                        (contraire, lit) in preferences for lit in arg.support
                    )
                    if attaque_inversee:
                        print(f"Attaque inversée : {cible} attaque {arg}")
                        liste_attaques.append((cible, arg, "inversée"))
                    else:
                        print(f"Attaque détectée : {arg} attaque {cible} (normale)")
                        liste_attaques.append((arg, cible, "normale"))

        self.attaques = liste_attaques
        # trie des attaques par nom de l'argument attaquant
        liste_attaques.sort(key=lambda attaque: attaque[0].name)
        print("liste attaques :")
        for arg in liste_attaques:
            print(arg)
        #print("Attaques détectées :", self.attaques)
    
    def transformeToNonCircular(self):
        """Retourne un nouvel ABA plat, atomique et non circulaire.

        Exemple : p <- a et q <- p deviennent p <- a et q <- a.
        Tous les supports distincts sont conservés, mais pas les arbres de
        preuve ni les noms des règles. Les cycles sans base disparaissent.
        Le calcul est fini, mais peut produire un nombre exponentiel de supports.
        """
        literals = self.getLiterals()
        assumptions = self.getAssumptions()

        # Une hypothèse ne doit pas être déduite par une règle dans un ABA plat.
        if not assumptions <= literals:
            raise ValueError('Les assumptions doivent appartenir a L.')
        for rule in self._rules:
            if not {rule.head, *rule.body} <= literals:
                raise ValueError(f'Regle {rule.name} : litteral absent de L.')
            if rule.head in assumptions:
                raise ValueError('ABA plat requis : une regle conclut une assumption.')

        # supports['p'] = {{a}, {b}} signifie : a OU b permet de déduire p.
        # Un frozenset est immuable : on peut le stocker dans un set sans doublons.
        supports = {literal: set() for literal in literals}
        for assumption in assumptions:
            supports[assumption].add(frozenset({assumption}))
        # supports initiaux : chaque hypothèse se supporte elle-même.

        # Repasser sur les règles tant qu'on découvre de nouveaux supports.
        changed = True
        while changed:
            changed = False
            for rule in self._rules:
                if any(not supports[literal] for literal in rule.body):
                    continue
                # Chaque prémisse choisit un support; product() traite aussi les faits.
                for combinaison in product(*(supports[literal] for literal in rule.body)):
                    support = frozenset().union(*combinaison)
                    if support not in supports[rule.head]:
                        supports[rule.head].add(support)
                        changed = True

        # Chaque support donne une règle directe : conclusion <- hypothèses.
        # on enregistre les nouvelles règles 
        # les litteraux et les assumptions sont copiés dans de nouvelles variables pour les nouvelles règles.
        new_literals=literals
        new_assumptions=assumptions
        
        # les nouvelles règles :
        # on trie pas les règles ici, on les garde dans l'ordre de génération
        new_rules = []
        # on parcourt chaque littéral et ses supports pour créer de nouvelles règles non circulaires
        for lit in literals:
            for support in supports[lit]:
                new_rules.append((f'non_circular_{len(new_rules) + 1}', lit, tuple(sorted(support))))
        
        print(new_rules)
        

        # Seules les règles changent ; le framework original reste intact.
        return ABA_generator(
            new_literals, new_assumptions, self.getContraries(), new_rules,
            self.getPreferences(),
        )
        
    
    
    def from_file(self, file_path):
        with open(file_path, 'r') as file:
            text = file.read()
        print("Lecture du fichier :", file_path)
        print("text:", text)
        return self.from_text(text=text)
    
    def from_text(self, text):
        """Lit le format du sujet; les titres ## et les lignes vides sont ignores.

        Les listes L et A sont obligatoires. Le corps vide de q <- est un
        fait. Plusieurs preferences se separent par des virgules, ou utilisent
        plusieurs lignes PREF. Les erreurs indiquent le numero de ligne.
        """
        literals = assumptions = None
        contraries, rules, preferences = {}, [], []
        # Les identifiants sont des symboles, pas des expressions logiques.
        symbol = r'[^\s,\[\]():<>#]+'

        def parse_list(content):
            if not content.strip():
                return []
            values = [value.strip() for value in content.split(',')]
            if any(re.fullmatch(symbol, value) is None for value in values):
                raise ValueError('Liste de litteraux invalide.')
            return values

        for line_number, raw_line in enumerate(text.splitlines(), 1):
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue
            declaration = re.fullmatch(r'(L|A)\s*:\s*\[(.*)\]', line)
            contrary = re.fullmatch(
                rf'C\(\s*({symbol})\s*\)\s*:\s*({symbol})', line
            )
            rule = re.fullmatch(
                rf'\[({symbol})\]\s*:\s*({symbol})\s*<-\s*(.*)', line
            )
            if declaration:
                values = parse_list(declaration[2])
                if declaration[1] == 'L':                        
                    literals = values
                else:                        
                    assumptions = values
            elif contrary:                    
                contraries[contrary[1]] = contrary[2]
            elif rule:
                rules.append(Rule(rule[1], rule[2], tuple(parse_list(rule[3]))))
            elif line.startswith('PREF:'):
                for preference in line[5:].split(','):
                    match = re.fullmatch(
                        rf'\s*({symbol})\s*>\s*({symbol})\s*', preference
                    )
                    if not match:
                        raise ValueError('Preference attendue : a > b.')
                    preferences.append((match[1], match[2]))


        print("Literals :", literals)
        print("Assumptions :", assumptions)
        print("Contraries :", contraries)
        print("Rules :", rules)
        print("Preferences :", preferences)
            
        aba=ABA_generator(
        literals=literals,
        assumptions=assumptions,
        contraries=contraries,
        rules=rules,
        preferences=preferences
        )

        return aba

    def visualize(self, filename="aba_framework", output_dir=".", format_="png", show=False):
        """Visualise le framework ABA sous forme de graphe."""
        if not hasattr(self, "arguments"):
            self.createArguments()
        if not hasattr(self, "attaques"):
            self.createAttacks()

        os.makedirs(output_dir, exist_ok=True)

        nodes = []
        for arg in sorted(self.arguments, key=lambda x: x.name):
            support = ", ".join(sorted(arg.support)) if arg.support else "∅"
            label = f"{arg.name}\\n{arg.conclusion}\\nSupport: {{{support}}}"
            nodes.append((arg.name, label))

        edges = []
        for attacker, target, kind in self.attaques:
            edges.append((attacker.name, target.name, kind))

        dot_lines = [
            "digraph ABA_Framework {",
            "  rankdir=LR;",
            "  node [shape=box, fontname=Helvetica];",
            "  edge [fontname=Helvetica];",
        ]
        print("Génération du code DOT...")
        print("Nombre de nœuds :", len(nodes))
        print("Nombre d'arêtes :", len(edges))

        for node_name, label in nodes:
            dot_lines.append(f'  "{node_name}" [label="{label}"];')

        for src, dst, kind in edges:
            dot_lines.append(f'  "{src}" -> "{dst}" [label="{kind}"];')

        dot_lines.append("}")
        dot_source = "\n".join(dot_lines)

        dot_path = f"{output_dir}/{filename}.dot"
        with open(dot_path, "w", encoding="utf-8") as f:
            f.write(dot_source)

        if shutil.which("dot") is not None:
            output_path = f"{output_dir}/{filename}.{format_}"
            try:
                subprocess.run([
                    "dot",
                    f"-T{format_}",
                    dot_path,
                    "-o",
                    output_path,
                ], check=True)
                print(f"Graphe généré : {output_path}")
            except subprocess.CalledProcessError:
                print("Échec de génération du PNG avec Graphviz.")
        else:
            print("Graphviz n'est pas installé. Le fichier .dot a bien été généré, mais le PNG n'a pas pu être produit.")
            print("Installer Graphviz sur Linux : sudo apt-get install graphviz")

        print("Code DOT généré :")
        print(dot_source)

        if show and shutil.which("xdg-open") is not None:
            try:
                print("Ouverture du fichier généré...")
                subprocess.run(["xdg-open", f"{output_dir}/{filename}.{format_}"], check=False)
            except Exception:
                print("Échec de l'ouverture du fichier généré.")
                pass
        print("Visualisation terminée.")
            

        return dot_source


if __name__ == '__main__':
    # Exemple d'utilisation de la classe ABA_generator

    
    aba = ABA_generator(
            literals=['a', 'b', 'c', 'd','e'],
            assumptions=['a', 'b'],
            contraries={'a': 'd', 'b': 'e'},
            rules=[('r1', 'c', ['a']),
                   ('r2', 'd', ['b','c']),
                   ('r3', 'e', ['c'])                    
                   ],
            preferences=[('a', 'b')]
        )
    
    aba = ABA_generator(
        literals=['a', 'b', 'c', 'p','q','r','s','t'],
        assumptions=['a', 'b','c'],
        contraries={'r': 'a', 's': 'b', 't': 'c'},
        rules=[('r1', 'p', ['q']), 
               ('r2', 'q', []), 
               ('r3', 'r', ['b', 'c'])               
               ],
        preferences=[('a', 'b')]
    )
    
    
    aba = ABA_generator(
            literals=['a', 'b', 'c', 'q','p','r','s','t'],
            assumptions=['a', 'b','c'],
            contraries={'r': 'a', 's': 'b', 't': 'c'},
            rules=[('r1', 'p', ['q', 'a']), 
                   ('r2', 'q', []), 
                   ('r3', 'r', ['b', 'c']),
                   ('r4', 't', ['p', 'c']),
                   ('r5', 's', ['t'])
                   ],
            preferences=[('a', 'b')]
    )
    
    aba = ABA_generator(
        literals=['a', 'p','q'],
        assumptions=['a'],
        contraries={'p': 'a'},
        rules=[('r1', 'q', ['p']), 
                ('r2', 'p', ['a'])                 
                ],
        preferences=[]
    )
        
    
    print("Literals:", aba.getLiterals())
    print("Assumptions:", aba.getAssumptions())
    print("Contraries:", aba.getContraries())
    print("Rules:", aba.getRules())
    print("Preferences:", aba.getPreferences())
    
    #aba.createArguments()
    #aba.createAttacks()
    #aba.visualize(filename="aba_framework", output_dir="/home/nico/python/IA_DYCO/TP1", format_="png", show=True)
    #aba.transformeToNonCircular()
    
    aba = aba.from_file("/home/nico/python/IA_DYCO/IA_AT_TP/exemple_aba3.txt")
    aba.createArguments()
    aba.createAttacks()
    

