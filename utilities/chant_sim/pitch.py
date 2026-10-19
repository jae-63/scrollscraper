import sys, os, numpy as np, parselmouth
sys.path.insert(0, os.path.dirname(__file__))
from align import load_audio, audio_path, SR
def f0(x):
    p=parselmouth.Sound(x.astype(np.float64),SR).to_pitch(time_step=0.01,pitch_floor=70,pitch_ceiling=400)
    f=p.selected_array['frequency']; return f
def med_semi(f):
    v=f[f>0]; return 12*np.log2(np.median(v)/110) if len(v) else np.nan
if __name__!='__main__': pass
elif sys.argv[1]=='books':
    for b in range(1,6):
        meds=[]
        from heb import REPO; d=f'{REPO}/local_ort_mp3s/t{b}'
        fs=sorted(os.listdir(d))[::60]
        for fn in fs: meds.append(med_semi(f0(load_audio(f'{d}/{fn}'))))
        print(f't{b} median pitch (semitones above A2): mean {np.nanmean(meds):.2f} sd {np.nanstd(meds):.2f} n={len(meds)}')
    w=[med_semi(f0(load_audio(audio_path(2,40,v)))) for v in [1,2,3,4,6,15,16,17,27,28,29,33,34,35,36]]
    print('wayback ch40', np.round(w,2))
else:
    a=load_audio(sys.argv[1]); b=load_audio(sys.argv[2])
    fa,fb=f0(a),f0(b)
    print(f'dur {len(a)/SR:.2f} vs {len(b)/SR:.2f}; median pitch {med_semi(fa):.2f} vs {med_semi(fb):.2f} st; voiced {np.mean(fa>0):.2f} vs {np.mean(fb>0):.2f}')
