import json,os
from pathlib import Path
import numpy as np
root=Path("P068_AUTHORITY")
receipts=[]
for p in sorted(root.glob("p068-primary-*/RECEIPTS_P068_*.json")):
    receipts += json.loads(p.read_text())
usable=[r for r in receipts if r.get("status")=="USABLE"]
if len(usable)!=30:
    raise SystemExit(f"FAIL_CLOSED_USABLE={len(usable)} expected 30")
shots=[int(r["shot_id"]) for r in usable]
if len(set(shots))!=30: raise SystemExit("DUPLICATE_SHOT")
per=[]; total_n=0; sse7=0.; sse8=0.
for r in usable:
    sid=int(r["shot_id"]); matches=list(root.glob(f"p068-primary-*/SHOT_{sid}_P068_M8_RAW_SCORE_PACKET.npz"))
    if len(matches)!=1: raise SystemExit(f"PACKET_COUNT_{sid}={len(matches)}")
    d=np.load(matches[0]); y=d["y_log_te"]; p7=d["m7_pred"]; p8=d["m8_pred"]; n=len(y)
    e7=float(np.mean((y-p7)**2)); e8=float(np.mean((y-p8)**2))
    if abs(e7-r["m7_mse"])>1e-12 or abs(e8-r["m8_mse"])>1e-12: raise SystemExit(f"RECON_MISMATCH_{sid}")
    per.append({"shot_id":sid,"n_pairs":n,"m7_mse":e7,"m8_mse":e8,"delta":e8-e7,"m8_wins":e8<e7})
    total_n+=n; sse7+=float(np.sum((y-p7)**2)); sse8+=float(np.sum((y-p8)**2))
shot7=float(np.mean([x["m7_mse"] for x in per])); shot8=float(np.mean([x["m8_mse"] for x in per])); pair7=sse7/total_n; pair8=sse8/total_n
d=np.array([x["delta"] for x in per],float)
rng=np.random.default_rng(680067); boot=np.empty(20000)
for i in range(len(boot)): boot[i]=np.mean(rng.choice(d,size=len(d),replace=True))
ci=[float(x) for x in np.quantile(boot,[.025,.975])]
result={"schema":"P068_FRESH_M8_VS_M7_RESULT_V1","usable_shots":30,"shot_ids":shots,"n_pairs":int(total_n),"m7_shot_balanced_mse":shot7,"m8_shot_balanced_mse":shot8,"delta_shot_balanced_m8_minus_m7":shot8-shot7,"relative_improvement_shot_balanced":(shot7-shot8)/shot7,"m7_pair_weighted_mse":pair7,"m8_pair_weighted_mse":pair8,"delta_pair_weighted_m8_minus_m7":pair8-pair7,"relative_improvement_pair_weighted":(pair7-pair8)/pair7,"m8_wins_shots":sum(x["m8_wins"] for x in per),"m7_wins_or_ties_shots":sum(not x["m8_wins"] for x in per),"bootstrap_shot_delta_ci95":ci,"Q_local":bool(shot8<shot7),"scientific_promotion":bool(ci[1]<0),"refit":False,"retune":False,"same_support":True,"independent_reconstruction":True}
(root/"P068_RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
(root/"P068_PER_SHOT.json").write_text(json.dumps(per,indent=2,sort_keys=True)+"\n")
(root/"RUN_PROVENANCE_P068.json").write_text(json.dumps({"schema":"P068_GITHUB_AUTHORITY_PROVENANCE_V1","run_id":os.environ.get("GITHUB_RUN_ID"),"head_sha":os.environ.get("GITHUB_SHA"),"workflow":"sc-fair-mast-p068-primary10.yml"},indent=2,sort_keys=True)+"\n")
print(json.dumps(result,sort_keys=True))
