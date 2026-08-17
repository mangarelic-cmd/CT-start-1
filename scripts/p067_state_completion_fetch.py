import os,json,traceback
from pathlib import Path
import numpy as np,pandas as pd,xarray as xr,s3fs
SHARD=int(os.environ['SHARD']); NSHARD=10; OUT=Path(f'p067-state-{SHARD}'); OUT.mkdir(exist_ok=True)
ENDPOINT='https://s3.echo.stfc.ac.uk'
SHOTS=[27411,21333,24432,24136,29420,27042,20013,23626,22399,21971,15052,14624,29369,15570,24126,15133,27935,13479,20918,16139,22213,12010,14373,13905,20505,14612,24430,30468,21707,20479]
SHARD_SHOTS=[s for i,s in enumerate(SHOTS) if i%NSHARD==SHARD]
CHANNELS={
 'summary':['ip','line_average_n_e','power_nbi','power_radiated','greenwald_density','neutron_rates_total'],
 'equilibrium':['q95','whmd','li','beta_normal','beta_pol','beta_tor','q_axis','elongation','triangularity_lower','triangularity_upper','major_radius','minor_radius','vloop_dynamic','vloop_static'],
 'magnetics':['ip'],
 'gas_injection':['inboard_total','outboard_total','pressure','total_injected'],
 'spectrometer_visible':['density_gradient','filter_spectrometer_dalpha_voltage','filter_spectrometer_bes_voltage']
}
fs=s3fs.S3FileSystem(anon=True,client_kwargs={'endpoint_url':ENDPOINT})
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
    m=np.isfinite(t)&np.isfinite(v);t=np.asarray(t)[m];v=np.asarray(v)[m]
    if len(t)<2:return np.full(len(q),np.nan)
    o=np.argsort(t);t=t[o];v=v[o];t,idx=np.unique(t,return_index=True);v=v[idx]
    z=np.interp(q,t,v,left=np.nan,right=np.nan);z[(q<t[0])|(q>t[-1])]=np.nan;return z
rows=[];receipts=[]
for sid in SHARD_SHOTS:
    key=f'mast/level2/shots/{sid}.zarr';rec={'shot_id':sid,'te_loaded':False,'ne_loaded':False,'unknown_is_zero':False}
    try:
        mp=fs.get_mapper(key);th=xr.open_zarr(mp,group='thomson_scattering',consolidated=None)
        td=np.asarray(th.coords['time'].load().values,float).reshape(-1)
        b=pd.DataFrame({'shot_id':sid,'time':td});cov={}
        for g,vs in CHANNELS.items():
            try:ds=xr.open_zarr(mp,group=g,consolidated=None)
            except Exception as e:
                for v in vs:b[f'{g}.{v}']=np.nan;cov[f'{g}.{v}']={'status':'GROUP_OPEN_FAIL:'+type(e).__name__,'coverage':0.0}
                continue
            for v in vs:
                ts,xs,st=getseries(ds,v);c=f'{g}.{v}'
                if st!='OK':b[c]=np.nan;cov[c]={'status':st,'coverage':0.0};continue
                vals=interp(ts,xs,td);b[c]=vals;cov[c]={'status':'OK','coverage':float(np.isfinite(vals).mean()),'source_points':int(len(ts))}
        pn=b['summary.power_nbi'].to_numpy(float);pr=b['summary.power_radiated'].to_numpy(float)
        b['derived.net_power']=np.where(np.isfinite(pn)&np.isfinite(pr),pn-pr,np.nan)
        b['derived.rad_fraction']=np.where(np.isfinite(pn)&np.isfinite(pr),np.maximum(pr,0)/(np.maximum(pr,0)+np.maximum(pn,0)+1.0),np.nan)
        rows.append(b);rec.update({'status':'OK','thomson_times':int(len(td)),'coverage':cov,'te_variable_present_but_not_loaded':bool('t_e' in th),'ne_variable_present_but_not_loaded':bool('n_e' in th)})
    except Exception as e:rec.update({'status':'FAILED','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()})
    receipts.append(rec)
df=pd.concat(rows,ignore_index=True) if rows else pd.DataFrame();df.to_csv(OUT/f'P067_STATE_SHARD_{SHARD}.csv',index=False)
summary={'schema':'P067_PRETE_STATE_COMPLETION_V1','shard':SHARD,'nshard':NSHARD,'requested_ids':SHARD_SHOTS,'successful_shots':sum(r.get('status')=='OK' for r in receipts),'failed_shots':sum(r.get('status')!='OK' for r in receipts),'rows':int(len(df)),'te_loaded_anywhere':False,'ne_loaded_anywhere':False,'unknown_is_zero':False}
(OUT/f'RECEIPTS_P067_{SHARD}.json').write_text(json.dumps(receipts,indent=2,sort_keys=True)+'\n');(OUT/f'SUMMARY_P067_{SHARD}.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary))
