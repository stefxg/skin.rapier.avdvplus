#!/usr/bin/env python3
"""Construit le contenu du dépôt Kodi (branche `repo`) à partir de la branche master.

Usage : python3 _tools/publish_repo.py <racine_du_depot_git> <dossier_sortie>

Produit dans <dossier_sortie> :
  addons.xml, addons.xml.md5
  skin.rapier.avdvplus/skin.rapier.avdvplus-<version>.zip + resources/ (icône, fanart, captures) + changelog-<version>.txt
  repository.stefxg/repository.stefxg-<version>.zip + icon.png
Seule la dernière version de chaque add-on est conservée (le dossier de sortie est recréé).
La branche `repo` est ensuite servie par https://raw.githubusercontent.com/stefxg/skin.rapier.avdvplus/repo/
"""
import hashlib, os, re, shutil, subprocess, sys
import xml.etree.ElementTree as ET

root = os.path.abspath(sys.argv[1])
out = os.path.abspath(sys.argv[2])
here = os.path.dirname(os.path.abspath(__file__))
build_zip = os.path.join(here, 'build_zip.py')

ADDONS = [
    # (dossier source, exclusions passées à build_zip)
    (root, ['themes', '_tools', '_repo', '.github']),
    (os.path.join(root, '_repo', 'repository.stefxg'), []),
]

if os.path.isdir(out):
    for x in os.listdir(out):
        if x == '.git':
            continue
        p = os.path.join(out, x)
        shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
os.makedirs(out, exist_ok=True)

entries = []
for src, excl in ADDONS:
    axml = os.path.join(src, 'addon.xml')
    tree = ET.parse(axml)
    aid, ver = tree.getroot().get('id'), tree.getroot().get('version')
    dst = os.path.join(out, aid)
    os.makedirs(dst, exist_ok=True)
    cmd = [sys.executable, '-I', build_zip, src, dst]
    for e in excl:
        cmd += ['--exclude', e]
    subprocess.run(cmd, check=True)
    # assets affichés par le navigateur de dépôts de Kodi : <datadir>/<id>/<chemin de l'asset>
    meta = tree.getroot().find("extension[@point='xbmc.addon.metadata']")
    assets = meta.find('assets') if meta is not None else None
    if assets is not None:
        for a in assets:
            if a.text:
                s = os.path.join(src, a.text)
                if os.path.isfile(s):
                    d = os.path.join(dst, a.text)
                    os.makedirs(os.path.dirname(d), exist_ok=True)
                    shutil.copy2(s, d)
    if os.path.isfile(os.path.join(src, 'changelog.txt')):
        shutil.copy2(os.path.join(src, 'changelog.txt'), os.path.join(dst, f'changelog-{ver}.txt'))
    txt = open(axml, encoding='utf-8').read()
    txt = re.sub(r'^\s*<\?xml[^>]*\?>\s*', '', txt)
    entries.append(txt.strip())
    print(f'{aid} {ver}')

addons = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n' + '\n\n'.join(entries) + '\n</addons>\n'
ET.fromstring(addons.encode('utf-8'))  # contrôle : XML bien formé
with open(os.path.join(out, 'addons.xml'), 'w', encoding='utf-8') as f:
    f.write(addons)
with open(os.path.join(out, 'addons.xml.md5'), 'w') as f:
    f.write(hashlib.md5(addons.encode('utf-8')).hexdigest())
with open(os.path.join(out, 'README.md'), 'w', encoding='utf-8') as f:
    f.write('# Dépôt Kodi stefxg\n\nBranche générée automatiquement par `_tools/publish_repo.py` (branche master). Ne pas modifier à la main.\n\n'
            'URL du dépôt : https://raw.githubusercontent.com/stefxg/skin.rapier.avdvplus/repo/\n')
print('addons.xml + md5 OK ->', out)
