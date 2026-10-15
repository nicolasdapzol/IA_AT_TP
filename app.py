from __future__ import annotations

import ipaddress
import os
import socket
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from flask import Flask, jsonify, render_template, request

from aba_args_attaques import argument_key, compute_attacks, create_arguments
from aba_conversion import (
    convert_to_non_circular_aba,
    framework_is_circular,
    is_atomic,
    to_atomic_framework,
)
from aba_generator import ABAFramework


ROOT = Path(__file__).resolve().parent
MAX_SOURCE_BYTES = 64 * 1024
MAX_REQUEST_BYTES = 144 * 1024
EXAMPLES = {
    f"exemple_aba{index}.txt": ROOT / f"exemple_aba{index}.txt"
    for index in range(1, 6)
}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_REQUEST_BYTES


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, url):
        return None


def parse_framework_text(text: str, source_name: str = "éditeur") -> ABAFramework:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Le contenu du framework est vide.")
    try:
        encoded = text.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError("Le contenu doit être encodé en UTF-8.") from error
    if len(encoded) > MAX_SOURCE_BYTES:
        raise ValueError("Le framework dépasse la limite de 64 Ko.")
    if "\x00" in text:
        raise ValueError("Le contenu contient un caractère nul invalide.")

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        ) as temporary_file:
            temporary_file.write(text.lstrip("\ufeff"))
            temporary_path = Path(temporary_file.name)
        return ABAFramework.from_file(temporary_path)
    except ValueError as error:
        message = str(error)
        if temporary_path is not None:
            message = message.replace(temporary_path.name, source_name)
        raise ValueError(message) from error
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def framework_source(framework: ABAFramework) -> str:
    lines = [
        f"L: [{', '.join(sorted(framework.literals))}]",
        f"A: [{', '.join(sorted(framework.assumptions))}]",
    ]
    lines.extend(
        f"C({assumption}): {contrary}"
        for assumption, contrary in sorted(framework.contraries.items())
    )
    lines.extend(
        f"[{rule.name}]: {rule.head} <- {', '.join(rule.body)}"
        for rule in framework.rules
    )
    if framework.preferences:
        preferences = ", ".join(
            f"{preferred} > {less_preferred}"
            for preferred, less_preferred in sorted(framework.preferences)
        )
        lines.append(f"PREF: {preferences}")
    return "\n".join(lines)


def framework_payload(framework: ABAFramework) -> dict:
    return {
        "display": framework.to_text(),
        "source": framework_source(framework),
        "stats": {
            "literals": len(framework.literals),
            "assumptions": len(framework.assumptions),
            "rules": len(framework.rules),
            "preferences": len(framework.preferences),
        },
    }


def _argument_payload(argument) -> dict:
    support = sorted(argument.support)
    return {
        "conclusion": argument.conclusion,
        "support": support,
        "label": f"{argument.conclusion} [{', '.join(support) if support else '∅'}]",
    }


def _analyze(framework: ABAFramework, action: str) -> dict:
    result = {
        "action": action,
        "input_framework": framework_payload(framework),
        "framework": framework_payload(framework),
    }

    if action == "arguments":
        arguments = sorted(create_arguments(framework), key=argument_key)
        attacks = sorted(
            compute_attacks(arguments, framework),
            key=lambda attack: (
                argument_key(attack.attacker),
                argument_key(attack.target),
                attack.kind,
            ),
        )
        result["arguments"] = [_argument_payload(argument) for argument in arguments]
        result["attacks"] = [
            {
                "attacker": _argument_payload(attack.attacker),
                "target": _argument_payload(attack.target),
                "kind": attack.kind,
            }
            for attack in attacks
        ]
    elif action == "properties":
        result["properties"] = {
            "atomic": is_atomic(framework),
            "circular": framework_is_circular(framework),
        }
    elif action == "noncircular":
        circular = framework_is_circular(framework)
        converted = convert_to_non_circular_aba(framework) if circular else framework
        if framework_is_circular(converted):
            raise ValueError("La transformation n'a pas supprimé tous les cycles.")
        result["transformed"] = circular
        result["framework"] = framework_payload(converted)
        result["properties"] = {
            "atomic": is_atomic(converted),
            "circular": False,
        }
    elif action == "atomic":
        circular = framework_is_circular(framework)
        converted = convert_to_non_circular_aba(framework) if circular else framework
        converted = to_atomic_framework(converted)
        if not is_atomic(converted):
            raise ValueError("La transformation n'a pas produit un framework atomique.")
        result["transformed"] = True
        result["framework"] = framework_payload(converted)
        result["properties"] = {
            "atomic": True,
            "circular": framework_is_circular(converted),
        }
    else:
        raise ValueError("Action inconnue.")

    return result


def _json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/healthz")
def healthcheck():
    return jsonify({"status": "ok"})


@app.get("/api/examples")
def list_examples():
    return jsonify(
        [
            {"name": name, "available": path.is_file()}
            for name, path in EXAMPLES.items()
        ]
    )


@app.get("/api/examples/<filename>")
def get_example(filename: str):
    path = EXAMPLES.get(filename)
    if path is None or not path.is_file():
        return _json_error("Cet exemple n'existe pas.", 404)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return _json_error("L'exemple ne peut pas être lu.", 500)
    return jsonify({"name": filename, "text": text})


@app.post("/api/validate")
def validate_framework():
    data = request.get_json(silent=True) or {}
    try:
        framework = parse_framework_text(data.get("text"), data.get("name", "éditeur"))
    except (TypeError, ValueError) as error:
        return _json_error(str(error))
    return jsonify({"ok": True, "framework": framework_payload(framework)})


@app.post("/api/analyze")
def analyze_framework():
    data = request.get_json(silent=True) or {}
    try:
        framework = parse_framework_text(data.get("text"), data.get("name", "éditeur"))
        result = _analyze(framework, data.get("action", ""))
    except (TypeError, ValueError) as error:
        return _json_error(str(error))
    return jsonify({"ok": True, **result})


def _validate_public_url(url: str) -> None:
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as error:
        raise ValueError("L'URL est invalide.") from error
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise ValueError("Utilisez une URL HTTP(S) publique, sans identifiants.")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, port or (443 if parsed.scheme == "https" else 80))
    except OSError as error:
        raise ValueError("Le nom d'hôte de l'URL est introuvable.") from error
    if not addresses or any(
        not ipaddress.ip_address(address[4][0]).is_global for address in addresses
    ):
        raise ValueError("L'URL doit pointer vers une adresse IP publique.")


@app.post("/api/import-url")
def import_url():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "")
    if not isinstance(url, str):
        return _json_error("L'URL est invalide.")
    try:
        _validate_public_url(url)
        opener = build_opener(_NoRedirectHandler())
        response = opener.open(
            Request(url, headers={"User-Agent": "ABA-Framework-Viewer/1.0"}),
            timeout=5,
        )
        with response:
            if response.status < 200 or response.status >= 300:
                return _json_error(f"Réponse HTTP non valide : {response.status}.")
            content = response.read(MAX_SOURCE_BYTES + 1)
        if len(content) > MAX_SOURCE_BYTES:
            return _json_error("Le framework téléchargé dépasse la limite de 64 Ko.")
        text = content.decode("utf-8-sig")
    except HTTPError as error:
        return _json_error(f"Réponse HTTP non valide : {error.code}.")
    except (URLError, TimeoutError, OSError) as error:
        return _json_error(f"Impossible de télécharger le framework : {error}.")
    except (UnicodeDecodeError, ValueError) as error:
        return _json_error(str(error) or "Le fichier doit être encodé en UTF-8.")
    return jsonify({"ok": True, "text": text})


@app.errorhandler(413)
def request_too_large(_error):
    return _json_error("La requête dépasse la limite autorisée.", 413)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))