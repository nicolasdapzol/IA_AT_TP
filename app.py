import os
from pathlib import Path

from flask import Flask, render_template, request

from aba_gen_nico import ABA_generator

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
SAMPLE_PATH = Path(__file__).with_name("exemple_aba3.txt")


def framework_details(framework):
    return {
        "literals": sorted(framework.getLiterals()),
        "assumptions": sorted(framework.getAssumptions()),
        "contraries": sorted(framework.getContraries().items()),
        "rules": [
            {"name": rule.name, "head": rule.head, "body": list(rule.body)}
            for rule in framework.getRules()
        ],
        "preferences": sorted(framework.getPreferences()),
    }


def calculate(text, convert=False):
    framework = ABA_generator().from_text(text)
    framework.createArguments()
    framework.createAttacks()

    arguments = sorted(framework.arguments, key=lambda argument: argument.name)
    attacks = [
        {
            "attacker": attacker.name,
            "target": target.name,
            "kind": kind,
        }
        for attacker, target, kind in framework.attaques
    ]
    result = {
        "framework": framework_details(framework),
        "arguments": [
            {
                "name": argument.name,
                "conclusion": argument.conclusion,
                "support": sorted(argument.support),
            }
            for argument in arguments
        ],
        "attacks": attacks,
    }

    if convert:
        converted = framework.transformeToNonCircular()
        converted.createArguments()
        converted.createAttacks()
        result["conversion"] = {
            "framework": framework_details(converted),
            "arguments": [
                {
                    "name": argument.name,
                    "conclusion": argument.conclusion,
                    "support": sorted(argument.support),
                }
                for argument in sorted(
                    converted.arguments, key=lambda argument: argument.name
                )
            ],
            "attacks": [
                {
                    "attacker": attacker.name,
                    "target": target.name,
                    "kind": kind,
                }
                for attacker, target, kind in converted.attaques
            ],
        }

    return result


def read_form_input():
    uploaded = request.files.get("framework_file")
    if uploaded and uploaded.filename:
        try:
            return uploaded.read().decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("Le fichier doit être encodé en UTF-8.") from error
    return request.form.get("framework_text", "")


@app.route("/", methods=["GET", "POST"])
def index():
    text = SAMPLE_PATH.read_text(encoding="utf-8")
    result = None
    error = None
    mode = "generate"

    if request.method == "POST":
        try:
            text = read_form_input()
            mode = request.form.get("mode", "generate")
            if not text.strip():
                raise ValueError("Le framework ABA est vide.")
            result = calculate(text, convert=mode == "convert")
        except (TypeError, ValueError, KeyError) as exception:
            error = str(exception) or "Le framework n'a pas pu être analysé."

    return render_template(
        "index.html", text=text, result=result, error=error, mode=mode
    )


@app.errorhandler(413)
def upload_too_large(_error):
    return render_template(
        "index.html",
        text="",
        result=None,
        error="Le fichier dépasse la taille maximale de 64 Ko.",
        mode="generate",
    ), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
