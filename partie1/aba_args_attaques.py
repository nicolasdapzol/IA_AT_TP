"""Calcul  des arguments et des attaques pour un framework ABA."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable

try:
    from .aba_generator import ABAFramework
except ImportError:  # Permet aussi l'import direct depuis ce dossier.
    from aba_generator import ABAFramework


@dataclass(frozen=True)
class Argument:
    """Un argument ABA : une conclusion dérivée et son support minimal."""

    conclusion: str
    support: frozenset[str]


@dataclass(frozen=True)
class Attack:
    """Une attaque entre arguments, qualifiée de normale ou d'inversée."""

    attacker: Argument
    target: Argument
    kind: str


def argument_key(argument: Argument) -> tuple[str, tuple[str, ...]]:
    """Clé stable pour présenter les arguments dans le même ordre."""
    return argument.conclusion, tuple(sorted(argument.support))


def create_arguments(framework: ABAFramework) -> set[Argument]:
    """Calcule les arguments minimaux à partir d'un unique ABAFramework.

    Une hypothèse se prouve par elle-même; un fait, par un support vide.
    Les choix de supports pour plusieurs prémisses sont combinés séparément,
    car ils représentent des preuves alternatives.
    """
    assumptions = framework.assumptions
    selected_rules = framework.rules
    # Initial arguments: assumptions and les faits (les règles sans corps)
    # assumptions
    arguments = {Argument(assumption, frozenset({assumption})) for assumption in assumptions}
    # faits 
    arguments.update(
        Argument(rule.head, frozenset()) for rule in selected_rules if not rule.body
    )
    # tant qu'on peut trouver des nouveaux arguments , on itère
    changed = True
    while changed:
        changed = False
        for rule in selected_rules:
            # pour chaque règle, on cherche à combiner les supports des littéraux du corps
            support_options: list[list[frozenset[str]]] = []
            candidat = True
            for literal in rule.body:
                literal_supports = [
                    argument.support
                    for argument in arguments
                    if argument.conclusion == literal
                ]
                if not literal_supports:
                    candidat = False
                    break
                support_options.append(literal_supports)
            # si aucune combinaison n'est possible, on passe à la règle suivante
            if not candidat:
                continue
            # sinon, on génère toutes les combinaisons possibles des supports des littéraux du corps
            # chaque combinaison de supports choisis correspond à un nouvel argument potentiel
            # on parcourt toutes les combinaisons possibles des supports choisis
            # par exemple, si le corps de la règle est [A, B] et qu'il existe des arguments pour A et B,
            
            for chosen_supports in product(*support_options):
                # on crée un nouvel argument avec le support combiné
                support = frozenset().union(*chosen_supports)
                # on vérifie si un argument avec le même head et un support inclus existe déjà
                current = {
                    argument for argument in arguments if argument.conclusion == rule.head
                }
                # si un tel argument existe déjà, on ne crée pas de doublon
                if any(argument.support <= support for argument in current):
                    continue
                # on supprime les arguments existants dont le support contient strictement le nouveau support
                arguments.difference_update(
                    argument for argument in current if support < argument.support
                )
                # on ajoute le nouvel argument
                arguments.add(Argument(rule.head, support))
                changed = True
    return arguments


def _preference_closure(
    preferences: Iterable[tuple[str, str]],
) -> set[tuple[str, str]]:
    """Calcule la transitivité des paires ``(préférée, moins_préférée)``."""
    closure = set(preferences)
    changed = True
    while changed:
        changed = False
        for preferred, middle in tuple(closure):
            for other_middle, less_preferred in tuple(closure):
                if middle == other_middle and (preferred, less_preferred) not in closure:
                    closure.add((preferred, less_preferred))
                    changed = True
    if any(first == second for first, second in closure):
        raise ValueError("Les préférences doivent former un ordre strict sans cycle.")
    return closure


def compute_attacks(
    arguments: Iterable[Argument],
    framework: ABAFramework,
) -> set[Attack]:
    """Calcule les attaques normales et inversées du framework ABA.

    Les préférences suivent la forme ``(préférée, moins_préférée)``. Une
    attaque est inversée si l'hypothèse visée est préférée à au moins une
    hypothèse du support attaquant.
    """
    argument_list = list(arguments)
    preferred_over = _preference_closure(framework.preferences)

    # Initialisation de l'ensemble des attaques.
    attacks: set[Attack] = set()
    # ça , c'est un algorithme pas très rapide !
    # pour chaque argument , on le considère comme attaquant, on vérifie s'il attaque d'autres arguments
    for attacker in argument_list:
        # pour chaque argument  on le considère comme cible, on vérifie s'il est attaqué par l'argument attaquant
        for target in argument_list:
            # est ce que la conclusion de l'attaquant est le contraire d'une hypothèse du support de la cible
            for support_cible in target.support:
                contrary = framework.contraries.get(support_cible)
                if contrary != attacker.conclusion:
                    continue
                # y a une attaque ! 
                # est elle inversée ?
                # Inversion si l'hypothèse visée est préférée à un élément du support attaquant.
                # l'attaque est inversée
                is_reversed = any(
                    (support_cible, support_attaquant) in preferred_over
                    for support_attaquant in attacker.support
                )
                if is_reversed:
                    attacks.add(Attack(target, attacker, "inversée"))
                else:
                    attacks.add(Attack(attacker, target, "normale"))
    return attacks

