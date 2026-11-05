#!/usr/bin/env python3
"""Publie l'add-on de ce dépôt dans le dépôt Kodi stefxg (branche `repo`).

Usage : python3 _tools/publish_repo.py <racine_du_depot_git> <dossier_sortie>

<dossier_sortie> est un clone de la branche `repo` de stefxg/skin.rapier.avdvplus,
servie par https://raw.githubusercontent.com/stefxg/skin.rapier.avdvplus/repo/
Plusieurs add-ons y cohabitent (skin.rapier.avdvplus, skin.next-rapier.avdvplus,
repository.stefxg) : ce script ne remplace que les dossiers des add-ons qu'il publie,
puis régénère addons.xml à partir de tous les <id>/addon.xml présents.

Pour chaque add-on publié :
  <id>/<id>-<version>.zip, <id>/addon.xml, resources/ (icône, fanart, captures),
  changelog-<version>.txt. Seule la dernière version est conservée.
"""
import hashlib, os, re, shutil, subprocess, sys
import xml.etree.ElementTree as ET

root = os.path.abspath(sys.argv[1])
out = os.path.abspath(sys.argv[2])
here = os.path.dirname(os.path.abspath(__file__))
build_zip = os.path.join(here, 'build_zip.py')

ADDONS = [(root, ['themes', '_tools', '_repo', '.github'])]
repo_addon = os.path.join(root, '_repo', 'repository.stefxg')
if os.path.isfile(os.path.join(repo_addon, 'addon.xml')):
    ADDONS.append((repo_addon, []))

os.makedirs(out, exist_ok=True)
for src, excl in ADDONS:
    axml = os.path.join(src, 'addon.xml')
    tree = ET.parse(axml)
    aid, ver = tree.getroot().get('id'), tree.getroot().get('version')
    dst = os.path.join(out, aid)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    cmd = [sys.executable, '-I', build_zip, src, dst]
    for e in excl:
        cmd += ['--exclude', e]
    subprocess.run(cmd, check=True)
    shutil.copy2(axml, os.path.join(dst, 'addon.xml'))
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
    print(f'publié : {aid} {ver}')

entries, ids = [], []
for d in sorted(os.listdir(out)):
    axml = os.path.join(out, d, 'addon.xml')
    if os.path.isfile(axml):
        txt = open(axml, encoding='utf-8').read()
        txt = re.sub(r'^\s*<\?xml[^>]*\?>\s*', '', txt)
        entries.append(txt.strip())
        ids.append(d)

addons = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n' + '\n\n'.join(entries) + '\n</addons>\n'
ET.fromstring(addons.encode('utf-8'))  # contrôle : XML bien formé
with open(os.path.join(out, 'addons.xml'), 'w', encoding='utf-8') as f:
    f.write(addons)
with open(os.path.join(out, 'addons.xml.md5'), 'w') as f:
    f.write(hashlib.md5(addons.encode('utf-8')).hexdigest())
with open(os.path.join(out, 'README.md'), 'w', encoding='utf-8') as f:
    f.write('# Dépôt Kodi stefxg\n\nBranche générée automatiquement par `_tools/publish_repo.py`. Ne pas modifier à la main.\n\n'
            'URL du dépôt : https://raw.githubusercontent.com/stefxg/skin.rapier.avdvplus/repo/\n\nAdd-ons :\n'
            + ''.join(f'- {i}\n' for i in ids))
print('addons.xml + md5 OK ->', out, '|', ', '.join(ids))
