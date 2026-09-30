#!/usr/bin/env python3
from __future__ import annotations
import bz2, csv, gzip, hashlib, json, lzma, math, os, random, statistics, struct, subprocess, time, zlib
from collections import Counter
from pathlib import Path
import numpy as np
import brotli
import lz4.frame

OUT = Path(__file__).resolve().parent
RESULTS_JSON = OUT / 'results.json'
RESULTS_CSV = OUT / 'results.csv'
SCALING_CSV = OUT / 'scaling.csv'
MASK = (1 << 64) - 1
MOD = 1 << 64
MAGIC = b'CMCB'
VERSION = 1
# SplitMix64 constants
MIX1 = 0xBF58476D1CE4E5B9
MIX2 = 0x94D049BB133111EB
INV_MIX1 = pow(MIX1, -1, MOD)
INV_MIX2 = pow(MIX2, -1, MOD)
DEFAULT_SEED = 0x123456789ABCDEF0
DEFAULT_GAMMA = 0x9E3779B97F4A7C15


def sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


def mix64(z: int) -> int:
    z &= MASK
    z = ((z ^ (z >> 30)) * MIX1) & MASK
    z = ((z ^ (z >> 27)) * MIX2) & MASK
    return (z ^ (z >> 31)) & MASK


def undo_xor_r(y: int, shift: int) -> int:
    x = y & MASK
    # fixed-point iteration converges after ceil(64/shift) rounds
    for _ in range((64 + shift - 1)//shift + 1):
        x = (y ^ (x >> shift)) & MASK
    return x


def unmix64(z: int) -> int:
    z = undo_xor_r(z, 31)
    z = (z * INV_MIX2) & MASK
    z = undo_xor_r(z, 27)
    z = (z * INV_MIX1) & MASK
    z = undo_xor_r(z, 30)
    return z & MASK


def verify_mix_inverse() -> None:
    vals = [0,1,2,DEFAULT_SEED, MASK, 0xDEADBEEFCAFEBABE]
    for v in vals:
        assert unmix64(mix64(v)) == v


def generate_base(n: int, seed: int, gamma: int) -> np.ndarray:
    arr = np.empty(n, dtype=np.uint64)
    s = seed & MASK
    g = gamma & MASK
    for i in range(n):
        s = (s + g) & MASK
        arr[i] = mix64(s)
    return arr


def make_dataset(n: int, coherence: float, dataset_seed: int) -> tuple[bytes, int, int]:
    base = generate_base(n, DEFAULT_SEED, DEFAULT_GAMMA)
    k = int(round(n * (1.0 - coherence)))
    rng = np.random.default_rng(dataset_seed)
    if k <= 0:
        arr = base
        return arr.astype('<u8', copy=False).tobytes(), 0, n
    if k >= n:
        vals = rng.integers(0, np.iinfo(np.uint64).max, size=n, dtype=np.uint64, endpoint=True)
        # guarantee no accidental equality
        same = vals == base
        vals[same] ^= np.uint64(0xD1B54A32D192ED03)
        return vals.astype('<u8', copy=False).tobytes(), n, 0
    # choose the smaller set to build the mask efficiently
    if k <= n // 2:
        anomaly_positions = np.sort(rng.choice(n, size=k, replace=False))
        arr = base.copy()
        vals = rng.integers(0, np.iinfo(np.uint64).max, size=k, dtype=np.uint64, endpoint=True)
        same = vals == arr[anomaly_positions]
        vals[same] ^= np.uint64(0xD1B54A32D192ED03)
        arr[anomaly_positions] = vals
    else:
        coherent_count = n-k
        coherent_positions = np.sort(rng.choice(n, size=coherent_count, replace=False))
        keep = np.zeros(n, dtype=bool)
        keep[coherent_positions] = True
        arr = rng.integers(0, np.iinfo(np.uint64).max, size=n, dtype=np.uint64, endpoint=True)
        # guarantee anomalies differ from base
        same = (arr == base) & (~keep)
        arr[same] ^= np.uint64(0xD1B54A32D192ED03)
        arr[keep] = base[keep]
    matches = int(np.count_nonzero(arr == base))
    actual_k = n - matches
    return arr.astype('<u8', copy=False).tobytes(), actual_k, matches


def encode_varint(x: int) -> bytes:
    out = bytearray()
    while True:
        b = x & 0x7F
        x >>= 7
        if x:
            out.append(b | 0x80)
        else:
            out.append(b)
            break
    return bytes(out)


def decode_varints(data: bytes, count: int) -> list[int]:
    out=[]; val=0; shift=0
    for b in data:
        val |= (b & 0x7F) << shift
        if b & 0x80:
            shift += 7
            if shift > 70: raise ValueError('varint overflow')
        else:
            out.append(val); val=0; shift=0
            if len(out)==count:
                if data[data.index(b)+1:]:
                    pass
                break
    if len(out)!=count or shift!=0:
        raise ValueError('bad varint stream')
    return out


def pack_gap_varints(indices: np.ndarray) -> bytes:
    prev=-1; out=bytearray()
    for p0 in indices:
        p=int(p0); d=p-prev
        out += encode_varint(d)
        prev=p
    return bytes(out)


def unpack_gap_varints(data: bytes, count: int) -> list[int]:
    deltas=[]; val=0; shift=0
    for b in data:
        val |= (b & 0x7F) << shift
        if b & 0x80:
            shift += 7
            if shift > 70: raise ValueError('varint overflow')
        else:
            deltas.append(val); val=0; shift=0
    if len(deltas)!=count or shift!=0:
        raise ValueError('bad varint count')
    out=[]; prev=-1
    for d in deltas:
        p=prev+d
        if p<=prev: raise ValueError('nonpositive gap')
        out.append(p); prev=p
    return out


def pack_bitmap(indices: np.ndarray, n: int) -> bytes:
    b = bytearray((n+7)//8)
    for p0 in indices:
        p=int(p0); b[p>>3] |= 1 << (p & 7)
    return bytes(b)


def unpack_bitmap(data: bytes, n: int, count: int) -> list[int]:
    out=[]
    for i in range(n):
        if data[i>>3] & (1 << (i&7)):
            out.append(i)
    if len(out)!=count: raise ValueError('bitmap count mismatch')
    return out


def discover_model(raw: bytes, sample_pairs: int = 20000, rng_seed: int = 0xD15C0A7) -> tuple[int,int,int,float]:
    vals = np.frombuffer(raw, dtype='<u8')
    n=len(vals)
    if n<2: raise ValueError('too short')
    rng = np.random.default_rng(rng_seed)
    m = min(sample_pairs, n-1)
    idx = rng.choice(n-1, size=m, replace=False) if m < n-1 else np.arange(n-1)
    cnt=Counter()
    # pair-adjacent state differences; clean adjacent observations yield same (seed,gamma)
    for i0 in idx:
        i=int(i0)
        s0=unmix64(int(vals[i])); s1=unmix64(int(vals[i+1]))
        gamma=(s1-s0)&MASK
        seed=(s0 - (gamma * (i+1))) & MASK
        cnt[(seed,gamma)] += 1
    (seed,gamma), hits = cnt.most_common(1)[0]
    # A repeated key is overwhelming evidence because false 128-bit keys almost never collide.
    if hits < max(8, int(0.0005*m)):
        raise ValueError(f'no stable model: top support {hits}/{m}')
    base=generate_base(n,seed,gamma)
    matches=int(np.count_nonzero(base == vals))
    return seed,gamma,hits,matches/n

# Header: magic, version, set_kind, pos_codec, reserved, n, seed, gamma, k, subset_count, pos_len
HEADER_FMT = '>4sBBBBQQQQQQ'
HEADER_SIZE = struct.calcsize(HEADER_FMT)
POS_NONE=0; POS_VARINT=1; POS_BITMAP=2
SET_ANOM=0; SET_COHERENT=1


def causal_encode(raw: bytes, blind: bool = True) -> tuple[bytes|None, dict]:
    vals=np.frombuffer(raw,dtype='<u8'); n=len(vals)
    t0=time.perf_counter()
    if blind:
        try:
            seed,gamma,discovery_hits,discovered_fraction=discover_model(raw)
            discovered=True
        except Exception as e:
            # fail closed: raw fallback
            return None, {'retained_bytes':len(raw),'mode':'KEEP_RAW','encode_s':time.perf_counter()-t0,'discovery':'FAIL','discovery_error':str(e)}
    else:
        seed,gamma=DEFAULT_SEED,DEFAULT_GAMMA; discovery_hits=None; discovered_fraction=None; discovered=True
    base=generate_base(n,seed,gamma)
    anomaly_mask = vals != base
    anom_idx=np.flatnonzero(anomaly_mask)
    k=len(anom_idx)
    coh_idx=np.flatnonzero(~anomaly_mask)
    if k <= n//2:
        subset=anom_idx; set_kind=SET_ANOM
    else:
        subset=coh_idx; set_kind=SET_COHERENT
    subset_count=len(subset)
    if subset_count==0:
        pos_codec=POS_NONE; pos_data=b''
    else:
        v=pack_gap_varints(subset)
        bm=pack_bitmap(subset,n)
        if len(v) <= len(bm): pos_codec=POS_VARINT; pos_data=v
        else: pos_codec=POS_BITMAP; pos_data=bm
    residual_vals=vals[anom_idx].astype('<u8',copy=False).tobytes()
    header=struct.pack(HEADER_FMT,MAGIC,VERSION,set_kind,pos_codec,0,n,seed,gamma,k,subset_count,len(pos_data))
    capsule=header+pos_data+residual_vals+sha256(raw)
    enc_s=time.perf_counter()-t0
    if len(capsule) >= len(raw):
        return None, {'retained_bytes':len(raw),'mode':'KEEP_RAW','encode_s':enc_s,'discovery':'PASS' if discovered else 'FAIL','discovery_hits':discovery_hits,'discovered_fraction':discovered_fraction,'k':k}
    return capsule, {'retained_bytes':len(capsule),'mode':'STRUCTURED','encode_s':enc_s,'discovery':'PASS','discovery_hits':discovery_hits,'discovered_fraction':discovered_fraction,'k':k,'pos_codec':pos_codec,'pos_bytes':len(pos_data),'residual_value_bytes':len(residual_vals),'header_integrity_bytes':HEADER_SIZE+32,'seed':seed,'gamma':gamma}


def causal_decode(capsule: bytes) -> bytes:
    if len(capsule) < HEADER_SIZE+32: raise ValueError('truncated')
    fields=struct.unpack(HEADER_FMT,capsule[:HEADER_SIZE])
    magic,ver,set_kind,pos_codec,_r,n,seed,gamma,k,subset_count,pos_len=fields
    if magic!=MAGIC or ver!=VERSION: raise ValueError('schema')
    expected=HEADER_SIZE+pos_len+8*k+32
    if len(capsule)!=expected: raise ValueError('length')
    pos_data=capsule[HEADER_SIZE:HEADER_SIZE+pos_len]
    vals_data=capsule[HEADER_SIZE+pos_len:-32]
    if pos_codec==POS_NONE:
        subset=[]
        if subset_count!=0 or pos_len!=0: raise ValueError('none mismatch')
    elif pos_codec==POS_VARINT:
        subset=unpack_gap_varints(pos_data,subset_count)
    elif pos_codec==POS_BITMAP:
        subset=unpack_bitmap(pos_data,n,subset_count)
    else: raise ValueError('pos codec')
    if subset and subset[-1]>=n: raise ValueError('position range')
    if set_kind==SET_ANOM:
        anom=np.array(subset,dtype=np.int64)
    elif set_kind==SET_COHERENT:
        keep=np.zeros(n,dtype=bool); keep[np.array(subset,dtype=np.int64)]=True
        anom=np.flatnonzero(~keep)
    else: raise ValueError('set kind')
    if len(anom)!=k: raise ValueError('k mismatch')
    base=generate_base(n,seed,gamma)
    residual=np.frombuffer(vals_data,dtype='<u8')
    if len(residual)!=k: raise ValueError('residual len')
    base[anom]=residual
    raw=base.astype('<u8',copy=False).tobytes()
    if sha256(raw)!=capsule[-32:]: raise ValueError('sha mismatch')
    return raw


def conventional_codecs(raw: bytes) -> dict:
    out={}
    funcs={
      'zlib9': (lambda d:zlib.compress(d,9), zlib.decompress),
      'gzip9': (lambda d:gzip.compress(d,compresslevel=9,mtime=0), gzip.decompress),
      'bzip2_9': (lambda d:bz2.compress(d,compresslevel=9), bz2.decompress),
      'xz_lzma9': (lambda d:lzma.compress(d,preset=9), lzma.decompress),
      'brotli11': (lambda d:brotli.compress(d,quality=11), brotli.decompress),
      'lz4_hc16': (lambda d:lz4.frame.compress(d,compression_level=16), lz4.frame.decompress),
    }
    for name,(enc,dec) in funcs.items():
        t=time.perf_counter(); c=enc(raw); enc_s=time.perf_counter()-t
        t=time.perf_counter(); r=dec(c); dec_s=time.perf_counter()-t
        assert r==raw
        out[name]={'bytes':len(c),'factor':len(raw)/len(c),'encode_s':enc_s,'decode_s':dec_s}
    t=time.perf_counter(); p=subprocess.run(['zstd','-19','-q','-c'],input=raw,stdout=subprocess.PIPE,check=True); enc_s=time.perf_counter()-t; c=p.stdout
    t=time.perf_counter(); q=subprocess.run(['zstd','-d','-q','-c'],input=c,stdout=subprocess.PIPE,check=True); dec_s=time.perf_counter()-t
    assert q.stdout==raw
    out['zstd19']={'bytes':len(c),'factor':len(raw)/len(c),'encode_s':enc_s,'decode_s':dec_s}
    return out


def exact_pos_bound_bits(n:int,k:int)->int:
    if k<=0 or k>=n: return 0
    c=math.comb(n,k)
    return (c-1).bit_length()


def run_ladder(n:int=1_000_000):
    verify_mix_inverse()
    levels=[0.0,0.10,0.25,0.50,0.75,0.90,0.99,0.999,0.9999,1.0]
    results=[]
    for j,c in enumerate(levels):
        print(f'LEVEL {c:.4%}',flush=True)
        raw,k,matches=make_dataset(n,c,0xBEEF0000+j)
        raw_sha=hashlib.sha256(raw).hexdigest()
        # Blind causal encode first
        cap,cm=causal_encode(raw,blind=True)
        if cap is None:
            cm_decode_s=0.0; cm_ok=True
        else:
            t=time.perf_counter(); rr=causal_decode(cap); cm_decode_s=time.perf_counter()-t; cm_ok=(rr==raw)
        conv=conventional_codecs(raw)
        best_name,minrec=min(conv.items(),key=lambda kv:kv[1]['bytes'])
        pos_bits=exact_pos_bound_bits(n,k)
        ideal_residual_bytes=(pos_bits+64*k+7)//8
        if cap is not None:
            ideal_self=HEADER_SIZE+32+ideal_residual_bytes
            actual=len(cap)
            overhead_ratio=actual/ideal_self if ideal_self else 1.0
        else:
            ideal_self=None; actual=len(raw); overhead_ratio=None
        row={
          'coherence_fraction':matches/n,
          'coherence_percent':100*matches/n,
          'n_words':n,
          'raw_bytes':len(raw),
          'raw_sha256':raw_sha,
          'anomaly_count':k,
          'causal_mode':cm.get('mode'),
          'causal_bytes':cm['retained_bytes'],
          'causal_factor':len(raw)/cm['retained_bytes'],
          'causal_saving_percent':100*(1-cm['retained_bytes']/len(raw)),
          'causal_encode_s':cm['encode_s'],
          'causal_decode_s':cm_decode_s,
          'causal_replay_exact':cm_ok,
          'blind_discovery':cm.get('discovery'),
          'blind_discovery_hits':cm.get('discovery_hits'),
          'blind_discovered_fraction':cm.get('discovered_fraction'),
          'position_codec':cm.get('pos_codec'),
          'position_bytes':cm.get('pos_bytes'),
          'residual_value_bytes':cm.get('residual_value_bytes'),
          'position_lower_bound_bits':pos_bits,
          'ideal_residual_bytes':ideal_residual_bytes,
          'ideal_self_contained_bytes':ideal_self,
          'actual_over_ideal_self':overhead_ratio,
          'best_conventional':best_name,
          'best_conventional_bytes':minrec['bytes'],
          'best_conventional_factor':len(raw)/minrec['bytes'],
        }
        for name,rec in conv.items():
            for key,val in rec.items(): row[f'{name}_{key}']=val
        results.append(row)
        print('  causal',row['causal_bytes'],row['causal_factor'],'best',best_name,minrec['bytes'],row['best_conventional_factor'],'discovery',row['blind_discovery'],flush=True)
    return results


def run_scaling():
    rows=[]
    for n in [1_000,10_000,100_000,1_000_000]:
        raw,k,m=make_dataset(n,1.0,0xACED+n)
        cap,cm=causal_encode(raw,blind=True)
        assert cap is not None and causal_decode(cap)==raw
        # Only fast representative conventional codecs here plus best strong codec brotli11
        conv={}
        for name,enc in [('zlib9',lambda d:zlib.compress(d,9)),('brotli11',lambda d:brotli.compress(d,quality=11))]:
            t=time.perf_counter(); c=enc(raw); conv[name]=(len(c),time.perf_counter()-t)
        rows.append({'n_words':n,'raw_bytes':len(raw),'causal_bytes':len(cap),'causal_factor':len(raw)/len(cap),'zlib9_bytes':conv['zlib9'][0],'zlib9_factor':len(raw)/conv['zlib9'][0],'brotli11_bytes':conv['brotli11'][0],'brotli11_factor':len(raw)/conv['brotli11'][0],'causal_encode_s':cm['encode_s']})
    return rows


def write_outputs(results,scaling):
    RESULTS_JSON.write_text(json.dumps({'ladder':results,'scaling':scaling},indent=2),encoding='utf-8')
    keys=list(results[0].keys())
    with RESULTS_CSV.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(results)
    with SCALING_CSV.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(scaling[0].keys())); w.writeheader(); w.writerows(scaling)

if __name__=='__main__':
    res=run_ladder(); sc=run_scaling(); write_outputs(res,sc)
    print('WROTE',RESULTS_JSON,RESULTS_CSV,SCALING_CSV)
