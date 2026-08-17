import os, json, hashlib, traceback
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import s3fs

SHARD=int(os.environ.get("SHARD","0")); NS=int(os.environ.get("NS","10"))
OUT=Path(f"p068-primary-{SHARD}"); OUT.mkdir(exist_ok=True)
EXCLUDED=set([11766, 12010, 12080, 12088, 12168, 12202, 12228, 12232, 12460, 12474, 12697, 12747, 12901, 12931, 12964, 13038, 13093, 13094, 13108, 13274, 13365, 13430, 13479, 13557, 13583, 13632, 13644, 13696, 13742, 13766, 13797, 13816, 13905, 14017, 14160, 14209, 14373, 14520, 14568, 14583, 14612, 14621, 14624, 14804, 15052, 15081, 15109, 15113, 15133, 15153, 15279, 15315, 15325, 15340, 15507, 15570, 15617, 15618, 15703, 15898, 15993, 16022, 16036, 16109, 16139, 16151, 16195, 16265, 16396, 16443, 16444, 16731, 16828, 16862, 16987, 17093, 17098, 17664, 17712, 17713, 17768, 17820, 17823, 17901, 17921, 17964, 17990, 17994, 17999, 18076, 18328, 18369, 18496, 18531, 18578, 18743, 18762, 18886, 19382, 19911, 19955, 20013, 20036, 20107, 20428, 20465, 20479, 20495, 20498, 20505, 20508, 20514, 20519, 20570, 20651, 20708, 20849, 20862, 20880, 20918, 21066, 21333, 21344, 21517, 21707, 21771, 21785, 21797, 21801, 21825, 21876, 21902, 21906, 21971, 22162, 22213, 22215, 22287, 22300, 22308, 22309, 22382, 22399, 22402, 22430, 22507, 22526, 22657, 23143, 23384, 23445, 23457, 23485, 23489, 23530, 23598, 23626, 23667, 23742, 23776, 23784, 23792, 23889, 24004, 24018, 24088, 24126, 24136, 24143, 24145, 24194, 24208, 24344, 24430, 24432, 24474, 24514, 24528, 24619, 24625, 24665, 24717, 24726, 24821, 24896, 24905, 24933, 25365, 25696, 25697, 26004, 26068, 26163, 26310, 26448, 26463, 26531, 26596, 26651, 26867, 26953, 27042, 27050, 27125, 27169, 27171, 27198, 27276, 27401, 27411, 27450, 27584, 27588, 27601, 27639, 27640, 27731, 27740, 27814, 27822, 27935, 28027, 28076, 28178, 28259, 28267, 28811, 28816, 28819, 28860, 28911, 28997, 29047, 29077, 29143, 29199, 29229, 29369, 29420, 29440, 29442, 29488, 29660, 29702, 29983, 30048, 30145, 30209, 30468])
REQ=["thomson_scattering-n_e","thomson_scattering-t_e","summary-greenwald_density","summary-power_nbi","summary-power_radiated","gas_injection-inboard_total","gas_injection-outboard_total"]
META_URL="https://raw.githubusercontent.com/UKAEA-IBM-STFC-Fusion-FMs/tokamark/1a200f4588addaad2ae3d53d438d9e1946c09294/src/MAST_tools/metadata/signal_availability.csv"
SEED="P068_M8_DYNAMIC_FUELING"

def trueish(v):
    if isinstance(v,(bool,np.bool_)): return bool(v)
    return str(v).strip().upper()=="TRUE"

meta=pd.read_csv(META_URL,usecols=REQ+["shot_id"])
elig=[]
for _,r in meta.iterrows():
    sid=int(r["shot_id"])
    if sid in EXCLUDED: continue
    if all(trueish(r[k]) for k in REQ): elig.append(sid)
elig=sorted(set(elig), key=lambda sid: hashlib.sha256(f"{SEED}|{sid}".encode()).hexdigest())
if len(elig)<50: raise SystemExit(f"FAIL_CLOSED_ELIGIBLE={len(elig)}")
PRIMARY=elig[:30]; RESERVE=elig[30:50]
selection={"schema":"P068_FROZEN_METADATA_ONLY_SELECTION_V1","seed":SEED,"metadata_source_commit":"1a200f4588addaad2ae3d53d438d9e1946c09294","required_columns":REQ,"excluded_count":len(EXCLUDED),"eligible_count":len(elig),"primary":PRIMARY,"reserves":RESERVE,"fresh_fair_mast_values_read_before_freeze":False,"fresh_Te_values_read_before_freeze":False}
(OUT/"FROZEN_SELECTION_P068.json").write_text(json.dumps(selection,indent=2,sort_keys=True)+"\n")

L=np.log(1e19)
A6=-44.10460779411159
MU_N5=1198323.3541824967; SD_N5=1182370.4221535327
C0=0.41225724854466805; B_RAD=-0.49493704322944887; B_NET=-0.19370038299807651
M8_B=np.array([0.03881345495128331,-0.17997322519938624,-0.12785474218295365,0.05794819945785843,0.06133852863061606],float)
M8_MU=np.array([4.352100967387832e21,9.113563978133691e21,6.441570771848568e21,-7.451853071196146e21],float)
M8_SD=np.array([6.169198453358396e21,1.1781699003230066e22,1.1378341400166194e23,2.7333708476375826e23],float)

fs=s3fs.S3FileSystem(anon=True,client_kwargs={"endpoint_url":"https://s3.echo.stfc.ac.uk"})
def gettime(ds):
    if "time" in ds.coords:return np.asarray(ds.coords["time"].load().values,float).reshape(-1)
    if "time" in ds:return np.asarray(ds["time"].load().values,float).reshape(-1)
    for c in ds.coords:
        if "time" in c.lower():return np.asarray(ds.coords[c].load().values,float).reshape(-1)
    raise KeyError("NO_TIME")
def series(ds,v):
    if v not in ds:return None,None
    t=gettime(ds); a=np.squeeze(np.asarray(ds[v].load().values,float))
    if a.ndim!=1 or len(a)!=len(t):return None,None
    return t,a
def interp(t,v,q):
    m=np.isfinite(t)&np.isfinite(v); t=np.asarray(t)[m]; v=np.asarray(v)[m]
    if len(t)<2:return np.full(len(q),np.nan)
    o=np.argsort(t); t=t[o]; v=v[o]; t,ix=np.unique(t,return_index=True); v=v[ix]
    z=np.interp(q,t,v,left=np.nan,right=np.nan); z[(q<t[0])|(q>t[-1])]=np.nan; return z
def orient(var,t):
    a=np.asarray(var.load().values,float); d=list(var.dims)
    if "time" in d:a=np.moveaxis(a,d.index("time"),-1)
    elif a.shape[-1]==len(t):pass
    elif a.shape[0]==len(t):a=np.moveaxis(a,0,-1)
    else:raise ValueError("NO_TIME_AXIS")
    return a.reshape((-1,len(t)))
def deriv_on_finite(t,v):
    t=np.asarray(t,float); v=np.asarray(v,float); out=np.full(len(t),np.nan)
    m=np.isfinite(t)&np.isfinite(v)
    if m.sum()<2:return out
    tt=t[m]; vv=v[m]; o=np.argsort(tt); tt=tt[o]; vv=vv[o]
    ut,ix=np.unique(tt,return_index=True); uv=vv[ix]
    if len(ut)<2:return out
    du=np.gradient(uv,ut)
    vals=np.interp(t[m],ut,du,left=np.nan,right=np.nan)
    out[np.where(m)[0]]=vals
    return out

def score_shot(sid):
    rec={"shot_id":sid,"split":"P068_FRESH","refit":False,"retune":False,"models":["M7","M8_DYNAMIC_FUELING"],"te_used_in_state_or_gate":False,"te_availability_mask_used_in_state_or_gate":False}
    try:
        mp=fs.get_mapper(f"mast/level2/shots/{sid}.zarr")
        th=xr.open_zarr(mp,group="thomson_scattering",consolidated=None); td=gettime(th)
        ne=orient(th["n_e"],td); te=orient(th["t_e"],td)
        su=xr.open_zarr(mp,group="summary",consolidated=None)
        tg,vg=series(su,"greenwald_density"); tn,vn=series(su,"power_nbi"); tr,vr=series(su,"power_radiated")
        gi=xr.open_zarr(mp,group="gas_injection",consolidated=None)
        ti,vi=series(gi,"inboard_total"); to,vo=series(gi,"outboard_total")
        if any(x is None for x in [tg,tn,tr,ti,to]): raise ValueError("STATE_SERIES_FAIL")
        gw=interp(tg,vg,td); nbi=interp(tn,vn,td); prad=interp(tr,vr,td); gin=interp(ti,vi,td); gout=interp(to,vo,td)
        dgin=deriv_on_finite(td,gin); dgout=deriv_on_finite(td,gout)
        Y=[];P7=[];P8=[];TT=[];GIN=[];GOUT=[];DGIN=[];DGOUT=[]
        for j,t in enumerate(td):
            st=[gw[j],nbi[j],prad[j],gin[j],gout[j],dgin[j],dgout[j]]
            if not all(np.isfinite(q) for q in st) or gw[j]<=0: continue
            mg=np.isfinite(ne[:,j])&(ne[:,j]>0)
            if not mg.any(): continue
            xg=np.log(ne[mg,j]); zn5=(nbi[j]-MU_N5)/SD_N5
            ug=(xg-L)-(4/3)*(np.log(gw[j])-L)-(1/5)*zn5+4/3
            gate=1/(1+np.exp(-np.clip(7*float(np.median(ug)),-60,60)))
            m=mg&np.isfinite(te[:,j])&(te[:,j]>0)
            if not m.any(): continue
            x=np.log(ne[m,j]); y=np.log(te[m,j]); u=(x-L)-(4/3)*(np.log(gw[j])-L)-(1/5)*zn5+4/3; H=np.logaddexp(0,7*u)/7
            m6=A6+(9/8)*(x-gate*H); radfrac=max(prad[j],0)/(max(prad[j],0)+max(nbi[j],0)+1.0); netmw=(nbi[j]-prad[j])/1e6
            m7=m6+C0+B_RAD*radfrac+B_NET*netmw
            f=np.array([gin[j],gout[j],dgin[j],dgout[j]],float); corr=M8_B[0]+float(np.dot(M8_B[1:],(f-M8_MU)/M8_SD)); m8=m7+corr
            Y.append(y); P7.append(m7); P8.append(m8); TT.append(np.full(m.sum(),t)); GIN.append(np.full(m.sum(),gin[j])); GOUT.append(np.full(m.sum(),gout[j])); DGIN.append(np.full(m.sum(),dgin[j])); DGOUT.append(np.full(m.sum(),dgout[j]))
        if not Y: raise ValueError("NO_PAIRABLE_M8_SUPPORT")
        y=np.concatenate(Y); p7=np.concatenate(P7); p8=np.concatenate(P8); tt=np.concatenate(TT)
        e7=float(np.mean((y-p7)**2)); e8=float(np.mean((y-p8)**2)); delta=e8-e7
        np.savez_compressed(OUT/f"SHOT_{sid}_P068_M8_RAW_SCORE_PACKET.npz",y_log_te=y,m7_pred=p7,m8_pred=p8,time_s=tt,gas_in=np.concatenate(GIN),gas_out=np.concatenate(GOUT),d_gas_in_dt=np.concatenate(DGIN),d_gas_out_dt=np.concatenate(DGOUT))
        rec.update({"status":"USABLE","n_pairs":int(len(y)),"m7_mse":e7,"m8_mse":e8,"delta_m8_minus_m7":delta,"m8_beats_m7":bool(delta<0)})
    except Exception as e:
        rec.update({"status":"FAILED","error_type":type(e).__name__,"error":str(e),"traceback":traceback.format_exc()})
    return rec

prim=[s for i,s in enumerate(PRIMARY) if i%NS==SHARD]; res=[s for i,s in enumerate(RESERVE) if i%NS==SHARD]
receipts=[]; failures=0
for sid in prim:
    r=score_shot(sid); receipts.append(r); failures += (r["status"]!="USABLE")
activated=[]
for sid in res[:failures]:
    activated.append(sid); receipts.append(score_shot(sid))
(OUT/f"RECEIPTS_P068_{SHARD}.json").write_text(json.dumps(receipts,indent=2,sort_keys=True)+"\n")
(OUT/f"SUMMARY_P068_{SHARD}.json").write_text(json.dumps({"schema":"P068_PRIMARY_SHARD_SUMMARY_V1","shard":SHARD,"primary":prim,"reserve_owned":res,"reserve_activated":activated,"usable":sum(r["status"]=="USABLE" for r in receipts),"failed":sum(r["status"]!="USABLE" for r in receipts),"refit":False,"retune":False},indent=2,sort_keys=True)+"\n")
print(json.dumps({"shard":SHARD,"primary":prim,"activated":activated,"receipts":len(receipts)}))
