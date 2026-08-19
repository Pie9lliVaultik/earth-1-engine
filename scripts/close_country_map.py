import sys, json, numpy as np; sys.path.insert(0,'.'); sys.path.insert(0,'scripts')
from earth1.alive import birth_world, live_one_day
from earth1.branch import apply
from earth1.genesis import GENESIS_COUNTRIES
from hormuz import SCENARIOS
SC=SCENARIOS[1]; nc=len(GENESIS_COUNTRIES)
DAYS=240; WARM=60

def unemp(w):
    lf=w.life.in_lf & w.health.alive
    a=np.bincount(w.civ.country,weights=lf.astype(float),minlength=nc)
    b=np.bincount(w.civ.country,weights=(lf&~w.life.employed).astype(float),minlength=nc)
    return b/np.maximum(a,1.0), a

def paired(seed):
    out={}
    for shock in (False,True):
        w=birth_world(200000,42); r=np.random.default_rng(seed)
        for _ in range(WARM): live_one_day(w,r)
        if shock: apply(w,SC,r)
        for _ in range(DAYS): live_one_day(w,r)
        out[shock]=unemp(w)
    return out[True][0]-out[False][0], out[False][1]

def ens(seeds):
    ds=[]; lf=None
    for s in seeds:
        d,l=paired(s); ds.append(d); lf=l
    return np.mean(ds,axis=0), lf

def spear(a,b):
    ra=np.argsort(np.argsort(-a)).astype(float); rb=np.argsort(np.argsort(-b)).astype(float)
    ra-=ra.mean(); rb-=rb.mean()
    return float(ra@rb/(np.linalg.norm(ra)*np.linalg.norm(rb)))

for reps in (2,4):
    a,lf=ens([1000+i for i in range(reps)])
    b,_ =ens([5000+i for i in range(reps)])
    k=lf>0
    rc=spear(a[k],b[k])
    regs=sorted({str(c.get('region','?')) for c in GENESIS_COUNTRIES})
    ri=np.array([regs.index(str(c.get('region','?'))) for c in GENESIS_COUNTRIES])
    nr=len(regs)
    ra_=np.bincount(ri,weights=a*lf,minlength=nr)/np.maximum(np.bincount(ri,weights=lf,minlength=nr),1)
    rb_=np.bincount(ri,weights=b*lf,minlength=nr)/np.maximum(np.bincount(ri,weights=lf,minlength=nr),1)
    kk=np.bincount(ri,weights=lf,minlength=nr)>0
    print(f'  paired x{reps} reps, {DAYS}d :  COUNTRY {rc:+.3f}   REGION {spear(ra_[kk],rb_[kk]):+.3f}', flush=True)
    json.dump({'reps':reps,'days':DAYS,'country':rc}, open(f'data/close_{reps}.json','w'))
