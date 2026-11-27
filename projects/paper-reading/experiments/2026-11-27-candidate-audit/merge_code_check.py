import numpy as np, itertools, json
from pathlib import Path
rng=np.random.default_rng(20261127)
D=rng.uniform(0,1,(8,4))
def q(x): return np.argmin(np.sum((D-x)**2,axis=1))
def merge(i,j): return int(q(np.maximum(D[i],D[j])))
fail=[]
for i,j,k in itertools.product(range(8),repeat=3):
 a=merge(merge(i,j),k);b=merge(i,merge(j,k))
 if a!=b:fail.append([i,j,k,a,b])
i,j,k,a,b=fail[0]
Z=np.array(list(itertools.product(range(2),repeat=3)))
A=rng.uniform(-1,1,(4,3))
def decode(z):return np.max(A+z[None,:],axis=1)
LD=np.array([decode(z) for z in Z])
maxerr=0
for z1,z2 in itertools.product(Z,repeat=2):maxerr=max(maxerr,float(np.max(np.abs(decode(np.maximum(z1,z2))-np.maximum(decode(z1),decode(z2))))))
witness=[]
for n in [2,4,8,16,32]:
 counts=[]
 for trial in range(1000):
  x=rng.normal(size=(n,64));counts.append(len(np.unique(np.argmax(x,axis=0))))
 witness.append({'nodes':n,'channels':64,'mean_required_witnesses':float(np.mean(counts)),'fraction':float(np.mean(counts)/n)})
out={'scope':'synthetic algebra checks, not task or real codebook benchmark','ordinary_3bit_vq_4d_dictionary':D.tolist(),'nonassociative_triples':len(fail),'total_triples':512,'first_failure':{'inputs':[i,j,k],'left_code':a,'right_code':b,'left_decoded':D[a].tolist(),'right_decoded':D[b].tolist(),'unquantized_fusion':np.max(D[[i,j,k]],axis=0).tolist()},'3bit_binary_lattice_maxplus_dictionary':LD.tolist(),'max_merge_decode_commutation_error':maxerr,'lattice_notes':'Exact algebra follows standard max-plus homomorphism, not a novel mathematical operator; its restrictive task representation is the unresolved issue. Scalar quantization+max and 1-bit bottleneck+OR are mandatory baselines.','generic_witness_sizes':witness}
Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps({'nonassociative_triples':len(fail),'max_commutation_error':maxerr,'witness':witness},indent=2))
