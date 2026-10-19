"""Build a self-contained listening page for Exodus 40 (genuine vs simulated audio) and print how to serve it.

usage: python make_listen_page.py OUTDIR [--sim DIR] [--loo DIR] [--misc DIR]
Browsers refuse to play audio from other local folders on a file:// page, so all audio is copied next to
index.html; serve it with:  python3 -m http.server --directory OUTDIR --bind 127.0.0.1 0
"""
import argparse, json, os, shutil, html, re
from heb import REPO
ap=argparse.ArgumentParser(); ap.add_argument('out')
ap.add_argument('--sim',default=f'{REPO}/misc_mp3s/t2/40/replacements')
ap.add_argument('--loo',default=None,help='dir with 40NN_loo.mp3 blind tests')
ap.add_argument('--prev',default=None,help='dir with an earlier simulation version, for A/B')
ap.add_argument('--misc',default=f'{REPO}/misc_mp3s/t2/40/from_scrollscraper')
a=ap.parse_args(); A=os.path.join(a.out,'audio'); os.makedirs(A,exist_ok=True)
ch=[b for b in json.load(open(f'{REPO}/data/entire_torah.json')) if b['title']=='Exodus'][0]['chapter'][39]
def cp(src,name):
    if src and os.path.exists(src): shutil.copy(src,os.path.join(A,name)); return f'audio/{name}'
prov={}
pf=os.path.join(a.sim,'PROVENANCE.txt')
if os.path.exists(pf):
    for b in open(pf).read().split('\n40:'):
        m=re.match(r'(?:40:)?(\d+) ',b)
        if m: prov[int(m.group(1))]=b
def player(src,label,cls): return f'<div><audio controls preload="none" src="{src}"></audio><span class="tag {cls}">{label}</span></div>'
rows=[]
for v in range(1,39):
    n=f'40{v:02d}.mp3'; cells=[]
    for d,label,cls in [(f'{REPO}/misc_mp3s/t2/40/from_wayback','genuine (Wayback)','real'),(a.misc,'genuine (ScrollScraper capture)','real')]:
        s=cp(os.path.join(d,n),cls+'_'+label[:4]+n)
        if s: cells.append(player(s,label,cls))
    s=cp(os.path.join(a.sim,n),'sim_'+n)
    if s: cells.append(player(s,'simulated' if not cells else 'simulated (genuine exists)','sim'))
    if a.prev:
        s=cp(os.path.join(a.prev,n),f'prev_{n}')
        if s: cells.append(player(s,'previous simulation version','prev'))
    if a.loo:
        s=cp(os.path.join(a.loo,f'40{v:02d}_loo.mp3'),f'loo_{n}')
        if s: cells.append(player(s,'blind simulation (real verse excluded)','loo'))
    det=f'<details><summary>how it was built</summary><pre>{html.escape(prov[v])}</pre></details>' if v in prov else ''
    rows.append(f'<tr><td class="n">40:{v}</td><td><div class="heb" dir="rtl">{ch[v-1]}</div>{"".join(cells) or "<i>no audio</i>"}{det}</td></tr>')
open(os.path.join(a.out,'index.html'),'w').write(f'''<!doctype html><meta charset="utf-8"><title>Exodus 40 audio review</title>
<style>body{{font-family:system-ui;max-width:900px;margin:2em auto;padding:0 16px}}.heb{{font-size:1.5em;font-family:"SBL Hebrew","Times New Roman",serif;margin:.3em 0}}td{{vertical-align:top;border-bottom:1px solid #ddd;padding:.6em}}.n{{font-weight:bold}}.tag{{font-size:.8em;padding:2px 6px;border-radius:4px;margin-left:8px}}.real{{background:#d4f5d4}}.sim{{background:#ffe2b8}}.loo{{background:#e2e2ff}}.prev{{background:#eee}}pre{{font-size:.75em;white-space:pre-wrap}}audio{{vertical-align:middle;height:32px;margin:2px 0}}</style>
<h1>Exodus 40 — genuine + simulated audio</h1><table>{"".join(rows)}</table>''')
print(f'wrote {a.out}/index.html\nserve with: python3 -m http.server --directory {a.out} --bind 127.0.0.1 0')
