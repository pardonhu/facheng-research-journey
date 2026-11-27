"""Original diagnostic, not a LoRa chipset/CRC/packet simulation.

Layer 1: oversampled periodic base upchirps, dechirp spectrum/correlation.
Layer 2: fixed transmission start grid; reassign transmitter identities only.
The objective in layer 2 is a waveform-coordinate proxy, not packet delivery.
"""
from pathlib import Path
import itertools, json
import numpy as np

OUT = Path(__file__).resolve().parent
BW = 125_000.0
SF = 8
N = 2**SF
TS = N/BW
OS = 8
t = np.arange(N*OS)/(OS*BW)

def chirp(q):
    q = q % TS
    return np.exp(1j*np.pi*(BW/TS*q*q-BW*q))

reference = chirp(t)
tau = TS/8
a = 10**(-1/20)  # interferer has 1 dB lower standalone power
cases = []
for cfo in [0.0, BW/8]:
    interferer = chirp(t-tau)*np.exp(2j*np.pi*cfo*t)
    correlation = np.mean(interferer*np.conj(reference))
    for relative_phase in [0.0, float(np.pi)]:
        received = reference+a*np.exp(1j*relative_phase)*interferer
        peak_power = abs(np.mean(received*np.conj(reference)))**2
        cases.append(dict(cfo_hz=cfo, phase_rad=relative_phase,
                          normalized_correlation_magnitude=float(abs(correlation)),
                          wanted_bin_power_relative_to_desired_alone_db=float(10*np.log10(peak_power))))

# Permuting identities on the same grid leaves nominal start gaps, number of
# transmissions, air time, and RF power unchanged. All payloads remain distinct.
K = 8
slots = np.arange(K)/K*TS
perms = np.array(list(itertools.permutations(range(K))),dtype=np.int16)
pair_i, pair_j = np.triu_indices(K,1)

def effective_gap(cfovs, permutation):
    positions = (np.asarray(cfovs)[permutation]-BW/TS*slots)%BW
    delta = abs(positions[...,pair_i]-positions[...,pair_j])
    return np.minimum(delta,BW-delta).min(axis=-1)

rng = np.random.default_rng(20261127)
records = []
for trial in range(12):
    # A deliberately bounded hypothetical oscillator set, not measured devices.
    cfos = rng.uniform(-8_000,8_000,K)
    baseline_order = np.arange(K)
    sorted_order = np.argsort(-cfos)
    gaps = effective_gap(cfos,perms)
    best_i = int(gaps.argmax())
    # Strong simple baseline: remove each transmitter's CFO in its carrier
    # register, keeping the original time grid. 32 MHz / 2^19 is the SX1276
    # synthesizer step. This assumes exact CFO estimates, static offsets and
    # common nominal carrier; estimation/drift costs must be measured separately.
    frequency_step = 32_000_000/2**19
    residual = cfos-np.round(cfos/frequency_step)*frequency_step
    ideal_compensated_gap = float(effective_gap(np.zeros(K),baseline_order))
    quantized_compensated_gap = float(effective_gap(residual,baseline_order))
    records.append(dict(trial=trial, cfo_hz=cfos.tolist(),
        baseline_order=baseline_order.tolist(),
        descending_cfo_order=sorted_order.tolist(),
        best_order=perms[best_i].tolist(),
        baseline_min_effective_gap_hz=float(effective_gap(cfos,baseline_order)),
        descending_cfo_min_effective_gap_hz=float(effective_gap(cfos,sorted_order)),
        best_min_effective_gap_hz=float(gaps[best_i]),
        ideal_carrier_precompensation_min_gap_hz=ideal_compensated_gap,
        quantized_carrier_precompensation_min_gap_hz=quantized_compensated_gap,
        quantized_carrier_residual_cfo_hz=residual.tolist()))

# Deterministic first generated case; no selection of the best-looking trial.
chosen = records[0]
result = dict(
    scope='Analytic waveform and schedule-coordinate diagnostic; no hardware, packet decoder, CRC or PRR was simulated.',
    bandwidth_hz=BW, sf=SF, symbol_us=TS*1e6, delay_us=tau*1e6,
    cancellation_cfo_hz=BW/8, cancellation_relative_ppm_at_915mhz=(BW/8)/915e6*1e6,
    samples_per_chirp=N*OS, oversampling=OS, amplitude_ratio=a,
    omitted=['RF front-end filters and nonlinearity','preamble lock-on state','SFD and header','channel multipath','phase-noise/CFO drift','CRC and payload demodulation'],
    waveform_cases=cases,
    schedule_assumptions={'nodes':K,'nominal_spacing_fraction':1/K,'nominal_min_spacing_us':TS/K*1e6,'slot_span_us':float(slots[-1]*1e6),'cfo_bound_hz':[-8000,8000],'seed':20261127},
    deterministic_first_trial=chosen, all_trials=records,
    summary={'number_trials':len(records),'best_beats_descending_sort_trials':sum(r['best_min_effective_gap_hz']>r['descending_cfo_min_effective_gap_hz']+1e-6 for r in records),
       'best_exceeds_10pct_BW_trials':sum(r['best_min_effective_gap_hz']>=0.1*BW for r in records),
       'fixed_order_exceeds_10pct_BW_trials':sum(r['baseline_min_effective_gap_hz']>=0.1*BW for r in records),
       'carrier_precompensation_beats_schedule_oracle_trials':sum(r['quantized_carrier_precompensation_min_gap_hz']>r['best_min_effective_gap_hz']+1e-6 for r in records),
       'quantized_carrier_precompensation_worst_gap_hz':min(r['quantized_carrier_precompensation_min_gap_hz'] for r in records)},
    carrier_precompensation_assumptions={'frequency_step_hz':frequency_step,'exact_cfo_estimate':True,'cfo_static':True,'no_phase_or_receiver_model':True,'source':'Semtech SX1276-7-8-9 datasheet, frequency settings and RegFrf'},
    interpretation='0.1 BW is only a comparison scale from HydraNet timing guard, not a validated CFO-aware chipset threshold. The best permutation is an exhaustive oracle baseline; proposing it alone is not an independent contribution. Carrier precompensation is the decisive simple baseline: if its measured total cost and reliability match or beat scheduling, the CFO-timing-scheduling research proposal must be rejected.'
)
(OUT/'cfo_timing_audit.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({'waveform_cases':cases,'first_trial':chosen,'summary':result['summary']},indent=2))
