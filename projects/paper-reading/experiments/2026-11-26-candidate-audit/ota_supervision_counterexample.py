"""Small analytic/numeric checks; this is not a FastSET reproduction."""
import json
import numpy as np

rng = np.random.default_rng(20261126)
n = 200000
def cn(var, size):
    return np.sqrt(var / 2) * (rng.standard_normal(size) + 1j * rng.standard_normal(size))
h = cn(1., n)
noise = cn(1., n)
y = h + noise
independent_target = h + cn(1., n)
def fit(target):
    return np.vdot(y, target).real / np.vdot(y, y).real
raw_gain = fit(y)
independent_gain = fit(independent_target)
sure_gain = max(0., 1. - 1. / np.mean(np.abs(y)**2))
ht = cn(1., n)
yt = ht + cn(1., n)
results = {}
for name, a in [('same_snapshot',raw_gain),('independent_noise_label',independent_gain),('known_variance_sure',sure_gain),('oracle_clean',.5)]:
    results[name] = {'gain':float(a), 'test_clean_mse':float(np.mean(np.abs(a*yt-ht)**2))}

# A pre-existing two-pilot identification construction for widely linear I/Q distortion.
a,b=0.8+0.3j, 0.12-0.08j
y0=a+b
y90=1j*a-1j*b
a_hat=(y0-1j*y90)/2
b_hat=(y0+1j*y90)/2
results['iq_two_phase_existing_baseline'] = {
    'a_error':float(abs(a_hat-a)), 'b_error':float(abs(b_hat-b)),
    'first_pilot_rank':1, 'two_phase_pilots_rank':2,
    'interpretation':'Existing joint channel/IQ calibration; not a new mechanism.'
}
print(json.dumps(results,indent=2))
