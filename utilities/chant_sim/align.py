import os, json, sys, torch, torchaudio, numpy as np, subprocess
sys.path.insert(0, os.path.dirname(__file__))
from heb import *
WB=os.path.join(REPO,'misc_mp3s/t2/40/from_wayback')
CACHE=os.path.join(os.path.expanduser('~'),'.cache','scrollscraper_align'); os.makedirs(CACHE,exist_ok=True)
SR=16000
def audio_path(b,c,v):
    if b==2 and c==40: return f'{WB}/40{v:02d}.mp3'
    return f'{REPO}/local_ort_mp3s/t{b}/{c:02d}{v:02d}.mp3'
def load_audio(p):
    raw=subprocess.run(['ffmpeg','-v','error','-i',p,'-ac','1','-ar',str(SR),'-f','f32le','-'],capture_output=True).stdout
    return np.frombuffer(raw,dtype=np.float32).copy()
def roman(w):
    s=strip_trope(w)
    if 'יהו' in s and len(s.replace('ְ','').replace('ָ','').replace('ִ','').replace('ֵ',''))<=5 and s.startswith('י'): return 'adonai'
    r=translit(w)
    if 'yehv' in r or 'yehov' in r: return r.replace('yehovi','elohim').replace('yehvi','elohim').replace('yehva','adonai').replace('yehova','adonai')
    return r
_m=None
def model():
    global _m
    if _m is None:
        b=torchaudio.pipelines.MMS_FA; _m=(b, b.get_model(with_star=False).eval(), b.get_dict(star=None))
    return _m
B=None
def verse_words(b,c,v):
    global B
    if B is None: B=load()
    return words(B[ORDER[b-1]][c-1][v-1])
def align(b,c,v):
    key=f'{CACHE}/{b}-{c}-{v}.json'
    if os.path.exists(key): return json.load(open(key))
    bundle,m,dic=model()
    ws=verse_words(b,c,v); toks=[roman(w) or 'a' for w in ws]
    wav=torch.from_numpy(load_audio(audio_path(b,c,v)))[None]
    with torch.inference_mode(): em,_=m(wav)
    ids=[[dic[ch] for ch in t if ch in dic] for t in toks]
    flat=torch.tensor([x for t in ids for x in t],dtype=torch.int32)[None]
    al,sc=torchaudio.functional.forced_align(em,flat,blank=0)
    spans=torchaudio.functional.merge_tokens(al[0],sc[0].exp())
    ratio=wav.shape[1]/em.shape[1]/SR
    out=[];k=0
    for w,t,tid in zip(ws,toks,ids):
        sp=spans[k:k+len(tid)]; k+=len(tid)
        out.append({'w':w,'r':t,'s':sp[0].start*ratio,'e':sp[-1].end*ratio,'score':float(np.mean([s.score for s in sp])),'cs':[[x.start*ratio,x.end*ratio] for x in sp] if len(sp)==len(t) else None})
    res={'dur':wav.shape[1]/SR,'words':out}
    json.dump(res,open(key,'w'),ensure_ascii=False); return res
if __name__=='__main__':
    b,c,v=map(int,sys.argv[1:4]); r=align(b,c,v)
    print(r['dur']); [print(f"{x['s']:6.2f}-{x['e']:6.2f} {x['score']:.2f} {x['r']}") for x in r['words']]

def align_audio(x, toks):
    bundle,m,dic=model()
    wav=torch.from_numpy(np.asarray(x,dtype=np.float32))[None]
    with torch.inference_mode(): em,_=m(wav)
    ids=[[dic[ch] for ch in t if ch in dic] for t in toks]
    flat=torch.tensor([y for t in ids for y in t],dtype=torch.int32)[None]
    al,sc=torchaudio.functional.forced_align(em,flat,blank=0)
    spans=torchaudio.functional.merge_tokens(al[0],sc[0].exp()); ratio=wav.shape[1]/em.shape[1]/SR
    out=[];k=0
    for t,tid in zip(toks,ids):
        sp=spans[k:k+len(tid)]; k+=len(tid); out.append([[s.start*ratio,s.end*ratio] for s in sp])
    return out
