import os, sys, json, numpy as np, soundfile as sf, subprocess, unicodedata, parselmouth
from parselmouth.praat import call
sys.path.insert(0, os.path.dirname(__file__))
from heb import *
from heb import REPO
from align import align, audio_path, load_audio, SR, roman
from pitch import f0
OUT=os.environ.get('CHANT_SIM_OUT', os.path.join(REPO,'misc_mp3s/t2/40/replacements')); os.makedirs(OUT,exist_ok=True)
Bk=load()
def norm(w,l): w=unicodedata.normalize('NFC',w); return w.replace('ֽ','') if l else w
avail={}
for bi,b in enumerate(ORDER):
    for ci,ch in enumerate(Bk[b]):
        for vi,v in enumerate(ch):
            k=(bi+1,ci+1,vi+1)
            if os.path.exists(audio_path(*k)): avail[k]=words(v)
_audio={}
def audio(k):
    if k not in _audio: _audio[k]=load_audio(audio_path(*k))
    return _audio[k]
def pref(k,tgt): b,c,v=k; return (0 if b==2 else 1, abs(c-tgt[1]) if b==2 else 0)
def word_span(k,i,n=1):
    al=align(*k); W=al['words']
    s=0.0 if i==0 else (W[i-1]['e']+W[i]['s'])/2
    e=al['dur'] if i+n==len(W) else (W[i+n-1]['e']+W[i+n]['s'])/2
    # internal words: don't swallow long trailing pause > 0.35s
    if i+n<len(W): e=min(e, W[i+n-1]['e']+0.35)
    if i>0: s=max(s, W[i]['s']-0.12)
    return s,e,W
def clip(k,i,n=1):
    s,e,W=word_span(k,i,n); return audio(k)[int(s*SR):int(e*SR)].copy(), W[i]['s']-s, W[i+n-1]['e']-s
# ---------------- index ----------------
def build(exclude):
    idx=[{},{}]; bylv={}; bysig={}
    for k,ws in avail.items():
        if k in exclude: continue
        for l in (0,1):
            nw=[norm(w,l) for w in ws]
            for i in range(len(nw)):
                for n in range(1,min(8,len(nw)-i)+1): idx[l].setdefault(tuple(nw[i:i+n]),[]).append((k,i))
        for i,w in enumerate(ws):
            bylv.setdefault(lv(w),[]).append((k,i))
            bysig.setdefault(accent_sig(w),[]).append((k,i))
    return idx,bylv,bysig
def plan(tgt, ws, idx):
    n=len(ws); INF=1e9; best=[INF]*(n+1); back=[None]*(n+1); best[0]=0
    for i in range(n):
        if best[i]>=INF: continue
        for j in range(i+1,min(n,i+8)+1):
            for l in (0,1):
                key=tuple(norm(w,l) for w in ws[i:j])
                if key in idx[l]:
                    c=idx[l][key]
                    if j==n: c=[x for x in c if x[1]+(j-i)==len(avail[x[0]])] or c
                    src=min(c,key=lambda x:(pref(x[0],tgt), x[1]!=0 if i==0 else 0))
                    cost=best[i]+1+0.3*l+0.2*pref(src[0],tgt)[0]+0.005*pref(src[0],tgt)[1]
                    if cost<best[j]: best[j]=cost; back[j]=('splice',i,src,j-i)
                    break
        if best[i]+4<best[i+1]: best[i+1]=best[i]+4; back[i+1]=('retrope',i,None,1)
    segs=[]; j=n
    while j>0: t,i,src,ln=back[j]; segs.append((t,i,src,ln)); j=i
    return segs[::-1]
# ------------- retrope ---------------
def melody_donor(ws,i,bysig,tgt):
    w=ws[i]; sig=accent_sig(w); ns=nsyl(w); g=groups_of(w); tail=nsyl(''.join(c+m for c,m in g[accent_group(w)+1:]))
    nxt=accent_sig(ws[i+1]) if i+1<len(ws) else None; final=i==len(ws)-1
    best=None
    for k,j in bysig.get(sig,[]):
        ws2=avail[k]; w2=ws2[j]
        if (j==len(ws2)-1)!=final: continue
        g2=groups_of(w2); tail2=nsyl(''.join(c+m for c,m in g2[accent_group(w2)+1:]))
        sc=abs(nsyl(w2)-ns)+2*abs(tail2-tail)+(0 if (accent_sig(ws2[j+1]) if j+1<len(ws2) else None)==nxt else 1.5)+0.3*pref(k,tgt)[0]
        if best is None or sc<best[0]: best=(sc,k,j)
    return best
def phon_donor(w,bylv,tgt):
    c=bylv.get(lv(w))
    if c: return min(c,key=lambda x:pref(x[0],tgt)), 'same word, other trope'
    return None,None
def contour(x):
    p=parselmouth.Sound(x.astype(np.float64),SR).to_pitch(time_step=0.01,pitch_floor=70,pitch_ceiling=400)
    t=p.xs(); f=p.selected_array['frequency']; return t,f
def retarget(phon, pon, poff, mel, mon, moff, shift=0.0, mel_override=None):
    """impose melody contour of `mel` on `phon`, matching durations; anchors at word onset/offset"""
    tm,fm=contour(mel) if mel_override is None else mel_override
    Dp=len(phon)/SR; Dm=len(mel)/SR
    snd=parselmouth.Sound(phon.astype(np.float64),SR)
    man=call(snd,"To Manipulation",0.01,70,400)
    pt=call("Create PitchTier","p",0,Dp)
    def m2p(t):  # piecewise linear: [0,mon,moff,Dm] -> [0,pon,poff,Dp]
        return float(np.interp(t,[0,mon,moff,Dm],[0,pon,poff,Dp]))
    v=fm>0
    for t,f in zip(tm[v],fm[v]): call(pt,"Add point",m2p(t),f*2**(shift/12))
    call([pt,man],"Replace pitch tier")
    dt=call("Create DurationTier","d",0,Dp)
    for a,b,c,d in [(0,pon,0,mon),(pon,poff,mon,moff),(poff,Dp,moff,Dm)]:
        fac=max(0.4,min(2.5,(d-c)/max(b-a,1e-3)))
        call(dt,"Add point",a+1e-4,fac); call(dt,"Add point",max(a+2e-4,b-1e-4),fac)
    call([dt,man],"Replace duration tier")
    out=call(man,"Get resynthesis (overlap-add)")
    return np.array(out.values[0],dtype=np.float32)
# --------- composite phonetics for words never seen -----------
_romcache=None
def rom_index(exclude):
    global _romcache
    if _romcache is None:
        _romcache=[(k,i,roman(w)) for k,ws in avail.items() if k not in exclude for i,w in enumerate(ws)]
    return _romcache
def composite(w, exclude, tgt):
    R=roman(w); pieces=[]; pos=0; RI=rom_index(exclude)
    while pos<len(R):
        bestp=None
        for L in range(len(R)-pos,0,-1):
            sub=R[pos:pos+L]
            c=[(k,i,r) for k,i,r in RI if (r.startswith(sub) if pos==0 else (r.endswith(sub) if pos+L==len(R) else sub in r))]
            if c: bestp=(sub,min(c,key=lambda x:(pref(x[0],tgt),abs(len(x[2])-L)))); break
        if not bestp: pos+=1; continue
        sub,(k,i,r)=bestp; al=align(*k); W=al['words'][i]
        cs=W.get('cs')
        off=r.find(sub) if pos>0 else 0
        if pos+len(sub)==len(R): off=len(r)-len(sub)
        a=audio(k); s,e,_=word_span(k,i)
        if cs:
            t0=s if off==0 else cs[off][0]; t1=e if off+len(sub)==len(r) else cs[off+len(sub)-1][1]+0.03
        else:
            t0=W['s']+(W['e']-W['s'])*off/len(r); t1=W['s']+(W['e']-W['s'])*(off+len(sub))/len(r)
        pieces.append((sub,k,a[int(t0*SR):int(t1*SR)].copy())); pos+=len(sub)
    out=pieces[0][2]
    for _,_,p in pieces[1:]: out=xfade(out,p,0.012)
    return out, ' + '.join(f'{s}<{k[0]}:{k[1]}:{k[2]}>' for s,k,_ in pieces)
def rms(x): return np.sqrt(np.mean(x**2)+1e-12)
def xfade(a,b,sec=0.025):
    f=int(sec*SR)
    if len(a)<=f or len(b)<=f: return np.concatenate([a,b])
    r=np.linspace(0,1,f,dtype=np.float32); return np.concatenate([a[:-f],a[-f:]*(1-r)+b[:f]*r,b[f:]])
def trim_sil(x, thr=0.02):
    e=np.abs(x); i=np.argmax(e>thr*e.max()); j=len(x)-np.argmax(e[::-1]>thr*e.max())
    return x[max(0,i-int(0.02*SR)):min(len(x),j+int(0.02*SR))]
# ---------------- main ----------------
def synth(tgt, exclude=(), tag='', bookend=False):
    exclude=set(exclude)|{tgt}
    idx,bylv,bysig=build(exclude)
    ws=words(Bk[ORDER[tgt[0]-1]][tgt[1]-1][tgt[2]-1]); segs=plan(tgt,ws,idx)
    pieces=[]; rep=[]
    for t,i,src,ln in segs:
        if t=='splice':
            k,p=src; x,_,_=clip(k,p,ln)
            rep.append(f'  splice  {" ".join(roman(w) for w in ws[i:i+ln]):40s} <- {k[0]}:{k[1]}:{k[2]}')
        else:
            md=melody_donor(ws,i,bysig,tgt); pd,how=phon_donor(ws[i],bylv,tgt)
            if pd:
                ph,pon,poff=clip(pd[0],pd[1]); pdesc=f'{pd[0][0]}:{pd[0][1]}:{pd[0][2]}'
            else:
                ph,pdesc=composite(ws[i],exclude,tgt); ph=trim_sil(ph); pon,poff=0.0,len(ph)/SR; how='assembled from pieces'
            if md:
                mel,mon,moff=clip(md[1],md[2]); x=retarget(ph,pon,poff,mel,mon,moff)
                rep.append(f'  retrope {roman(ws[i]):40s} phonetics<-{pdesc} ({how}); melody<-{md[1][0]}:{md[1][1]}:{md[1][2]} "{roman(avail[md[1]][md[2]])}"')
            else:
                x=ph; rep.append(f'  RAW     {roman(ws[i])} (no melody donor) {pdesc}')
        x=x*(0.08/rms(x)); pieces.append((i,ln,x))
    if bookend: pieces,extra=apply_bookend(ws,pieces,exclude,tgt); rep+=extra
    out=pieces[0][2]
    for _,_,p in pieces[1:]: out=xfade(out,p)
    out=np.concatenate([np.zeros(int(0.07*SR),np.float32),out])
    out=out/max(1e-6,np.abs(out).max())*0.89
    name=f'{OUT}/{tgt[1]:02d}{tgt[2]:02d}{tag}'
    sf.write(name+'.wav',out,SR)
    subprocess.run(['ffmpeg','-v','error','-y','-i',name+'.wav','-ar','16000','-ac','2','-b:a','48k',name+'.mp3'])
    return name,rep
def retarget_multi(phon, ap, mel, am, shift=0.0, maxfac=8.0):
    tm,fm=contour(mel); Dp=len(phon)/SR; Dm=len(mel)/SR
    ap=[0.0]+list(ap)+[Dp]; am=[0.0]+list(am)+[Dm]
    snd=parselmouth.Sound(phon.astype(np.float64),SR); man=call(snd,"To Manipulation",0.01,70,400)
    pt=call("Create PitchTier","p",0,Dp); v=fm>0
    for t,f in zip(tm[v],fm[v]): call(pt,"Add point",float(np.interp(t,am,ap)),f*2**(shift/12))
    call([pt,man],"Replace pitch tier")
    dt=call("Create DurationTier","d",0,Dp)
    for a,b,c,d in zip(ap[:-1],ap[1:],am[:-1],am[1:]):
        if b-a<1e-3: continue
        fac=max(0.3,min(maxfac,(d-c)/(b-a)))
        call(dt,"Add point",a+1e-4,fac); call(dt,"Add point",max(a+2e-4,b-1e-4),fac)
    call([dt,man],"Replace duration tier")
    return np.array(call(man,"Get resynthesis (overlap-add)").values[0],dtype=np.float32)
def stressed_vowel_anchor(r, cs, last_vowel=True):
    vow=[i for i,ch in enumerate(r) if ch in 'aeiou']
    i=vow[-1] if last_vowel else vow[0]
    return cs[i][0]
def apply_bookend(ws,pieces,exclude,tgt):
    """End-of-book style modelled on Deut 34:12: verse raised ~+2 st; the tipcha word takes the contour of
    Deut 'leene' (tipcha), and the closing silluq phrase takes Deut 'kal yisrael' incl. its long final melisma."""
    from align import align_audio
    T=(5,34,12); n=len(ws); extra=[]
    iy=n-3  # yisrael (tipcha)  ;  n-2..n-1 behal masehem (silluq phrase)
    bounds={p[0] for p in pieces}
    if not (iy in bounds and n-2 in bounds): return pieces,['  bookend SKIPPED (piece boundaries)']
    d=audio(T); Wd=align(*T)['words']
    s9,e9,_=word_span(T,9); s10,_,_=word_span(T,10,2)
    melA=d[int(s9*SR):int(s10*SR)]; melB=d[int(s10*SR):]
    # target pieces
    A=np.concatenate([p[2] for p in pieces if p[0]==iy]); Bp=[p[2] for p in pieces if p[0]>=n-2]
    B=Bp[0]
    for p in Bp[1:]: B=xfade(B,p)
    A=trim_sil(A); B=trim_sil(B)
    rA=[roman(ws[iy])]; rB=[roman(w) for w in ws[n-2:]]; rDA=['leene']; rDB=['kal','yisrael']
    cA=align_audio(A,rA)[0]; cDA=align_audio(melA,rDA)[0]
    newA=retarget_multi(A,[cA[0][0],stressed_vowel_anchor(rA[0],cA),cA[-1][1]],melA,[cDA[0][0],stressed_vowel_anchor('leene',cDA),cDA[-1][1]],maxfac=4)
    cB=align_audio(B,rB); cDB=align_audio(melB,rDB)
    def last_voiced(x): t,f=contour(x); return float(t[f>0][-1])
    apB=[cB[0][0][0],cB[1][0][0],stressed_vowel_anchor(rB[1],cB[1]),last_voiced(B)]
    amB=[cDB[0][0][0],cDB[1][0][0],stressed_vowel_anchor('yisrael',cDB[1]),last_voiced(melB)]
    newB=retarget_multi(B,apB,melB,amB,maxfac=12)
    extra.append(f'  bookend: {rA[0]} <- Deut 34:12 "leene" contour; {" ".join(rB)} <- Deut 34:12 "kal yisrael" contour ({len(B)/SR:.1f}s -> {len(newB)/SR:.1f}s); rest of verse +2 st')
    out=[]
    for i,ln,x in pieces:
        if i<iy:
            tm,fm=contour(x); out.append((i,ln,retarget(x,0,len(x)/SR,x,0,len(x)/SR,shift=2.0,mel_override=(tm,fm))))
    out.append((iy,1,newA*(0.08/rms(newA)))); out.append((n-2,2,newB*(0.08/rms(newB))))
    return out,extra
if __name__=='__main__':
    tag=sys.argv[2] if len(sys.argv)>2 else ''
    for v in map(int,sys.argv[1].split(',')):
        name,rep=synth((2,40,v),tag=tag,bookend=(v==38 and tag==''))
        print(f'40:{v} -> {os.path.basename(name)}.mp3'); print('\n'.join(rep), flush=True)
