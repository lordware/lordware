"""Render lordware's instrument-face profile identity. Standard library only."""
from pathlib import Path
from html import escape
import instrument_materials as materials

ROOT = Path(__file__).resolve().parent.parent
BG = '#111416'
PANEL = '#171b1e'
INK = '#dfddd4'
MUTED = '#8d979a'
AMBER = '#e6ad59'
BORDER = '#343a3d'
FONT = "Consolas, 'Liberation Mono', monospace"


def t(x,y,value,size=13,fill=INK,weight=400,spacing=0):
    return f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{fill}" font-weight="{weight}" letter-spacing="{spacing}">{escape(value)}</text>'


def rect(x,y,w,h,fill,stroke='none',rx=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}"/>'


def line(x1,y1,x2,y2,stroke=BORDER,width=1):
    return f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{stroke}" stroke-width="{width}" fill="none"/>'


def screw(x,y):
    return materials.fastener(x,y,4)


def led(x,y,kind='on'):
    return (f'<g transform="translate({x} {y})"><circle cy=".6" r="5.7" fill="#060b0e"/>'
            '<circle r="4.9" fill="url(#mat-screw)" stroke="#17252a" stroke-width=".6"/>'
            '<circle r="3.8" fill="#080e10"/>'
            f'<circle class="{kind}" r="2.9" fill="{"url(#mat-led)" if kind != "off" else "#5e512f"}"/>'
            '<ellipse cx="-.8" cy="-1.1" rx="1" ry=".5" fill="#fff2c9" opacity=".63"/></g>')


DEFS = '''
<linearGradient id="chassis" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#2a3033"/><stop offset=".1" stop-color="#1e2427"/><stop offset=".75" stop-color="#171c1f"/><stop offset="1" stop-color="#23292c"/></linearGradient>
<linearGradient id="metal" x1="0" y1="0" x2=".9" y2="1"><stop stop-color="#c5cac9"/><stop offset=".17" stop-color="#727c80"/><stop offset=".38" stop-color="#e1dfd4"/><stop offset=".55" stop-color="#626f74"/><stop offset=".79" stop-color="#a9b0ae"/><stop offset="1" stop-color="#566269"/></linearGradient>
<linearGradient id="shell" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#869296"/><stop offset=".3" stop-color="#c0c5c0"/><stop offset=".5" stop-color="#68777e"/><stop offset="1" stop-color="#39464c"/></linearGradient>
<linearGradient id="screen" x1="0" y1="0" x2=".2" y2="1"><stop stop-color="#171b17"/><stop offset=".3" stop-color="#101510"/><stop offset="1" stop-color="#0c100f"/></linearGradient>
<linearGradient id="bezel" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#070a0b"/><stop offset=".8" stop-color="#111517"/><stop offset="1" stop-color="#4c5355"/></linearGradient>
<pattern id="brush" width="7" height="4" patternUnits="userSpaceOnUse"><path d="M0 .5H7M2 2.5H6" stroke="#c5cccc" stroke-opacity=".025" stroke-width=".5"/></pattern>
<pattern id="pixels" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="1" height="1" fill="#e6ad59" opacity=".045"/></pattern>
<style>@keyframes blink{0%,46%{opacity:1}50%,96%{opacity:.28}100%{opacity:1}}@keyframes activity{0%,15%,35%,90%,100%{opacity:.25}17%,29%,37%,86%{opacity:1}}.rx{animation:activity 4s linear infinite}.tx{animation:activity 6s linear infinite}.cursor{animation:blink 1.8s steps(1) infinite}@media(prefers-reduced-motion:reduce){.rx,.tx,.cursor{animation:none}}</style>
'''


def svg(w,h,title,art):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title"><title id="title">{escape(title)}</title><defs>{DEFS}{materials.definitions()}{HARDWARE_DEFS}</defs>{art}</svg>\n'


HARDWARE_DEFS = '''
<linearGradient id="hw-flange" x1=".12" y1="0" x2=".82" y2="1"><stop stop-color="#dae1de"/><stop offset=".12" stop-color="#8f9d9e"/><stop offset=".35" stop-color="#c5d0cc"/><stop offset=".43" stop-color="#7b898d"/><stop offset=".7" stop-color="#8b9697"/><stop offset="1" stop-color="#465457"/></linearGradient>
<linearGradient id="hw-edge" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#edf0e8"/><stop offset=".16" stop-color="#a1aeaf"/><stop offset=".4" stop-color="#45565e"/><stop offset=".65" stop-color="#a5b4b4"/><stop offset=".89" stop-color="#d3dbd2"/><stop offset="1" stop-color="#3a4b52"/></linearGradient>
<linearGradient id="hw-cavity" x1="0" y1="0" x2=".1" y2="1"><stop stop-color="#020507"/><stop offset=".3" stop-color="#0b1012"/><stop offset="1" stop-color="#252d30"/></linearGradient>
<linearGradient id="hw-polymer" x1="0" y1="0" x2=".2" y2="1"><stop stop-color="#263033"/><stop offset=".3" stop-color="#131b1e"/><stop offset="1" stop-color="#0c1215"/></linearGradient>
<linearGradient id="hw-gold" x1="0" y1="0" x2=".65" y2="1"><stop stop-color="#fff0b2"/><stop offset=".2" stop-color="#c1a15f"/><stop offset=".47" stop-color="#6d5128"/><stop offset=".65" stop-color="#e7c984"/><stop offset="1" stop-color="#907041"/></linearGradient>
<radialGradient id="hw-bore" cx=".38" cy=".25" r=".75"><stop stop-color="#030506"/><stop offset=".5" stop-color="#070b0c"/><stop offset=".73" stop-color="#1e292b"/><stop offset=".83" stop-color="#82908d"/><stop offset=".9" stop-color="#202b2e"/><stop offset="1" stop-color="#c3cbc4"/></radialGradient>
<pattern id="hw-machining" width="3" height="2" patternUnits="userSpaceOnUse"><path d="M0 .25H3" stroke="#edf2ea" stroke-opacity=".09" stroke-width=".35"/></pattern>
<filter id="hw-shadow" x="-.25" y="-.5" width="1.5" height="2"><feGaussianBlur stdDeviation="3"/></filter>
'''


def engraved(x,y,value,size=11,fill=MUTED,spacing=.4):
    return t(x,y+.8,value,size,'#090e10',500,spacing)+t(x,y,value,size,fill,500,spacing)


def connector(x,y,s=1):
    # Front of a nine-contact D-sub connector. Metal flange, recessed insulator,
    # two staggered contact rows (5 + 4), and captive hex jack screws.
    a=f'<g transform="translate({x} {y}) scale({s})">'
    a+='<ellipse cx="3" cy="34" rx="112" ry="15" fill="#000" opacity=".75" filter="url(#hw-shadow)"/>'
    a+=rect(-114,-36,228,79,'#080d10','#0a1012',10)
    a+=rect(-110,-35,220,74,'#35454b','#687578',8)
    a+=rect(-111,-39,220,72,'url(#hw-flange)','#c7d1ce',8)
    a+=rect(-110,-38,218,70,'url(#hw-machining)',rx=7)
    a+=line(-102,-37,99,-37,'#e0e5dc',.7)
    a+=line(-103,31,101,31,'#34474d',.9)
    # Sparse machining and handling marks on the flange, with no noise over pins.
    a+='<path d="M-79-32l14 .3M-47-34l20 .2M65 27l13-.3M-101 24l8 .2M82-29l13 .3" stroke="#e0e6dc" stroke-opacity=".3" stroke-width=".5"/>'
    for xx in [-89,89]:
        a+=f'<circle cx="{xx}" cy="-1" r="13" fill="#1b292e" opacity=".8"/><circle cx="{xx}" cy="-4" r="12" fill="url(#hw-edge)" stroke="#516166" stroke-width=".7"/>'
        a+=f'<polygon points="{xx-10},-9 {xx-5},-17 {xx+5},-17 {xx+10},-9 {xx+5},1 {xx-5},1" fill="#3b4b51" transform="translate(0 4)"/>'
        a+=f'<polygon points="{xx-10},-9 {xx-5},-17 {xx+5},-17 {xx+10},-9 {xx+5},1 {xx-5},1" fill="url(#hw-flange)" stroke="#d1d9d0" stroke-width=".65"/>'
        a+=f'<circle cx="{xx}" cy="-8" r="5.4" fill="url(#hw-bore)" stroke="#58666a" stroke-width=".65"/>'
        for rr in [4.3,3.45,2.6]:
            a+=f'<path d="M{xx-rr} -8a{rr} {rr} 0 0 1 {rr*2} 0" fill="none" stroke="#b0bbb5" stroke-width=".45" opacity=".63"/>'
    a+='<path d="M-66-28H64Q79-28 74-11L64 21Q62 30 49 30H-49Q-62 30-64 21L-74-11Q-79-28-66-28Z" fill="#101b21" stroke="#536368" stroke-width="1.2"/>'
    a+='<path d="M-66-33H64Q79-33 74-16L64 16Q62 25 49 25H-49Q-62 25-64 16L-74-16Q-79-33-66-33Z" fill="url(#hw-edge)" stroke="#d5ded7" stroke-width=".8"/>'
    a+='<path d="M-63-28H61Q72-28 69-17L59 13Q57 21 48 21H-48Q-57 21-59 13L-69-17Q-72-28-63-28Z" fill="url(#hw-cavity)" stroke="#3b4c51" stroke-width=".9"/>'
    a+='<path d="M-60-22H59Q67-22 64-13L55 13Q53 17 46 17H-46Q-53 17-55 13L-64-13Q-67-22-60-22Z" fill="url(#hw-polymer)" stroke="#303b3e" stroke-width=".6"/>'
    a+='<path d="M-59-22H58M-45 18H45" stroke="#5b6665" stroke-opacity=".48" stroke-width=".6"/>'
    for row,xxs in [(-12,[-44,-22,0,22,44]),(6,[-33,-11,11,33])]:
        for xx in xxs:
            a+=f'<circle cx="{xx}" cy="{row+.6}" r="5.5" fill="#050a0d" stroke="#343e40" stroke-width=".65"/><circle cx="{xx}" cy="{row}" r="4" fill="url(#hw-gold)" stroke="#947743" stroke-width=".45"/><circle cx="{xx}" cy="{row+.25}" r="2.15" fill="#070c0d" stroke="#655330" stroke-width=".5"/><path d="M{xx-1.45} {row+1.3}v-1.9" stroke="#bc9c5d" stroke-width=".5" opacity=".7"/>'
    # Female mating face: contact numbering mirrors the male front view.
    for xx,yy,label in [(-55,-10,'5'),(52,-10,'1'),(-47,8,'9'),(42,8,'6')]:
        a+=t(xx,yy,label,4.5,'#7c8580')
    return a+'</g>'


def hero(mobile=False):
    w,h=(480,538) if mobile else (960,360)
    a=materials.chassis(w,h)
    a+=engraved(34,28,'LW–01',13,'#c7ba99')
    a+=engraved(105,28,'EMBEDDED SYSTEMS',11,MUTED,1.2)
    if not mobile: a+=engraved(702,28,'ENGINEERING / LÜBECK, DE',11,MUTED,.4)
    sw=424 if mobile else 596
    a+=materials.display(28,61,sw+4,231,4)
    a+=t(48,91,'/dev/lordware',12,AMBER)
    a+=t(317 if mobile else 458,91,'FIRMWARE / SYSTEMS',10,'#9c906c')
    a+=line(48,105,sw+9,105,'#393c2c')
    a+=t(43,167,'lordware',66,'url(#mat-phosphor)',700,spacing=-3)
    a+=t(48,195,'Software developer · Embedded systems',14,'#c7bc9f')
    a+=line(48,214,sw+9,214,'#323829')
    a+=t(48,239,'STACK',10,'#958b6d')
    a+=t(110,239,'C · C++ · Python · C#',13,'#d6c9a7')
    a+=t(48,264,'SINCE',10,'#958b6d')
    a+=t(110,264,'2017',13,'#d6c9a7')
    a+=t(241,264,'LÜBECK, DE',11,'#b3a98c')
    a+=materials.overlay(36,69,sw-12,215)
    if mobile:
        a+=led(47,322,'rx')+t(59,326,'RX',10,MUTED)
        a+=led(97,322,'tx')+t(109,326,'TX',10,MUTED)
        a+=t(326,326,'CAN / DE-9',10,MUTED)
        a+=connector(140,386,.9)
        a+=engraved(42,440,'CAN / DE-9',10)
        a+=engraved(271,361,'PIN  SIGNAL',10)
        a+=engraved(271,384,' 2   CAN_L',12,INK)
        a+=engraved(271,404,' 7   CAN_H',12,INK)
        a+=engraved(271,424,' 3   CAN_GND',12,INK)
        y=463
        a+=line(29,y-9,451,y-9,'#363f41')
        a+=engraved(36,y+15,'CANopen / RS-232 / Arduino',12,INK)
        a+=t(36,y+43,'> ./lordware --interface can0',11,AMBER)
    else:
        a+=line(650,64,650,287,'#101517')
        a+=line(651,64,651,287,'#3c4446')
        a+=engraved(679,80,'CAN INTERFACE',11,MUTED,1)
        a+=led(860,76,'rx')+t(872,80,'RX',10,MUTED)
        a+=led(907,76,'tx')+t(919,80,'TX',10,MUTED)
        a+=connector(802,151,1.04)
        a+=engraved(695,216,'2  CAN_L',12,INK)+engraved(822,216,'7  CAN_H',12,INK)
        a+=engraved(695,239,'3  CAN_GND',11)+engraved(822,239,'DE-9',11)
        a+=line(680,249,925,249,'#394145')
        a+=engraved(695,276,'CANopen',12,'#c6b385')+engraved(822,276,'RS-232',12,'#c6b385')
        a+=line(28,310,932,310,'#080c0e')
        a+=line(28,311,932,311,'#3f484b')
        a+=t(37,337,'> ./lordware --interface can0',13,AMBER)
        a+=rect(265,326,7,13,AMBER).replace('/>',' class="cursor"/>')
        a+=engraved(533,337,'C / C++',11,INK)
        a+=engraved(650,337,'ARDUINO',11,INK)
        a+=engraved(781,337,'FIELDBUS / SERIAL',11)
    return svg(w,h,'lordware — embedded software developer, Lübeck, DE. C, C++, Python, C#, CANopen and RS-232. Instrument face illustration with a CAN DE-9 connector.',a)


def identity():
    a=materials.chassis(240,240)
    a+=engraved(35,28,'LW–01',11)
    a+=materials.display(31,49,178,139,4)
    a+=t(61,130,'lw',76,'url(#mat-phosphor)',700,spacing=-6)
    a+=t(55,163,'EMBEDDED SYSTEMS',11,'#a49a7b')
    a+=materials.overlay(39,57,162,123)
    a+=engraved(37,212,'LORDWARE / DE',12)
    return svg(240,240,'lordware — amber embedded systems instrument monogram',a)


def generate(out_dir=ROOT/'assets'):
    out_dir=Path(out_dir)
    out_dir.mkdir(parents=True,exist_ok=True)
    artwork={'hero-next.svg':hero(),'profile-hero-mobile.svg':hero(True),'mark.svg':identity()}
    for name,value in artwork.items(): (out_dir/name).write_text(value,encoding='utf-8')
    return [out_dir/name for name in artwork]


if __name__=='__main__':
    for path in generate(): print(path.name)
