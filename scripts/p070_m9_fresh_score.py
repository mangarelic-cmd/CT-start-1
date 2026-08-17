import os, json, hashlib, traceback
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import s3fs

SHARD=int(os.environ.get('SHARD','0')); NS=int(os.environ.get('NS','10'))
OUT=Path(f'p070-primary-{SHARD}'); OUT.mkdir(exist_ok=True)
EXCLUDED=set(json.loads(Path('scripts/p070_excluded.json').read_text())['excluded_prior_unique'])
REQ=['thomson_scattering-n_e','thomson_scattering-t_e','summary-greenwald_density','summary-power_nbi','summary-power_radiated','gas_injection-inboard_total','gas_injection-outboard_total','equilibrium-beta_pol']
META_URL='https://raw.githubusercontent.com/UKAEA-IBM-STFC-Fusion-FMs/tokamark/1a200f4588addaad2ae3d53d438d9e1946c09294/src/MAST_tools/metadata/signal_availability.csv'
SEED='P070_M9_OUTBOARD_BETAPOL'

def trueish(v):
    if isinstance(v,(bool,np.bool_)): return bool(v)
    return str(v).strip().upper()=='TRUE'

# PHASE A — metadata only. No FAIR-MAST value can be read before PRIMARY/RESERVES are frozen.
meta=pd.read_csv(META_URL,usecols=REQ+['shot_id'])
elig=[]
for _,r in meta.iterrows():
    sid=int(r['shot_id'])
    if sid in EXCLUDED: continue
    if all(trueish(r[k]) for k in REQ): elig.append(sid)
elig=sorted(set(elig),key=lambda sid: hashlib.sha256(f'{SEED}|{sid}'.encode()).hexdigest())
if len(elig)<50: raise SystemExit(f'FAIL_CLOSED_ELIGIBLE={len(elig)}')
PRIMARY=elig[:30]; RESERVE=elig[30:50]
selection={'schema':'P070_FROZEN_METADATA_ONLY_SELECTION_V1','seed':SEED,'metadata_source_commit':'1a200f4588addaad2ae3d53d438d9e1946c09294','required_columns':REQ,'excluded_count':len(EXCLUDED),'eligible_count':len(elig),'primary':PRIMARY,'reserves':RESERVE,'fresh_fair_mast_values_read_before_freeze':False,'fresh_Te_values_read_before_freeze':False,'model':'M9_OUTBOARD_BETAPOL_BOUNDED_GATE_FROZEN_P069','comparators':['M7','M8'],'refit':False,'retune':False}
(OUT/'FROZEN_SELECTION_P070.json').write_text(json.dumps(selection,indent=2,sort_keys=True)+'\n')

# Frozen models: M7 inherited P065/P066, M8 P067/P068, M9 exactly P069.
L=np.log(1e19); A6=-44.10460779411159
MU_N5=1198323.3541824967; SD_N5=1182370.4221535327
C0=0.41225724854466805; B_RAD=-0.49493704322944887; B_NET=-0.19370038299807651
M8_B=np.array([0.03881345495128331,-0.17997322519938624,-0.12785474218295365,0.05794819945785843,0.06133852863061606],float)
M8_MU=np.array([4.352100967387832e21,9.113563978133691e21,6.441570771848568e21,-7.451853071196146e21],float)
M8_SD=np.array([6.169198453358396e21,1.1781699003230066e22,1.1378341400166194e23,2.7333708476375826e23],float)
GOUT_MU=9.113563978133691e21; GOUT_SD=1.1781699003230066e22
BP_MU=0.2517740158441083; BP_SD=0.3637966500802105
M9_B=np.array([0.5231876665903527,0.2426207414595824,-0.40141631782818105],float)

fs=s3fs.S3FileSystem(anon=True,client_kwargs={'endpoint_url':'https://s3.echo.stfc.ac.uk'})
def gettime(ds):
    if 'time' in ds.coords:return np.asarray(ds.coords['time'].load().values,float).reshape(-1)
    if 'time' in ds:return np.asarray(ds['time'].load().values,float).reshape(-1)
    for c in ds.coords:
        if 'time' in c.lower():return np.asarray(ds.coords[c].load().values,float).reshape(-1)
    raise KeyError('NO_TIME')
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
    if 'time' in d:a=np.moveaxis(a,d.index('time'),-1)
    elif a.shape[-1]==len(t):pass
    elif a.shape[0]==len(t):a=np.moveaxis(a,0,-1)
    else:raise ValueError('NO_TIME_AXIS')
    return a.reshape((-1,len(t)))
def deriv_on_finite(t,v):
    t=np.asarray(t,float); v=np.asarray(v,float); out=np.full(len(t),np.nan); m=np.isfinite(t)&np.isfinite(v)
    if m.sum()<2:return out
    tt=t[m]; vv=v[m]; o=np.argsort(tt); tt=tt[o]; vv=vv[o]; ut,ix=np.unique(tt,return_index=True); uv=vv[ix]
    if len(ut)<2:return out
    du=np.gradient(uv,ut); out[np.where(m)[0]]=np.interp(t[m],ut,du,left=np.nan,right=np.nan); return out

def score_shot(sid):
    rec={'shot_id':sid,'split':'P070_FRESH','refit':False,'retune':False,'models':['M7','M8','M9_OUTBOARD_BETAPOL'],'te_used_in_state_or_gate':False,'te_availability_mask_used_in_state_or_gate':False,'missing_beta_pol':'FAIL_CLOSED'}
    try:
        mp=fs.get_mapper(f'mast/level2/shots/{sid}.zarr')
        th=xr.open_zarr(mp,group='thomson_scattering',consolidated=None); td=gettime(th); ne=orient(th['n_e'],td); te=orient(th['t_e'],td)
        su=xr.open_zarr(mp,group='summary',consolidated=None)
        tg,vg=series(su,'greenwald_density'); tn,vn=series(su,'power_nbi'); tr,vr=series(su,'power_radiated')
        gi=xr.open_zarr(mp,group='gas_injection',consolidated=None); ti,vi=series(gi,'inboard_total'); to,vo=series(gi,'outboard_total')
        eq=xr.open_zarr(mp,group='equilibrium',consolidated=None); tb,vb=series(eq,'beta_pol')
        if any(x is None for x in [tg,tn,tr,ti,to,tb]): raise ValueError('STATE_SERIES_FAIL')
        gw=interp(tg,vg,td); nbi=interp(tn,vn,td); prad=interp(tr,vr,td); gin=interp(ti,vi,td); gout=interp(to,vo,td); beta=interp(tb,vb,td)
        dgin=deriv_on_finite(td,gin); dgout=deriv_on_finite(td,gout)
        Y=[];P7=[];P8=[];P9=[];TT=[];GOUT=[];BP=[];GATE9=[]
        for j,t in enumerate(td):
            # M9 primary support is decided entirely from pre-target state. Missing beta_pol is fail-closed.
            st=[gw[j],nbi[j],prad[j],gin[j],gout[j],dgin[j],dgout[j],beta[j]]
            if not all(np.isfinite(q) for q in st) or gw[j]<=0: continue
            mg=np.isfinite(ne[:,j])&(ne[:,j]>0)
            if not mg.any(): continue
            xg=np.log(ne[mg,j]); zn5=(nbi[j]-MU_N5)/SD_N5
            ug=(xg-L)-(4/3)*(np.log(gw[j])-L)-(1/5)*zn5+4/3
            gate=1/(1+np.exp(-np.clip(7*float(np.median(ug)),-60,60)))
            # Target enters only after state/gate/support are fixed.
            m=mg&np.isfinite(te[:,j])&(te[:,j]>0)
            if not m.any(): continue
            x=np.log(ne[m,j]); y=np.log(te[m,j]); u=(x-L)-(4/3)*(np.log(gw[j])-L)-(1/5)*zn5+4/3; H=np.logaddexp(0,7*u)/7
            m6=A6+(9/8)*(x-gate*H)
            radfrac=max(prad[j],0)/(max(prad[j],0)+max(nbi[j],0)+1.0); netmw=(nbi[j]-prad[j])/1e6
            m7=m6+C0+B_RAD*radfrac+B_NET*netmw
            f=np.array([gin[j],gout[j],dgin[j],dgout[j]],float); c8=M8_B[0]+float(np.dot(M8_B[1:],(f-M8_MU)/M8_SD)); m8=m7+c8
            zg=(gout[j]-GOUT_MU)/GOUT_SD; zb=(beta[j]-BP_MU)/BP_SD; g9=float(np.clip(M9_B[0]+M9_B[1]*zg+M9_B[2]*zb,0,1)); m9=m7+g9*c8
            Y.append(y);P7.append(m7);P8.append(m8);P9.append(m9);TT.append(np.full(m.sum(),t));GOUT.append(np.full(m.sum(),gout[j]));BP.append(np.full(m.sum(),beta[j]));GATE9.append(np.full(m.sum(),g9))
        if not Y: raise ValueError('NO_PAIRABLE_M9_SUPPORT')
        y=np.concatenate(Y); p7=np.concatenate(P7); p8=np.concatenate(P8); p9=np.concatenate(P9); tt=np.concatenate(TT)
        e7=float(np.mean((y-p7)**2)); e8=float(np.mean((y-p8)**2)); e9=float(np.mean((y-p9)**2))
        np.savez_compressed(OUT/f'SHOT_{sid}_P070_M9_RAW_SCORE_PACKET.npz',y_log_te=y,m7_pred=p7,m8_pred=p8,m9_pred=p9,time_s=tt,gas_out=np.concatenate(GOUT),beta_pol=np.concatenate(BP),g9=np.concatenate(GATE9))
        rec.update({'status':'USABLE','n_pairs':int(len(y)),'m7_mse':e7,'m8_mse':e8,'m9_mse':e9,'delta_m9_minus_m7':e9-e7,'delta_m9_minus_m8':e9-e8,'m9_beats_m7':bool(e9<e7),'m9_beats_m8':bool(e9<e8)})
    except Exception as e:
        rec.update({'status':'FAILED','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()})
    return rec

prim=[s for i,s in enumerate(PRIMARY) if i%NS==SHARD]; res=[s for i,s in enumerate(RESERVE) if i%NS==SHARD]
receipts=[]; failures=0
for sid in prim:
    r=score_shot(sid); receipts.append(r); failures += (r['status']!='USABLE')
activated=[]
for sid in res[:failures]:
    activated.append(sid); receipts.append(score_shot(sid))
(OUT/f'RECEIPTS_P070_{SHARD}.json').write_text(json.dumps(receipts,indent=2,sort_keys=True)+'\n')
(OUT/f'SUMMARY_P070_{SHARD}.json').write_text(json.dumps({'schema':'P070_PRIMARY_SHARD_SUMMARY_V1','shard':SHARD,'primary':prim,'reserve_owned':res,'reserve_activated':activated,'usable':sum(r['status']=='USABLE' for r in receipts),'failed':sum(r['status']!='USABLE' for r in receipts),'refit':False,'retune':False},indent=2,sort_keys=True)+'\n')
print(json.dumps({'shard':SHARD,'primary':prim,'activated':activated,'receipts':len(receipts)}))
