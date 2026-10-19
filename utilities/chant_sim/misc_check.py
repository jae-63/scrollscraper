import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
# Checks the hand-collected Exodus 40 recordings in MISC_DIR (default /tmp/miscExodus40) against the Wayback copies.
MISC=os.environ.get('MISC_DIR','/tmp/miscExodus40')
import numpy as np
from align import load_audio, align_audio, verse_words, roman, SR
from pitch import f0, med_semi
import subprocess
def st(x): v=x[x>0]; return 12*np.log2(np.median(v)/110), 12*np.log2(np.percentile(v,95)/110)
for v in [31,32,33,34,38]:
    a=load_audio(f'{MISC}/{v}.40.{v}..1REC.mp3')
    med,p95=st(f0(a))
    # alignment fit against own text vs other candidate verses (mean char-span score proxy via align_audio duration coverage)
    print(f'40:{v} dur {len(a)/SR:5.1f}s median {med:5.2f}st p95 {p95:5.2f}st')
    # voiced segments / silence structure
    env=np.convolve(np.abs(a),np.ones(1600)/1600,'same'); thr=0.1*env.max()
    on=np.flatnonzero(np.diff((env>thr).astype(int))==1)/SR; off=np.flatnonzero(np.diff((env>thr).astype(int))==-1)/SR
    print('   sound starts', np.round(on[:3],2), '... ends', np.round(off[-3:],2), 'longest silence', round(max([b-a2 for a2,b in zip(off[:-1],on[1:])] or [0]),2))
for v in [33,34]:
    a=load_audio(f'{MISC}/{v}.40.{v}..1REC.mp3'); b=load_audio(f'{sys.argv[1]}/40{v}.mp3')
    fa,fb=f0(a),f0(b); n=min(len(fa),len(fb))
    print(f'40:{v} misc {len(a)/SR:.1f}s vs wayback {len(b)/SR:.1f}s; medians {st(fa)[0]:.2f} vs {st(fb)[0]:.2f}')
# 31 vs 34 similarity
a=load_audio(f'{MISC}/31.40.31..1REC.mp3'); b=load_audio(f'{MISC}/34.40.34..1REC.mp3')
n=min(len(a),len(b)); print('31 vs 34 waveform corr', np.corrcoef(a[:n],b[:n])[0,1])
fa,fb=f0(a),f0(b); n=min(len(fa),len(fb)); print('31 vs 34 pitch-track corr', np.corrcoef(fa[:n],fb[:n])[0,1])
