#!/usr/bin/env python3
"""Construit <id>-<version>.zip installable via Kodi > Extensions > Installer depuis un fichier zip.
Usage : python3 build_zip.py <dossier_skin> [dossier_sortie] [--exclude chemin/relatif ...]
Le zip doit contenir UN dossier racine portant exactement l'id de l'add-on (ex. skin.monskin/addon.xml).
Exclut les fichiers de dev (.git, __pycache__, *.psd, *.xcf, Thumbs.db, .DS_Store)."""
import os, sys, zipfile
import xml.etree.ElementTree as ET

args = sys.argv[1:]
extra = set()
while '--exclude' in args:
    i = args.index('--exclude'); extra.add(os.path.normpath(args[i + 1])); del args[i:i + 2]
src = os.path.abspath(args[0])
out = os.path.abspath(args[1] if len(args) > 1 else os.path.dirname(src))
root = ET.parse(os.path.join(src, 'addon.xml')).getroot()
aid, ver = root.get('id'), root.get('version')
EXCL_DIRS = {'.git', '.github', '__pycache__', '.mypy_cache', '.pytest_cache', '.idea', '.vscode'}
EXCL_EXT = ('.psd', '.xcf', '.pyc', '.pyo')
EXCL_FILES = {'Thumbs.db', '.DS_Store', '.gitignore'}
os.makedirs(out, exist_ok=True)
zpath = os.path.join(out, f'{aid}-{ver}.zip')
n = 0
with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
    for dp, dn, fn in os.walk(src):
        dn[:] = [d for d in dn if d not in EXCL_DIRS and os.path.normpath(os.path.relpath(os.path.join(dp, d), src)) not in extra]
        for f in fn:
            if f in EXCL_FILES or f.endswith(EXCL_EXT):
                continue
            full = os.path.join(dp, f)
            z.write(full, os.path.join(aid, os.path.relpath(full, src)))
            n += 1
print(f'{zpath} ({n} fichiers)')
