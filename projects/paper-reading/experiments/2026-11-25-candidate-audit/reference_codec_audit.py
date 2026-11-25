"""Original synthetic candidate audit; not a paper reproduction or hardware result.

Run with Python and NumPy. Writes results next to this script.
The README daily note records assumptions and the rejected proposal.
"""

import json
from pathlib import Path
import numpy as np

# Fixed-rate 64-QAM -> 16-codeword reference encoder. No target realization is
# available at the encoder. Its only channel knowledge is a support bound.
rng = np.random.default_rng(20261125)
N, L, trials, passes = 128, 16, 12, 8
q64 = np.array([a + 1j*b for a in [-7,-5,-3,-1,1,3,5,7]
                for b in [-7,-5,-3,-1,1,3,5,7]]) / np.sqrt(42)
codebook = np.array([a + 1j*b for a in [-6,-2,2,6]
                     for b in [-6,-2,2,6]]) / np.sqrt(42)
lags = np.arange(-L+1, L)
A = np.exp(2j*np.pi*np.outer(lags, np.arange(N))/N)/N
F = np.exp(-2j*np.pi*np.outer(np.arange(N), np.arange(L))/N)
budget = 4*N
J = budget//6
subset = np.sort(rng.choice(N, J, replace=False))
records = []
for _ in range(trials):
    x = rng.choice(q64, N)
    nearest = np.argmin(abs(x[:,None]-codebook[None,:])**2, axis=1)
    indices = nearest.copy()
    w = x/codebook[indices]-1
    residual = A @ w
    # Minimize the multiplicative error kernel on the full difference set.
    # Every output remains a 4-bit lookup-table index; no invented error vector.
    for __ in range(passes):
        for j in rng.permutation(N):
            options = x[j]/codebook-1
            changes = options-w[j]
            costs = np.sum(abs(residual[:,None]+A[:,j,None]*changes)**2, axis=0)
            pick = int(np.argmin(costs))
            residual += A[:,j]*changes[pick]
            w[j] = options[pick]
            indices[j] = pick
    h = np.zeros(L, complex)
    h[1] = 1
    h[9] = .01*np.exp(.3j)
    H = F @ h
    # Same received waveform in all methods, fixed real/imag AWGN variance.
    noise = 1e-3*(rng.normal(size=N)+1j*rng.normal(size=N))/np.sqrt(2)
    y = x*H+noise
    h_mse = np.fft.ifft(y/codebook[nearest])[:L]
    h_shaped = np.fft.ifft(y/codebook[indices])[:L]
    # Strong equal-budget alternative: exact QAM indices on J resource elements.
    h_subset = np.linalg.lstsq(F[subset], y[subset]/x[subset], rcond=None)[0]
    # Reconstruct original RF samples, so its covariance is handled correctly.
    h_subset_wls = np.linalg.lstsq(x[subset,None]*F[subset], y[subset], rcond=None)[0]
    records.append({
        'reference_mse_nearest': float(np.mean(abs(x-codebook[nearest])**2)),
        'reference_mse_shaped': float(np.mean(abs(x-codebook[indices])**2)),
        'kernel_protected_energy_nearest': float(np.sum(abs(A@(x/codebook[nearest]-1))**2)),
        'kernel_protected_energy_shaped': float(np.sum(abs(A@w)**2)),
        **{name: float(abs(est[9]-h[9])) for name,est in [
            ('weak_amplitude_error_nearest',h_mse),('weak_amplitude_error_shaped',h_shaped),
            ('weak_amplitude_error_exact_subset',h_subset),
            ('weak_amplitude_error_exact_subset_wls',h_subset_wls)]},
        **{name: float(np.max(abs(np.delete(est-h,[1,9])))) for name,est in [
            ('max_spurious_nearest',h_mse),('max_spurious_shaped',h_shaped),
            ('max_spurious_exact_subset_wls',h_subset_wls)]}
    })
summary = {'settings': {'N':N,'support_bins':L,'trials':trials,'passes':passes,
    'fixed_codeword_count':len(codebook),'shaped_bits':budget,'exact_subset_bits':6*J,
    'full_exact_bits':6*N,'weak_amplitude':.01,'complex_noise_std':.001,
    'not_a_full_paper_reproduction':True},
    'mean':{k:float(np.mean([r[k] for r in records])) for k in records[0]},
    'records':records}
Path(__file__).with_suffix('.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='records'},indent=2))
