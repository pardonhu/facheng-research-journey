"""Original existence audit, not an RFDT replication or a new estimator.

Samples layouts before observing any result. Enumerates analytic integer aliases
for one horizontal reflector at one calibration center, then checks whether a
second observation excludes them and whether a random target changes beam choice.
An arbitrary common complex scalar is fitted per packet; array relative response
is calibrated. Fixed total energy per snapshot. No hardware results.
"""
import importlib.util
import json
from pathlib import Path
import sys
import time
import numpy as np

sys.dont_write_bytecode = True
base = Path(__file__).resolve().parents[1] / '2026-11-25-candidate-audit'
spec = importlib.util.spec_from_file_location('alias', base/'rf_phase_alias.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
rng = np.random.default_rng(20261126)
N = 400
# Independent locations, no symmetric calibration and no selected target.
layouts = np.c_[rng.uniform(-.08,.08,N), rng.uniform(1,4,(N,2)), rng.uniform(4,7,N)]

def dist(x, da, db, n, bw, sigma, slope=False):
    a = m.channel(x, da, 20, n=n, bandwidth=bw)
    b = m.channel(x, db, 20, n=n, bandwidth=bw)
    freqs = np.linspace(-bw/2,bw/2,a.shape[0])
    delays = np.linspace(-50e-9,50e-9,41) if slope else [0]
    candidates = a[None,:,:]*np.exp(-2j*np.pi*np.array(delays)[:,None,None]*freqs[None,:,None])
    flat=candidates.reshape(len(delays),-1)
    bflat=b.ravel()
    gains=(flat.conj()@bflat)/(np.abs(flat)**2).sum(axis=1)
    return float(np.sqrt(np.min(np.sum(np.abs(flat*gains[:,None]-bflat)**2,axis=1)))/np.sqrt(a.size)/sigma)

def beams(x,d):
    h=m.channel(x,d,20,n=2,bandwidth=0).ravel()
    return np.abs(np.array([[1,1],[1,-1]])@h/np.sqrt(2))**2

start=time.perf_counter()
rows=[]
for n,bw in [(2,20e6),(2,80e6),(2,320e6),(8,20e6)]:
    eligible=0; near=0; harmful=0; probe_survive=0; examples=[]
    for da,x1,x2,xt in layouts:
        L=np.sqrt(x1*x1+(2-2*da)**2)
        sigma=abs(float(m.fresnel(20,x1,1,da)))/L*.05
        alternatives=[]
        for k in [-3,-2,-1,1,2,3]:
            lb=L+k*m.WAVELENGTH
            if lb<=x1: continue
            db=(2-np.sqrt(lb*lb-x1*x1))/2
            if not -.2<=db<=.2: continue
            dc=np.hypot(dist(x1,da,db,n,bw,sigma),dist(x2,da,db,n,bw,sigma))
            pa,pb=beams(xt,da),beams(xt,db)
            wrong=int(np.argmax(pb)); correct=int(np.argmax(pa))
            loss=float(10*np.log10(pa[correct]/pa[wrong]))
            alternatives.append((dc,loss,db))
        eligible+=bool(alternatives)
        near+=any(a[0]<2 for a in alternatives)
        bad=[a for a in alternatives if a[0]<2 and a[1]>3]
        if bad:
            harmful+=1
            # Fixed spatial-diversity baseline: +0.5 m from first calibration.
            survived=any(np.hypot(dc,dist(x1+.5,da,db,n,bw,sigma))<2 for dc,loss,db in bad)
            probe_survive+=survived
            if len(examples)<2:
                dc,loss,db=bad[0]
                examples.append(dict(da=da,db=db,x1=x1,x2=x2,target=xt,distance_sigma=dc,loss_db=loss,
                    with_unknown_delay_slope_sigma=float(np.hypot(dist(x1,da,db,n,bw,sigma,True),dist(x2,da,db,n,bw,sigma,True)))))
    rows.append(dict(antennas=n,bandwidth_mhz=bw/1e6,layouts=N,eligible=eligible,
                     layouts_with_alias_under_2sigma=near,layouts_with_alias_and_loss_over_3db=harmful,
                     harmful_alias_remaining_after_fixed_probe=probe_survive,examples=examples))
out=dict(seed=20261126,rows=rows,seconds=time.perf_counter()-start,
         interpretation='Mean-separation existence screen, not error probability, likelihood posterior, estimator failure rate or population prevalence. Alias candidates use ground truth to construct counterexamples. Both worlds have epsilon=20. Higher-resolution checks require no extra pilot energy. A fixed probe adds one snapshot.')
print(json.dumps(out,ensure_ascii=False,indent=2))
