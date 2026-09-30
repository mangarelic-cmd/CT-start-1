#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, os, shutil, tempfile, importlib.util
spec=importlib.util.spec_from_file_location('b','benchmark.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
levels=[0.90,0.999,1.0]
rows=[]
for j,c in enumerate(levels):
    raw,k,m=b.make_dataset(1_000_000,c,0xD3110000+j)
    expected=hashlib.sha256(raw).hexdigest()
    cap,meta=b.causal_encode(raw,blind=True)
    assert cap is not None
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); src=td/'source.bin'; cp=td/'capsule.cmem'
        src.write_bytes(raw); cp.write_bytes(cap)
        src.unlink()
        assert not src.exists()
        recovered=b.causal_decode(cp.read_bytes())
        got=hashlib.sha256(recovered).hexdigest()
        ok=(got==expected)
        # corruption must fail closed
        bad=bytearray(cp.read_bytes()); bad[len(bad)//2] ^= 1
        blocked=False
        try: b.causal_decode(bytes(bad))
        except Exception: blocked=True
        rows.append({'coherence_percent':100*c,'source_deleted_before_decode':True,'capsule_bytes':len(cap),'byte_identical':ok,'sha256_match':ok,'corruption_blocked':blocked})
Path('destructive_check.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
