"""v3: Viterbi unit selection with join costs (pitch continuity, tempo, timbre), gentle re-pitching (no time warp).
Units must match letters, vowels and trope marks exactly; see README, "How the ta'amim are used"."""
import os, sys, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from synth2 import (avail, audio, word_span, clip, norm, pref, Bk, ORDER, words, lv, accent_sig, nsyl, groups_of,
                    accent_group, contour, composite, trim_sil, xfade, rms, apply_bookend, SR, roman, align)
import synth2, soundfile as sf, subprocess, parselmouth
from parselmouth.praat import call
OUT=os.environ.get('CHANT_SIM_OUT', os.path.join(REPO,'misc_mp3s/t2/40/replacements')); os.makedirs(OUT,exist_ok=True)
WAYBACK=lambda k: k[0]==2 and k[1]==40
FEAT={}
def st(f): return 12*np.log2(f/110)
def feats(k,i,n):
    key=(k,i,n)
    if key in FEAT: return FEAT[key]
    x,on,off=clip(k,i,n); t,f=contour(x); v=f>0
    if v.sum()<5: r=dict(p0=np.nan,p1=np.nan,med=np.nan,rate=np.nan,tim=np.zeros(8))
    else:
        tv=t[v]; fv=st(f[v])
        p0=np.median(fv[tv<tv[0]+0.25]); p1=np.median(fv[tv>tv[-1]-0.25])
        syl=sum(nsyl(w) for w in avail[k][i:i+n]); rate=syl/max(0.2,off-on)
        X=np.abs(np.fft.rfft(x[:len(x)//1024*1024].reshape(-1,1024)*np.hanning(1024),axis=1)).mean(0)
        bands=np.array([X[a:b].sum() for a,b in zip(np.geomspace(4,512,9).astype(int)[:-1],np.geomspace(4,512,9).astype(int)[1:])])
        r=dict(p0=p0,p1=p1,med=np.median(fv),rate=rate,tim=np.log(bands/bands.sum()+1e-9))
    FEAT[key]=r; return r
def candidates(idx,ws,i,j,tgt,K=8):
    out=[]
    for l in (0,1):
        key=tuple(norm(w,l) for w in ws[i:j])
        if key in idx[l]:
            c=idx[l][key]
            if j==len(ws): c=[x for x in c if x[1]+(j-i)==len(avail[x[0]])] or c
            # internal position match matters a little (verse-initial words have onset breath)
            c=sorted(c,key=lambda x:(WAYBACK(x[0]), pref(x[0],tgt), (x[1]==0)!=(i==0)))[:K]
            out+= [(x,l) for x in c]; break
    return out
def unit_cost(f,l,k):
    return 1.0+0.3*l+(0.6 if WAYBACK(k) else 0)+(0 if not np.isnan(f['med']) and abs(f['med']-11)<3 else 0.5)
def join_cost(fa,fb):
    if np.isnan(fa['p1']) or np.isnan(fb['p0']): return 0.5
    jump=abs(fa['p1']-fb['p0']); tempo=abs(np.log(fa['rate']/fb['rate'])) if fa['rate']>0 and fb['rate']>0 else 0
    tim=np.sqrt(np.mean((fa['tim']-fb['tim'])**2))
    return 0.12*max(0,jump-2)+1.0*tempo+0.8*tim
def plan(tgt, ws, idx):
    n=len(ws)
    # lattice nodes: (i,j,cand) ; Viterbi over end positions
    nodes={}  # j -> list of (cost, i, src, l, feat, backptr)
    nodes[0]=[(0.0,None,None,None,None,None)]
    for j in range(1,n+1):
        lst=[]
        for i in range(max(0,j-8),j):
            if not nodes.get(i): continue
            for (src,l) in candidates(idx,ws,i,j,tgt):
                f=feats(src[0],src[1],j-i); uc=unit_cost(f,l,src[0])
                best=None
                for bi,prev in enumerate(nodes[i]):
                    c=prev[0]+uc+(join_cost(prev[4],f) if prev[4] is not None else 0)
                    if best is None or c<best[0]: best=(c,i,src,l,f,(i,bi))
                lst.append(best)
            if not candidates(idx,ws,i,j,tgt) and j==i+1:
                bestprev=min(range(len(nodes[i])),key=lambda b:nodes[i][b][0])
                lst.append((nodes[i][bestprev][0]+4.0,i,None,9,None,(i,bestprev)))
        lst.sort(key=lambda x:x[0]); nodes[j]=lst[:12]
    segs=[]; j=n; b=0
    while j>0:
        c,i,src,l,f,bp=nodes[j][b]; segs.append(('splice' if src else 'retrope',i,src,j-i)); j,b=bp
    return segs[::-1]
# ---------- gentle retrope ----------
def melody_cands(ws,i,bysig,tgt,K=12):
    w=ws[i]; sig=accent_sig(w); ns=nsyl(w); g=groups_of(w); tail=nsyl(''.join(c+m for c,m in g[accent_group(w)+1:]))
    nxt=accent_sig(ws[i+1]) if i+1<len(ws) else None; final=i==len(ws)-1; sc=[]
    for k,j in bysig.get(sig,[]):
        ws2=avail[k]; w2=ws2[j]
        if (j==len(ws2)-1)!=final or WAYBACK(k): continue
        g2=groups_of(w2); tail2=nsyl(''.join(c+m for c,m in g2[accent_group(w2)+1:]))
        s=abs(nsyl(w2)-ns)+2*abs(tail2-tail)+(0 if (accent_sig(ws2[j+1]) if j+1<len(ws2) else None)==nxt else 1.5)+0.3*pref(k,tgt)[0]
        sc.append((s,k,j))
    sc.sort(); return sc[:K]
def norm_contour(x):
    t,f=contour(x); v=f>0
    if v.sum()<5: return None
    tv=t[v]; fv=st(f[v]); 
    # remove octave glitches
    m=np.median(fv); fv=np.where(fv>m+9,fv-12,np.where(fv<m-9,fv+12,fv))
    u=(tv-tv[0])/max(1e-3,tv[-1]-tv[0]); return u,fv,tv[0],tv[-1]
def best_retrope(ws,i,bylv,bysig,tgt,exclude):
    mels=[]
    for s,k,j in melody_cands(ws,i,bysig,tgt):
        x,_,_=clip(k,j); c=norm_contour(x)
        if c: mels.append((s,k,j,c))
    phs=[]
    for k,j in (bylv.get(lv(ws[i])) or []):
        if k in exclude: continue
        phs.append((k,j))
    phs=sorted(phs,key=lambda x:(WAYBACK(x[0]),pref(x[0],tgt)))[:12]
    best=None
    for k,j in phs:
        x,_,_=clip(k,j); c=norm_contour(x)
        if not c: continue
        for s,mk,mj,mc in mels[:6]:
            grid=np.linspace(0,1,50); a=np.interp(grid,c[0],c[1]); b=np.interp(grid,mc[0],mc[1])
            d=np.sqrt(np.mean((a-b)**2)); cost=d+0.3*s+(1 if WAYBACK(k) else 0)
            if best is None or cost<best[0]: best=(cost,x,c,(k,j),(mk,mj),mc,d)
    if best is None:  # composite phonetics
        x,desc=composite(ws[i],exclude,tgt); x=trim_sil(x); c=norm_contour(x)
        s,mk,mj,mc=mels[0]; grid=np.linspace(0,1,50)
        d=np.sqrt(np.mean((np.interp(grid,c[0],c[1])-np.interp(grid,mc[0],mc[1]))**2)) if c else 9
        best=(d,x,c,('composite',desc),(mk,mj),mc,d)
    cost,x,c,pd,md,mc,d=best
    if d<0.9 or c is None: return x,pd,md,d,'raw'
    # impose melody shape on donor's own voiced span, no time warp; blend toward donor contour to limit shift
    snd=parselmouth.Sound(x.astype(np.float64),SR); man=call(snd,"To Manipulation",0.01,70,400)
    pt=call("Create PitchTier","p",0,len(x)/SR)
    grid=np.linspace(0,1,80); tgtc=np.interp(grid,mc[0],mc[1]); own=np.interp(grid,c[0],c[1])
    tgtc=tgtc-np.median(tgtc)+np.median(own)              # keep donor's register
    tgtc=own+np.clip(tgtc-own,-4,4)                        # cap shifts at 4 semitones
    tgtc=np.convolve(np.pad(tgtc,3,mode='edge'),np.ones(7)/7,'valid')
    for g,v in zip(grid,tgtc): call(pt,"Add point",c[2]+g*(c[3]-c[2]),110*2**(v/12))
    call([pt,man],"Replace pitch tier")
    y=np.array(call(man,"Get resynthesis (overlap-add)").values[0],dtype=np.float32)
    return y,pd,md,d,'repitched'
def synth(tgt, exclude=(), tag='', bookend=False):
    exclude=set(exclude)|{tgt}
    idx,bylv,bysig=synth2.build(exclude)
    ws=words(Bk[ORDER[tgt[0]-1]][tgt[1]-1][tgt[2]-1]); segs=plan(tgt,ws,idx)
    pieces=[]; rep=[]
    for t,i,src,ln in segs:
        if t=='splice':
            k,p=src; x,_,_=clip(k,p,ln); rep.append(f'  splice  {" ".join(roman(w) for w in ws[i:i+ln]):40s} <- {k[0]}:{k[1]}:{k[2]}{" (wayback)" if WAYBACK(k) else ""}')
        else:
            x,pd,md,d,how=best_retrope(ws,i,bylv,bysig,tgt,exclude)
            pdesc=f'{pd[0][0]}:{pd[0][1]}:{pd[0][2]}' if pd[0]!='composite' else 'pieces '+pd[1]
            rep.append(f'  {how:9s} {roman(ws[i]):38s} phonetics<-{pdesc}; melody<-{md[0][0]}:{md[0][1]}:{md[0][2]} (contour diff {d:.1f}st)')
        pieces.append((i,ln,x*(0.08/rms(x))))
    if bookend: pieces,extra=apply_bookend(ws,pieces,exclude,tgt); rep+=extra
    out=pieces[0][2]
    for _,_,p in pieces[1:]: out=xfade(out,p,0.03)
    out=np.concatenate([np.zeros(int(0.07*SR),np.float32),out]); out=out/max(1e-6,np.abs(out).max())*0.89
    name=f'{OUT}/{tgt[1]:02d}{tgt[2]:02d}{tag}'; sf.write(name+'.wav',out,SR)
    subprocess.run(['ffmpeg','-v','error','-y','-i',name+'.wav','-ar','16000','-ac','2','-b:a','48k',name+'.mp3'])
    return name,rep
if __name__=='__main__':
    tag=sys.argv[2] if len(sys.argv)>2 else ''
    for v in map(int,sys.argv[1].split(',')):
        name,rep=synth((2,40,v),tag=tag,bookend=(v==38 and tag==''))
        print(f'40:{v} -> {os.path.basename(name)}.mp3'); print('\n'.join(rep), flush=True)
