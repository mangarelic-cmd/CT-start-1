import json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path('p066-download')
OUT=Path('p066-authority')
OUT.mkdir(exist_ok=True)
sel_files=sorted(ROOT.rglob('FROZEN_SELECTION_P066.json'))
if not sel_files: raise SystemExit('NO_SELECTION_FILES')
selections=[json.loads(p.read_text()) for p in sel_files]
canon=json.dumps(selections[0],sort_keys=True,separators=(',',':'))
if any(json.dumps(s,sort_keys=True,separators=(',',':'))!=canon for s in selections):
    raise SystemExit('SELECTION_MISMATCH_ACROSS_SHARDS')
selection=selections[0]
(OUT/'FROZEN_SELECTION_P066.json').write_text(json.dumps(selection,indent=2,sort_keys=True)+'\n')
receipts=[]
for p in sorted(ROOT.rglob('RECEIPTS_P066_*.json')): receipts.extend(json.loads(p.read_text()))
byid={int(r['shot_id']):r for r in receipts}
primary=[int(x) for x in selection['primary']]
ordered=[byid[s] for s in primary if s in byid]
missing=[s for s in primary if s not in byid]
usable=[r for r in ordered if r.get('status')=='USABLE']
failed=[r for r in ordered if r.get('status')!='USABLE']
rows=[]
for r in ordered:
    rows.append({k:r.get(k) for k in ['shot_id','status','n_pairs','m6_mse','m7_mse','delta_m7_minus_m6','m7_beats_m6','mean_rad_fraction','mean_net_power_mw','mean_activation_gate','error_type','error']})
pd.DataFrame(rows).to_csv(OUT/'PER_SHOT_P066.csv',index=False)
complete=(len(usable)==30 and not missing and not failed)
result={
 'schema':'P066_FRESH_M7_VS_M6_RESULT_V1',
 'primary_frozen':primary,
 'reserve_frozen':selection['reserves'],
 'primary_receipts_found':len(ordered),
 'usable_primary':len(usable),
 'failed_primary':len(failed),
 'missing_primary_receipts':missing,
 'refit':False,'retune':False,
 'same_support_required':True,
 'complete_30':complete,
}
if usable:
    d=np.array([r['delta_m7_minus_m6'] for r in usable],float)
    e6=np.array([r['m6_mse'] for r in usable],float);e7=np.array([r['m7_mse'] for r in usable],float)
    w=np.array([r['n_pairs'] for r in usable],float)
    result.update({
      'n_pairs':int(w.sum()),
      'm6_shot_balanced_mse':float(e6.mean()),
      'm7_shot_balanced_mse':float(e7.mean()),
      'delta_shot_balanced_m7_minus_m6':float(d.mean()),
      'relative_improvement_shot_balanced':float((e6.mean()-e7.mean())/e6.mean()),
      'm7_wins_shots':int(np.sum(d<0)),
      'm6_wins_or_ties_shots':int(np.sum(d>=0)),
      'm6_pair_weighted_mse':float(np.average(e6,weights=w)),
      'm7_pair_weighted_mse':float(np.average(e7,weights=w)),
      'delta_pair_weighted_m7_minus_m6':float(np.average(d,weights=w)),
    })
    rng=np.random.default_rng(660185)
    boots=np.empty(20000)
    n=len(d)
    for i in range(len(boots)):
        ix=rng.integers(0,n,n);boots[i]=float(d[ix].mean())
    lo,hi=np.quantile(boots,[0.025,0.975])
    result['bootstrap_shot_delta_ci95']=[float(lo),float(hi)]
    result['Q_local']=bool(complete and d.mean()<0)
    result['scientific_promotion']=bool(complete and hi<0 and np.average(d,weights=w)<0)
else:
    result['Q_local']=False;result['scientific_promotion']=False
if not complete:
    result['reserve_activation_required']=30-len(usable)
else:
    result['reserve_activation_required']=0
(OUT/'P066_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
prov={'schema':'P066_GITHUB_AUTHORITY_PROVENANCE_V1','run_id':'GITHUB_RUN_ID_PLACEHOLDER','run_attempt':'GITHUB_RUN_ATTEMPT_PLACEHOLDER','head_sha':'GITHUB_SHA_PLACEHOLDER','workflow':'sc-fair-mast-p066-primary10.yml'}
(OUT/'RUN_PROVENANCE_TEMPLATE.json').write_text(json.dumps(prov,indent=2,sort_keys=True)+'\n')
for p in sorted(OUT.iterdir()):
    if p.is_file():
        (OUT/'SHA256SUMS.txt').open('a').write(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n') if p.name!='SHA256SUMS.txt' else None
print(json.dumps(result,indent=2,sort_keys=True))
