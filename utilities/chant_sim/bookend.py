import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from align import align, load_audio, audio_path, SR
from pitch import f0
def profile(k):
    al=align(*k); a=load_audio(audio_path(*k)); f=f0(a); out=[]
    for w in al['words']:
        seg=f[int(w['s']*100):int(w['e']*100)+1]; v=seg[seg>0]
        out.append((w['r'], round(12*np.log2(np.median(v)/110),1) if len(v) else None, round(12*np.log2(v.max()/110),1) if len(v) else None, round(w['e']-w['s'],2)))
    return al['dur'],out
for k in [(1,50,26),(3,27,34),(4,36,13),(5,34,12),(5,34,11),(1,50,25),(2,40,36)]:
    d,p=profile(k); print(k, f'{d:.1f}s'); print('   ',p)
