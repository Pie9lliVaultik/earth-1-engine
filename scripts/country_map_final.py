"""Run the country map at the repeat count the arithmetic says works."""
import sys, json, numpy as np
sys.path.insert(0,'.'); sys.path.insert(0,'scripts')
from earth1.alive import birth_world, live_one_day
from earth1.branch import apply
from earth1.genesis import GENESIS_COUNTRIES
from hormuz import SCENARIOS
SC=SCENARIOS[1]; nc=len(GENESIS_COUNTRIES); POP=200000; DAYS=240; WARM=60

def unemp(w):
    lf=w.life.in_lf & w.health.alive
    a=np.bincount(w.civ.country,weights=lf.astype(float),minlength=nc)
    b=np.bincount(w.civ.country,weights=(lf&~w.life.employed).astype(float),minlength=nc)
    return b/np.maximum(a,1.0), a

def paired(seed):
    out={}
    for shock in (False,True):
        w=birth_world(POP,42); r=np.random.default_rng(seed)
        for _ in range(WARM): live_one_day(w,r)
        if shock: apply(w,SC,r)
        for _ in range(DAYS): live_one_day(w,r)
        out[shock]=unemp(w)
    return out[True][0]-out[False][0], out[False][1]

def spear(a,b):
    ra=np.argsort(np.argsort(-a)).astype(float); rb=np.argsort(np.argsort(-b)).astype(float)
    ra-=ra.mean(); rb-=rb.mean()
    return float(ra@rb/(np.linalg.norm(ra)*np.linalg.norm(rb)))

A=[]; B=[]; lf=None
for i in range(20):
    d,l=paired(1000+i); A.append(d); lf=l
    d,_=paired(5000+i); B.append(d)
    if (i+1) in (2,4,8,12,16,20):
        a=np.mean(A,axis=0); b=np.mean(B,axis=0); k=lf>0
        rc=spear(a[k],b[k])
        print(f'  {i+1:2d} paired repeats -> COUNTRY rank corr {rc:+.3f}'
              + ('   <== WORKS' if rc>=0.5 else ''), flush=True)
        json.dump({'repeats':i+1,'country_rank_corr':rc},
                  open('data/country_map_final.json','w'))
        if rc>=0.5:
            print(f'\n  COUNTRY MAP WORKS at {i+1} paired repeats.'); break
