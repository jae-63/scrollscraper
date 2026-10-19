import re, json, unicodedata
import os
REPO=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
CONS={'א':'','ב':'v','ג':'g','ד':'d','ה':'h','ו':'v','ז':'z','ח':'h','ט':'t','י':'y','כ':'h','ך':'h','ל':'l','מ':'m','ם':'m','נ':'n','ן':'n','ס':'s','ע':'','פ':'f','ף':'f','צ':'ts','ץ':'ts','ק':'k','ר':'r','ש':'sh','ת':'t'}
DAG={'ב':'b','כ':'k','ך':'k','פ':'p'}
V={'ַ':'a','ָ':'a','ֲ':'a','ֳ':'o','ֶ':'e','ֵ':'e','ֱ':'e','ִ':'i','ֹ':'o','ֺ':'o','ֻ':'u','ְ':''}
def strip_trope(w):  # keep letters + niqqud (05B0-05BC, 05C1,05C2, 05C7)
    return ''.join(c for c in w if 'א'<=c<='ת' or 'ְ'<=c<='ּ' or c in 'ׇׁׂ')
def translit(w):
    w=strip_trope(w); out=[]; i=0
    # group letters with marks
    groups=[]
    for c in w:
        if 'א'<=c<='ת': groups.append([c,''])
        elif groups: groups[-1][1]+=c
    for gi,(c,m) in enumerate(groups):
        dag='ּ' in m
        if c=='ו' and dag and not any(x in m for x in V if x!='ְ'): out.append('u'); continue
        if c=='ו' and 'ֹ' in m and gi>0: out.append('o'); continue
        if c=='י' and not any(x in m for x in V) and gi>0 and groups[gi-1][1] and any(x in groups[gi-1][1] for x in 'ִֵֶ'): continue
        if c=='ה' and gi==len(groups)-1 and not dag: 
            pass_cons=''
        elif c=='ש': pass_cons='s' if 'ׂ' in m else 'sh'
        elif dag and c in DAG: pass_cons=DAG[c]
        else: pass_cons=CONS[c]
        v=''
        for x,val in V.items():
            if x in m: v=val
        if c=='ח' and gi==len(groups)-1 and 'ַ' in m: out.append('a'+pass_cons); continue  # patah genuva
        if 'ְ' in m and gi==0: v='e'
        out.append(pass_cons+v)
    return ''.join(out)
def load():
    d=json.load(open(f'{REPO}/data/entire_torah.json'))
    return {b['title']:b['chapter'] for b in d}
ORDER=['Genesis','Exodus','Leviticus','Numbers','Deuteronomy']
def words(v):
    v=re.sub(r'\([^)]*\)','',v).replace('׃','').replace('׀','').replace('׀','')
    return [w for w in re.split(r'[\s־]+',v) if w]
if __name__=='__main__':
    B=load()
    for w in words(B['Exodus'][39][26]): print(w, translit(w))

ACC=set(chr(c) for c in range(0x0591,0x05AF))
def groups_of(w):
    g=[]
    for c in unicodedata.normalize('NFC',w):
        if 'א'<=c<='ת': g.append([c,''])
        elif g: g[-1][1]+=c
    return g
def accent_sig(w):
    return ''.join(sorted(c for c in w if c in ACC)) or ('ֽ' if 'ֽ' in w else '')
def lv(w): return ''.join(c for c in unicodedata.normalize('NFC',w) if c not in ACC and c!='ֽ')
def accent_group(w):
    g=groups_of(w); idx=[i for i,(c,m) in enumerate(g) if any(x in ACC for x in m)]
    # prepositive/postpositive accents (pashta, zarqa, segol, telisha) sit on edge letters; treat as last vowel group
    if not idx: idx=[i for i,(c,m) in enumerate(g) if 'ֽ' in m]
    if not idx: return len(g)-1
    i=idx[-1] if len(idx)>1 else idx[0]
    return i
def nsyl(w): return sum(1 for c,m in groups_of(w) if any(x in m for x in 'ֱֲֳִֵֶַָֹֺֻ') or (c=='ו' and 'ּ' in m and len(m)<=2))
