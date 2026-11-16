"""Recording screen of Glossy Slate (design "Recording@2x.png", 640 x 480,
halved) as a recording screen skin (.wrs), without a browser:

    python3 tools/build_recording.py

writes .rockbox/wps/glossyslate.wrs and into .rockbox/wps/glossyslate/
rec_dot.bmp, rec_track.bmp, rec_meter.bmp. The cfg loads the skin with
"wrs: /.rockbox/wps/glossyslate.wrs".

Left: status bar "Recording" with a red dot while recording, the peak meters
L and R, then the settings list of the recording screen (%Vi(-,...)); the
fork shows each setting as name and value. Right: the blue side panel with
the source (%Ri), the microphone tile, the recording time and the size.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from tools import raster as R  # noqa: E402

PKG = os.path.join(os.path.dirname(HERE), '.rockbox')
OUT = os.path.join(PKG, 'wps', 'glossyslate')
VERSION = '1.0'
B13, B17, B11, TILES, DOT = 2, 3, 4, 7, 9
MIC = ''  # microphone in 113-GlossySlate-Tiles.fnt


def save(name, frames):
    R.write_bmp32(os.path.join(OUT, name), frames)


def art():
    dot = R.Canvas(8, 8)
    dot.paint(R.coverage(8, 8, R.circle(4, 4, 4)), R.hexc('9E2A22'))
    dot.paint(R.coverage(8, 8, R.circle(4, 4, 3.3)),
              R.vgrad([(0, R.hexc('F49088')), (.5, R.hexc('D9352F')), (1, R.hexc('B8281C'))], .7, 7.3))
    save('rec_dot.bmp', [dot])
    track = R.Canvas(130, 5)
    track.paint(R.coverage(130, 5, R.rrect(0, 0, 130, 5, 2.5)),
                R.vgrad([(0, R.hexc('A3A8AF')), (.35, R.hexc('C5CBD3')), (1, R.hexc('E4E7ED'))], 0, 5))
    save('rec_track.bmp', [track])
    meter = R.Canvas(130, 5)
    meter.paint(R.coverage(130, 5, R.rrect(0, 0, 130, 5, 2.5)),
                R.vgrad([(0, R.hexc('B8D89C')), (.6, R.hexc('86BD57')), (1, R.hexc('86BD57'))], 0, 5))
    save('rec_meter.bmp', [meter])


def skin():
    L = ['#  Glossy Slate %s for Rockbox - recording screen (.wrs)' % VERSION,
         '#  made by tools/build_recording.py',
         '%wd',
         '%%Fl(%d,16-GlossySlate-Bold13.fnt,160)' % B13,
         '%%Fl(%d,20-GlossySlate-Bold17.fnt,160)' % B17,
         '%%Fl(%d,14-GlossySlate-Bold11.fnt,160)' % B11,
         '%%Fl(%d,113-GlossySlate-Tiles.fnt,2)' % TILES,
         '%%Fl(%d,1-GlossySlate-Dot.fnt,1)' % DOT,
         '#--- images ---#',
         '%xl(Sidebar,sidebar.bmp,0,0)', '%xl(TileFrame,tileframe.bmp,41,79)',
         '%xl(Batt,status_battery.bmp,0,0,12)', '%xl(Charge,status_charge.bmp,0,0,12)',
         '%xl(Charged,status_charged.bmp,0,0)',
         '%xl(Lock,status_lock.bmp,0,0)', '%xl(RecDot,rec_dot.bmp,0,0)',
         '%xl(RecTrack,rec_track.bmp,0,0)',
         '#--- settings list of the recording screen ---#',
         '%Vi(-,0,47,160,193,-)',
         '#--- backdrop layer: white, status bar, rule, side panel ---#',
         '%%V(0,0,160,240,%d)%%VB' % DOT,
         '%dr(0,0,160,240,ffffff)',
         '%dr(0,0,160,21,ffffff,979797)', '%dr(0,21,160,1,1e1e1e)',
         '%dr(0,46,160,1,d3d8df)',
         '%%V(160,0,160,240,%d)%%VB%%xd(Sidebar)%%xd(TileFrame)' % DOT,
         '# empty foreground viewports: a full update copies the finished',
         '# backdrop there (the screen holds a copy of the previous one)',
         '%%V(0,0,160,47,%d)' % DOT, '%%V(160,0,160,240,%d)' % DOT,
         '#--- status bar ---#',
         '%%V(8,2,72,16,%d)%%Vf(14171c)' % B13, '%s%al%Sx(Recording)',
         '%V(102,4,10,12,-)', '%?mh<%xd(Lock)>',
         '%V(115,6,8,8,-)', '%?Rr<%xd(RecDot)>',
         '%V(128,4,26,13,-)', '%?bp<%?bc<%xd(Charge,%bl)|%xd(Charged)>|%xd(Batt,%bl)>',
         '#--- peak meters ---#',
         '%%V(8,24,12,14,%d)%%Vf(5b6371)' % B11, '%alL',
         '%%V(8,35,12,14,%d)%%Vf(5b6371)' % B11, '%alR',
         '%V(22,27,130,5,-)', '%pL(0,0,130,5,rec_meter.bmp,backdrop,RecTrack)',
         '%V(22,38,130,5,-)', '%pR(0,0,130,5,rec_meter.bmp,backdrop,RecTrack)',
         '#--- side panel: source, tile, time, size ---#',
         '%%V(165,17,150,20,%d)%%Vf(ffffff)' % B17, '%s%ac%Ri',
         '%%V(201,79,78,113,%d)%%Vf(dfe6f3)' % TILES, '%al' + MIC,
         '%V(208,190,8,8,-)', '%?Rr<%xd(RecDot)>',
         '%%V(220,186,92,16,%d)%%Vf(ffffff)' % B13, '%al%Rh:%Rn:%Rs',
         '%%V(165,203,150,16,%d)%%Vf(ffffff)' % B13, '%ac%RS']
    open(os.path.join(PKG, 'wps', 'glossyslate.wrs'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')


if __name__ == '__main__':
    art()
    skin()
    print('recording screen ok')
