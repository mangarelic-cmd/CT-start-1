import json, os
from pathlib import Path
import numpy as np
root=Path('P072_AUTHORITY')
receipts=[]
for p in sorted(root.glob('p072-primary-*/RECEIPTS_P072_*.json')): receipts += json.loads(p.read_text())
usable=[r for r in receipts if r.get('status')=='USABLE']
if len(usable)!=30: raise SystemExit(f'FAIL_CLOSED_USABLE={len(usable)} expected 30')
shots=[int(r['shot_id']) for r in usable]
if len(set(shots))!=30: raise SystemExit('DUPLICATE_SHOT')
per=[]; total_n=0; sse7=sse8=sse9=sse10=0.; active_pairs=0
for r in usable:
    sid=int(r['shot_id']); matches=list(root.glob(f'p072-primary-*/SHOT_{sid}_P072_M10_RAW_SCORE_PACKET.npz'))
    if len(matches)!=1: raise SystemExit(f'PACKET_COUNT_{sid}={len(matches)}')
    d=np.load(matches[0]); y=d['y_log_te']; p7=d['m7_pred']; p8=d['m8_pred']; p9=d['m9_pred']; p10=d['m10_pred']; pa=d['pressure_available'].astype(bool); n=len(y)
    e7=float(np.mean((y-p7)**2)); e8=float(np.mean((y-p8)**2)); e9=float(np.mean((y-p9)**2)); e10=float(np.mean((y-p10)**2))
    if max(abs(e7-r['m7_mse']),abs(e8-r['m8_mse']),abs(e9-r['m9_mse']),abs(e10-r['m10_mse']))>1e-12: raise SystemExit(f'RECON_MISMATCH_{sid}')
    if int(pa.sum()) != int(r['pressure_active_pairs']): raise SystemExit(f'PRESSURE_COUNT_MISMATCH_{sid}')
    per.append({'shot_id':sid,'n_pairs':n,'pressure_active_pairs':int(pa.sum()),'pressure_active_fraction':float(pa.mean()),'pressure_active_any':bool(pa.any()),'m7_mse':e7,'m8_mse':e8,'m9_mse':e9,'m10_mse':e10,'delta_m10_m9':e10-e9,'delta_m10_m7':e10-e7,'m10_wins_m9':e10<e9,'m10_wins_m7':e10<e7})
    total_n+=n; active_pairs+=int(pa.sum()); sse7+=float(np.sum((y-p7)**2)); sse8+=float(np.sum((y-p8)**2)); sse9+=float(np.sum((y-p9)**2)); sse10+=float(np.sum((y-p10)**2))
shot7=float(np.mean([x['m7_mse'] for x in per])); shot8=float(np.mean([x['m8_mse'] for x in per])); shot9=float(np.mean([x['m9_mse'] for x in per])); shot10=float(np.mean([x['m10_mse'] for x in per])); pair7=sse7/total_n; pair8=sse8/total_n; pair9=sse9/total_n; pair10=sse10/total_n
d9=np.array([x['delta_m10_m9'] for x in per]); d7=np.array([x['delta_m10_m7'] for x in per]); rng=np.random.default_rng(720071); b9=np.empty(20000); b7=np.empty(20000)
for i in range(20000):
    ix=rng.integers(0,len(per),len(per)); b9[i]=d9[ix].mean(); b7[i]=d7[ix].mean()
ci9=[float(x) for x in np.quantile(b9,[.025,.975])]; ci7=[float(x) for x in np.quantile(b7,[.025,.975])]
shot_desc9=bool(shot10<shot9); pair_desc9=bool(pair10<pair9)
result={'schema':'P072_FRESH_M10_VS_M9_M8_M7_RESULT_V1','usable_shots':30,'shot_ids':shots,'n_pairs':int(total_n),'pressure_active_shots':sum(x['pressure_active_any'] for x in per),'pressure_active_pairs':int(active_pairs),'pressure_active_pair_fraction':float(active_pairs/total_n),'m7_shot_balanced_mse':shot7,'m8_shot_balanced_mse':shot8,'m9_shot_balanced_mse':shot9,'m10_shot_balanced_mse':shot10,'relative_improvement_m10_vs_m9_shot_balanced':(shot9-shot10)/shot9,'relative_improvement_m10_vs_m7_shot_balanced':(shot7-shot10)/shot7,'m7_pair_weighted_mse':pair7,'m8_pair_weighted_mse':pair8,'m9_pair_weighted_mse':pair9,'m10_pair_weighted_mse':pair10,'relative_improvement_m10_vs_m9_pair_weighted':(pair9-pair10)/pair9,'relative_improvement_m10_vs_m7_pair_weighted':(pair7-pair10)/pair7,'m10_wins_m9_shots':sum(x['m10_wins_m9'] for x in per),'m10_wins_m7_shots':sum(x['m10_wins_m7'] for x in per),'bootstrap_m10_minus_m9_ci95':ci9,'bootstrap_m10_minus_m7_ci95':ci7,'Q_local_vs_m9':shot_desc9,'Q_local_vs_m7':bool(shot10<shot7),'both_aggregates_descend_vs_m9':bool(shot_desc9 and pair_desc9),'scientific_promotion_vs_m9':bool(shot_desc9 and pair_desc9 and ci9[1]<0),'scientific_promotion_vs_m7':bool(shot10<shot7 and pair10<pair7 and ci7[1]<0),'scientific_promotion_joint':bool(shot_desc9 and pair_desc9 and ci9[1]<0 and shot10<shot7 and pair10<pair7 and ci7[1]<0),'pressure_conditioned_selection':False,'missing_pressure_exact_fallback_m9':True,'refit':False,'retune':False,'same_support':True,'independent_reconstruction':True}
(root/'P072_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); (root/'P072_PER_SHOT.json').write_text(json.dumps(per,indent=2,sort_keys=True)+'\n'); (root/'RUN_PROVENANCE_P072.json').write_text(json.dumps({'schema':'P072_GITHUB_AUTHORITY_PROVENANCE_V1','run_id':os.environ.get('GITHUB_RUN_ID'),'head_sha':os.environ.get('GITHUB_SHA'),'workflow':'sc-fair-mast-p072-primary10.yml'},indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
