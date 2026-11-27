import numpy as np,itertools,json
rng=np.random.default_rng(20261127)
K,T=4,3
angles=np.deg2rad([-40,-10,15,35])
a=np.exp(1j*np.pi*np.arange(2)[:,None]*np.sin(angles)[None,:])
W=np.array([[1,0],[.8,.6*np.exp(1j*np.pi/3)],[.6,.8*np.exp(-1j*np.pi/5)]],complex)
B=W.conj()@a
perms=np.array(list(itertools.permutations(range(K))))
tri=np.triu_indices(K,1)
def sig(Y):
 z=Y[1:]/Y[0:1]
 # Unit-energy pair products of normalized complex response ratios, invariant to a common complex row gain.
 z=z/np.linalg.norm(z,axis=1,keepdims=True)
 return np.stack([zz[:,None]*zz.conj()[None,:] for zz in z])
base=sig(B)
margin=min(np.linalg.norm(sig(B[:,p])-base) for p in perms if not np.array_equal(p,np.arange(K)))
def profile_pick(A,Y):
 C=np.transpose(Y[:,perms],(1,0,2))
 ratio=C/A[None,:,:]
 U,S,Vh=np.linalg.svd(ratio,full_matrices=False)
 u=U[:,:,0]*np.sqrt(S[:,0,None]);v=Vh[:,0,:]*np.sqrt(S[:,0,None])
 for step in range(35):
  Z=A[None,:,:]*v[:,None,:]
  u=np.sum(Z.conj()*C,axis=2)/np.maximum(np.sum(abs(Z)**2,axis=2),1e-18)
  Z=u[:,:,None]*A[None,:,:]
  v=np.sum(Z.conj()*C,axis=1)/np.maximum(np.sum(abs(Z)**2,axis=1),1e-18)
 fit=u[:,:,None]*A[None,:,:]*v[:,None,:]
 cost=np.sum(abs(C-fit)**2,axis=(1,2))
 return perms[np.argmin(cost)]
def bgpc_directions(Y):
 A=W.conj()
 U,S,Vh=np.linalg.svd(A,full_matrices=True)
 n=U[:,-1]
 C=Y.T*n.conj()[None,:]
 _,_,Vh=np.linalg.svd(C,full_matrices=False)
 gamma=Vh[-1].conj()
 X=np.linalg.pinv(A)@(gamma[:,None]*Y)
 return np.angle(X[1]/X[0])/np.pi
def bgpc_pick(Y0,Y1):
 x0=bgpc_directions(Y0);x1=bgpc_directions(Y1)
 return perms[np.argmin(np.sum((x1[perms]-x0[None,:])**2,axis=1))]
results=[]
for snr,violate in [(100,0),(30,0),(20,0),(10,0),(20,.1),(20,.3)]:
 correct,naive,profile,bgpc,err=0,0,0,0,[]
 for it in range(400):
  ys=[];orders=[]
  for rx in range(2):
   ar=rng.uniform(.5,2,K)*np.exp(1j*rng.uniform(0,2*np.pi,K))
   gr=rng.uniform(.7,1.3,T)*np.exp(1j*rng.uniform(0,2*np.pi,T))
   y=gr[:,None]*B*ar[None,:]
   y*=1+violate/np.sqrt(2)*(rng.normal(size=y.shape)+1j*rng.normal(size=y.shape))
   sigma=np.sqrt(np.mean(abs(y)**2)*10**(-snr/10))
   y+=sigma/np.sqrt(2)*(rng.normal(size=y.shape)+1j*rng.normal(size=y.shape))
   order=rng.permutation(K);orders.append(order);ys.append(y[:,order])
  truth=np.array([np.flatnonzero(orders[1]==k)[0] for k in orders[0]])
  target=sig(ys[0]);costs=np.array([np.linalg.norm(sig(ys[1][:,p])-target) for p in perms]);pick=perms[np.argmin(costs)]
  z0=ys[0][1:]/ys[0][0:1];z1=ys[1][1:]/ys[1][0:1]
  # Ablation: individual target signatures, without removing per-RX/probe common gain.
  npick=perms[np.argmin([np.linalg.norm(z0-z1[:,p]) for p in perms])]
  correct+=int(np.array_equal(pick,truth));naive+=int(np.array_equal(npick,truth));profile+=int(np.array_equal(profile_pick(ys[0],ys[1]),truth));bgpc+=int(np.array_equal(bgpc_pick(ys[0],ys[1]),truth))
 results.append({'snr_db':snr,'target_by_probe_model_violation_scale':violate,'trials':400,'whole_permutation_accuracy':correct/400,'single_target_ratio_ablation':naive/400,'profile_row_column_gain_als':profile/400,'known_array_nullspace_bgpc_aod':bgpc/400})
out={'seed':20261127,'tx_antennas':2,'targets':K,'illuminations':T,'angles_degrees':np.rad2deg(angles).tolist(),'tx_weight_energy':np.sum(abs(W)**2,axis=1).tolist(),'min_amplitude_at_targets':float(abs(B).min()),'min_permutation_signature_distance':float(margin),'results':results,'payload_reference':'raw T*K complex amplitudes per RX; ratios (T-1)*K complex amplitudes; actual quantization, packet overhead, beam timing and miss handling not tested','bgpc_scope':'Same observed 3x4 response matrices and known transmit array weights; per-RX nullspace estimates inverse row gain, pseudoinverse recovers 2-element AoD response, then matches inferred sin(theta). This is a classical BGPC specialization, no new estimator claimed.', 'profile_scope':'35 alternating LS iterations per permutation; complex SVD initialization; reference receiver treated as a noisy regressor, not a full errors-in-variables maximum likelihood solver; same 3 probe measurements and same candidate permutations as invariant method', 'scope':'synthetic separable point-scatterer amplitude model; compares an invariant, row-column ALS and known-array BGPC-AoD; no full errors-in-variables ML, TSP19 beam design or waveform optimization. Unknown nuisance gains sampled independently per receiver/illumination.'}
print(json.dumps(out,indent=2));from pathlib import Path;Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2),encoding='utf8')
