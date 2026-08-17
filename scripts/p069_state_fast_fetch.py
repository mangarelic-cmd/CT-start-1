import os,json,traceback
from pathlib import Path
import numpy as np,pandas as pd,xarray as xr,s3fs
SHARD=int(os.environ['SHARD']); NS=10; OUT=Path(f'p069-fast-{SHARD}'); OUT.mkdir(exist_ok=True)
ALL=[30257,27830,17978,17967,22316,13879,12489,16382,18890,18900,20610,15621,23736,23888,22492,12083,16727,24594,29942,13423,17887,15272,24751,28021,30090,20306,28206,16445,16260,20320]; SHOTS=[s for i,s in enumerate(ALL) if i%NS==SHARD]
CH={'summary':['ip','line_average_n_e','power_nbi','power_radiated','greenwald_density','neutron_rates_total'],'equilibrium':['q95','li','q_axis','beta_pol','beta_tor','elongation','minor_radius','triangularity_lower','triangularity_upper','vloop_dynamic','vloop_static'],'magnetics':['ip']}
fs=s3fs.S3FileSystem(anon=True,client_kwargs={'endpoint_url':'https://s3.echo.stfc.ac.uk'})
def gt(ds):
 if 'time' in ds.coords:return np.asarray(ds.coords['time'].load().values,float).reshape(-1)
 if 'time' in ds:return np.asarray(ds['time'].load().values,float).reshape(-1)
 for c in ds.coords:
  if 'time' in c.lower():return np.asarray(ds.coords[c].load().values,float).reshape(-1)
 raise KeyError('NO_TIME')
def gs(ds,v):
 if v not in ds:return None,None,'ABSENT_VAR'
 try:t=gt(ds)
 except Exception as e:return None,None,'NO_TIME:'+type(e).__name__
 a=np.squeeze(np.asarray(ds[v].load().values,float))
 if a.ndim!=1 or len(a)!=len(t):return None,None,f'NON_1D:{list(np.shape(a))}'
 return t,a,'OK'
def ip(t,v,q):
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
    for v in vs:b[f'{g}.{v}']=np.nan;cov[f'{g}.{v}']={'status':'GROUP_OPEN_FAIL:'+type(e).__name__,'coverage':0.0}
    continue
   for v in vs:
    t,x,st=gs(ds,v);c=f'{g}.{v}'
    if st!='OK':b[c]=np.nan;cov[c]={'status':st,'coverage':0.0};continue
    z=ip(t,x,td);b[c]=z;cov[c]={'status':'OK','coverage':float(np.isfinite(z).mean())}
  a=b['summary.line_average_n_e'].to_numpy(float);g=b['summary.greenwald_density'].to_numpy(float);b['derived.f_greenwald']=np.where(np.isfinite(a)&np.isfinite(g)&(g!=0),a/g,np.nan)
  pn=b['summary.power_nbi'].to_numpy(float);pr=b['summary.power_radiated'].to_numpy(float);b['derived.rad_fraction']=np.where(np.isfinite(pn)&np.isfinite(pr),np.maximum(pr,0)/(np.maximum(pr,0)+np.maximum(pn,0)+1),np.nan);b['derived.net_power_mw']=np.where(np.isfinite(pn)&np.isfinite(pr),(pn-pr)/1e6,np.nan)
  rows.append(b);r.update({'status':'OK','rows':int(len(b)),'coverage':cov})
 except Exception as e:r.update({'status':'FAILED','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()})
 recs.append(r)
df=pd.concat(rows,ignore_index=True) if rows else pd.DataFrame();df.to_csv(OUT/f'P069_FAST_STATE_{SHARD}.csv',index=False);(OUT/f'RECEIPTS_P069_FAST_{SHARD}.json').write_text(json.dumps(recs,indent=2,sort_keys=True)+'\n');print(json.dumps({'shard':SHARD,'shots':SHOTS,'ok':sum(r['status']=='OK' for r in recs),'failed':sum(r['status']!='OK' for r in recs),'te_loaded':False,'ne_loaded':False}))