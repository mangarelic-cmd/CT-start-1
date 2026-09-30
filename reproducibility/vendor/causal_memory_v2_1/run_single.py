#!/usr/bin/env python3
import argparse, json, math, hashlib, time, importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('bench',str(Path(__file__).with_name('benchmark.py')))
b=importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
p=argparse.ArgumentParser();p.add_argument('coherence',type=float);p.add_argument('--n',type=int,default=1_000_000);p.add_argument('--index',type=int,default=0);a=p.parse_args()
raw,k,matches=b.make_dataset(a.n,a.coherence,0xBEEF0000+a.index)
cap,cm=b.causal_encode(raw,blind=True)
if cap is None:
    cm_decode_s=0.0; cm_ok=True
else:
    t=time.perf_counter(); rr=b.causal_decode(cap); cm_decode_s=time.perf_counter()-t; cm_ok=(rr==raw)
conv=b.conventional_codecs(raw)
best_name,minrec=min(conv.items(),key=lambda kv:kv[1]['bytes'])
pos_bits=b.exact_pos_bound_bits(a.n,k)
ideal_residual_bytes=(pos_bits+64*k+7)//8
ideal_self=(b.HEADER_SIZE+32+ideal_residual_bytes) if cap is not None else None
actual=len(cap) if cap is not None else len(raw)
row={
 'coherence_fraction':matches/a.n,'coherence_percent':100*matches/a.n,'n_words':a.n,'raw_bytes':len(raw),'raw_sha256':hashlib.sha256(raw).hexdigest(),'anomaly_count':k,
 'causal_mode':cm.get('mode'),'causal_bytes':cm['retained_bytes'],'causal_factor':len(raw)/cm['retained_bytes'],'causal_saving_percent':100*(1-cm['retained_bytes']/len(raw)),'causal_encode_s':cm['encode_s'],'causal_decode_s':cm_decode_s,'causal_replay_exact':cm_ok,
 'blind_discovery':cm.get('discovery'),'blind_discovery_hits':cm.get('discovery_hits'),'blind_discovered_fraction':cm.get('discovered_fraction'),'position_codec':cm.get('pos_codec'),'position_bytes':cm.get('pos_bytes'),'residual_value_bytes':cm.get('residual_value_bytes'),
 'position_lower_bound_bits':pos_bits,'ideal_residual_bytes':ideal_residual_bytes,'ideal_self_contained_bytes':ideal_self,'actual_over_ideal_self':(actual/ideal_self if ideal_self else None),
 'best_conventional':best_name,'best_conventional_bytes':minrec['bytes'],'best_conventional_factor':len(raw)/minrec['bytes'],
}
for name,rec in conv.items():
    for key,val in rec.items(): row[f'{name}_{key}']=val
out=Path(__file__).with_name(f'level_{a.index:02d}_{a.coherence:.6f}.json'); out.write_text(json.dumps(row,indent=2)); print(json.dumps({'out':str(out),'coherence':row['coherence_percent'],'causal_factor':row['causal_factor'],'best_conventional_factor':row['best_conventional_factor'],'causal_bytes':row['causal_bytes'],'ideal_self':row['ideal_self_contained_bytes'],'over_ideal':row['actual_over_ideal_self'],'discovery':row['blind_discovery'],'hits':row['blind_discovery_hits']},indent=2))
