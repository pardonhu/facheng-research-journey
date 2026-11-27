import numpy as np,json
rng=np.random.default_rng(20261127)
T,R,reps,sigma=256,16,2000,0.15
# Three synchronized sensing slots share a coarse timestamp, but no carrier phase.
nodes=np.array([[0.,0.],[2.,0.],[0.,2.]])
target=np.array([4.,3.]);wl=.05
ranges=np.linalg.norm(nodes-target,axis=1)
psi=-2*np.pi*np.array([ranges[0]+ranges[1],ranges[1]+ranges[2],ranges[2]+ranges[0]])/wl
truth=np.exp(1j*psi.sum())
err={k:[] for k in ['full','sample','ams','mean_then_close']}
for q in range(reps):
 phi=rng.uniform(0,2*np.pi,(3,T))
 x=np.exp(1j*(np.stack([phi[0]-phi[1],phi[1]-phi[2],phi[2]-phi[0]])+psi[:,None]))
 x+=sigma/np.sqrt(2)*(rng.normal(size=x.shape)+1j*rng.normal(size=x.shape))
 idx=rng.choice(T,R,replace=False)
 s=np.exp(1j*rng.uniform(0,2*np.pi,(R,T)));t=np.exp(1j*rng.uniform(0,2*np.pi,(R,T)))
 est={'full':np.mean(np.prod(x,axis=0)), 'sample':np.mean(np.prod(x[:,idx],axis=0)), 'ams':np.mean((s@x[0])*(t@x[1])*((s*t).conj()@x[2]))/T, 'mean_then_close':np.prod(np.mean(x,axis=1))}
 for k,v in est.items():err[k].append(float(abs(v-truth)**2))
out={'seed':20261127,'T':T,'R':R,'repetitions':reps,'sigma':sigma,'physical_model':'three directed bistatic channels; one stationary point target; unknown iid node carrier phase per frame; known coarse frame alignment; additive independent complex Gaussian receiver noise','truth_real':float(truth.real),'truth_imag':float(truth.imag),'mse':{k:float(np.mean(v)) for k,v in err.items()},'complex_values_uploaded':{'full':3*T,'sample':3*R,'ams':3*R,'mean_then_close':3},'scope':'synthetic mechanism test, not hardware result. Shared sample index / projection seed metadata not charged; same seed metadata convention. Full sensing ADC cost common to all. AMS arithmetic is substantially larger.'}
print(json.dumps(out,indent=2))
from pathlib import Path
Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2),encoding='utf8')
