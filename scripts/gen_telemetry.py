"""GitHub snapshot instruments. Offline rendering never accesses the network."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET

import _github
import gen_stats
import gen_log
import instrument_materials as materials

BG, PANEL, BORDER = '#111416', '#171b1e', '#343a3d'
INK, MUTED, AMBER, DIM, GRID = '#dfddd4', '#8d979a', '#e6ad59', '#886b3e', '#242c2f'
USER = gen_stats.USER
NS = '{http://www.w3.org/2000/svg}'


def text(x, y, value, size=13, color=INK, anchor='start', weight=400):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{escape(str(value))}</text>'


def rect(x, y, w, h, fill=PANEL, stroke=None, radius=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}"' + (f' stroke="{stroke}"' if stroke else '') + '/>'


def line(x1, y1, x2, y2, color=BORDER):
    return f'<path d="M{x1} {y1}H{x2}" stroke="{color}"/>' if y1 == y2 else f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{color}"/>'


def screen(x, y, w, h):
    return materials.display(x,y,w,h)


def segment_counter(x, y, value, width, height=34):
    """Precision seven-segment polygons; retain the exact value in accessibility text."""
    label=number(value)
    if value is None:
        return text(x,y+height-3,label,height,AMBER,weight=700)
    shapes=['M3 1H17L14 4H6Z','M18 2V16L15 14V5Z',
            'M18 18V32L15 29V20Z','M3 33H17L14 30H6Z',
            'M2 18V32L5 29V20Z','M2 2V16L5 14V5Z',
            'M3 17L6 14.8H14L17 17L14 19.2H6Z']
    mapping={'0':'012345','1':'12','2':'01346','3':'01236','4':'1256',
             '5':'02356','6':'023456','7':'012','8':'0123456','9':'012356'}
    count=max(4,len(label))
    scale=min(height/34,width/(count*24))
    p=[f'<g role="img" aria-label="{escape(label)}"><title>{label}</title>',
       f'<g transform="translate({x} {y}) scale({scale})" aria-hidden="true">']
    for i,char in enumerate(label.rjust(count)):
        p.append(f'<g transform="translate({i*24} 0)">')
        if char==',':
            p.append('<path d="M9 29H13V33L9 37H7L9 33Z" fill="url(#led-active)"/>')
        else:
            for j,path in enumerate(shapes):
                active=str(j) in mapping.get(char,'')
                p.append(f'<path d="{path}" fill="'+('url(#led-active)' if active else '#292b23')+'"'+(' stroke="#f3ca80" stroke-width=".24"' if active else '')+'/>')
        p.append('</g>')
    p.append('</g></g>')
    return ''.join(p)


def bargraph(x,y,w,pct):
    """Backlit segments fill the exact fraction, including partial last segments."""
    p=[rect(x-2,y-2,w+4,18,'#503e29','#746047',2),
       rect(x-1,y-1,w+2,16,'#070b0c','#101414',1)]
    count=50
    step=w/count
    for i in range(count):
        bx=x+i*step
        sw=step-2
        p.append(rect(round(bx,3),y+1,round(sw,3),10,'#242a24'))
        lit=max(0,min(sw,w*pct-i*step))
        if lit>0:
            p.append(rect(round(bx,3),y+1,round(lit,3),10,'url(#led-active)'))
        if i%5==0:
            p.append(line(round(bx,3),y+15,round(bx,3),y+18,'#68716b'))
    p.append(line(x,y,w+x,y,'#111512'))
    return ''.join(p)


def load_snapshot(path, kind):
    """Read both original raw metadata and the versioned snapshot envelope."""
    if not path.exists():
        return {'version': 2, 'kind': kind, 'sampled_at': None, 'status': 'UNAVAILABLE', 'data': [] if kind in ('repos', 'syslog') else {}}
    raw = path.read_text(encoding='utf-8')
    root = ET.fromstring(raw)
    el = root.find(f"{NS}metadata[@id='{kind}-cache']")
    if el is None:
        raise ValueError(f'{path}: missing {kind} metadata')
    data = json.loads(el.text or 'null')
    if isinstance(data, dict) and data.get('version') == 2 and 'data' in data:
        return data
    match = re.search(r'sampled (\d{4}-\d\d-\d\d \d\d:\d\d:\d\dZ)', raw)
    stamp = match.group(1).replace(' ', 'T') if match else None
    if kind == 'repos':
        stamp = data.get('generated_at', stamp)
        data = data.get('repos', [])
    if kind == 'syslog':
        # The legacy renderer inserted an invented placeholder into its cache.
        placeholders = [e for e in data if e.get('msg', '').startswith('no public events visible')]
        if placeholders and not stamp:
            stamp = placeholders[0].get('ts')
        data = [e for e in data if not e.get('msg', '').startswith('no public events visible')]
    return {'version': 2, 'kind': kind, 'sampled_at': stamp, 'status': 'CACHED', 'data': data}


def stamp(snapshot):
    value = snapshot.get('sampled_at')
    if not value:
        return 'timestamp unavailable'
    try:
        return dt.datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    except (ValueError, TypeError):
        return str(value)


def shell(w, h, kind, title, snapshot, description, css=''):
    status = snapshot.get('status', 'CACHED')
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
         f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>',
         '<defs>'+materials.definitions()+'</defs>',
         '<defs><linearGradient id="led-active" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#ffe0a1"/><stop offset=".42" stop-color="#eab760"/><stop offset="1" stop-color="#a9702d"/></linearGradient>',
         f'<style>text{{font-family:Consolas,\'Liberation Mono\',monospace}}{css}@media(prefers-reduced-motion:reduce){{.event-scroll{{animation:none!important}}}}</style></defs>',
         f'<metadata id="{kind}-cache">{escape(json.dumps(snapshot, separators=(",", ":"), sort_keys=True))}</metadata>',
         materials.chassis(w,h),
         text(32,25,title,13,INK,weight=700), text(w-32,25,status,13,AMBER,'end')]
    p.extend([line(16,h-30,w-16,h-30),text(24,h-11,stamp(snapshot),13,MUTED)])
    if w > 480:
        p.append(text(w-24,h-11,'GITHUB / '+USER,13,MUTED,'end'))
    return p


def number(value):
    return 'N/A' if value is None else f'{int(value):,}'


def render_stats(snapshot, mobile):
    w,h = (480,408) if mobile else (960,202)
    s = snapshot['data']
    p = shell(w,h,'stats','01 / ACCOUNT COUNTERS',snapshot,'GitHub account snapshot: stars, owned public repositories, followers, observed push commits within 90 days, and contribution streak. Unavailable counters read N/A.')
    fields = [('STARS',s.get('stars'),'owned repositories'),('REPOSITORIES',s.get('repos'),'public / non-fork'),('FOLLOWERS',s.get('followers'),'GitHub accounts'),('COMMITS / 90d',s.get('commits_90d'),'public events only'),('STREAK / DAYS',s.get('current_streak'),'contribution calendar')]
    for i,(label,value,sub) in enumerate(fields):
        x = 18+(i%2)*226 if mobile else 18+i*187
        y = 54+(i//2)*106 if mobile else 54
        cw,ch = (218,94) if mobile else (177,104)
        if mobile and i==4:
            cw=444
        p.extend([screen(x,y,cw,ch),text(x+12,y+19,label,13,MUTED),
                  rect(x+9,y+27,cw-18,43,'#080d0b','#30372e',2),
                  line(x+11,y+28,x+cw-11,y+28,'#030505'),
                  segment_counter(x+15,y+32,value,cw-30),
                  line(x+12,y+72,x+cw-12,y+72,'#343c32')])
        if not mobile or i<4:
            p.append(text(x+12,y+ch-10,sub,11 if not mobile else 13,MUTED))
        else:
            p.append(text(x+cw-12,y+ch-9,sub,13,MUTED,'end'))
    p.append('</svg>')
    return '\n'.join(p)


def byte_size(n):
    n=int(n or 0)
    for unit, divisor in [('GB',1e9),('MB',1e6),('kB',1e3)]:
        if n>=divisor:
            return f'{n/divisor:.1f} {unit}'
    return f'{n} B'


def render_repos(snapshot,mobile):
    repos = snapshot['data']
    w=480 if mobile else 960
    rh=86 if mobile else 36
    h=max(240,(116 if mobile else 144)+max(len(repos),1)*rh)
    p=shell(w,h,'repos','07 / REPOSITORY INDEX',snapshot,'Actual owned public non-fork, non-archived repository records. Size is GitHub repository size in KiB, not process memory or CPU usage.')
    p.extend([text(24,61,f'{len(repos):02d} RECORDS / OWNED PUBLIC',13,INK),screen(18,73,w-36,h-113)])
    if not mobile:
        p.append(rect(20,75,w-40,27,'#262c2c'))
        for x,label,anchor in [(28,'REPOSITORY','start'),(477,'LANGUAGE','start'),(703,'SIZE [KiB]','end'),(789,'STARS','end'),(822,'PUSHED [UTC]','start')]:
            p.append(text(x,93,label,12,MUTED,anchor))
        p.append(line(19,101,w-19,101))
        for x in (465,600,719,807):
            p.append(line(x,79,x,h-48,'#303a37'))
    for i,r in enumerate(repos):
        y=77+i*rh if mobile else 103+i*rh
        if i%2==0:
            p.append(f'<rect x="20" y="{y}" width="{w-40}" height="{rh}" fill="#b4bcb0" opacity=".028"/>')
        p.append(line(24,y+rh-1,w-24,y+rh-1,'#28312d'))
        name=r.get('name','?')
        if mobile:
            # Long repository names fit on a second line rather than disappearing.
            chunks=[name[j:j+42] for j in range(0,len(name),42)] or ['?']
            for j,chunk in enumerate(chunks[:2]):
                p.append(text(28,y+19+j*17,chunk,13,AMBER,weight=700))
            p.extend([text(28,y+54,f"{r.get('lang') or 'N/A'}  /  {r.get('size',0):,} KiB  /  {r.get('stars',0)} stars",13,INK),text(28,y+74,'PUSHED '+(r.get('pushed_at') or 'N/A')[:10],13,MUTED)])
        else:
            p.extend([text(28,y+23,name,13,AMBER,weight=700),text(477,y+23,r.get('lang') or 'N/A',13),text(703,y+23,number(r.get('size')),13,INK,'end'),text(789,y+23,number(r.get('stars')),13,INK,'end'),text(822,y+23,(r.get('pushed_at') or 'N/A')[:10],13,MUTED)])
    if not repos:
        p.append(text(28,129,'Repository data unavailable',13,MUTED))
    p.append('</svg>')
    return '\n'.join(p)


def render_lang(snapshot,mobile):
    totals=snapshot['data']
    items=sorted(totals.items(),key=lambda kv:(-kv[1],kv[0]))
    grand=sum(totals.values())
    w=480 if mobile else 960
    rh=52 if mobile else 36
    h=max(230,112+max(len(items),1)*rh)
    p=shell(w,h,'lang','08 / SOURCE BYTE DISTRIBUTION',snapshot,'GitHub language byte counts across owned public non-fork, non-archived repositories. Bars and percentages show shares of the complete byte total, not CPU load.')
    p.extend([text(24,62,f'{byte_size(grand)} / {len(items)} LANGUAGES',13,INK),text(w-24,62,'BYTES',13,MUTED,'end'),screen(18,76,w-36,h-116)])
    for i,(name,value) in enumerate(items):
        y=82+i*rh
        pct=value/grand if grand else 0
        bx,bw,by=(28,310,y+23) if mobile else (180,540,y+5)
        if mobile:
            p.extend([text(28,y+15,name,13,INK),text(w-28,y+15,byte_size(value),13,MUTED,'end'),text(w-28,y+34,f'{pct:.1%}',13,AMBER,'end')])
        else:
            p.extend([text(28,y+18,name,13,INK),text(837,y+18,byte_size(value),13,MUTED,'end'),text(w-28,y+18,f'{pct:.1%}',13,AMBER,'end')])
        p.append(bargraph(bx,by,bw,pct))
    if not items:
        p.append(text(28,110,'Language data unavailable',13,MUTED))
    p.append('</svg>')
    return '\n'.join(p)


def render_syslog(snapshot,mobile):
    events=snapshot['data']
    w,h=(480,322) if mobile else (960,264)
    rh=62 if mobile else 27
    visible=3 if mobile else 4
    top=111 if not mobile else 91
    records=[]
    for event in events:
        msg=event.get('msg','')
        columns=52 if mobile else 89
        chunks=[msg[j:j+columns] for j in range(0,len(msg),columns)] or ['']
        records.append((event,chunks,max(rh,(30 if mobile else 12)+17*len(chunks))))
    period=sum(row_height for _,_,row_height in records)
    scroll=period>h-42-(top-7)
    css=f'.event-scroll{{animation:events {max(40,period/5)}s linear infinite}}@keyframes events{{0%,8%{{transform:translateY(0)}}100%{{transform:translateY(-{period}px)}}}}' if scroll else ''
    p=shell(w,h,'syslog','09 / EVENT JOURNAL',snapshot,'Public GitHub events from the account and owned repositories. A recorded snapshot, not a live hardware log. Reduced motion retains a complete static first page.',css)
    p.extend([text(24,62,f'{len(events):02d} RETAINED EVENTS',13,INK),text(w-24,62,'PUBLIC API',13,MUTED,'end'),screen(18,77,w-36,h-117)])
    if not mobile:
        p.extend([rect(20,79,w-40,24,'#262c2c'),text(28,96,'TIMESTAMP / UTC',12,MUTED),text(230,96,'EVENT RECORD',12,MUTED),line(22,103,w-22,103,'#39433d')])
    if not events:
        p.extend([rect(31,118,5,5,AMBER),text(47,127,'NO PUBLIC EVENTS IN SNAPSHOT',15,AMBER,weight=700),text(32,154,'No event records retained by the source.',13,MUTED),line(32,171,w-32,171,GRID),text(32,192,'SOURCE / github.com/'+USER,13,MUTED)])
    else:
        p.extend([f'<defs><clipPath id="event-clip"><rect x="20" y="{top-7}" width="{w-40}" height="{h-42-(top-7)}"/></clipPath></defs>','<g clip-path="url(#event-clip)">',f'<g transform="translate(0 {top})"><g class="event-scroll"><g id="event-cycle">'])
        y=0
        for i,(event,chunks,row_height) in enumerate(records):
            ts=event.get('ts','').replace('T',' ')[:19]
            if i%2==0:
                p.append(f'<rect x="20" y="{y-7}" width="{w-40}" height="{row_height}" fill="#b4bcb0" opacity=".028"/>')
            if mobile:
                p.append(text(28,y+8,ts+' UTC',13,MUTED))
                for j,chunk in enumerate(chunks):
                    p.append(text(28,y+27+j*17,chunk,13,AMBER if j==0 else INK))
            else:
                p.append(text(28,y+12,ts,13,MUTED))
                for j,chunk in enumerate(chunks):
                    p.append(text(230,y+12+j*17,chunk,13,AMBER))
            y+=row_height
        p.append('</g>')
        if scroll:
            p.append(f'<use href="#event-cycle" transform="translate(0 {period})" aria-hidden="true"/>')
        p.extend(['</g></g></g>'])
    p.append('</svg>')
    return '\n'.join(p)


def fetch_online():
    """Strict fetches: any failed source keeps that panel's previous timestamp."""
    now=dt.datetime.now(dt.timezone.utc)
    results={}
    errors={}
    try:
        raw=_github.get_paged(f'users/{USER}/repos',sort='updated',per_page=100,max_pages=100)
    except _github.GitHubError as exc:
        raw=None
        errors.update({k:str(exc) for k in ('repos','stats','lang','syslog')})
    if raw is None:
        return results,errors
    owned=[r for r in raw if not r.get('fork') and not r.get('private')]
    active=[r for r in owned if not r.get('archived')]
    results['repos']=sorted([{'name':r.get('name','?'),'size':int(r.get('size',0) or 0),'stars':int(r.get('stargazers_count',0) or 0),'forks':int(r.get('forks_count',0) or 0),'lang':r.get('language') or '', 'pushed_at':r.get('pushed_at') or r.get('updated_at') or ''} for r in active],key=lambda r:(r['stars'],r['pushed_at']),reverse=True)
    try:
        totals={}
        for r in active:
            langs=_github.get(f"repos/{r['full_name']}/languages")
            if not isinstance(langs,dict):
                raise _github.GitHubError('invalid language response')
            for lang,count in langs.items():
                totals[lang]=totals.get(lang,0)+int(count)
        results['lang']=totals
    except (_github.GitHubError,ValueError,KeyError) as exc:
        errors['lang']=str(exc)
    try:
        user=_github.get(f'users/{USER}')
        if not isinstance(user,dict) or 'followers' not in user:
            raise _github.GitHubError('invalid user response')
        s={'followers':user['followers'],'following':user.get('following'),'repos':len(owned),'public_repos':user.get('public_repos'),'stars':sum(r.get('stargazers_count',0) or 0 for r in owned),'forks':sum(r.get('forks_count',0) or 0 for r in owned),'commits_90d':None,'current_streak':None,'longest_streak':None,'total_year':None}
        try:
            events=_github.get_paged(f'users/{USER}/events/public',per_page=100,max_pages=3)
            pushes=[e for e in events if e.get('type')=='PushEvent' and e.get('created_at','')>= (now-dt.timedelta(days=90)).isoformat()]
            # A missing PushEvent size is unknown, never an invented zero.
            if all(isinstance((e.get('payload') or {}).get('size'),int) for e in pushes):
                s['commits_90d']=sum(e['payload']['size'] for e in pushes)
        except _github.GitHubError:
            pass
        try:
            g=_github.graphql(gen_stats.GRAPHQL_QUERY,{'login':USER})
            cal=g['user']['contributionsCollection']['contributionCalendar']
            if not cal.get('weeks'):
                raise ValueError('missing contribution calendar')
            s['current_streak'],s['longest_streak']=gen_stats._streaks(cal['weeks'],now.date())
            s['total_year']=cal.get('totalContributions')
        except (_github.GitHubError,TypeError,KeyError,ValueError):
            pass
        results['stats']=s
    except _github.GitHubError as exc:
        errors['stats']=str(exc)
    try:
        events=_github.get_paged(f'users/{USER}/events/public',per_page=100,max_pages=3)
        for r in active:
            events.extend(_github.get_paged(f"repos/{r['full_name']}/events",per_page=100,max_pages=1))
        unique={e['id']:e for e in events if e.get('id')}
        journal=[]
        for e in sorted(unique.values(),key=lambda e:e.get('created_at',''),reverse=True):
            renderer=gen_log.EVENT_RENDERERS.get(e.get('type'))
            if not renderer or gen_log._is_noise(e):
                continue
            facility,_,fmt=renderer
            journal.append({'ts':e.get('created_at',''),'facility':facility,'msg':fmt(e)})
        results['syslog']=journal[:40]
    except (_github.GitHubError,KeyError,ValueError,TypeError) as exc:
        errors['syslog']=str(exc)
    return results,errors


def generate(out_dir: str | Path, offline: bool=False) -> list[Path]:
    out=Path(out_dir)
    out.mkdir(parents=True,exist_ok=True)
    snapshots={kind:load_snapshot(out/f'{kind}.svg',kind) for kind in ('stats','repos','lang','syslog')}
    fresh,errors=({}, {}) if offline else fetch_online()
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    paths=[]
    for kind,render in [('stats',render_stats),('repos',render_repos),('lang',render_lang),('syslog',render_syslog)]:
        s=snapshots[kind]
        if kind in fresh:
            s={'version':2,'kind':kind,'sampled_at':now,'status':'SNAPSHOT','data':fresh[kind]}
        elif s.get('sampled_at') or s.get('data'):
            s={**s,'status':'CACHED'}
        if kind in errors:
            print(f'[telemetry] {kind}: source unavailable; retaining prior snapshot')
        for mobile in (False,True):
            svg=render(s,mobile)
            ET.fromstring(svg)
            path=out/(f'profile-{kind}-mobile.svg' if mobile else f'{kind}.svg')
            path.write_text(svg,encoding='utf-8',newline='\n')
            assert load_snapshot(path,kind)==s
            paths.append(path)
    return paths


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline',action='store_true')
    parser.add_argument('--out-dir',type=Path,default=Path(__file__).resolve().parents[1]/'assets')
    args=parser.parse_args()
    for path in generate(args.out_dir,offline=args.offline):
        print(path)
