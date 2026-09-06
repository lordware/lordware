"""Supporting instrument panels: ticker, visitor counter, activity and contact."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import re
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from html import escape
import yaml
import instrument_materials as materials
from gen_profile import t, rect, line, screw, led, svg, BG, PANEL, INK, MUTED, AMBER, BORDER

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'scripts'/'data'


def shell(w,h,title,right=''):
    a=materials.chassis(w,h)
    a+=t(27,26,title,12,MUTED,700,spacing=.5)
    if right: a+=t(w-27-len(right)*6.05,26,right,11,AMBER)
    a+=line(1,39,w-1,39,'#080c0d')
    a+=line(1,40,w-1,40,'#394246')
    return a


def ticker(mobile=False):
    items=yaml.safe_load((DATA/'content.yml').read_text(encoding='utf-8'))['ticker']
    w,h=(480,170) if mobile else (960,132)
    a=shell(w,h,'02 / WORK QUEUE','ROTATING BUFFER')
    a+=materials.display(16,54,w-32,h-70)
    # Each row is completely readable before the next frame. No high-speed marquee.
    blocks=[]
    for i,item in enumerate(items):
        category={'shipping':'BUILD','tinkering':'INTERFACE','learning':'RESEARCH','reading':'REFERENCE','dreaming':'CONCEPT'}.get(item['category'],'NOTE')
        msg=item['message'].replace(' (yes, really)','').replace('a homemade logic analyzer that fits in an Altoids tin','compact logic analyzer / portable enclosure').replace('an open-source replacement for the AD2 logic analyzer','open-source logic analyzer / AD2 alternative')
        size=13 if mobile else 14
        y=83 if mobile else 88
        block=t(30,y,category,11,AMBER,700)
        if mobile:
            import textwrap
            for j,part in enumerate(textwrap.wrap(msg,width=49)):
                block+=t(30,108+j*19,part,size,INK)
        else:
            block+=t(148,y,msg,size,INK)
        blocks.append(f'<g class="note n{i}">{block}</g>')
    rules=''.join(f'.n{i}{{animation-delay:{i*7}s}}' for i in range(len(items)))
    a+=f'<style>.note{{opacity:0;animation:queue {len(items)*7}s linear infinite}}.n0{{opacity:1}}@keyframes queue{{0%,9%{{opacity:1}}10%,100%{{opacity:0}}}}{rules}@media(prefers-reduced-motion:reduce){{.note{{animation:none;opacity:0}}.n0{{opacity:1}}}}</style>'
    a+=''.join(blocks)
    return svg(w,h,'Work queue — firmware, interfaces and embedded systems research notes',a)


def visitors(count,mobile=False,stamp='LAST SAVED COUNT'):
    w,h=(480,168) if mobile else (960,137)
    a=shell(w,h,'11 / PROFILE COUNTER',stamp)
    a+=t(28,75,'VISITORS',11,MUTED,700,spacing=1)
    a+=t(28,98,'lordware / github',12,INK)
    n=str(count).zfill(6) if count is not None else '------'
    dx=217 if mobile else 602
    for i,digit in enumerate(n[-8:]):
        x=dx+i*33
        a+=materials.display(x,61,29,46,2)
        a+=rect(x+2,63,25,42,'url(#mat-counter-drum)',rx=1)
        a+=t(x+4,95,digit,31,AMBER,700)
        a+=line(x+2,84,x+27,84,'#060d10',.8)
        a+=line(x+2,84.8,x+27,84.8,'#717d73',.3)
    a+=t(28,h-15,'SOURCE: KOMAREV  /  CACHED BETWEEN REFRESHES',10,MUTED)
    return svg(w,h,f'Profile visitor counter: {count if count is not None else "unavailable"}',a).replace('role="img"',f'role="img" data-count="{count if count is not None else ""}"',1)


def connect(mobile=False):
    w,h=(480,236) if mobile else (960,155)
    a=shell(w,h,'12 / CONTACT','LORDWARE')
    a+=materials.display(16,53,w-32,h-96)
    if mobile:
        fields=[(28,76,'INTERFACE','Discord'),(28,124,'ADDRESS','lordware1'),(262,76,'LOCATION','Lübeck, DE'),(262,124,'SINCE','2017')]
    else:
        fields=[(28,77,'INTERFACE','Discord'),(260,77,'ADDRESS','lordware1'),(515,77,'LOCATION','Lübeck, DE'),(770,77,'SINCE','2017')]
    for x,y,key,value in fields:
        a+=t(x,y,key,10,MUTED,spacing=1)
        a+=t(x,y+25,value,22 if key=='ADDRESS' else 18,AMBER if key=='ADDRESS' else INK,700)
    a+=line(24,h-34,w-24,h-34)
    a+=t(28,h-13,'END OF TRANSMISSION',10,MUTED,spacing=1.5)
    a+=t(w-99,h-13,'0x6C77',10,AMBER)
    return svg(w,h,'Contact lordware on Discord: lordware1. Lübeck, DE. Developing since 2017.',a)


def activity_source(offline):
    cache=DATA/'activity-source.svg'
    if not offline:
        try:
            url='https://raw.githubusercontent.com/lordware/lordware/output/github-contribution-grid-snake-dark.svg'
            req=urllib.request.Request(url,headers={'User-Agent':'lordware-profile'})
            with urllib.request.urlopen(req,timeout=10) as response: content=response.read().decode('utf-8')
            ET.fromstring(content)
            cache.write_text(content,encoding='utf-8')
        except Exception as error:
            print(f'[activity] retaining cached source: {type(error).__name__}')
    if not cache.exists():
        content=subprocess.run(['git','show','origin/output:github-contribution-grid-snake-dark.svg'],cwd=ROOT,capture_output=True,check=True).stdout.decode('utf-8')
        cache.write_text(content,encoding='utf-8')
    return cache.read_text(encoding='utf-8')


def activity(raw,mobile=False):
    w,h=(480,241) if mobile else (960,289)
    # Keep the original contribution graph and exact snake path; recolor and
    # mount it inside the same instrument chassis. No fabricated contributions.
    source=ET.fromstring(raw)
    ns={'s':'http://www.w3.org/2000/svg'}
    style=source.find('s:style',ns)
    if style is None: raise ValueError('Activity source has no style')
    style.text=re.sub(r':root\{[^}]*\}', ':root{--cb:#343a3d;--cs:#e6ad59;--ce:#171d1f;--c0:#171d1f;--c1:#55482e;--c2:#886b3e;--c3:#b08a4d;--c4:#e6ad59}',style.text)
    style.text+='@media(prefers-reduced-motion:reduce){.c,.s,.u{animation:none!important}}'
    # Input is generated by Platane/snk; no script/external fetch/foreignObject.
    for node in source.iter():
        if node.tag.split('}')[-1] in {'script','foreignObject','image'}: raise ValueError('Unsupported activity source node')
    ET.register_namespace('','http://www.w3.org/2000/svg')
    source.set('x','22')
    source.set('y','75' if mobile else '54')
    source.set('width',str(w-44))
    source.set('height',str((w-44)*192/880))
    a=shell(w,h,'10 / CONTRIBUTION ACTIVITY','GITHUB')
    a+=materials.display(16,53,w-32,h-(97 if mobile else 82))
    a+=ET.tostring(source,encoding='unicode')
    a+=t(25,h-19,'CONTRIBUTION GRID / SNAKE',10,MUTED)
    if not mobile: a+=t(w-359,h-19,'SNAPSHOT FROM OUTPUT BRANCH',10,MUTED)
    return svg(w,h,'GitHub contribution activity — original snake animation in amber',a)


def generate(out_dir=ROOT/'assets',offline=False):
    out_dir=Path(out_dir)
    count_path=out_dir/'visitors.svg'
    match=re.search(r'data-count="(\d+)"',count_path.read_text(encoding='utf-8')) if count_path.exists() else None
    count=int(match[1]) if match else None
    if not offline:
        from gen_visitors import _fetch_count
        fetched=_fetch_count()
        if fetched is not None: count=fetched
    raw=activity_source(offline)
    art={'ticker.svg':ticker(),'profile-ticker-mobile.svg':ticker(True),'visitors.svg':visitors(count),
         'profile-visitors-mobile.svg':visitors(count,True),'profile-connect.svg':connect(),'profile-connect-mobile.svg':connect(True),
         'activity.svg':activity(raw),'profile-activity-mobile.svg':activity(raw,True)}
    for name,content in art.items():
        ET.fromstring(content)
        (out_dir/name).write_text(content,encoding='utf-8')
    return [out_dir/name for name in art]


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--offline',action='store_true')
    args=parser.parse_args()
    for path in generate(offline=args.offline): print(path.name)
