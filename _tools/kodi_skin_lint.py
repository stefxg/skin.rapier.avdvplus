#!/usr/bin/env python3
"""kodi_skin_lint.py — vérifications statiques d'une skin Kodi (sans lancer Kodi).

Usage : python3 kodi_skin_lint.py <dossier_skin> [--kodi-colors chemin/system/colors.xml] [--strict]

Contrôles :
  - XML bien formé (tous les .xml / .xsp) ;
  - addon.xml : id, version, import xbmc.gui, dossiers <res> existants, Includes.xml / Font.xml / font13 présents ;
  - includes : <include>X</include>, <include content="X"> → définis ; $PARAM[x] → déclarés dans l'include ;
  - $VAR[...] / $ESCVAR[...] → <variable> ; $EXP[...] → <expression> ; $MAP / $ESCMAP → <map> ;
  - <font> → défini dans Font.xml ; couleurs nommées → colors/defaults.xml (+ couleurs système si fournies) ;
  - textures statiques → présentes dans media/ (ou thème) ;
  - $LOCALIZE[31000-31999] (+ labels numériques de cette plage) → présents dans strings.po en_gb ;
  - après expansion des includes : ids en double, defaultcontrol / navigation numérique vers un id inexistant.
Les includes conditionnels sont tous développés (les deux branches) : un avertissement de navigation peut donc être un faux positif.
"""
import os, re, sys, glob
import xml.etree.ElementTree as ET

args = [a for a in sys.argv[1:] if not a.startswith('--')]
opts = sys.argv[1:]
if not args:
    print(__doc__); sys.exit(2)
SKIN = os.path.abspath(args[0])
STRICT = '--strict' in opts
SYS_COLORS = None
if '--kodi-colors' in opts:
    SYS_COLORS = opts[opts.index('--kodi-colors') + 1]

errors, warnings = [], []
def err(f, m): errors.append(f'ERREUR  {os.path.relpath(f, SKIN)}: {m}')
def warn(f, m): warnings.append(f'ATTENTION {os.path.relpath(f, SKIN)}: {m}')

def parse(path):
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as e:
        err(path, f'XML mal formé : {e}')
    except OSError as e:
        err(path, f'illisible : {e}')
    return None

# ---------- 1. bien-formé ----------
for p in glob.glob(os.path.join(SKIN, '**', '*.xml'), recursive=True) + glob.glob(os.path.join(SKIN, '**', '*.xsp'), recursive=True):
    parse(p)

# ---------- 2. addon.xml ----------
addon = parse(os.path.join(SKIN, 'addon.xml'))
xmldirs = []
if addon is not None:
    if not addon.get('id', '').startswith('skin.'):
        warn(os.path.join(SKIN, 'addon.xml'), "l'id devrait commencer par 'skin.'")
    if not re.match(r'^\d+\.\d+\.\d+', addon.get('version', '')):
        err(os.path.join(SKIN, 'addon.xml'), 'version absente ou non sémantique (x.y.z)')
    gui = [i for i in addon.iter('import') if i.get('addon') == 'xbmc.gui']
    if not gui:
        err(os.path.join(SKIN, 'addon.xml'), "pas d'<import addon=\"xbmc.gui\">")
    ext = [e for e in addon.iter('extension') if e.get('point') == 'xbmc.gui.skin']
    if not ext:
        err(os.path.join(SKIN, 'addon.xml'), 'pas d\'<extension point="xbmc.gui.skin">')
    else:
        res = ext[0].findall('res')
        if not res:
            err(os.path.join(SKIN, 'addon.xml'), 'aucun <res>')
        if not any(r.get('default') == 'true' for r in res):
            warn(os.path.join(SKIN, 'addon.xml'), 'aucun <res default="true">')
        for r in res:
            d = os.path.join(SKIN, r.get('folder', ''))
            if not os.path.isdir(d):
                err(os.path.join(SKIN, 'addon.xml'), f"dossier <res folder=\"{r.get('folder')}\"> introuvable")
            elif d not in xmldirs:
                xmldirs.append(d)
if not xmldirs:
    xmldirs = [os.path.join(SKIN, 'xml')]
XML = xmldirs[0]


def ci_path(path):
    """Résolution comme Kodi : nom exact, sinon nom en minuscules (FS sensibles à la casse)."""
    if os.path.exists(path):
        return path
    d, f = os.path.split(path)
    alt = os.path.join(d, f.lower())
    if os.path.exists(alt):
        return alt
    if os.path.isdir(d):
        for x in os.listdir(d):
            if x.lower() == f.lower():
                return os.path.join(d, x)
    return path
# ---------- 3. collecte des définitions ----------
includes, variables, expressions, maps, constants, defaults = {}, set(), set(), set(), set(), set()
def load_includes(path, seen):
    if path in seen or not os.path.exists(path):
        if not os.path.exists(path):
            err(path, 'fichier d\'includes introuvable')
        return
    seen.add(path)
    root = parse(path)
    if root is None:
        return
    for el in root:
        if el.tag == 'include' and el.get('file'):
            load_includes(ci_path(os.path.join(os.path.dirname(path), el.get('file'))), seen)
        elif el.tag == 'include' and el.get('name'):
            if el.get('name') in includes:
                warn(path, f"include '{el.get('name')}' défini plusieurs fois (le dernier gagne)")
            includes[el.get('name')] = (el, path)
        elif el.tag == 'variable':
            variables.add(el.get('name'))
        elif el.tag == 'expression':
            expressions.add(el.get('name'))
        elif el.tag == 'map':
            maps.add(el.get('name'))
        elif el.tag == 'constant':
            constants.add(el.get('name'))
        elif el.tag == 'default':
            defaults.add(el.get('type'))
inc_root = ci_path(os.path.join(XML, 'Includes.xml'))
if not os.path.exists(inc_root):
    err(inc_root, 'Includes.xml absent (obligatoire)')
load_includes(inc_root, set())

fonts = set()
FONTX = ci_path(os.path.join(XML, 'Font.xml'))
fx = parse(FONTX) if os.path.exists(FONTX) else None
if fx is None:
    err(os.path.join(XML, 'Font.xml'), 'Font.xml absent')
else:
    for fs in fx.iter('fontset'):
        names = {f.findtext('name') for f in fs.iter('font')}
        if 'font13' not in names:
            err(os.path.join(XML, 'Font.xml'), f"fontset '{fs.get('id')}' sans font13 (obligatoire)")
        fonts |= names

colors = set()
cdir = os.path.join(SKIN, 'colors')
cd = parse(os.path.join(cdir, 'defaults.xml')) if os.path.exists(os.path.join(cdir, 'defaults.xml')) else None
if cd is not None:
    colors |= {c.get('name') for c in cd.iter('color')}
if SYS_COLORS and os.path.exists(SYS_COLORS):
    sc = parse(SYS_COLORS)
    if sc is not None:
        colors |= {c.get('name') for c in sc.iter('color')}
else:
    colors |= {'white', 'black', 'red', 'green', 'blue', 'yellow', 'grey', 'gray', 'orange', 'transparent'}

strings = set()
po = os.path.join(SKIN, 'language', 'resource.language.en_gb', 'strings.po')
if os.path.exists(po):
    strings = {int(m) for m in re.findall(r'msgctxt\s+"#(\d+)"', open(po, encoding='utf-8').read())}
else:
    warn(po, 'strings.po en_gb absent')

media = set()
for base in [os.path.join(SKIN, 'media')] + glob.glob(os.path.join(SKIN, 'themes', '*')):
    for p in glob.glob(os.path.join(base, '**', '*'), recursive=True):
        if os.path.isfile(p):
            media.add(os.path.relpath(p, base).replace(os.sep, '/').lower())

# ---------- 4. expansion des includes ----------
PARAM_RE = re.compile(r'\$PARAM\[([^\]]+)\]')
def subst(text, params):
    if text is None:
        return None
    return PARAM_RE.sub(lambda m: params.get(m.group(1), m.group(0)), text)

def expand(el, params, fpath, depth=0):
    """Retourne une copie de el où les <include> sont remplacés par leur contenu."""
    out = ET.Element(el.tag, {k: subst(v, params) for k, v in el.attrib.items()})
    out.text, out.tail = subst(el.text, params), subst(el.tail, params)
    for ch in el:
        if ch.tag == 'include' and not ch.get('file'):
            name = ch.get('content') or (ch.text or '').strip()
            name = subst(name, params)
            if name not in includes:
                err(fpath, f"include '{name}' non défini")
                continue
            if depth > 40:
                err(fpath, f"récursion d'includes trop profonde ({name})")
                continue
            inc, ipath = includes[name]
            # paramètres : défauts de l'include, puis valeurs passées
            p2 = {}
            declared = set()
            for pd in inc.findall('param'):
                declared.add(pd.get('name'))
                if pd.get('default') is not None:
                    p2[pd.get('name')] = pd.get('default')
                elif pd.text is not None or pd.get('value') is not None:
                    p2[pd.get('name')] = pd.get('value') if pd.get('value') is not None else (pd.text or '')
            for pa in ch.findall('param'):
                v = pa.get('value') if pa.get('value') is not None else (pa.text or '')
                p2[pa.get('name')] = subst(v, params)
            body = inc.find('definition')
            src = body if body is not None else inc
            for sub in src:
                if sub.tag == 'param':
                    continue
                # $PARAM non déclarés
                raw = ET.tostring(sub, encoding='unicode')
                for pn in set(PARAM_RE.findall(raw)):
                    if pn not in declared and pn not in p2:
                        warn(ipath, f"include '{name}' : $PARAM[{pn}] non déclaré ni fourni")
                out.append(expand(sub, p2, fpath, depth + 1))
        else:
            out.append(expand(ch, params, fpath, depth))
    return out

# ---------- 5. vérifications par fenêtre ----------
VAR_RE = re.compile(r'\$(?:ESC)?VAR\[([^\],]+)')
EXP_RE = re.compile(r'\$EXP\[([^\]]+)\]')
MAP_RE = re.compile(r'\$(?:ESC)?MAP\[([^\],]+)')
LOC_RE = re.compile(r'\$LOCALIZE\[(\d+)\]')
COLOR_TAGS = {'textcolor', 'focusedcolor', 'disabledcolor', 'selectedcolor', 'shadowcolor', 'invalidcolor', 'backgroundcolor'}
TEX_TAGS = {'texture', 'texturefocus', 'texturenofocus', 'alttexturefocus', 'alttexturenofocus', 'texturebg', 'lefttexture',
            'midtexture', 'righttexture', 'overlaytexture', 'texturesliderbackground', 'texturesliderbar', 'texturesliderbarfocus',
            'textureradioonfocus', 'textureradioonnofocus', 'textureradioofffocus', 'textureradiooffnofocus', 'textureup', 'texturedown',
            'textureupfocus', 'texturedownfocus', 'imagepath', 'bordertexture'}
NAV_TAGS = {'onup', 'ondown', 'onleft', 'onright', 'onback', 'defaultcontrol', 'pagecontrol'}

def is_color_literal(v):
    return re.fullmatch(r'[0-9A-Fa-f]{8}', v) or v.startswith('$') or v in colors

def check_tree(root, fpath, window=True):
    ids = {}
    navs = []
    for el in root.iter():
        txt = (el.text or '').strip()
        blob = txt + ' ' + ' '.join(el.attrib.values())
        for v in VAR_RE.findall(blob):
            if v not in variables:
                err(fpath, f"$VAR[{v}] : variable non définie")
        for v in EXP_RE.findall(blob):
            if v not in expressions:
                err(fpath, f"$EXP[{v}] : expression non définie")
        for v in MAP_RE.findall(blob):
            if v not in maps:
                err(fpath, f"$MAP[{v}] : map non définie")
        for v in LOC_RE.findall(blob):
            n = int(v)
            if 31000 <= n <= 31999 and strings and n not in strings:
                err(fpath, f"$LOCALIZE[{n}] absent de strings.po")
        if el.tag in ('label', 'label2', 'altlabel') and re.fullmatch(r'3\d{4}', txt) and strings and int(txt) not in strings and 31000 <= int(txt) <= 31999:
            err(fpath, f"<{el.tag}>{txt}</{el.tag}> absent de strings.po")
        if el.tag == 'font' and txt and not txt.startswith('$') and txt not in fonts:
            err(fpath, f"police '{txt}' absente de Font.xml")
        if el.tag in COLOR_TAGS and txt and not is_color_literal(txt):
            (err if STRICT else warn)(fpath, f"couleur '{txt}' non définie (colors/defaults.xml ou couleurs système)")
        if el.get('colordiffuse') and not is_color_literal(el.get('colordiffuse')):
            (err if STRICT else warn)(fpath, f"colordiffuse '{el.get('colordiffuse')}' non définie")
        if el.tag in TEX_TAGS and txt and not re.search(r'[\$:]|^/|^\\\\', txt):
            if txt.lower() not in media and el.tag != 'imagepath':
                warn(fpath, f"texture '{txt}' introuvable dans media/ (ou thèmes)")
        if el.tag == 'control' and el.get('id') and not el.get('id').startswith('$'):
            i = el.get('id')
            if i in ids:
                warn(fpath, f"id {i} utilisé par plusieurs contrôles ({ids[i]} et {el.get('type')})")
            ids[i] = el.get('type')
        if el.tag in NAV_TAGS and re.fullmatch(r'\d+', txt) and el.get('condition') is None:
            navs.append((el.tag, txt))
    if window:
        for tag, target in navs:
            if target not in ids:
                warn(fpath, f"<{tag}>{target}</{tag}> : aucun contrôle id={target} dans la fenêtre")

SKIP = {'includes.xml', 'font.xml', 'timers.xml'}
inc_files = {os.path.normcase(p) for _, p in includes.values()}
for p in sorted(glob.glob(os.path.join(XML, '*.xml'))):
    if os.path.basename(p).lower() in SKIP or os.path.normcase(p) in inc_files:
        continue
    root = parse(p)
    if root is None:
        continue
    if root.tag != 'window':
        if root.tag != 'includes':
            warn(p, f"racine <{root.tag}> inattendue (attendu <window>)")
        continue
    check_tree(expand(root, {}, p), p)
    if os.path.basename(p).lower().startswith('custom'):
        if not (root.get('id') or root.findtext('id')):
            err(p, 'fenêtre custom sans id (attribut id="11xx")')

# Includes jamais utilisés
used = set()
for p in glob.glob(os.path.join(XML, '*.xml')):
    t = open(p, encoding='utf-8', errors='ignore').read()
    used |= set(re.findall(r'<include(?:\s+condition="[^"]*")?>\s*([^<\s]+)\s*</include>', t))
    used |= set(re.findall(r'<include[^>]*content="([^"]+)"', t))
for n, (_, ip) in includes.items():
    if n not in used:
        warn(ip, f"include '{n}' jamais utilisé")

# Timers.xml
tp = os.path.join(XML, 'Timers.xml')
if os.path.exists(tp):
    tr = parse(tp)
    if tr is not None:
        for t in tr.iter('timer'):
            if not t.findtext('name'):
                err(tp, '<timer> sans <name>')
            if t.find('start') is None:
                warn(tp, f"timer '{t.findtext('name')}' sans <start> (démarrage manuel par Skin.TimerStart uniquement)")

from collections import Counter
for m, n in list(Counter(errors).items()) + list(Counter(warnings).items()):
    print(m + (f'  (×{n})' if n > 1 else ''))
print(f'\n{len(errors)} erreur(s), {len(warnings)} avertissement(s) — {len(includes)} includes, {len(variables)} variables, '
      f'{len(expressions)} expressions, {len(fonts)} polices, {len(colors)} couleurs, {len(media)} textures, {len(strings)} chaînes')
sys.exit(1 if errors else 0)
