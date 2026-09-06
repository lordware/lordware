"""Self-contained engineering instrument SVGs; all readings are demonstration data."""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
import zlib
import math
import instrument_materials as materials

BG, PANEL, BORDER = '#111416', '#171b1e', '#343a3d'
INK, MUTED, AMBER, DIM, GRID = '#dfddd4', '#8d979a', '#e6ad59', '#886b3e', '#242c2f'


def text(x, y, value, size=13, color=INK, anchor='start', weight=400):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{escape(str(value))}</text>'


def rect(x, y, w, h, fill=PANEL, stroke=None, radius=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}"' + (f' stroke="{stroke}"' if stroke else '') + '/>'


def line(x1, y1, x2, y2, color=BORDER, dash=None):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>'


def screen(x,y,w,h):
    return materials.display(x,y,w,h)


def shell(w, h, module, title, description, extra='', stamp='DEMO CAPTURE'):
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',
         f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>',
         '<defs>'+materials.definitions(),
         f'<style>text{{font-family:Consolas,\'Liberation Mono\',monospace}}.scan{{animation:scan 8s linear infinite}}@keyframes scan{{0%,100%{{opacity:.12}}50%{{opacity:.65}}}}{extra}@media(prefers-reduced-motion:reduce){{.frames,.scan,.step-highlight{{animation:none!important}}}}</style></defs>',
         materials.chassis(w,h),
         text(24, 24, module, 12, MUTED, weight=700), text(w-24, 24, stamp, 11, AMBER, 'end')]
    return p


# CANopen default connection set, node 0x1A. SDO requests are client -> server.
FRAMES = [
    ('000.000', 0x000, 'NMT', bytes.fromhex('01 1A'), 'start node 0x1A'),
    ('000.004', 0x71A, 'HEARTBEAT', bytes.fromhex('05'), 'operational'),
    ('000.010', 0x080, 'SYNC', b'', 'cycle marker'),
    ('000.011', 0x19A, 'TPDO1', bytes.fromhex('27 00 00 00 00 00'), 'node -> master'),
    ('000.012', 0x21A, 'RPDO1', bytes.fromhex('0F 00 00 00 00 00'), 'master -> node'),
    ('000.020', 0x61A, 'SDO REQ', bytes.fromhex('40 41 60 00 00 00 00 00'), 'read 6041:00'),
    ('000.021', 0x59A, 'SDO RES', bytes.fromhex('4B 41 60 00 27 00 00 00'), 'statusword 0x0027'),
    ('001.004', 0x71A, 'HEARTBEAT', bytes.fromhex('05'), 'operational'),
]


def bus(mobile=False):
    w, h = (480, 380) if mobile else (960, 340)
    row_h, top, visible = (27, 134, 162) if mobile else (25, 131, 150)
    period = len(FRAMES)*row_h
    css = f'.frames{{animation:frames 32s linear infinite}}@keyframes frames{{to{{transform:translateY(-{period}px)}}}}'
    p = shell(w, h, '03 / FIELDBUS ANALYZER', 'CANopen bus monitor — demo capture',
              'Simulated CANopen traffic for node 0x1A. Default COB-IDs, valid NMT start command, operational heartbeat and SDO statusword upload. Slow repeating frame sequence; no live hardware.', css)
    p.extend([text(24, 67, 'CANopen / bus monitor', 20, INK, weight=700),
              text(24, 88, 'CAN 2.0A  /  500 kbit/s  /  NODE 0x1A', 12, MUTED),
              screen(16,104,w-32,visible+top-104+5)])
    if not mobile:
        p.extend([rect(731,52,204,35,BG,BORDER,2),text(743,74,'BUS STATE',11,MUTED),text(923,74,'OPERATIONAL',12,AMBER,'end')])
    cols = [25,103,209,248] if mobile else [28,142,220,359,413,658]
    headings = ['COB-ID','SERVICE','DLC','DATA [HEX]'] if mobile else ['TIME [s]','COB-ID','SERVICE','DLC','DATA [HEX]','INTERPRETATION']
    for x, name in zip(cols,headings):
        p.append(text(x,123,name,11,MUTED,weight=700))
    p.extend([line(17,130,w-17,130),f'<defs><clipPath id="frames-clip"><rect x="17" y="{top}" width="{w-34}" height="{visible}"/></clipPath></defs>',
              '<g clip-path="url(#frames-clip)">', f'<g transform="translate(0 {top})"><g class="frames">'])
    for i, (ts, cob, service, data, meaning) in enumerate(FRAMES*2):
        y = i*row_h
        if i%2==0:
            p.append(rect(17,y,w-34,row_h,PANEL))
        values = [f'0x{cob:03X}',service,str(len(data)),' '.join(f'{b:02X}' for b in data) or '—'] if mobile else [ts,f'0x{cob:03X}',service,str(len(data)),' '.join(f'{b:02X}' for b in data) or '—',meaning]
        for j,(x,value) in enumerate(zip(cols,values)):
            p.append(text(x,y+18,value,13,AMBER if j==(0 if mobile else 1) else (MUTED if j==len(values)-1 and not mobile else INK)))
    p.extend(['</g></g></g>'])
    if mobile:
        p.extend([text(24,321,'SDO / 6041:00 → 0x0027',14,AMBER,weight=700),
                  text(24,344,'CiA 402 · operation enabled',13,INK),text(24,364,'HEARTBEAT 0x71A · 05 = operational',12,MUTED)])
    else:
        p.extend([text(24,307,'SDO DECODE',11,MUTED,weight=700),text(133,307,'6041:00 → 0x0027',14,AMBER,weight=700),
                  text(339,307,'CiA 402 · operation enabled',13),text(24,328,'DEFAULT COB-ID SET',10,MUTED),
                  text(196,328,'NMT 000  /  SYNC 080  /  TPDO1 180+N  /  RPDO1 200+N  /  SDO 600+N ⇄ 580+N',11,MUTED)])
    p.append('</svg>')
    return '\n'.join(p)


def uart_bits(value):
    return [0]+[(value>>i)&1 for i in range(8)]+[1]


def trace(bits, x, step, hi, lo):
    d = [f'M {x} {hi}']
    for i,b in enumerate(bits):
        d.extend([f'V {hi if b else lo}',f'H {x+(i+1)*step}'])
    path=' '.join(d)
    return (f'<path d="{path}" fill="none" stroke="{AMBER}" stroke-opacity=".13" stroke-width="5" stroke-linejoin="miter"/>'
            f'<path d="{path}" fill="none" stroke="#f1c979" stroke-width="1.6" stroke-linejoin="miter"/>')


def rotary(x,y,r=21):
    p=[f'<g transform="translate({x} {y})">',
       f'<circle cy="2.5" r="{r+3}" fill="#05090c" opacity=".75"/>',
       f'<circle r="{r+1}" fill="url(#mat-screw)" stroke="#788383" stroke-width=".6"/>',
       f'<circle r="{r}" fill="#11191e"/>']
    for i in range(48):
        a=math.tau*i/48
        x1,y1=math.cos(a)*(r-2.5),math.sin(a)*(r-2.5)
        x2,y2=math.cos(a)*r,math.sin(a)*r
        p.append(f'<path d="M{x1:.2f} {y1:.2f}L{x2:.2f} {y2:.2f}" stroke="{"#748085" if i>23 else "#354349"}" stroke-width=".8"/>')
    p.extend([f'<circle r="{r-4}" fill="url(#mat-face)" stroke="#090e12"/>',
              f'<circle r="{r-5.5}" fill="none" stroke="#687579" stroke-opacity=".3" stroke-width=".6"/>',
              f'<path d="M-4 {-r+7}L-2 {-r+13}" stroke="#e8bc70" stroke-width="2" stroke-linecap="round"/>','</g>'])
    return ''.join(p)


def bnc(x,y):
    return (f'<g transform="translate({x} {y})"><ellipse cy="3" rx="20" ry="19" fill="#060b0f"/>'
            '<circle r="18" fill="url(#mat-screw)" stroke="#9aa6a3" stroke-width=".6"/>'
            '<circle r="14" fill="#17252c" stroke="#33454c" stroke-width="2"/>'
            '<circle r="11" fill="url(#mat-screw)" stroke="#c6cfbd" stroke-width=".5"/>'
            '<circle r="8" fill="#b5b3a0" stroke="#536262" stroke-width="1.5"/>'
            '<circle r="3.5" fill="#0b1c22" stroke="#8c7045"/>'
            '<circle r="1.7" fill="#d2ab65"/><rect x="-20" y="-3" width="5" height="6" rx="1" fill="url(#mat-screw)"/>'
            '<rect x="15" y="-3" width="5" height="6" rx="1" fill="url(#mat-screw)"/></g>')


def waveform(p,value,x,step,hi,lo,label_y):
    bits=uart_bits(value)
    p.append(rect(x,hi-8,step,lo-hi+16,PANEL))
    for i in range(11):
        p.append(line(x+i*step,hi-12,x+i*step,lo+11,GRID))
    for y in (hi,(hi+lo)/2,lo):
        p.append(line(x, y, x+10*step,y,GRID))
    p.extend([line(x,(hi+lo)/2,x+10*step,(hi+lo)/2,DIM,'3 5'),trace(bits,x,step,hi,lo)])
    for i,b in enumerate(bits):
        p.append(text(x+(i+.5)*step,label_y,('S' if i==0 else 'P' if i==9 else str(b)),12,AMBER if i in (0,9) else MUTED,'middle'))
    p.append(f'<path d="M {x-4} {hi-19} H {x+4} L {x} {hi-13} Z" fill="{AMBER}"/>')


def scope(mobile=False):
    w,h=(480,414) if mobile else (960,343)
    p=shell(w,h,'04 / LOGIC ANALYZER','UART logic capture — ASCII lw, 9600 baud, 8N1',
            'Demonstration TTL UART waveform at the logic side of an RS-232 transceiver. ASCII l is 0x6C and w is 0x77, eight data bits least significant bit first, one start and one stop bit. Bit period 104.17 microseconds. 3.3 V logic, falling edge trigger at 1.65 V.')
    p.extend([text(24,65,'UART / serial decode',20,INK,weight=700),text(24,85,'TTL UART · RS-232 transceiver logic side',12,MUTED)])
    if mobile:
        p.append(screen(16,99,448,192))
        for n,(value,hi) in enumerate(((0x6C,120),(0x77,213))):
            p.extend([text(27,hi+5,f'0x{value:02X}',14,AMBER,weight=700),text(27,hi+25,f"'{chr(value)}'",13,INK),text(27,hi+43,'3V3',10,MUTED)])
            waveform(p,value,104,33,hi,hi+31,hi+51)
        p.extend([text(24,309,'9600 8N1 · 104.17 µs/bit · LSB FIRST',12),text(24,324,'S=start  P=stop  /  trigger ↓ 1.65 V',11,MUTED)])
    else:
        p.extend([text(933,63,'9600 baud / 8N1',13,AMBER,'end'),text(933,85,'CH1  3.3 V / TTL',12,MUTED,'end'),screen(16,102,928,121)])
        for x,y,label in ((28,130,'3.3 V'),(28,156,'1.65'),(28,174,'0 V')):
            p.append(text(x,y,label,11,MUTED))
        x,step=104,37
        waveform(p,0x6C,x,step,124,169,188)
        waveform(p,0x77,x+10*step,step,124,169,188)
        p.extend([line(82,124,x,124,AMBER),line(x+20*step,124,928,124,AMBER)])
        for n,v in enumerate((0x6C,0x77)):
            bx=x+n*10*step
            p.extend([rect(bx,196,10*step,19,PANEL,BORDER),text(bx+5*step,210,f"0x{v:02X}  /  '{chr(v)}'",12,AMBER,'middle')])
        p.extend([text(24,243,'Δt / BIT  104.17 µs',12,AMBER),text(296,243,'TRIGGER ↓ 1.65 V',12),text(575,243,'LSB FIRST  /  S=start  P=stop',12,MUTED),
                  text(24,260,'DECODE  6C 77 → "lw"',11,MUTED),text(933,260,'10 bits/frame · 1.0417 ms/frame',11,MUTED,'end')])
    sy=347 if mobile else 280
    p.extend([line(17,sy,w-17,sy,'#10191e'),line(17,sy+1,w-17,sy+1,'#506064')])
    if mobile:
        p.extend([bnc(53,378),text(81,375,'CH1',11,AMBER),text(81,392,'TTL',10,MUTED),
                  text(184,374,'POSITION',10,MUTED),rotary(275,380,19),
                  text(326,374,'TRIGGER',10,MUTED),rotary(429,380,19)])
    else:
        p.extend([bnc(55,309),text(86,303,'CH1 / UART',11,AMBER),text(86,321,'3.3 V LOGIC',10,MUTED),
                  text(350,311,'POSITION',11,MUTED),rotary(463,310),
                  text(664,311,'TRIGGER',11,MUTED),rotary(776,310),
                  text(829,313,'1.65 V',12,INK)])
    p.append('</svg>')
    return '\n'.join(p)


DESCRIPTOR = b'lordware\x00embedded systems\x00firmware\x00C\x00C++\x00CANopen\x00UART\x00SPI\x00I2C\x00AVR\x00Arduino\x00'
DESCRIPTOR_CRC = zlib.crc32(DESCRIPTOR) & 0xFFFFFFFF
HIGHLIGHT_CSS = '.step-highlight{animation:highlight 18s linear infinite;opacity:0}@keyframes highlight{0%,12%,100%{opacity:0}3%,8%{opacity:.1}}'


def row_highlight(x,y,w,h,index):
    return f'<rect class="step-highlight" x="{x}" y="{y}" width="{w}" height="{h}" fill="{AMBER}" style="animation-delay:{index*1.8}s"/>'


def boot(mobile=False):
    w,h=(480,390) if mobile else (960,340)
    p=shell(w,h,'05 / STARTUP DIAGNOSTICS','Embedded target POST simulation',
            'Fixed simulated startup diagnostics for an ATmega2560 target. Hardware statuses are demonstration fixtures, not measurements. The descriptor length and CRC32 are computed from the exact fixed byte buffer in the memory inspector.',
            HIGHLIGHT_CSS,'POST SIMULATION')
    p.extend([text(24,67,'Power-on / self-test',20,INK,weight=700),text(24,89,'LORDWARE  /  AVR2560  /  COLD START',12,MUTED)])
    rows=[('00','RESET','POR vector','PASS'),('01','CLOCK','16.000 MHz','PASS'),
          ('02','SRAM','8,192 B / 00-FF','PASS'),('03','UART0','9600 / 8N1','PASS'),
          ('04','SPI','MCP2515 / W25Q64','PASS'),('05','CAN','500 kbit/s','PASS'),
          ('06','ROM CRC',f'{DESCRIPTOR_CRC:08X}','MATCH')]
    table_w=448 if mobile else 586
    p.extend([screen(16,105,table_w,204),text(28,126,'SEQ',10,MUTED,weight=700),text(71,126,'STAGE',10,MUTED,weight=700),
              text(164 if mobile else 198,126,'TEST FIXTURE',10,MUTED,weight=700),text(449 if mobile else 582,126,'RESULT',10,MUTED,'end',700),line(17,134,15+table_w,134)])
    for i,(seq,stage,detail,result) in enumerate(rows):
        y=136+i*24
        if i%2==0: p.append(rect(18,y,table_w-4,24,PANEL))
        p.extend([row_highlight(18,y,table_w-4,24,i),text(28,y+17,seq,13,MUTED),text(71,y+17,stage,13),
                  text(164 if mobile else 198,y+17,detail,12 if mobile else 13,AMBER),text(449 if mobile else 582,y+17,result,12,MUTED,'end')])
    if mobile:
        p.extend([text(24,335,'ROM / profile descriptor',13),text(24,355,f'{len(DESCRIPTOR):03d} bytes  ·  CRC32 {DESCRIPTOR_CRC:08X}',13,AMBER),text(24,377,'FIXTURE COMPLETE  /  07 OF 07',11,MUTED)])
    else:
        p.extend([screen(623,105,321,204),text(640,126,'TARGET CONFIGURATION',11,MUTED,weight=700)])
        for i,(key,value) in enumerate([('MCU','ATmega2560'),('SRAM','8 KiB'),('SPI FLASH','W25Q64 / 8 MiB'),('CAN CTRL','MCP2515'),('DESCRIPTOR',f'{len(DESCRIPTOR)} bytes')]):
            p.extend([text(640,151+i*24,key,11,MUTED),text(927,151+i*24,value,13,INK,'end')])
        p.extend([line(640,259,927,259),text(640,284,'CRC32',11,MUTED),text(927,285,f'{DESCRIPTOR_CRC:08X}',19,AMBER,'end',700),
                  text(24,329,'FIXTURE COMPLETE  /  07 OF 07',11,MUTED),text(934,329,'ROM / profile descriptor',11,MUTED,'end')])
    p.append('</svg>')
    return '\n'.join(p)


def hexdump(mobile=False):
    width=8 if mobile else 16
    rows=[DESCRIPTOR[i:i+width] for i in range(0,len(DESCRIPTOR),width)]
    w,h=(480,169+len(rows)*25) if mobile else (960,210+len(rows)*27)
    p=shell(w,h,'06 / MEMORY INSPECTOR','Byte-accurate lordware profile descriptor',
            f'Fixed {len(DESCRIPTOR)} byte ASCII descriptor. Hex and printable ASCII are generated from the same bytes; dots represent NUL or other nonprintable bytes. CRC32 {DESCRIPTOR_CRC:08X}.',
            HIGHLIGHT_CSS,'FIXED DATA')
    p.extend([text(24,67,'ROM / hex inspector',20,INK,weight=700),text(24,88,'profile.bin  /  ASCII + NUL  /  READ ONLY',12,MUTED)])
    y0=135
    rh=25 if mobile else 27
    p.extend([screen(16,105,w-32,len(rows)*rh+34),text(27,125,'OFFSET',10,MUTED,weight=700)])
    hx=95 if mobile else 146
    step=29 if mobile else 34
    ax=340 if mobile else 720
    for i in range(width):
        p.append(text(hx+i*step,125,f'{i:02X}',11,MUTED))
    p.extend([text(ax,125,'ASCII',11,MUTED),line(17,132,w-17,132),line(ax-14,107,ax-14,135+len(rows)*rh,GRID)])
    for n,chunk in enumerate(rows):
        y=y0+n*rh
        if n%2==0: p.append(rect(18,y,w-36,rh,PANEL))
        p.extend([row_highlight(18,y,w-36,rh,n),text(27,y+18,f'{n*width:04X}' if mobile else f'{n*width:08X}',13,MUTED)])
        for i,b in enumerate(chunk):
            p.append(text(hx+i*step,y+18,f'{b:02X}',13,AMBER if b==0 else INK))
        p.append(text(ax,y+18,''.join(chr(b) if 32<=b<127 else '.' for b in chunk),13,AMBER))
    fy=147+len(rows)*rh
    if mobile:
        p.extend([text(24,fy,f'{len(DESCRIPTOR)} BYTES  /  CRC32 {DESCRIPTOR_CRC:08X}',12,AMBER),text(24,fy+17,'00 = NUL  ·  . = nonprintable',11,MUTED)])
    else:
        p.extend([text(24,fy+3,f'LENGTH  {len(DESCRIPTOR):04d} bytes',12,MUTED),text(337,fy+3,f'CRC32  {DESCRIPTOR_CRC:08X}',12,AMBER),text(933,fy+3,'00 = NUL  /  . = nonprintable',12,MUTED,'end'),
                  line(24,fy+17,934,fy+17,GRID),text(24,fy+39,'SELECTION',10,MUTED),text(144,fy+39,'0000–0007',12,INK),text(337,fy+39,'6C 6F 72 64 77 61 72 65',12,AMBER),text(933,fy+39,'"lordware"',12,INK,'end')])
    p.append('</svg>')
    return '\n'.join(p)


def validate_protocol():
    assert {f[1] for f in FRAMES} == {0x000,0x080,0x19A,0x21A,0x61A,0x59A,0x71A}
    assert all(len(f[3])<=8 for f in FRAMES)
    assert FRAMES[0][3] == b'\x01\x1a' and FRAMES[1][3] == b'\x05'
    assert int.from_bytes(FRAMES[6][3][1:3],'little')==0x6041
    assert int.from_bytes(FRAMES[6][3][4:6],'little')==0x0027
    assert (0x0027 & 0x006F)==0x0027  # CiA 402 state mask.
    assert bytes.fromhex('6C 6F 72 64 77 61 72 65') == DESCRIPTOR[:8]
    assert zlib.crc32(DESCRIPTOR)&0xFFFFFFFF == DESCRIPTOR_CRC
    assert b''.join(DESCRIPTOR[i:i+8] for i in range(0,len(DESCRIPTOR),8)) == DESCRIPTOR
    for value in (0x6C,0x77):
        bits=uart_bits(value)
        assert bits[0]==0 and bits[-1]==1 and len(bits)==10
        assert sum(b<<i for i,b in enumerate(bits[1:9]))==value


def generate(out_dir: str | Path = 'assets') -> list[Path]:
    validate_protocol()
    out=Path(out_dir)
    out.mkdir(parents=True,exist_ok=True)
    paths=[]
    for name,render in [('bus',bus),('scope',scope)]:
        for mobile in (False,True):
            svg=render(mobile)
            ET.fromstring(svg)
            path=out/(f'profile-{name}-mobile.svg' if mobile else ('can-bus.svg' if name=='bus' else 'scope.svg'))
            path.write_text(svg,encoding='utf-8',newline='\n')
            paths.append(path)
    for name,render in [('boot',boot),('hexdump',hexdump)]:
        for mobile in (False,True):
            svg=render(mobile)
            ET.fromstring(svg)
            path=out/(f'profile-{name}-mobile.svg' if mobile else f'{name}.svg')
            path.write_text(svg,encoding='utf-8',newline='\n')
            paths.append(path)
    return paths


if __name__=='__main__':
    for result in generate(Path(__file__).resolve().parents[1]/'assets'):
        print(result)
