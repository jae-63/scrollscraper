import json, re, os, sys
REPO=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
WB=os.path.join(REPO,'misc_mp3s/t2/40/from_wayback')
d=json.load(open(f'{REPO}/data/entire_torah.json'))
books={b['title']:b['chapter'] for b in d}
order=['Genesis','Exodus','Leviticus','Numbers','Deuteronomy']
def words(v):
    v=re.sub(r'\(.\)','',v).replace('׃','').replace('׀','')
    return [w for w in re.split(r'[\s־]+',v) if w]
avail={}
for bi,b in enumerate(order):
    for ci,ch in enumerate(books[b]):
        for vi,v in enumerate(ch):
            fn=f'{REPO}/local_ort_mp3s/t{bi+1}/{ci+1:02d}{vi+1:02d}.mp3'
            if bi==1 and ci==39: fn=f'{WB}/40{vi+1:02d}.mp3'
            if os.path.exists(fn): avail[(bi+1,ci+1,vi+1)]=words(v)
print('available verses',len(avail))
missing=[5]+list(range(7,15))+list(range(18,27))+[30,31,32,37,38]
# index n-grams
idx={}
for k,ws in avail.items():
    for i in range(len(ws)):
        for n in range(1,len(ws)-i+1):
            idx.setdefault(tuple(ws[i:i+n]),[]).append((k,i))
tot=0;spl=0
for m in missing:
    ws=words(books['Exodus'][39][m-1]); i=0; segs=[]
    while i<len(ws):
        n=len(ws)-i
        while n>0 and tuple(ws[i:i+n]) not in idx: n-=1
        if n==0: segs.append(('MISSING',ws[i])); i+=1; continue
        segs.append((n,idx[tuple(ws[i:i+n])][0][0])); i+=n
    miss=[s for s in segs if s[0]=='MISSING']
    tot+=len(ws); spl+=len(segs)
    print(f'40:{m} words={len(ws)} segments={len(segs)} unmatched={len(miss)}', [s[1] for s in miss] if miss else '', [s for s in segs if s[0]!='MISSING'])
