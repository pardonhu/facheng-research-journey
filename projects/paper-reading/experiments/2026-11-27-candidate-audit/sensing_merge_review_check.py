"""Independent algebra checks for sensing-third-candidate; no task evidence."""
import json
from pathlib import Path
import numpy as np

# Linear spatial interpolation does not commute with feature max.
a=np.array([1.,0.]); b=np.array([0.,1.]); w=np.array([.5,.5])
warp_after_join=float(w@np.maximum(a,b))
join_after_warps=float(max(w@a,w@b))
assert warp_after_join==1 and join_after_warps==.5

# Arbitrary (nonhomomorphic) decoder still produces tree-independent result
# whenever join is performed in the same coordinate system in latent space.
c1=np.array([0,1]); c2=np.array([1,0]); c3=np.array([0,0])
def decode(c): return np.array([float((c[0]-c[1])**2)])
left=decode(np.maximum(np.maximum(c1,c2),c3))
right=decode(np.maximum(c1,np.maximum(c2,c3)))
assert np.array_equal(left,right)
hom_left=decode(np.maximum(c1,c2))
hom_right=np.maximum(decode(c1),decode(c2))
assert not np.array_equal(hom_left,hom_right)

# Max is nonexpansive: a homomorphic decoder transfers the worst local
# feature-reconstruction bound to any aligned collection of nodes.
rng=np.random.default_rng(20261127)
f=rng.normal(size=(32,64)); eps=.1
fhat=f+rng.uniform(-eps,eps,f.shape)
fusion_error=float(np.max(np.abs(np.max(f,axis=0)-np.max(fhat,axis=0))))
assert fusion_error<=eps+1e-12

out={'scope':'algebra only, not real task precision or new mathematical results',
 'warp_max_counterexample':{'a':a.tolist(),'b':b.tolist(),'weights':w.tolist(),
 'warp_after_max':warp_after_join,'max_after_warp':join_after_warps},
 'arbitrary_decoder_latent_max':{'tree_left':left.tolist(),'tree_right':right.tolist(),
 'decode_after_max':hom_left.tolist(),'max_after_decode':hom_right.tolist(),
 'conclusion':'Tree invariance requires associative latent merge, not decoder homomorphism'},
 'known_nonexpansive_bound_check':{'local_linf_bound':eps,'fused_linf_error':fusion_error,
 'conclusion':'Requires all local errors bounded and same coordinate system; does not bound AP'}}
Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps(out,indent=2))
