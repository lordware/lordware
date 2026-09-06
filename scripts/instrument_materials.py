"""Shared vector materials for the physical instrument faceplates.

Geometry and tiled textures stay static; no full-surface filters or raster assets.
The light source is above-left, with recessed glass and dark lower/right edges.
"""
import math


def definitions():
    grain=[]
    for i in range(48):
        x=(i*17+7)%59
        y=(i*23+11)%43
        r=.16+(i%4)*.08
        grain.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{"#e2e4dd" if i%3 else "#040708"}" opacity="{.09 if i%3 else .2}"/>')
    return '''
<linearGradient id="mat-face" x1="0" y1="0" x2=".12" y2="1"><stop stop-color="#3c4448"/><stop offset=".025" stop-color="#272f33"/><stop offset=".3" stop-color="#242c30"/><stop offset=".82" stop-color="#1b2226"/><stop offset="1" stop-color="#252d31"/></linearGradient>
<linearGradient id="mat-edge" x1="0" y1="0" x2=".35" y2="1"><stop stop-color="#9a9d97"/><stop offset=".035" stop-color="#586368"/><stop offset=".45" stop-color="#222c31"/><stop offset="1" stop-color="#080d10"/></linearGradient>
<linearGradient id="mat-header" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#40494d"/><stop offset=".07" stop-color="#343d41"/><stop offset=".65" stop-color="#282f33"/><stop offset="1" stop-color="#20272b"/></linearGradient>
<radialGradient id="mat-light" cx=".15" cy="0" r="1.1"><stop stop-color="#9ca6a3" stop-opacity=".07"/><stop offset=".6" stop-color="#9ca6a3" stop-opacity="0"/><stop offset="1" stop-color="#000609" stop-opacity=".14"/></radialGradient>
<linearGradient id="mat-screw" x1="0" y1="0" x2=".9" y2="1"><stop stop-color="#c3c8c3"/><stop offset=".2" stop-color="#737f83"/><stop offset=".45" stop-color="#acb3af"/><stop offset=".7" stop-color="#48575e"/><stop offset="1" stop-color="#26363e"/></linearGradient>
<linearGradient id="mat-bezel" x1="0" y1="0" x2=".05" y2="1"><stop stop-color="#05090b"/><stop offset=".14" stop-color="#111b20"/><stop offset=".86" stop-color="#19252a"/><stop offset="1" stop-color="#647074"/></linearGradient>
<linearGradient id="mat-glass" x1="0" y1="0" x2=".12" y2="1"><stop stop-color="#111c1d"/><stop offset=".16" stop-color="#091314"/><stop offset=".7" stop-color="#0a1313"/><stop offset="1" stop-color="#121a17"/></linearGradient>
<linearGradient id="mat-reflection" x1="0" y1="0" x2=".8" y2="1"><stop stop-color="#c4d3cd" stop-opacity=".085"/><stop offset=".3" stop-color="#c4d3cd" stop-opacity=".013"/><stop offset="1" stop-color="#c4d3cd" stop-opacity="0"/></linearGradient>
<linearGradient id="mat-phosphor" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#ffe1a0"/><stop offset=".35" stop-color="#e9b666"/><stop offset="1" stop-color="#c48b3c"/></linearGradient>
<linearGradient id="mat-amber-meter" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#f4cf8a"/><stop offset=".18" stop-color="#ecbc6f"/><stop offset=".62" stop-color="#d59d47"/><stop offset="1" stop-color="#98612d"/></linearGradient>
<linearGradient id="mat-counter-drum" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#050a0c"/><stop offset=".22" stop-color="#263031"/><stop offset=".48" stop-color="#1c2627"/><stop offset=".51" stop-color="#111d20"/><stop offset=".77" stop-color="#1b282a"/><stop offset="1" stop-color="#060d10"/></linearGradient>
<radialGradient id="mat-led"><stop stop-color="#fff2bb"/><stop offset=".22" stop-color="#f3ca76"/><stop offset=".63" stop-color="#d89c3a"/><stop offset="1" stop-color="#6e421e"/></radialGradient>
<pattern id="mat-brush" width="73" height="6" patternUnits="userSpaceOnUse"><path d="M0 .5H73M9 2.5H42M49 4.5H71" fill="none" stroke="#dae0de" stroke-width=".3" opacity=".075"/><path d="M4 1.5H46M32 5.5H69" stroke="#030608" stroke-width=".4" opacity=".14"/></pattern>
<pattern id="mat-pixels" width="3" height="3" patternUnits="userSpaceOnUse"><path d="M0 .5H3" stroke="#050809" stroke-width=".45" opacity=".2"/><circle cx="1.5" cy="1.5" r=".22" fill="#a8b7a8" opacity=".085"/></pattern>
<pattern id="mat-grain" width="59" height="43" patternUnits="userSpaceOnUse">'''+''.join(grain)+'''</pattern>
<filter id="mat-small-bloom" x="-35%" y="-45%" width="170%" height="190%" color-interpolation-filters="sRGB"><feGaussianBlur stdDeviation=".75"/></filter>
'''


def fastener(x,y,radius=4):
    points=[]
    for i in range(12):
        a=i*math.pi/6-math.pi/2
        r=radius*(.46 if i%2==0 else .31)
        points.append(f'{math.cos(a)*r:.3f},{math.sin(a)*r:.3f}')
    return (f'<g transform="translate({x} {y})">'
            f'<circle cy=".65" r="{radius+1.3}" fill="#060a0d" opacity=".9"/>'
            f'<circle r="{radius+.45}" fill="#111a1f" stroke="#4d585d" stroke-width=".45"/>'
            f'<circle r="{radius}" fill="url(#mat-screw)"/>'
            f'<circle r="{radius-.8}" fill="none" stroke="#d3d5c9" stroke-opacity=".23" stroke-width=".35"/>'
            f'<polygon points="{" ".join(points)}" fill="#0d171d" stroke="#1b2b33" stroke-width=".5"/>'
            f'<path d="M{-radius*.65} {-radius*.58}Q0 {-radius*1.04} {radius*.6} {-radius*.68}" fill="none" stroke="#f2f0dd" stroke-opacity=".5" stroke-width=".45"/>'
            '</g>')


def chassis(w,h):
    art=(f'<rect x="1" y="3" width="{w-2}" height="{h-4}" rx="6" fill="#05090c"/>'
         f'<rect x=".5" y=".5" width="{w-1}" height="{h-2}" rx="6" fill="url(#mat-face)" stroke="#070d11"/>'
         f'<rect x="1.5" y="1.5" width="{w-3}" height="{h-4}" rx="5" fill="none" stroke="url(#mat-edge)"/>'
         f'<rect x="3" y="3" width="{w-6}" height="{h-8}" rx="4" fill="url(#mat-light)"/>'
         f'<rect x="3" y="3" width="{w-6}" height="{h-8}" rx="4" fill="url(#mat-brush)"/>'
         f'<rect x="3" y="3" width="{w-6}" height="{h-8}" rx="4" fill="url(#mat-grain)"/>'
         f'<rect x="4" y="4" width="{w-8}" height="30" rx="3" fill="url(#mat-header)"/>'
         f'<path d="M6 35.5H{w-6}" stroke="#0d1418"/>'
         f'<path d="M6 36.5H{w-6}" stroke="#60696a" stroke-opacity=".32"/>'
         f'<path d="M8 {h-3.5}H{w-8}" stroke="#68736f" stroke-opacity=".23"/>')
    for x in (11,w-11):
        art+=fastener(x,20,3)
    return art


def display(x,y,w,h,radius=3):
    return (f'<rect x="{x-3}" y="{y-3}" width="{w+6}" height="{h+6}" rx="{radius+2}" fill="#080f13" stroke="#34454d" stroke-width=".6"/>'
            f'<rect x="{x-2}" y="{y-2}" width="{w+4}" height="{h+4}" rx="{radius+1}" fill="url(#mat-bezel)"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="url(#mat-glass)" stroke="#080f10"/>'
            f'<rect x="{x+.5}" y="{y+.5}" width="{w-1}" height="{h-1}" rx="{radius}" fill="url(#mat-pixels)"/>'
            f'<path d="M{x+radius} {y+1}H{x+w-radius}" stroke="#03090b" stroke-width="2"/>'
            f'<path d="M{x+1} {y+radius}V{y+h-radius}" stroke="#03090b" stroke-width="1.4"/>'
            f'<path d="M{x+radius} {y+h+1.5}H{x+w-radius}" stroke="#81908b" stroke-opacity=".32" stroke-width=".7"/>'
            f'<rect x="{x+2}" y="{y+2}" width="{w-4}" height="{h-4}" rx="{max(0,radius-1)}" fill="url(#mat-reflection)"/>')


def overlay(x,y,w,h):
    # A broad, static softbox reflection never obscures the important center.
    return f'<path d="M{x+3} {y+3}H{x+w*.55}L{x+3} {y+h*.42}Z" fill="url(#mat-reflection)" opacity=".35"/>'
