import json, os
from pathlib import Path
import numpy as np
root=Path('P070_AUTHORITY')
receipts=[]
for p in sorted(root.glob('p070-primary-*/RECEIPTS_P070_*.json')): receipts += json.loads(p.read_text())
usable=[r for r in receipts if r.get('status')=='USABLE']
if len(usable)!=30: raise SystemExit(f'FAIL_CLOSED_USABLE={len(usable)} expected 30')
shots=[int(r['shot_id']) for r in usable]
if len(set(shots))!=30: raise SystemExit('DUPLICATE_SHOT')
per=[]; total_n=0; sse7=sse8=sse9=0.
for r in usable:
    sid=int(r['shot_id']); matches=list(root.glob(f'p070-primary-*/SHOT_{sid}_P070_M9_RAW_SCORE_PACKET.npz'))
    if len(matches)!=1: raise SystemExit(f'PACKET_COUNT_{sid}={len(matches)}')
    d=np.load(matches[0]); y=d['y_log_te']; p7=d['m7_pred']; p8=d['m8_pred']; p9=d['m9_pred']; n=len(y)
    e7=float(np.mean((y-p7)**2)); e8=float(np.mean((y-p8)**2)); e9=float(np.mean((y-p9)**2))
    if max(abs(e7-r['m7_mse']),abs(e8-r['m8_mse']),abs(e9-r['m9_mse']))>1e-12: raise SystemExit(f'RECON_MISMATCH_{sid}')
    per.append({'shot_id':sid,'n_pairs':n,'m7_mse':e7,'m8_mse':e8,'m9_mse':e9,'delta_m9_m7':e9-e7,'delta_m9_m8':e9-e8,'m9_wins_m7':e9<e7,'m9_wins_m8':e9<e8})
    total_n+=n; sse7+=float(np.sum((y-p7)**2)); sse8+=float(np.sum((y-p8)**2)); sse9+=float(np.sum((y-p9)**2))
shot7=float(np.mean([x['m7_mse'] for x in per])); shot8=float(np.mean([x['m8_mse'] for x in per])); shot9=float(np.mean([x['m9_mse'] for x in per])); pair7=sse7/total_n; pair8=sse8/total_n; pair9=sse9/total_n
d7=np.array([x['delta_m9_m7'] for x in per]); d8=np.array([x['delta_m9_m8'] for x in per]); rng=np.random.default_rng(700069); b7=np.empty(20000); b8=np.empty(20000)
for i in range(20000):
    ix=rng.integers(0,len(per),len(per)); b7[i]=d7[ix].mean(); b8[i]=d8[ix].mean()
ci7=[float(x) for x in np.quantile(b7,[.025,.975])]; ci8=[float(x) for x in np.quantile(b8,[.025,.975])]
result={'schema':'P070_FRESH_M9_VS_M7_M8_RESULT_V1','usable_shots':30,'shot_ids':shots,'n_pairs':int(total_n),'m7_shot_balanced_mse':shot7,'m8_shot_balanced_mse':shot8,'m9_shot_balanced_mse':shot9,'relative_improvement_m9_vs_m7_shot_balanced':(shot7-shot9)/shot7,'relative_improvement_m9_vs_m8_shot_balanced':(shot8-shot9)/shot8,'m7_pair_weighted_mse':pair7,'m8_pair_weighted_mse':pair8,'m9_pair_weighted_mse':pair9,'relative_improvement_m9_vs_m7_pair_weighted':(pair7-pair9)/pair7,'relative_improvement_m9_vs_m8_pair_weighted':(pair8-pair9)/pair8,'m9_wins_m7_shots':sum(x['m9_wins_m7'] for x in per),'m9_wins_m8_shots':sum(x['m9_wins_m8'] for x in per),'bootstrap_m9_minus_m7_ci95':ci7,'bootstrap_m9_minus_m8_ci95':ci8,'Q_local_vs_m7':bool(shot9<shot7),'Q_local_vs_m8':bool(shot9<shot8),'scientific_promotion_vs_m7':bool(ci7[1]<0),'scientific_promotion_vs_m8':bool(ci8[1]<0),'scientific_promotion_joint':bool(ci7[1]<0 and ci8[1]<0),'refit':False,'retune':False,'same_support':True,'independent_reconstruction':True}
(root/'P070_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); (root/'P070_PER_SHOT.json').write_text(json.dumps(per,indent=2,sort_keys=True)+'\n'); (root/'RUN_PROVENANCE_P070.json').write_text(json.dumps({'schema':'P070_GITHUB_AUTHORITY_PROVENANCE_V1','run_id':os.environ.get('GITHUB_RUN_ID'),'head_sha':os.environ.get('GITHUB_SHA'),'workflow':'sc-fair-mast-p070-primary10.yml'},indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
