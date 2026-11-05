#!/usr/bin/env python3
"""Génère 720p/includes_AvdvDefaults.xml à partir d'un settings.xml de skin.

Usage :
    python3 _tools/make_defaults.py <settings.xml> <racine_skin>

<settings.xml> est le fichier de réglages de la skin d'une box déjà configurée :
    /storage/.kodi/userdata/addon_data/skin.rapier.avdvplus/settings.xml

Seuls les réglages différents des valeurs par défaut de Kodi sont repris :
booléens à true et chaînes non vides. Les états transitoires de l'interface
(onglet sélectionné, dialogue ouvert, etc.) sont ignorés.

Le fichier généré contient deux includes :
  - AvdvDefaultsOnLoad  : <onload> pour Startup.xml, appliqué une seule fois
                          (drapeau avdv.defaults.<version>) ;
  - AvdvDefaultsOnClick : <onclick> pour le bouton « Réinitialiser » des
                          réglages de la skin.
Changer DEFAULTS_VERSION force une nouvelle application sur les box existantes.
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

DEFAULTS_VERSION = "1"
FLAG = f"avdv.defaults.v{DEFAULTS_VERSION}"

# États d'interface, pas des préférences
TRANSIENT = {
    "brightnessvar", "categoryactionsdialog", "currentviewmode",
    "extendedinfodialog", "selectedexpandedbtn", "skinsettingscategory",
}
TRANSIENT_PREFIXES = ("expand", "avdv.defaults.")


def is_transient(sid: str) -> bool:
    s = sid.lower()
    return s in TRANSIENT or s.startswith(TRANSIENT_PREFIXES) or s == "expandedsettings"


def esc(value: str) -> str:
    return (value.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace('"', "&quot;"))


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, root = Path(sys.argv[1]), Path(sys.argv[2])
    bools, strings = [], []
    for st in ET.parse(src).getroot().iter("setting"):
        sid, typ, val = st.get("id", ""), st.get("type", ""), (st.text or "").strip()
        if not sid or is_transient(sid):
            continue
        if typ == "bool" and val == "true":
            bools.append(sid)
        elif typ == "string" and val:
            if any(c in val for c in ",()[]"):
                print(f"ignoré (caractères spéciaux) : {sid} = {val}")
                continue
            strings.append((sid, val))
    bools.sort()
    strings.sort()

    actions = [f"Skin.SetBool({b})" for b in bools]
    actions += [f"Skin.SetString({k},{esc(v)})" for k, v in strings]
    actions.append(f"Skin.SetBool({FLAG})")

    cond = f"!Skin.HasSetting({FLAG})"
    onload = "\n".join(f'\t\t<onload condition="{cond}">{a}</onload>' for a in actions)
    onclick = "\n".join(f"\t\t<onclick>{a}</onclick>" for a in actions)
    out = f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- Généré par _tools/make_defaults.py depuis {src.name} : ne pas éditer à la main. -->
<!-- Réglages par défaut de la skin ({len(bools)} options activées, {len(strings)} valeurs). -->
<includes>
	<include name="AvdvDefaultsOnLoad">
{onload}
	</include>

	<include name="AvdvDefaultsOnClick">
{onclick}
	</include>
</includes>
"""
    dest = root / "720p" / "includes_AvdvDefaults.xml"
    dest.write_text(out, encoding="utf-8")
    print(f"{dest} : {len(bools)} booléens, {len(strings)} chaînes, drapeau {FLAG}")


if __name__ == "__main__":
    main()
