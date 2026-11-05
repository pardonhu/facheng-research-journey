from pathlib import Path
import json, math
import numpy as np
out=Path('outputs/ble-matched-study');rng=np.random.default_rng(20261104);samples=50000
# Independent 10% erasure for POLL and DATA. Reserve both slots on every failed attempt.
nb1=rng.negative_binomial(300,.81,size=samples)+300
nb10=rng.negative_binomial(30,.81,size=samples)+30
success5=rng.binomial(300,1-.1**5,size=samples)==300
profiles=[('BLE listed 60/196 us',60,196,60),('BLE table reconstruction 60/194 us',60,194,60)]
def air(pre,bytes):
 bits=8*bytes;return (pre+8)*1.01763+21*1.02564+(bits+48*math.ceil(bits/330))*.12821
for pre in (128,64,32):profiles.append((f'UWB preamble {pre}',air(pre,34),air(pre,68),air(pre,30)))
rows=[]
for name,data1,data10,poll in profiles:
 for case,agg in [('single',1),('aggregate',10),('repeat5',1),('poll',1),('poll_aggregate',10)]:
  data=data1 if agg==1 else data10
  if case.startswith('poll'):times=(nb1 if agg==1 else nb10)*(poll+150+data+150)-150
  else:times=np.full(samples,(300//agg)*(5 if case=='repeat5' else 1)*(data+150)-150)
  rows.append(dict(profile=name,case=case,records=300,aggregation=agg,simulation_rounds=samples,data_air_us=data,poll_air_us=poll,mean_ms=float(times.mean()/1000),p95_ms=float(np.quantile(times,.95,method='higher')/1000),p99_ms=float(np.quantile(times,.99,method='higher')/1000),all_success_rate=float(success5.mean()) if case=='repeat5' else 1.0,success_assumption='single: ideal no loss; repeat5: independent DATA PER=.1; poll: independent POLL/DATA PER=.1 with unlimited selective retry'))
check=dict(ble_poll_exact_mean_ms=(300/.81*420-150)/1000,ble_poll_aggregate_listed_exact_mean_ms=(30/.81*556-150)/1000,ble_poll_aggregate_reconstructed_exact_mean_ms=(30/.81*554-150)/1000,repeat5_300_all_success_exact=(1-.1**5)**300,provided_repeat5_success=.9284,provided_group_aggregation_mean_ms=31.080,group_aggregation_status='Not reconstructed: intra-group acquisition and channel concurrency rules were not provided.')
(out/'model-results.json').write_text(json.dumps(dict(seed=20261104,simulation_rounds=samples,ifs_us=150,profiles=rows,reference_checks=check,airtime_source='Qorvo DW3000 Datasheet v1.1 Table 18 and section 4.5; https://www.mouser.com/catalog/specsheets/Qorvo_DW3000.pdf'),indent=2));print(json.dumps(check))
