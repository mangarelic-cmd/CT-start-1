import os,json,traceback,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr
import s3fs

SHARD=int(os.environ['SHARD']); NSHARD=10
OUT=Path(f'p062-primary-{SHARD}'); OUT.mkdir(exist_ok=True)
ENDPOINT='https://s3.echo.stfc.ac.uk'
PRIMARY=[23776,21876,24933,22507,23384,16109,20849,17713,24208,28911,12080,26310,27639,27814,21902,17990,28076,12232,20519,13094,30209,12460,26531,16444,14568,26448,24625,27588,29660,14160]
SHOTS=[s for i,s in enumerate(PRIMARY) if i%NSHARD==SHARD]
assert len(PRIMARY)==30 and len(set(PRIMARY))==30
A_FREE=-44.513129165037206; B_FREE=1.1298640950106758
BREAK=3.063183234813295e19; XBREAK=float(np.log(BREAK))
HINGE={'a':-46.69165902985799,'b_low':1.1801355372796194,'b_high':0.269593964785707,'break':BREAK}
MU_G=5.871582432471866e19; SD_G=1.5023544031605223e19
MU_N=952344.2518214888; SD_N=1158166.6796491619
COEF=np.asarray([0.15972140812282293,0.08382833178625544,0.12585836867392203,0.14506538830036136],float)
FREEZE_SHA='64b8c7ccee796e07918faad5cfa5e0b83bb81c940d816a38297e22b9f9ad7ca2'
SELECTION_SEED='SC_FAIR_MAST_P061_FRESH_HELDOUT_M4_V1'
fs=s3fs.S3FileSystem(anon=True,client_kwargs={'endpoint_url':ENDPOINT})

def p059(x):
    return HINGE['a']+HINGE['b_low']*x+(HINGE['b_high']-HINGE['b_low'])*np.maximum(0.0,x-XBREAK)

def gettime(ds):
    if 'time' in ds.coords:return np.asarray(ds.coords['time'].load().values,float).reshape(-1)
    if 'time' in ds:return np.asarray(ds['time'].load().values,float).reshape(-1)
    for c in ds.coords:
        if 'time' in c.lower():return np.asarray(ds.coords[c].load().values,float).reshape(-1)
    raise KeyError('NO_TIME')

def getseries(ds,v):
    if v not in ds:return None,None,'ABSENT_VAR'
    try:t=gettime(ds)
    except Exception as e:return None,None,'NO_TIME:'+type(e).__name__
    a=np.squeeze(np.asarray(ds[v].load().values,float))
    if a.ndim!=1 or len(a)!=len(t):return None,None,f'NON_1D:{list(np.shape(a))}:ntime={len(t)}'
    return t,a,'OK'

def interp(t,v,q):
    m=np.isfinite(t)&np.isfinite(v); t=np.asarray(t,float)[m];v=np.asarray(v,float)[m]
    if len(t)<2:return np.full(len(q),np.nan)
    o=np.argsort(t);t=t[o];v=v[o];t,idx=np.unique(t,return_index=True);v=v[idx]
    z=np.interp(q,t,v,left=np.nan,right=np.nan);z[(q<t[0])|(q>t[-1])]=np.nan
    return z

def orient(var,time):
    a=np.asarray(var.load().values,float); dims=list(var.dims)
    if 'time' in dims:
        a=np.moveaxis(a,dims.index('time'),-1)
    elif a.shape[-1]==len(time):
        pass
    elif a.shape[0]==len(time):
        a=np.moveaxis(a,0,-1)
    else: raise ValueError(f'NO_TIME_AXIS shape={a.shape} ntime={len(time)} dims={dims}')
    return a.reshape((-1,len(time)))

receipts=[]
for sid in SHOTS:
    rec={'shot_id':sid,'split':'FRESH_PRIMARY_P062','freeze_digest_sha256':FREEZE_SHA,'selection_seed':SELECTION_SEED,'refit':False,'retune':False,'unknown_is_zero':False}
    try:
        mp=fs.get_mapper(f'mast/level2/shots/{sid}.zarr')
        th=xr.open_zarr(mp,group='thomson_scattering',consolidated=None)
        td=gettime(th)
        if 'n_e' not in th or 't_e' not in th: raise KeyError('MISSING_THOMSON_NE_OR_TE')
        ne=orient(th['n_e'],td); te=orient(th['t_e'],td)
        if ne.shape!=te.shape: raise ValueError(f'NE_TE_SHAPE_MISMATCH {ne.shape} {te.shape}')
        su=xr.open_zarr(mp,group='summary',consolidated=None)
        tg,vg,sg=getseries(su,'greenwald_density'); tn,vn,sn=getseries(su,'power_nbi')
        if sg!='OK' or sn!='OK': raise ValueError(f'STATE_SERIES_FAIL greenwald={sg} nbi={sn}')
        g=interp(tg,vg,td); nbi=interp(tn,vn,td)
        z1=(g-MU_G)/SD_G; z2=(nbi-MU_N)/SD_N
        X=[];Y=[];T=[];G=[];N=[];TI=[]; time_rows=[]
        for j,t in enumerate(td):
            if not (np.isfinite(z1[j]) and np.isfinite(z2[j])): continue
            m=np.isfinite(ne[:,j])&np.isfinite(te[:,j])&(ne[:,j]>0)&(te[:,j]>0)
            if not np.any(m): continue
            x=np.log(ne[m,j]); y=np.log(te[m,j])
            base=A_FREE+B_FREE*x
            m4=base + COEF[0]*z1[j] + COEF[1]*z2[j] + COEF[2]*z1[j]*(x-XBREAK) + COEF[3]*z2[j]*(x-XBREAK)
            h=p059(x)
            time_rows.append({'shot_id':sid,'time':float(t),'n_pairs':int(len(x)),'greenwald_density':float(g[j]),'power_nbi':float(nbi[j]),'m0_mse':float(np.mean((y-base)**2)),'p059_hinge_mse':float(np.mean((y-h)**2)),'m4_mse':float(np.mean((y-m4)**2)),'fraction_above_break':float(np.mean(np.exp(x)>BREAK))})
            X.append(x);Y.append(y);T.append(np.full(len(x),float(t)));G.append(np.full(len(x),float(g[j])));N.append(np.full(len(x),float(nbi[j])));TI.append(np.full(len(x),j,dtype=np.int32))
        if not X: raise ValueError('NO_PAIRABLE_STATE_GATED_THOMSON_POINTS')
        x=np.concatenate(X);y=np.concatenate(Y);tt=np.concatenate(T);gg=np.concatenate(G);nn=np.concatenate(N);ti=np.concatenate(TI)
        zz1=(gg-MU_G)/SD_G;zz2=(nn-MU_N)/SD_N
        m0=A_FREE+B_FREE*x
        h=p059(x)
        m4=m0+COEF[0]*zz1+COEF[1]*zz2+COEF[2]*zz1*(x-XBREAK)+COEF[3]*zz2*(x-XBREAK)
        mse0=float(np.mean((y-m0)**2)); mseh=float(np.mean((y-h)**2)); msem4=float(np.mean((y-m4)**2))
        np.savez_compressed(OUT/f'SHOT_{sid}_P062_RAW_SCORE_PACKET.npz',x_log_ne=x,y_log_te=y,time_s=tt,time_index=ti,greenwald_density=gg,power_nbi=nn,m0_pred=m0,p059_pred=h,m4_pred=m4)
        pd.DataFrame(time_rows).to_csv(OUT/f'SHOT_{sid}_P062_TIME_METRICS.csv',index=False)
        rec.update({'status':'USABLE','ntime_thomson':int(len(td)),'ntime_state_gated':int(len(time_rows)),'n_pairs':int(len(x)),'m0_mse':mse0,'p059_hinge_mse':mseh,'m4_mse':msem4,'delta_m4_vs_m0':msem4-mse0,'delta_m4_vs_p059':msem4-mseh,'m4_beats_m0':bool(msem4<mse0),'m4_beats_p059':bool(msem4<mseh),'greenwald_coverage_on_thomson':float(np.isfinite(g).mean()),'nbi_coverage_on_thomson':float(np.isfinite(nbi).mean())})
    except Exception as e:
        rec.update({'status':'FAILED','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()})
    receipts.append(rec)
(OUT/f'PRIMARY_RECEIPTS_SHARD_{SHARD}_P062.json').write_text(json.dumps(receipts,indent=2,sort_keys=True)+'\n')
summary={'shard':SHARD,'nshard':NSHARD,'requested_ids':SHOTS,'requested_count':len(SHOTS),'usable_count':sum(r['status']=='USABLE' for r in receipts),'failed_count':sum(r['status']!='USABLE' for r in receipts),'refit':False,'retune':False,'freeze_digest_sha256':FREEZE_SHA,'selection_seed':SELECTION_SEED}
(OUT/f'PRIMARY_SUMMARY_SHARD_{SHARD}_P062.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,sort_keys=True))
