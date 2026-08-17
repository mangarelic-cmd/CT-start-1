import os, json, traceback
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import s3fs

SHARD = int(os.environ['SHARD'])
NS = int(os.environ.get('NS','10'))
CANDIDATES = [27411,21333,24432,24136,29420,27042,20013,23626,22399,27276,21971,15052,21825,19911,16022,18076,14624,15315,29369,15570,24126,15133,27935,13816,13479,20918,16139,22213,12010,14373,13905,20505,14612,24430,30468,19955,21707,21906,20479]
REQ = ['thomson_scattering-n_e','thomson_scattering-t_e','summary-greenwald_density','summary-power_nbi','summary-power_radiated']
META_URL = 'https://raw.githubusercontent.com/UKAEA-IBM-STFC-Fusion-FMs/tokamark/1a200f4588addaad2ae3d53d438d9e1946c09294/src/MAST_tools/metadata/signal_availability.csv'
OUT = Path(f'p066-primary-{SHARD}')
OUT.mkdir(exist_ok=True)

def trueish(v):
    if isinstance(v,(bool,np.bool_)): return bool(v)
    return str(v).strip().upper() == 'TRUE'

# PHASE A: metadata-only selection. This file is committed to artifact before any FAIR-MAST values are opened.
meta = pd.read_csv(META_URL, usecols=REQ+['shot_id'])
meta = meta.set_index('shot_id', drop=False)
eligible=[]
meta_rows=[]
for sid in CANDIDATES:
    if sid not in meta.index:
        meta_rows.append({'shot_id':sid,'present':False,'eligible':False})
        continue
    row=meta.loc[sid]
    flags={k:trueish(row[k]) for k in REQ}
    ok=all(flags.values())
    meta_rows.append({'shot_id':sid,'present':True,'eligible':ok,'flags':flags})
    if ok: eligible.append(sid)
if len(eligible) < 30:
    raise SystemExit(f'FAIL_CLOSED_METADATA_GATE eligible={len(eligible)} < 30')
PRIMARY=eligible[:30]
RESERVES=eligible[30:]
SELECTION={
  'schema':'P066_FROZEN_METADATA_ONLY_SELECTION_V1',
  'candidate_rank':CANDIDATES,
  'required_columns':REQ,
  'metadata_source_commit':'1a200f4588addaad2ae3d53d438d9e1946c09294',
  'metadata_source_url':META_URL,
  'eligible_rank':eligible,
  'primary':PRIMARY,
  'reserves':RESERVES,
  'fresh_fair_mast_values_read_before_freeze':False,
  'fresh_Te_values_read_before_freeze':False,
  'selection_rows':meta_rows,
}
(OUT/'FROZEN_SELECTION_P066.json').write_text(json.dumps(SELECTION,indent=2,sort_keys=True)+'\n')
SHOTS=[s for i,s in enumerate(PRIMARY) if i%NS==SHARD]

# PHASE B: only now may FAIR-MAST values be opened.
fs=s3fs.S3FileSystem(anon=True,client_kwargs={'endpoint_url':'https://s3.echo.stfc.ac.uk'})
L=np.log(1e19)
A6=-44.10460779411159
MU_N5=1198323.3541824967
SD_N5=1182370.4221535327
C0=0.41225724854466805
B_RAD=-0.49493704322944887
B_NET=-0.19370038299807651

def gettime(ds):
    if 'time' in ds.coords:return np.asarray(ds.coords['time'].load().values,float).reshape(-1)
    if 'time' in ds:return np.asarray(ds['time'].load().values,float).reshape(-1)
    for c in ds.coords:
        if 'time' in c.lower():return np.asarray(ds.coords[c].load().values,float).reshape(-1)
    raise KeyError('NO_TIME')

def series(ds,v):
    if v not in ds:return None,None
    t=gettime(ds);a=np.squeeze(np.asarray(ds[v].load().values,float))
    if a.ndim!=1 or len(a)!=len(t):return None,None
    return t,a

def interp(t,v,q):
    m=np.isfinite(t)&np.isfinite(v);t=np.asarray(t)[m];v=np.asarray(v)[m]
    if len(t)<2:return np.full(len(q),np.nan)
    o=np.argsort(t);t=t[o];v=v[o];t,ix=np.unique(t,return_index=True);v=v[ix]
    z=np.interp(q,t,v,left=np.nan,right=np.nan)
    z[(q<t[0])|(q>t[-1])]=np.nan
    return z

def orient(var,t):
    a=np.asarray(var.load().values,float);d=list(var.dims)
    if 'time' in d:a=np.moveaxis(a,d.index('time'),-1)
    elif a.shape[-1]==len(t):pass
    elif a.shape[0]==len(t):a=np.moveaxis(a,0,-1)
    else:raise ValueError('NO_TIME_AXIS')
    return a.reshape((-1,len(t)))

receipts=[]
for sid in SHOTS:
    r={'shot_id':sid,'split':'P066_FRESH_PRIMARY','refit':False,'retune':False,'models':['M6','M7_RADIATIVE_BALANCE'],'te_used_in_gate':False,'te_availability_mask_used_in_gate':False}
    try:
        mp=fs.get_mapper(f'mast/level2/shots/{sid}.zarr')
        th=xr.open_zarr(mp,group='thomson_scattering',consolidated=None)
        td=gettime(th)
        ne=orient(th['n_e'],td)
        te=orient(th['t_e'],td)
        su=xr.open_zarr(mp,group='summary',consolidated=None)
        tg,vg=series(su,'greenwald_density')
        tn,vn=series(su,'power_nbi')
        tr,vr=series(su,'power_radiated')
        if tg is None or tn is None or tr is None:raise ValueError('STATE_SERIES_FAIL')
        gw=interp(tg,vg,td);nbi=interp(tn,vn,td);prad=interp(tr,vr,td)
        X=[];Y=[];GW=[];NBI=[];PR=[];TT=[];GA=[];UU=[];HH=[]
        for j,t in enumerate(td):
            # State/gate support is decided without Te or its finite mask.
            if not(np.isfinite(gw[j]) and gw[j]>0 and np.isfinite(nbi[j]) and np.isfinite(prad[j])):continue
            mg=np.isfinite(ne[:,j])&(ne[:,j]>0)
            if not mg.any():continue
            xg=np.log(ne[mg,j]);zn5=(nbi[j]-MU_N5)/SD_N5
            ug=(xg-L)-(4/3)*(np.log(gw[j])-L)-(1/5)*zn5+4/3
            ubar=float(np.median(ug))
            gate=1/(1+np.exp(-np.clip(7*ubar,-60,60)))
            # Te enters only after state/gate has been frozen for this time.
            m=mg&np.isfinite(te[:,j])&(te[:,j]>0)
            if not m.any():continue
            x=np.log(ne[m,j]);y=np.log(te[m,j])
            u=(x-L)-(4/3)*(np.log(gw[j])-L)-(1/5)*zn5+4/3
            H=np.logaddexp(0,7*u)/7
            X.append(x);Y.append(y);GW.append(np.full(m.sum(),gw[j]));NBI.append(np.full(m.sum(),nbi[j]));PR.append(np.full(m.sum(),prad[j]));TT.append(np.full(m.sum(),t));GA.append(np.full(m.sum(),gate));UU.append(u);HH.append(H)
        if not X:raise ValueError('NO_PAIRABLE_M7_SUPPORT')
        x=np.concatenate(X);y=np.concatenate(Y);gwv=np.concatenate(GW);nbiv=np.concatenate(NBI);prv=np.concatenate(PR);tt=np.concatenate(TT);ga=np.concatenate(GA);u=np.concatenate(UU);H=np.concatenate(HH)
        m6=A6+(9/8)*(x-ga*H)
        radfrac=np.maximum(prv,0)/(np.maximum(prv,0)+np.maximum(nbiv,0)+1.0)
        netmw=(nbiv-prv)/1e6
        m7=m6+C0+B_RAD*radfrac+B_NET*netmw
        e6=float(np.mean((y-m6)**2));e7=float(np.mean((y-m7)**2));delta=e7-e6
        np.savez_compressed(OUT/f'SHOT_{sid}_P066_M7_RAW_SCORE_PACKET.npz',x_log_ne=x,y_log_te=y,time_s=tt,greenwald_density=gwv,power_nbi=nbiv,power_radiated=prv,u_sat=u,H_sat=H,activation_gate=ga,rad_fraction=radfrac,net_power_mw=netmw,m6_pred=m6,m7_pred=m7)
        r.update({'status':'USABLE','n_pairs':int(len(x)),'m6_mse':e6,'m7_mse':e7,'delta_m7_minus_m6':delta,'m7_beats_m6':bool(delta<0),'mean_rad_fraction':float(np.mean(radfrac)),'mean_net_power_mw':float(np.mean(netmw)),'mean_activation_gate':float(np.mean(ga))})
    except Exception as e:
        r.update({'status':'FAILED','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()})
    receipts.append(r)
(OUT/f'RECEIPTS_P066_{SHARD}.json').write_text(json.dumps(receipts,indent=2,sort_keys=True)+'\n')
(OUT/f'SUMMARY_P066_{SHARD}.json').write_text(json.dumps({'schema':'P066_PRIMARY_SHARD_SUMMARY_V1','shard':SHARD,'shots':SHOTS,'usable':sum(x['status']=='USABLE' for x in receipts),'failed':sum(x['status']!='USABLE' for x in receipts),'refit':False,'retune':False,'selection_primary':PRIMARY,'selection_reserves':RESERVES},indent=2,sort_keys=True)+'\n')
