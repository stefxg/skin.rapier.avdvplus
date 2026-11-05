# Outils de développement (non inclus dans le zip)

Exécuter depuis la racine du dépôt :

| Script | Rôle |
|---|---|
| `make_flags.py .` | Génère les drapeaux `hdr10plus.png`, `hdrvivid.png` et `flagbox.png` (thèmes default et white) à partir de `hdr10.png`. |
| `patch_mediaflags.py .` | Adapte `720p/includes_MediaFlags.xml` de Rapier aux codecs et types HDR d'avdvplus (à appliquer sur le fichier d'origine de Rapier). |
| `kodi_skin_lint.py . --kodi-colors <xbmc>/system/colors.xml` | Contrôle statique : XML, includes, variables, polices, couleurs, textures, chaînes, ids. |
| `build_zip.py . <dossier_sortie> --exclude themes --exclude _tools --exclude .github` | Construit `skin.rapier.avdvplus-<version>.zip` installable depuis Kodi. |

Les thèmes `themes/` (orange, red, flat) ne sont pas inclus : ils doivent être compilés en `.xbt` avec TexturePacker.
| `publish_repo.py . <worktree_branche_repo>` | Génère le dépôt Kodi (addons.xml, md5, zips, icônes) à publier sur la branche `repo`. |
| `make_defaults.py <settings.xml> .` | Régénère `720p/includes_AvdvDefaults.xml` (réglages par défaut de la skin) depuis le `settings.xml` d'une box configurée (`/storage/.kodi/userdata/addon_data/skin.rapier.avdvplus/settings.xml`). Incrémenter `DEFAULTS_VERSION` pour réappliquer sur les box existantes. |

## Dépôt Kodi
- Add-on dépôt : `_repo/repository.stefxg/` (id `repository.stefxg`).
- Données servies par `https://raw.githubusercontent.com/stefxg/skin.rapier.avdvplus/repo/` (branche `repo`, générée).
- Publication d'une version : incrémenter `version` dans `addon.xml` (master), committer, puis
  `python3 _tools/publish_repo.py . <worktree repo>` et committer / pousser la branche `repo`.
