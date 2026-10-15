"""Transformations de frameworks ABA en formes non circulaire et atomique."""

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
from itertools import product
from aba_generator import ABAFramework, Rule, create_aba_framework
from aba_args_attaques import Argument, Attack, argument_key, compute_attacks, create_arguments

def _strongly_connected_components(graph: dict[str, set[str]]) -> list[set[str]]:
    """Retourne les composantes fortement connexes avec l'algorithme de Tarjan."""
    next_index = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[set[str]] = []

    def visit(node: str) -> None:
        nonlocal next_index
        indices[node] = next_index
        lowlinks[node] = next_index
        next_index += 1
        stack.append(node)
        on_stack.add(node)

        for neighbor in sorted(graph[node]):
            if neighbor not in indices:
                visit(neighbor)
                lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
            elif neighbor in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[neighbor])

        if lowlinks[node] == indices[node]:
            component: set[str] = set()
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.add(member)
                if member == node:
                    break
            components.append(component)

    for node in sorted(graph):
        if node not in indices:
            visit(node)
    return components


def _dependency_graph(framework: ABAFramework) -> dict[str, set[str]]:
    """Construit le graphe des dépendances entre prémisses et conclusions."""
    graph = {literal: set() for literal in framework.literals}
    for rule in framework.rules:
        for premise in rule.body:
            graph[premise].add(rule.head)
    return graph


def _cyclic_literals(graph: dict[str, set[str]]) -> set[str]:
    """Retourne les littéraux appartenant à un cycle de déduction."""
    cyclic: set[str] = set()
    for component in _strongly_connected_components(graph):
        if len(component) > 1 or any(node in graph[node] for node in component):
            cyclic.update(component)
    return cyclic


def framework_is_circular(framework: ABAFramework) -> bool:
    """Indique si les règles du framework contiennent un cycle de déduction."""
    return bool(_cyclic_literals(_dependency_graph(framework)))


def _rule_is_atomic(rule: Rule, assumptions: set[str]) -> bool:
    return set(rule.body) <= assumptions


def is_atomic(framework: ABAFramework) -> bool:
    """Indique si le corps de chaque règle contient uniquement des hypothèses."""
    return all(
        _rule_is_atomic(rule, framework.assumptions) for rule in framework.rules
    )


def convert_to_non_circular_aba(framework: ABAFramework) -> ABAFramework:
    """Duplique les littéraux et les règles pour supprimer les cycles de déduction.

    Une règle est atomique lorsque toutes ses prémisses sont des hypothèses.
    """
    literals = framework.literals
    assumptions = framework.assumptions
    if not assumptions <= literals:
        raise ValueError("Les hypothèses doivent appartenir à L.")
    for rule in framework.rules:
        if not {rule.head, *rule.body} <= literals:
            raise ValueError(f"Règle {rule.name} : symbole absent de L.")
        if rule.head in assumptions:
            raise ValueError("Framework plat requis : une règle conclut une hypothèse.")

    k = len(literals - assumptions)
    if k == 0:
        return framework
    
    converted_rules: list[Rule] = []
    used_names: set[str] = set(rule.name for rule in framework.rules)
    
        # On commence par déclarer les nouveaux littéraux  : il faut creer k copies pour chaque littéral non hypothèse
    nouveau_literals = set(literals)
    copies: dict[tuple[str, int], str] = {}
    for literal in sorted(literals - assumptions):
        for index in range(1, k + 1):
            copied_literal = f"{literal}^{index}"
            nouveau_literals.add(copied_literal)
            copies[literal, index] = copied_literal
    
    literals = nouveau_literals
    converted_rules: list[Rule] = []
    # used_names: set[str] = set()

    # du CM 4A
    # - for each **atomic** rule $r = s \leftarrow p_1, \dots, p_n$:
    # - We create $r_1, r_2, \dots, r_k$, where $r_i = s^i \leftarrow p_1, \dots, p_n$ and $s^k  =s$
    
    for rule in framework.rules:
            atomic = _rule_is_atomic(rule, assumptions)
            
            if atomic:
                # pour chaque règle atomique, on crée k copies avec des les meme body / les noms des règles changent ainsi que les tetes des règles
                for index in range(1, k + 1):
                    if index==k:
                        head = rule.head
                    else:
                        head = copies[rule.head, index]
                    body = rule.body
                    name = f"{rule.name}_{index}"
                    converted_rules.append(Rule(name, head, body))
                    
    # DU CM :
    # - for each **non-atomic** rule r = s <- p_1, , p_n:
    # - we create r_2, , r_k, where r_i = s^i <- p’_1, , p’_n and s^k = s and:
    #     - $p’_j = p_j$ if $p_j \in A$
    #     - $p’_j = p_j^{i-1}$ otherwise.
            else:
                # pour chaque règle non-atomique, on crée k-1 copies avec des bodies modifiés selon les hypothèses et les copies précédentes
                
                for index in range(2, k + 1):
                    if index == k:
                        head = rule.head
                    else:
                        head = copies[rule.head, index]
                        
                    premises_nouvelles = []
                    for premise in rule.body:
                        if premise in assumptions:
                            # si le prémisse est une hypothèse, on le garde tel quel
                            premises_nouvelles.append(premise)
                        else:
                            premises_nouvelles.append(copies[premise, index - 1])
                    body = tuple(premises_nouvelles)
                    name = f"{rule.name}_{index}"
                    converted_rules.append(Rule(name, head, body))
            



    return create_aba_framework(
        nouveau_literals,
        assumptions,
        framework.contraries,
        converted_rules,
        framework.preferences,
    )







def to_atomic_framework(framework: ABAFramework) -> ABAFramework:
    """Construit un framework atomique à partir des arguments minimaux."""
    arguments=create_arguments(framework)
    
    arg_trie = sorted(arguments, key=argument_key)
    
    rules = [
        Rule(f"r_{index}", argument.conclusion, argument.support)
        for index, argument in enumerate(arg_trie, start=1)
    ]
    return create_aba_framework(
        framework.literals,
        framework.assumptions,
        framework.contraries,
        rules,
        framework.preferences,
    )


if __name__ == "__main__":
    num_choisi = 4
    path = Path(__file__).parent / f"exemple_aba{num_choisi}.txt"
    framework = ABAFramework.from_file(path)
    framework.print_framework()
    circular = framework_is_circular(framework)
    statut_circular = "oui" if circular else "non"
    print(f"\nFramework circulaire (cycle de déduction) : {statut_circular}")
    framework_conv = (
        convert_to_non_circular_aba(framework) if circular else framework
    )
    framework_conv.print_framework()
    atomic_framework = to_atomic_framework(framework_conv)
    print("\n====== Atomic ABA Framework dérivé ======")
    atomic_framework.print_framework()
    
    