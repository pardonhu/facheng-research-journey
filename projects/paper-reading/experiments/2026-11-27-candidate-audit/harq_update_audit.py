"""Algebra audit only; no neural training, LDPC, CRC, or radio measurements.

Checks whether one retained observation supports later likelihood revisions.
It does NOT claim that changing receiver versions breaks calibrated HARQ.
"""
import json
from pathlib import Path
import numpy as np

rng = np.random.default_rng(20261127)
nr, rank, nt, count = 8, 2, 1, 1000
q, _ = np.linalg.qr(rng.normal(size=(nr, rank)) + 1j*rng.normal(size=(nr, rank)))
y = rng.normal(size=(count, nr)) + 1j*rng.normal(size=(count, nr))
z = y @ q.conj()
maxerr = 0.0
for _ in range(12):
    c = rng.normal(size=(rank, nt)) + 1j*rng.normal(size=(rank, nt))
    h = q @ c
    # BPSK log P(y|+1)/P(y|-1), complex noise variance 1.
    full = 4*(y @ h.conj()).real
    replay = 4*(z @ c.conj()).real
    maxerr = max(maxerr, float(np.max(np.abs(full-replay))))
assert maxerr < 1e-12

# Two observations with identical old LLR but different revised LLR:
pair = np.array([[1.,1.],[1.,-1.]])
h_old = np.array([1.,0.])
h_new = np.array([1.,1.])/np.sqrt(2)
old_llr = 4*pair@h_old
new_llr = 4*pair@h_new
assert np.allclose(old_llr[0], old_llr[1])
assert not np.allclose(new_llr[0], new_llr[1])

# A one-dimensional parameter family can require all input directions.
# v(t)=(1,t,...,t^7): eight distinct t yield an invertible Vandermonde.
t = np.linspace(-1, 1, nr)
v = np.vander(t, N=nr, increasing=True)
update_span_rank = int(np.linalg.matrix_rank(v))
assert update_span_rank == nr

# A physical channel change must be indexed by round, not replaced by new h.
old_y, old_h, current_h = 1., 1., -1.
history_correct = 4*old_h*old_y
history_wrong = 4*current_h*old_y
assert history_correct > 0 and history_wrong < 0

# Out-of-family update: residual energy bounds the missing matched-filter term.
h_test = rng.normal(size=nr)+1j*rng.normal(size=nr)
h_in = q @ (q.conj().T @ h_test)
h_res = h_test-h_in
y_res = y-z@q.T
missing_llr = 4*(y@h_res.conj()).real
bound = 4*np.linalg.norm(y_res,axis=1)*np.linalg.norm(h_res)
assert np.all(np.abs(missing_llr) <= bound + 1e-10)

result = {
  'type': 'algebra_and_storage_audit_not_HARQ_performance',
  'seed': 20261127,
  'exact_family': {'receive_dimensions':nr,'projection_rank':rank,
    'random_observations':count,'allowed_channel_variants':12,
    'maximum_LLR_difference_full_vs_projected':maxerr},
  'irrecoverable_from_old_LLR':{'observations':pair.tolist(),
    'old_LLR':old_llr.tolist(),'revised_LLR':new_llr.tolist()},
  'latent_dimension_counterexample':{'parameter_dimension':1,
    'required_linear_observation_span_rank':update_span_rank},
  'historical_channel_counterexample':{'old_y':old_y,'old_h':old_h,
    'current_h':current_h,'correct_historical_LLR':history_correct,
    'wrong_current_h_on_old_y_LLR':history_wrong},
  'out_of_family_LLR_error_bound':{'samples':count,'violations':int(np.sum(np.abs(missing_llr)>bound+1e-10)),
    'maximum_actual_error_over_bound':float(np.max(np.abs(missing_llr)/bound)),
    'meaning':'BPSK LLR numerical bound only, not a coded-BLER or safety certificate'},
  'illustrative_partial_storage_bits_per_data_symbol':{
    'settings':'8 Rx, 1 stream, 64-QAM, 1024 data symbols, 64 retained pilots; 8-bit real IQ/projection, 6-bit LLR; basis 16-bit real',
    'LLR_only':36,'raw_IQ_with_pilots':136,
    'rank2_projection_pilots_basis':40.5,
    'rank4_projection_pilots_basis':73,
    'excludes':'per-symbol residual norm e (adds 8 bits/symbol if quantized to 8 bits), headers, noise/covariance/CSI metadata, quantizer scales, codec working memory; these are partial subtotals, not total cache costs; unequal errors must be measured'},
  'not_tested':['neural receiver adaptation','actual HARQ loss','LDPC CRC',
    'finite precision projection quality','out-of-family update rate',
    'process-pinned receiver baseline','calibrated mixed-version LLR baseline']
}
out = Path(__file__).with_suffix('.json')
out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
