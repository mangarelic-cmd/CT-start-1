import os,json,traceback,math
from pathlib import Path
import numpy as np,pandas as pd,xarray as xr,s3fs
SHARD=int(os.environ.get('SHARD','0'));NS=int(os.environ.get('NS','10'))
PRIMARY=[17925,30311,14356,29074,22476,17658,12534,14015,12435,14201,22734,24347,21781,20438,23789,12519,12231,18511,13357,29101,14510,27653,27891,13994,27149,12250,30272,15687,17190,14179]
SHOTS=[s for i,s in enumerate(PRIMARY) if i%NS==SHARD]
OUT=Path(os.environ.get('OUT',f'p065-primary-{SHARD}'));OUT.mkdir(exist_ok=True)
MU=1198323.3541824967;SD=1182370.4221535327;L=np.log(1e19);A5=-44.07528851419499;A6=-44.10460779411159;THR=1-math.sqrt(2)
fs=s3fs.S3FileSystem(anon=True,client_kwargs={'endpoint_url':'https://s3.echo.stfc.ac.uk'})
def gt(ds):
 if 'time' in ds.coords:return np.asarray(ds.coords['time'].load().values,float).reshape(-1)
 if 'time' in ds:return np.asarray(ds['time'].load().values,float).reshape(-1)
 for c in ds.coords:
  if 'time' in c.lower():return np.asarray(ds.coords[c].load().values,float).reshape(-1)
 raise KeyError('NO_TIME')
def ori(v,t):
 a=np.asarray(v.load().values,float);d=list(v.dims)
 if 'time' in d:a=np.moveaxis(a,d.index('time'),-1)
 elif a.shape[-1]==len(t):pass
 elif a.shape[0]==len(t):a=np.moveaxis(a,0,-1)
 else:raise ValueError('NO_TIME_AXIS')
 return a.reshape((-1,len(t)))
def ser(ds,v):
 t=gt(ds);a=np.squeeze(np.asarray(ds[v].load().values,float))
 if a.ndim!=1 or len(a)!=len(t):raise ValueError('BAD_'+v)
 return t,a
def ip(t,v,q):
 m=np.isfinite(t)&np.isfinite(v);t=t[m];v=v[m]
 if len(t)<2:return np.full(len(q),np.nan)
 o=np.argsort(t);t=t[o];v=v[o];t,ix=np.unique(t,return_index=True);v=v[ix];z=np.interp(q,t,v,left=np.nan,right=np.nan);z[(q<t[0])|(q>t[-1])]=np.nan;return z
receipts=[]
for sid in SHOTS:
 r={'shot_id':sid,'split':'P065_FRESH_PRIMARY','model_id':'M7_EXACT_PRETE_SHOT_REGIME_GATE','threshold':THR,'refit':False,'retune':False,'te_loaded_before_decision':False}
 try:
  mp=fs.get_mapper(f'mast/level2/shots/{sid}.zarr');th=xr.open_zarr(mp,group='thomson_scattering',consolidated=None);tt=gt(th);ne=ori(th['n_e'],tt)
  su=xr.open_zarr(mp,group='summary',consolidated=None);tg,vg=ser(su,'greenwald_density');tn,vn=ser(su,'power_nbi');gw=ip(tg,vg,tt);nb=ip(tn,vn,tt)
  ub=[];gate_by_time=np.full(len(tt),np.nan)
  for j in range(len(tt)):
   if not(np.isfinite(gw[j]) and gw[j]>0 and np.isfinite(nb[j])):continue
   m=np.isfinite(ne[:,j])&(ne[:,j]>0)
   if not m.any():continue
   x=np.log(ne[m,j]);u=(x-L)-(4/3)*(np.log(gw[j])-L)-(1/5)*((nb[j]-MU)/SD)+4/3;u0=float(np.median(u));ub.append(u0);gate_by_time[j]=1/(1+np.exp(-np.clip(7*u0,-60,60)))
  if not ub:raise ValueError('NO_PRETE_STATE_POINTS')
  u_time_mean=float(np.mean(ub));use_m6=bool(u_time_mean>THR);decision='M6' if use_m6 else 'M5'
  # Target is loaded only after the frozen pre-Te decision above.
  te=ori(th['t_e'],tt);r['te_loaded_before_decision']=False;r['decision']=decision;r['u_time_mean']=u_time_mean
  X=[];Y=[];G=[];N=[];T=[];GA=[]
  for j,t in enumerate(tt):
   if not(np.isfinite(gw[j]) and gw[j]>0 and np.isfinite(nb[j]) and np.isfinite(gate_by_time[j])):continue
   m=np.isfinite(ne[:,j])&np.isfinite(te[:,j])&(ne[:,j]>0)&(te[:,j]>0)
   if not m.any():continue
   X.append(np.log(ne[m,j]));Y.append(np.log(te[m,j]));G.append(np.full(m.sum(),gw[j]));N.append(np.full(m.sum(),nb[j]));T.append(np.full(m.sum(),t));GA.append(np.full(m.sum(),gate_by_time[j]))
  if not X:raise ValueError('NO_PAIRABLE_STATE_GATED_THOMSON_POINTS')
  x=np.concatenate(X);y=np.concatenate(Y);gg=np.concatenate(G);nn=np.concatenate(N);t=np.concatenate(T);ga=np.concatenate(GA)
  u=(x-L)-(4/3)*(np.log(gg)-L)-(1/5)*((nn-MU)/SD)+4/3;H=np.logaddexp(0,7*u)/7;m5=A5+(9/8)*(x-H);m6=A6+(9/8)*(x-ga*H);m7=m6 if use_m6 else m5
  e5=float(np.mean((y-m5)**2));e6=float(np.mean((y-m6)**2));e7=float(np.mean((y-m7)**2))
  np.savez_compressed(OUT/f'SHOT_{sid}_P065_RAW_SCORE_PACKET.npz',x_log_ne=x,y_log_te=y,time_s=t,greenwald_density=gg,power_nbi=nn,u_sat=u,H_sat=H,activation_gate=ga,m5_pred=m5,m6_pred=m6,m7_pred=m7,u_time_mean=np.array([u_time_mean]),threshold=np.array([THR]),decision_m6=np.array([use_m6]))
  r.update({'status':'USABLE','n_pairs':len(x),'m5_mse':e5,'m6_mse':e6,'m7_mse':e7,'best_old_mse':min(e5,e6),'m7_vs_m5':e7-e5,'m7_vs_m6':e7-e6,'selected_model':decision})
 except Exception as e:r.update({'status':'FAILED','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()})
 receipts.append(r)
(OUT/f'RECEIPTS_{SHARD}.json').write_text(json.dumps(receipts,indent=2,sort_keys=True)+'\n');(OUT/f'SUMMARY_{SHARD}.json').write_text(json.dumps({'shard':SHARD,'shots':SHOTS,'usable':sum(r['status']=='USABLE' for r in receipts),'failed':sum(r['status']!='USABLE' for r in receipts),'refit':False,'retune':False,'target_loaded_after_decision_only':True},indent=2,sort_keys=True)+'\n')
