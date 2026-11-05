# Outils de développement (non inclus dans le zip)

Exécuter depuis la racine du dépôt :

| Script | Rôle |
|---|---|
| `make_flags.py .` | Génère les drapeaux `hdr10plus.png`, `hdrvivid.png` et `flagbox.png` (thèmes default et white) à partir de `hdr10.png`. |
| `patch_mediaflags.py .` | Adapte `720p/includes_MediaFlags.xml` de Rapier aux codecs et types HDR d'avdvplus (à appliquer sur le fichier d'origine de Rapier). |
| `kodi_skin_lint.py . --kodi-colors <xbmc>/system/colors.xml` | Contrôle statique : XML, includes, variables, polices, couleurs, textures, chaînes, ids. |
| `build_zip.py . <dossier_sortie> --exclude themes --exclude _tools --exclude .github` | Construit `skin.rapier.avdvplus-<version>.zip` installable depuis Kodi. |

Les thèmes `themes/` (orange, red, flat) ne sont pas inclus : ils doivent être compilés en `.xbt` avec TexturePacker.
