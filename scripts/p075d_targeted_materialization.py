import os,json,traceback
from pathlib import Path
import numpy as np,xarray as xr,s3fs
SHARD=int(os.environ['SHARD']); NS=10
ALL=[26993,17746,20727,12779,24198,18826,29159,16738,17822,14281,27613,17930,22785,17792,30410,25008,27446,21338,27500,23288,16374,25009,12989,30022,15060,15094,30419,21725,26790,24668]
SHOTS=[s for i,s in enumerate(ALL) if i%NS==SHARD]
OUT=Path(f'p075d-material-{SHARD}'); OUT.mkdir(exist_ok=True)
fs=s3fs.S3FileSystem(anon=True,client_kwargs={'endpoint_url':'https://s3.echo.stfc.ac.uk'})
TARGETS={'charge_exchange':['time','major_radius','t_i','v_i'],'equilibrium':['time','whmd','da_rating','ip_rating','beta_pol','beta_tor','q95'],'summary':['time','power_nbi','power_radiated','neutron_rates_total']}
def clean_attrs(a):
 out={}
 for k,v in dict(a).items():
  try: json.dumps(v); out[k]=v
  except: out[k]=str(v)
 return out
rows=[]
for sid in SHOTS:
 rec={'shot_id':sid,'unknown_is_zero':False,'te_loaded':False,'thomson_ne_loaded':False,'groups':{}}
 try:
  mp=fs.get_mapper(f'mast/level2/shots/{sid}.zarr')
  for g,vs in TARGETS.items():
   gr={}
   try: ds=xr.open_zarr(mp,group=g,consolidated=None)
   except Exception as e:
    rec['groups'][g]={'open_status':'FAIL:'+type(e).__name__}; continue
   for v in vs:
    if v in ds:
     da=ds[v]
     ent={'present':True,'dims':list(da.dims),'shape':list(da.shape),'attrs':clean_attrs(da.attrs)}
     try:
      a=np.asarray(da.load().values)
      ent['dtype']=str(a.dtype); ent['finite_count']=int(np.isfinite(a.astype(float)).sum()) if np.issubdtype(a.dtype,np.number) else None
      ent['size']=int(a.size)
      if np.issubdtype(a.dtype,np.number) and a.size and np.isfinite(a.astype(float)).any():
       af=a.astype(float); m=np.isfinite(af); ent['min']=float(np.nanmin(af[m])); ent['max']=float(np.nanmax(af[m]))
       if v in ('t_i','major_radius','whmd') and a.size<=200000:
        np.save(OUT/f'{sid}_{g}_{v}.npy',a)
     except Exception as e: ent['load_status']='FAIL:'+type(e).__name__
     gr[v]=ent
    else: gr[v]={'present':False}
   rec['groups'][g]=gr
  rec['status']='OK'
 except Exception as e:
  rec.update({'status':'FAILED','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()})
 rows.append(rec)
(OUT/f'MATERIALIZATION_RECEIPTS_{SHARD}.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
print(json.dumps({'shard':SHARD,'shots':SHOTS,'ok':sum(r['status']=='OK' for r in rows)}))