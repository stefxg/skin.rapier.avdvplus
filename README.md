# Rapier avdvplus

Portage personnel de la skin **Rapier** (Scarfa & Gade) pour **Kodi 21 Omega** sous
**CoreELEC avdvplus** (Amlogic, testé pour Ugoos AM6B+ / S922X).

- Skin d'origine : Rapier 13.0.14, https://github.com/gade01/Rapier, créée par **Scarfa et Gade**.
- Cible : CoreELEC avdvplus (https://github.com/avdvplus/Builds), fork Kodi 21.3 `aml-4.9-21.3-cpm`.
- Usage : **personnel, non commercial**.
- Identifiant : `skin.rapier.avdvplus` (s'installe à côté de Rapier ; ses réglages sont indépendants).

## Ce que change ce portage

### Phase 1 : compatibilité Kodi 21 Omega
- `xbmc.gui` 5.17.0.
- La fenêtre Favoris (`DialogFavourites.xml`, supprimée en v21) est remplacée par `FavouritesBrowser`.
- Fiche vidéo : boutons **Versions** (id 14) et **Extras** (id 15). L'ancien bouton « bande-annonce fenêtrée » passe de l'id 15 à l'id 216.
- Nouvelles fenêtres : `DialogVideoManager.xml` (gestion des versions et extras) et `DialogFullScreenInfo.xml`.
- `ListItem.Episodes` (inexistant) est remplacé par `ListItem.Property(TotalEpisodes)`.
- Les tests de batterie sont retirés : `System.BatteryLevel` n'existe pas dans avdvplus.

### Phase 2 : fonctions avdvplus (en cours)
- **Logos HDR** : HDR10, HDR10+ (nouveau), HLG, HDR Vivid (nouveau).
  - Le type principal et le type alternatif sont affichés : `ListItem.HdrTypeAlt`, et pendant la lecture `video.source.additional.hdr.type`.
- **Badge du profil Dolby Vision** (P5, P7, P8.1…) dans les listes, la fiche et la lecture.
  - Pendant la lecture, un badge FEL / MEL s'y ajoute.
- **Codecs audio avdvplus** reconnus : `truehd_atmos`, `eac3_ddp_atmos`, `dtshd_ma_x`, `dtshd_ma_x_imax`, `dts_es`, `dts_96_24`, `dts_express`, `pcm_*`, ainsi que `ListItem.AudioProfile` (Atmos, DTS:X, DTS-ES).
- **Panneau avdvplus dans les informations de lecture**, en trois colonnes :
  - Source vidéo / HDR10 : format, couleurs, MaxCLL/MaxFALL, mastering, bandes noires, débit instantané.
  - Dolby Vision : profil (et profil source si converti), codec, couches RPU/BL/EL, métadonnées CM, L6, L1, L5.
  - Sortie Amlogic : mode d'affichage, EOTF/gamut, VS10, format de pixel, fps et images perdues, HDR de l'écran, tampons.
- Réglages (Réglages de la skin > Médias > avdvplus) : masquer le badge du profil DV, masquer le panneau avdvplus.

Sur un Kodi standard (hors avdvplus), les infolabels propres à avdvplus sont vides et les éléments correspondants restent masqués.

## Installation
1. Kodi > Paramètres > Extensions > **Installer depuis un fichier zip** > `skin.rapier.avdvplus-<version>.zip`.
2. Les dépendances (`script.favourites`, `script.embuary.helper`, `resource.images.studios.white`) s'installent depuis le dépôt officiel Kodi.
3. Paramètres > Interface > Skin > **Rapier avdvplus**.

## Limites connues
- Les thèmes de couleur *orange / red / flat* (dossier `themes/`) doivent être compilés en `.xbt` (TexturePacker) pour être sélectionnables. Ils ne sont pas inclus dans le zip ; seul le thème par défaut est disponible.
- `script.embuary.helper` et `script.favourites` ne sont plus maintenus (branche Matrix du dépôt). Ils restent installables sur Omega.

## Crédits et licence
Rapier © **Scarfa** et **Gade**. Ce portage reprend leur travail sous la même licence :
[Creative Commons BY-NC-SA 3.0](http://creativecommons.org/licenses/by-nc-sa/3.0/) (voir `LICENSE.txt`).
Les noms des infolabels avdvplus proviennent de l'API du fork Kodi avdvplus. Aucun fichier XML de la skin avdvplus Estuary n'a été copié.
