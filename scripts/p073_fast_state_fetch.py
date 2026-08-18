import os,json,traceback
from pathlib import Path
import numpy as np,pandas as pd,xarray as xr,s3fs
SHARD=int(os.environ['SHARD']);NS=10;OUT=Path(f'p073-fast-{SHARD}');OUT.mkdir(exist_ok=True)
ALL=[26993,27613,16374,17746,17930,25009,20727,22785,12989,12779,17792,30022,24198,30410,15060,18826,25008,15094,29159,27446,30419,16738,21338,21725,17822,27500,26790,14281,23288,24668];SHOTS=[s for i,s in enumerate(ALL) if i%NS==SHARD]
CH={'summary':['ip','line_average_n_e','power_nbi','power_radiated','greenwald_density','neutron_rates_total'],'equilibrium':['q95','li','q_axis','beta_pol','beta_tor','elongation','minor_radius','triangularity_lower','triangularity_upper','vloop_dynamic','vloop_static'],'magnetics':['ip'],'gas_injection':['inboard_total','outboard_total','pressure','total_injected'],'spectrometer_visible':['density_gradient']}
fs=s3fs.S3FileSystem(anon=True,client_kwargs={'endpoint_url':'https://s3.echo.stfc.ac.uk'})
def gt(ds):
 if 'time' in ds.coords:return np.asarray(ds.coords['time'].load().values,float).reshape(-1)
 if 'time' in ds:return np.asarray(ds['time'].load().values,float).reshape(-1)
 for c in ds.coords:
  if 'time' in c.lower():return np.asarray(ds.coords[c].load().values,float).reshape(-1)
 raise KeyError('NO_TIME')
def gs(ds,v):
 if v not in ds:return None,None,'ABSENT_VAR'
 try:t=gt(ds);a=np.squeeze(np.asarray(ds[v].load().values,float))
 except Exception as e:return None,None,'LOAD_FAIL:'+type(e).__name__
 if a.ndim!=1 or len(a)!=len(t):return None,None,f'NON_1D:{list(np.shape(a))}'
 return t,a,'OK'
def interp(t,v,q):
 m=np.isfinite(t)&np.isfinite(v);t=np.asarray(t)[m];v=np.asarray(v)[m]
 if len(t)<2:return np.full(len(q),np.nan)
 o=np.argsort(t);t=t[o];v=v[o];t,ix=np.unique(t,return_index=True);v=v[ix];z=np.interp(q,t,v,left=np.nan,right=np.nan);z[(q<t[0])|(q>t[-1])]=np.nan;return z
rows=[];recs=[]
for sid in SHOTS:
 r={'shot_id':sid,'te_loaded':False,'ne_loaded':False,'unknown_is_zero':False}
 try:
  mp=fs.get_mapper(f'mast/level2/shots/{sid}.zarr');th=xr.open_zarr(mp,group='thomson_scattering',consolidated=None);td=gt(th);b=pd.DataFrame({'shot_id':sid,'time':td});cov={}
  for g,vs in CH.items():
   try:ds=xr.open_zarr(mp,group=g,consolidated=None)
   except Exception as e:
    for v in vs:b[f'{g}.{v}']=np.nan;cov[f'{g}.{v}']='GROUP_OPEN_FAIL:'+type(e).__name__
    continue
   for v in vs:
    t,x,st=gs(ds,v);c=f'{g}.{v}'
    if st!='OK':b[c]=np.nan;cov[c]=st;continue
    b[c]=interp(t,x,td);cov[c]='OK'
  rows.append(b);r.update({'status':'OK','rows':len(b),'coverage':cov})
 except Exception as e:r.update({'status':'FAILED','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()})
 recs.append(r)
df=pd.concat(rows,ignore_index=True,sort=False) if rows else pd.DataFrame();df.to_csv(OUT/f'P073_FAST_STATE_SHARD_{SHARD}.csv',index=False);(OUT/f'RECEIPTS_P073_FAST_{SHARD}.json').write_text(json.dumps(recs,indent=2,sort_keys=True)+'\n');print(json.dumps({'shard':SHARD,'ok':sum(r.get('status')=='OK' for r in recs),'failed':sum(r.get('status')!='OK' for r in recs),'te_loaded':False,'ne_loaded':False}))
