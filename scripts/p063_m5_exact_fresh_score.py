import os,json,traceback
from pathlib import Path
import numpy as np,pandas as pd,xarray as xr,s3fs
SHARD=int(os.environ['SHARD']);NS=10
PRIMARY=[12697,20498,15081,24194,21801,18369,24905,23889,18762,14209,22402,23742,28259,24726,30145,18886,23784,24145,15617,16987,15618,17093,12747,29199,24088,23445,29143,24344,16443,29702]
SHOTS=[s for i,s in enumerate(PRIMARY) if i%NS==SHARD]
OUT=Path(f'p063-primary-{SHARD}');OUT.mkdir(exist_ok=True)
fs=s3fs.S3FileSystem(anon=True,client_kwargs={'endpoint_url':'https://s3.echo.stfc.ac.uk'})
# Frozen comparators
A0=-44.513129165037206;B0=1.1298640950106758
BREAK=3.063183234813295e19;XB=float(np.log(BREAK));AH=-46.69165902985799;BL=1.1801355372796194;BH=0.269593964785707
MU_G=5.871582432471866e19;SD_G=1.5023544031605223e19;MU_N4=952344.2518214888;SD_N4=1158166.6796491619;C4=np.array([0.15972140812282293,0.08382833178625544,0.12585836867392203,0.14506538830036136])
# Frozen exact M5
A5=-44.07528851419499; MU_N5=1198323.3541824967; SD_N5=1182370.4221535327; L=np.log(1e19)
def h059(x):return AH+BL*x+(BH-BL)*np.maximum(0,x-XB)
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
 z=np.interp(q,t,v,left=np.nan,right=np.nan);z[(q<t[0])|(q>t[-1])]=np.nan;return z
def orient(var,t):
 a=np.asarray(var.load().values,float);d=list(var.dims)
 if 'time' in d:a=np.moveaxis(a,d.index('time'),-1)
 elif a.shape[-1]==len(t):pass
 elif a.shape[0]==len(t):a=np.moveaxis(a,0,-1)
 else:raise ValueError('NO_TIME_AXIS')
 return a.reshape((-1,len(t)))
receipts=[]
for sid in SHOTS:
 r={'shot_id':sid,'split':'P063_FRESH_PRIMARY','refit':False,'retune':False}
 try:
  mp=fs.get_mapper(f'mast/level2/shots/{sid}.zarr');th=xr.open_zarr(mp,group='thomson_scattering',consolidated=None);td=gettime(th);ne=orient(th['n_e'],td);te=orient(th['t_e'],td)
  su=xr.open_zarr(mp,group='summary',consolidated=None);tg,vg=series(su,'greenwald_density');tn,vn=series(su,'power_nbi')
  if tg is None or tn is None:raise ValueError('STATE_SERIES_FAIL')
  g=interp(tg,vg,td);nbi=interp(tn,vn,td); X=[];Y=[];G=[];N=[];T=[]
  for j,t in enumerate(td):
   if not(np.isfinite(g[j]) and g[j]>0 and np.isfinite(nbi[j])):continue
   m=np.isfinite(ne[:,j])&np.isfinite(te[:,j])&(ne[:,j]>0)&(te[:,j]>0)
   if m.any():X.append(np.log(ne[m,j]));Y.append(np.log(te[m,j]));G.append(np.full(m.sum(),g[j]));N.append(np.full(m.sum(),nbi[j]));T.append(np.full(m.sum(),t))
  if not X:raise ValueError('NO_PAIRABLE_STATE_GATED_THOMSON_POINTS')
  x=np.concatenate(X);y=np.concatenate(Y);gg=np.concatenate(G);nn=np.concatenate(N);tt=np.concatenate(T)
  m0=A0+B0*x;p59=h059(x)
  zg=(gg-MU_G)/SD_G;zn4=(nn-MU_N4)/SD_N4;xa=x-XB;m4=m0+C4[0]*zg+C4[1]*zn4+C4[2]*zg*xa+C4[3]*zn4*xa
  zn5=(nn-MU_N5)/SD_N5;u=(x-L)-(4/3)*(np.log(gg)-L)-(1/5)*zn5+4/3;H=np.logaddexp(0,7*u)/7;m5=A5+(9/8)*(x-H)
  ms=[float(np.mean((y-p)**2)) for p in [m0,p59,m4,m5]]
  np.savez_compressed(OUT/f'SHOT_{sid}_P063_RAW_SCORE_PACKET.npz',x_log_ne=x,y_log_te=y,time_s=tt,greenwald_density=gg,power_nbi=nn,m0_pred=m0,p059_pred=p59,m4_pred=m4,m5_pred=m5,u_sat=u,H_sat=H)
  r.update({'status':'USABLE','n_pairs':len(x),'m0_mse':ms[0],'p059_mse':ms[1],'m4_mse':ms[2],'m5_mse':ms[3],'best_old_mse':min(ms[:3]),'delta_m5_vs_best_old':ms[3]-min(ms[:3]),'m5_beats_best_old':ms[3]<min(ms[:3])})
 except Exception as e:r.update({'status':'FAILED','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()})
 receipts.append(r)
(OUT/f'RECEIPTS_{SHARD}.json').write_text(json.dumps(receipts,indent=2,sort_keys=True)+'\n')
(OUT/f'SUMMARY_{SHARD}.json').write_text(json.dumps({'shard':SHARD,'shots':SHOTS,'usable':sum(x['status']=='USABLE' for x in receipts),'failed':sum(x['status']!='USABLE' for x in receipts)},indent=2,sort_keys=True)+'\n')
