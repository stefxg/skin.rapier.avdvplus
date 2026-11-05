#!/usr/bin/env python3
"""Adapte includes_MediaFlags.xml de Rapier aux codecs / HDR d'avdvplus (Kodi 21 CoreELEC fork).

- HDR : HDR10 / HDR10+ / HLG / HDR Vivid, type principal + type alternatif
  (ListItem.HdrTypeAlt ; pendant la lecture video.source.additional.hdr.type.raw).
- Dolby Vision : badge profil (P8.1, P7…) + FEL / MEL pendant la lecture.
- Audio : codecs avdvplus truehd_atmos, eac3_ddp_atmos, dtshd_ma_x(_imax), dts_es,
  dts_96_24, dts_express, pcm_s24le… + ListItem.AudioProfile (Atmos, DTS:X, DTS-ES).
Usage : python3 patch_mediaflags.py <skin_dir>
"""
import sys, os

skin = sys.argv[1]
p = os.path.join(skin, '720p', 'includes_MediaFlags.xml')
s = open(p, encoding='utf-8').read()

def rep(old, new, count=1):
    global s
    n = s.count(old)
    if n != count:
        sys.exit(f'motif trouvé {n} fois (attendu {count}) :\n{old}')
    s = s.replace(old, new)

def badge(label, visible, width=56):
    return f'''		<control type="group">
			<width>{width}</width>
			<height>35</height>
			<visible>{visible}</visible>
			<control type="image">
				<width>{width}</width>
				<height>35</height>
				<texture border="6">flagging/$VAR[MediaFlagTheme]/video/flagbox.png</texture>
			</control>
			<control type="label">
				<width>{width}</width>
				<height>35</height>
				<font>MediaFlagSubtitleFont</font>
				<textcolor>SelectedColor</textcolor>
				<align>center</align>
				<aligny>center</aligny>
				<label>[B]{label}[/B]</label>
			</control>
		</control>
'''

def image(desc, tex, width, visible):
    return f'''		<control type="image">
			<description>{desc}</description>
			<width>{width}</width>
			<height>35</height>
			<texture>flagging/$VAR[MediaFlagTheme]/video/{tex}</texture>
			<visible>{visible}</visible>
		</control>
'''

# ---------------------------------------------------------------- HDR (liste + lecture)
for P, ALT_IS, DV_LABEL, DV_VIS, EL in (
    ('ListItem',
     lambda t, raw: f'String.IsEqual(ListItem.HdrTypeAlt,{t})',
     '$INFO[ListItem.DvProfile,P]',
     'String.IsEqual(ListItem.HdrType,dolbyvision) + !String.IsEmpty(ListItem.DvProfile) + !Skin.HasSetting(avdv.HideDVProfileBadge)',
     None),
    ('VideoPlayer',
     lambda t, raw: f'Integer.IsEqual(Player.Process(video.source.additional.hdr.type.raw),{raw})',
     '$INFO[Player.Process(video.dovi.profile),P]$INFO[Player.Process(video.dovi.bl.signal.compatibility),.]',
     'String.IsEqual(VideoPlayer.HdrType,dolbyvision) + !String.IsEmpty(Player.Process(video.dovi.profile)) + !Skin.HasSetting(avdv.HideDVProfileBadge)',
     True),
):
    # Dolby Vision : badge du profil juste après le logo
    old = f'''			<visible>String.Contains({P}.HdrType,dolbyvision)</visible>
		</control>
'''
    extra = badge(DV_LABEL, DV_VIS)
    if EL:
        extra += badge('$VAR[PlayerDVELTypeVar]', 'String.IsEqual(VideoPlayer.HdrType,dolbyvision) + [String.IsEqual(Player.Process(video.dovi.el.type),full) | String.IsEqual(Player.Process(video.dovi.el.type),minimum)]', 48)
    rep(old, f'''			<visible>String.IsEqual({P}.HdrType,dolbyvision)</visible>
		</control>
''' + extra)

    # HDR10 (exact : « hdr10plus » contient « hdr10 ») + HDR10+ / HDR Vivid
    rep(f'<visible>String.Contains({P}.HdrType,hdr10)</visible>\n\t\t</control>\n',
        f'<visible>String.IsEqual({P}.HdrType,hdr10) | {ALT_IS("hdr10", 1)}</visible>\n\t\t</control>\n'
        + image('HDR10+', 'hdr10plus.png', 91, f'String.IsEqual({P}.HdrType,hdr10plus) | {ALT_IS("hdr10plus", 2)}')
        + image('HDR Vivid', 'hdrvivid.png', 122, f'String.IsEqual({P}.HdrType,hdrvivid) | {ALT_IS("hdrvivid", 5)}'))
    rep(f'<visible>String.Contains({P}.HdrType,hlg)</visible>',
        f'<visible>String.IsEqual({P}.HdrType,hlg) | {ALT_IS("hlg", 4)}</visible>')

# ---------------------------------------------------------------- Audio
for P, F, PROF in (('ListItem', 'ListItem.FilenameAndPath', 'ListItem.AudioProfile'),
                   ('VideoPlayer', 'Player.FilenameAndPath', None)):
    C = f'{P}.AudioCodec'
    atmos = f'[String.Contains({C},atmos) | String.Contains({F},.atmos)' + (f' | String.Contains({PROF},Atmos)' if PROF else '') + ']'
    dtses = f'[String.IsEqual({C},dts_es) | String.Contains({F},dtses) | String.Contains({F},dts-es)' + (f' | String.Contains({PROF},DTS-ES)' if PROF else '') + ']'
    dtsx = f'[String.Contains({C},dtshd_ma_x) | String.Contains({F},dtsx) | String.Contains({F},dts-x)' + (f' | String.Contains({PROF},DTS:X)' if PROF else '') + ']'
    dts_core = f'[String.IsEqual({C},dca) | String.IsEqual({C},dts) | String.IsEqual({C},dts_es) | String.IsEqual({C},dts_96_24) | String.IsEqual({C},dts_express)]'

    # DTS / DTS-ES
    rep(f'<visible>String.Contains({C},dca) + ![String.Contains({F},dtses) | String.Contains({F},dts-es)]</visible>',
        f'<visible>{dts_core} + !{dtses}</visible>')
    rep(f'<visible>String.Contains({C},dca) + [String.Contains({F},dtses) | String.Contains({F},dts-es)]</visible>',
        f'<visible>{dts_core} + {dtses}</visible>')
    # PCM (toutes variantes, dont pcm_s24le / pcm_s32le)
    rep(f'<visible>String.Contains({C},pcm_s16be) | String.Contains({C},pcm_s16le) | String.Contains({C},pcm_u8) | String.Contains({C},pcm_bluray)</visible>',
        f'<visible>String.StartsWith({C},pcm)</visible>')
    # EAC3 / TrueHD / Atmos
    rep(f'<visible>String.Contains({C},eac3) + !String.Contains({F},.atmos)</visible>',
        f'<visible>String.Contains({C},eac3) + !{atmos}</visible>')
    rep(f'<visible>String.Contains({C},truehd) + !String.Contains({F},.atmos)</visible>',
        f'<visible>String.Contains({C},truehd) + !{atmos}</visible>')
    rep(f'<visible>[String.Contains({C},eac3) | String.Contains({C},truehd)] + String.Contains({F},.atmos)</visible>',
        f'<visible>[String.Contains({C},eac3) | String.Contains({C},truehd)] + {atmos}</visible>')

# Variables DTS-HD → DTS:X
rep('<value condition="String.Contains(ListItem.AudioCodec,dtshd_ma) + [String.Contains(ListItem.FilenameAndPath,dtsx) | String.Contains(ListItem.FilenameAndPath,dts-x)]">dtsx.png</value>',
    '<value condition="String.Contains(ListItem.AudioCodec,dtshd_ma_x) | String.Contains(ListItem.AudioProfile,DTS:X) | [String.Contains(ListItem.AudioCodec,dtshd_ma) + [String.Contains(ListItem.FilenameAndPath,dtsx) | String.Contains(ListItem.FilenameAndPath,dts-x)]]">dtsx.png</value>')
rep('<value condition="String.Contains(VideoPlayer.AudioCodec,dtshd_ma) + [String.Contains(Player.FilenameAndPath,dtsx) | String.Contains(Player.FilenameAndPath,dts-x)]">dtsx.png</value>',
    '<value condition="String.Contains(VideoPlayer.AudioCodec,dtshd_ma_x) | [String.Contains(VideoPlayer.AudioCodec,dtshd_ma) + [String.Contains(Player.FilenameAndPath,dtsx) | String.Contains(Player.FilenameAndPath,dts-x)]]">dtsx.png</value>')

# Variable FEL / MEL (lecture)
rep('''	<variable name="PlayerDTSHDMediaFlag">''', '''	<variable name="PlayerDVELTypeVar">
		<value condition="String.IsEqual(Player.Process(video.dovi.el.type),full)">FEL</value>
		<value condition="String.IsEqual(Player.Process(video.dovi.el.type),minimum)">MEL</value>
	</variable>

	<variable name="PlayerDTSHDMediaFlag">''')

open(p, 'w', encoding='utf-8').write(s)
print('includes_MediaFlags.xml patché')
