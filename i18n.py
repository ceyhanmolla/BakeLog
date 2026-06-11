import json
import os
from flask import request, session

LOCALES_DIR = os.path.join(os.path.dirname(__file__), "locales")

_translations = {}


def load_translations():
    for lang in ["tr", "en", "de"]:
        path = os.path.join(LOCALES_DIR, f"{lang}.json")
        with open(path, "r", encoding="utf-8") as f:
            _translations[lang] = json.load(f)


def get_lang():
    lang = request.args.get("lang", "")
    if lang in _translations:
        session["lang"] = lang
        return lang
    if "lang" in session and session["lang"] in _translations:
        return session["lang"]
    accept = request.headers.get("Accept-Language", "tr")
    for l in ["tr", "en", "de"]:
        if l in accept:
            return l
    return "tr"


def t(key, **kwargs):
    lang = get_lang()
    val = _translations.get(lang, {}).get(key, key)
    if kwargs:
        val = val.format(**kwargs)
    return val
