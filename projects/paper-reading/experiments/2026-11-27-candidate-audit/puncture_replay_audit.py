"""Original observation-dependency counterexample; no neural receiver/LDPC run.

Two payload BPSK symbols s1,s2 and parity s3=s1*s2 form a (3,2) code.
A weak pilot disambiguates unknown h in {1,j}. A code-agnostic Bayesian
demapper uses every available unknown data symbol for channel inference.
Compare dropping final parity LLR vs dropping its observation and recomputing
the same demapper before decoding the rate-1 payload. All trials are retained;
there is no conditioning on successful mother-code packets.
"""
import json
from pathlib import Path
import numpy as np

rng=np.random.default_rng(20261127)
n=120_000
payload=rng.choice([-1.,1.],size=(n,2))
symbols=np.column_stack([payload,payload[:,0]*payload[:,1]])
h=rng.choice(np.array([1+0j,1j]),size=n)
pilot_amplitude=np.sqrt(0.1)

def llrs(y,pilot,noisevar):
    """Independent constellation prior, with channel marginalized jointly."""
    channels=np.array([1+0j,1j])[None,:]
    logpilot=-abs(pilot[:,None]-pilot_amplitude*channels)**2/noisevar
    lp=-abs(y[:,:,None]-channels[:,None,:])**2/noisevar
    lm=-abs(y[:,:,None]+channels[:,None,:])**2/noisevar
    marginal=np.logaddexp(lp,lm)-np.log(2)
    total=logpilot+marginal.sum(axis=1)
    out=[]
    for i in range(y.shape[1]):
        other=total-marginal[:,i,:]
        out.append(np.logaddexp.reduce(other+lp[:,i,:],axis=1)-np.logaddexp.reduce(other+lm[:,i,:],axis=1))
    return np.column_stack(out)

results=[]
for snr_db in [-3,0,3,6]:
    nv=10**(-snr_db/10)
    noise=np.sqrt(nv/2)*(rng.normal(size=(n,3))+1j*rng.normal(size=(n,3)))
    pn=np.sqrt(nv/2)*(rng.normal(size=n)+1j*rng.normal(size=n))
    y=h[:,None]*symbols+noise
    yp=pilot_amplitude*h+pn
    # Old low-rate observation includes parity. Post-LLR puncturing leaves its
    # contribution inside the channel posterior used for payload LLRs.
    ghost=llrs(y,yp,nv)[:,:2]
    replay=llrs(y[:,:2],yp,nv)
    truth=payload>0
    eghost=np.any((ghost>0)!=truth,axis=1)
    ereplay=np.any((replay>0)!=truth,axis=1)
    oracle=2*np.real(y[:,:2]*np.conj(h[:,None]))/nv
    eoracle=np.any((oracle>0)!=truth,axis=1)
    delta=ereplay.astype(float)-eghost.astype(float)
    results.append(dict(snr_db=snr_db,post_llr_puncture_error=float(eghost.mean()),
        observation_mask_recompute_error=float(ereplay.mean()),
        known_channel_error=float(eoracle.mean()),
        paired_error_difference=float(delta.mean()),
        paired_difference_standard_error=float(delta.std(ddof=1)/np.sqrt(n))))

result={'scope':'Synthetic Bayesian demapper counterexample, not FastSET, DeepRx, LDPC or hardware measurement',
 'seed':20261127,'trials_per_snr':n,'channel_prior':['1','j'],
 'pilot_energy':0.1,'data_energy_each':1.0,'code':'(3,2) parity, s3=s1*s2',
 'counterfactual':'Retain the first two BPSK resource elements at identical times, frequencies and powers; omit the parity observation.',
 'what_is_proved':'Deleting an output LLR does not in general remove information already used by a data-aided front-end. Recompute on the retained observation set.',
 'limitations':['This deletion frees a resource element, not a shortened block or higher modulation MCS.','No front-end AGC, RF nonlinearities or cross-RE interference.','No successful-packet selection.','Demapper marginalizes independent data priors and does not exploit the parity check explicitly.'],
 'results':results}
Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result,indent=2))
