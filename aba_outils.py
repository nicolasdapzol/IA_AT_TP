from __future__ import annotations

from pathlib import Path
from aba_args_attaques import Argument, Attack, argument_key, compute_attacks, create_arguments
from aba_generator import ABAFramework
from aba_conversion import (
    convert_to_non_circular_aba,
    framework_is_circular,
    is_atomic,
    to_atomic_framework,
)





def ToNonCircular(framework: ABAFramework) -> ABAFramework:
    """Convertit un framework circulaire en framework non circulaire."""
    if framework_is_circular(framework):
        return convert_to_non_circular_aba(framework)
    return framework


def charger_et_afficher_exemple(
    file_path: str | Path,
) -> tuple[ABAFramework, set[Argument], set[Attack]]:
    """Charge un exemple ABA, affiche son analyse et retourne les résultats.

    Le framework, les arguments et les attaques sont affichés dans un ordre
    stable pour faciliter la lecture et la comparaison entre plusieurs essais.
    Les erreurs de lecture ou de validation du fichier sont propagées à l'appelant.
    """
    # Chargement et validation du framework déclaré dans le fichier exemple.
    framework = ABAFramework.from_file(file_path)

    print("====== Framework ABA importé ======")
    framework.print_framework()
    circular = framework_is_circular(framework)
    statut_circularite = "oui" if circular else "non"
    print(f"\nFramework circulaire (cycle de déduction) : {statut_circularite}")
    # Les arguments et attaques sont calculés sur le framework analysé.
    framework_conv = framework

    if circular:
        framework_conv = ToNonCircular(framework)
        print("\n====== Framework ABA non circulaire dérivé ======")
        framework_conv.print_framework()

    # Les arguments et attaques sont calculés sur le framework analysé.
    arguments = create_arguments(framework_conv)
    attacks = compute_attacks(arguments, framework_conv)


    if is_atomic(framework_conv):
        print("\nFramework atomique : oui")
    else:
        print("\nFramework atomique : non, conversion en graphe atomique")
        atomic_framework = to_atomic_framework(framework_conv)
        print("\n====== Framework atomique dérivé ======")
        atomic_framework.print_framework()
        framework_conv = atomic_framework


    return framework, arguments, attacks





if __name__ == "__main__":
    # test fichier ABA en important et affichant son contenu
    # fichier exemple à tester
    charger_et_afficher_exemple(Path(__file__).parent / "exemple_aba1.txt")  
    framework_2, arguments_2, attaques_2 = charger_et_afficher_exemple(Path(__file__).parent / "exemple_aba2.txt")