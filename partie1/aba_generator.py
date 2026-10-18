"""Création et affichage de frameworks ABA depuis des fichiers ou des données."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, TextIO


@dataclass(frozen=True)
class Rule:
    """Règle nommée de la forme ``head <- body``; un corps vide est un fait."""

    name: str
    head: str
    body: tuple[str, ...] = ()


@dataclass
class ABAFramework:
    """Les cinq composants d'un framework ABA : L, A, C, R et préférences."""
    
    # Composants du framework ABA : littéraux, hypothèses, contraires, règles et préférences.
    literals: set[str] = field(default_factory=set)
    assumptions: set[str] = field(default_factory=set)
    # les contraires sont définis par un dictionnaire mappant chaque hypothèse à son contraire.
    contraries: dict[str, str] = field(default_factory=dict)
    # les règles sont stockées sous forme de liste d'objets Rule (avec name, head, body)
    rules: list[Rule] = field(default_factory=list)
    # les préférences sont stockées sous forme de paires (a, b) signifiant a > b.
    preferences: set[tuple[str, str]] = field(default_factory=set)

    @classmethod
    # trois méthodes d'importation sont prévues : depuis un fichier et depuis des données brutes ou depuis la liste des parametres.
    def from_data(cls, literals: set[str], assumptions: set[str], contraries: dict[str, str], rules: list[Rule], preferences: set[tuple[str, str]]) -> ABAFramework:
        """Crée un framework ABA à partir de données brutes."""
        return cls(literals, assumptions, contraries, rules, preferences)
    
    @classmethod
    def from_file(cls, file_path: str | Path) -> ABAFramework:
        """Importe un fichier texte ABA et signale les erreurs avec leur ligne."""
        path = Path(file_path)
        framework = cls()
        declarations: set[str] = set()
        symbol = r"[^\s,\[\]():<>#]+"

        def parse_symbols(content: str) -> list[str]:
            if not content.strip():
                return []
            values = [value.strip() for value in content.split(",")]
            if any(re.fullmatch(symbol, value) is None for value in values):
                raise ValueError("Liste de symboles invalide.")
            return values

        for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                declaration = re.fullmatch(r"(L|A)\s*:\s*\[(.*)\]", line)
                contrary = re.fullmatch(rf"C\(\s*({symbol})\s*\)\s*:\s*({symbol})", line)
                rule = re.fullmatch(rf"\[({symbol})\]\s*:\s*({symbol})\s*<-\s*(.*)", line)
                if declaration:
                    kind = declaration[1]
                    if kind in declarations:
                        raise ValueError(f"Déclaration {kind} répétée.")
                    declarations.add(kind)
                    values = set(parse_symbols(declaration[2]))
                    if kind == "L":
                        framework.literals = values
                    else:
                        framework.assumptions = values
                elif contrary:
                    if contrary[1] in framework.contraries:
                        raise ValueError("Contraire déclaré plusieurs fois.")
                    framework.contraries[contrary[1]] = contrary[2]
                elif rule:
                    if any(existing.name == rule[1] for existing in framework.rules):
                        raise ValueError("Nom de règle répété.")
                    framework.rules.append(
                        Rule(rule[1], rule[2], tuple(parse_symbols(rule[3])))
                    )
                elif line.startswith("PREF:"):
                    content = line[5:].strip()
                    if content:
                        for preference in content.split(","):
                            match = re.fullmatch(
                                rf"\s*({symbol})\s*>\s*({symbol})\s*", preference
                            )
                            if match is None:
                                raise ValueError("Préférence attendue : a > b.")
                            framework.preferences.add((match[1], match[2]))
                else:
                    raise ValueError("Ligne non reconnue.")
            except ValueError as error:
                raise ValueError(f"{path.name}, ligne {line_number} : {error}") from error

        if declarations != {"L", "A"}:
            raise ValueError(f"{path.name} : déclarations L et A obligatoires.")
        _validate_framework(framework)
        return framework

    def to_text(self) -> str:
        """Retourne une représentation lisible et stable du framework."""
        lines = [
            f"L: [{', '.join(sorted(self.literals))}]",
            f"A: [{', '.join(sorted(self.assumptions))}]",
            "Contraires :",
        ]
        if self.contraries:
            lines.extend(
                f"  C({assumption}): {contrary}"
                for assumption, contrary in sorted(self.contraries.items())
            )
        else:
            lines.append("  (aucun)")
        lines.append("Règles :")
        if self.rules:
            lines.extend(
                f"  [{rule.name}]: {rule.head} <- {', '.join(rule.body)}"
                for rule in self.rules
            )
        else:
            lines.append("  (aucune)")
        lines.append("Préférences :")
        if self.preferences:
            lines.extend(
                f"  {preferred} > {less_preferred}"
                for preferred, less_preferred in sorted(self.preferences)
            )
        else:
            lines.append("  (aucune)")
        return "\n".join(lines)

    def print_framework(self, file: TextIO | None = None) -> None:
        """Affiche le framework dans la console ou dans un flux texte fourni."""
        print(self.to_text(), file=file)

# Validation du framework ABA : vérifie la cohérence des symboles utilisés.
def _validate_framework(framework: ABAFramework) -> None:
    """Vérifie que les symboles utilisés sont déclarés dans le langage."""
    if not framework.assumptions <= framework.literals:
        raise ValueError("Toutes les assumptions doivent appartenir à L.")
    for rule in framework.rules:
        if not {rule.head, *rule.body} <= framework.literals:
            raise ValueError(f"Règle {rule.name} : symbole absent de L.")
    for assumption, contrary in framework.contraries.items():
        if assumption not in framework.assumptions or contrary not in framework.literals:
            raise ValueError("Le contraire ou l'assumption de C n'est pas déclaré.")

# Fonctions de création de frameworks ABA à partir de composants ou de fichiers.
def create_aba_framework(
    literals: Iterable[str],
    assumptions: Iterable[str],
    contraries: dict[str, str],
    rules: Iterable[Rule],
    preferences: Iterable[tuple[str, str]] = (),
) -> ABAFramework:
    """Construit un framework à partir de ses composants fournis directement.

    Les contraires suivent la notation des fichiers : ``{assumption: contraire}``.
    """
    framework = ABAFramework(
        literals=set(literals),
        assumptions=set(assumptions),
        contraries=dict(contraries),
        rules=list(rules),
        preferences=set(preferences),
    )
    _validate_framework(framework)
    return framework


def create_aba_framework_from_file(file_path: str | Path) -> ABAFramework:
    """Construit un framework ABA en important un fichier exemple."""
    return ABAFramework.from_file(file_path)



if __name__ == "__main__":
    # test fichier ABA en important et affichant son contenu
    # fichier exemple à tester
    num_choisi=1
    path = Path(__file__).parent / f"exemple_aba{num_choisi}.txt"
    


    if path:
        try:
            print(f"\n=== Import fichier : {path.name} ===")
            create_aba_framework_from_file(path).print_framework()
        except (OSError, ValueError) as error:
            print(str(error))

    