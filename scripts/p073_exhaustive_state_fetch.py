import os,json,traceback
from pathlib import Path
import numpy as np,pandas as pd,xarray as xr,s3fs

SHARD=int(os.environ['SHARD']); NS=10
OUT=Path(f'p073-state-{SHARD}'); OUT.mkdir(exist_ok=True)
ALL=[26993,27613,16374,17746,17930,25009,20727,22785,12989,12779,17792,30022,24198,30410,15060,18826,25008,15094,29159,27446,30419,16738,21338,21725,17822,27500,26790,14281,23288,24668]
SHOTS=[s for i,s in enumerate(ALL) if i%NS==SHARD]
META_URL='https://raw.githubusercontent.com/UKAEA-IBM-STFC-Fusion-FMs/tokamark/1a200f4588addaad2ae3d53d438d9e1946c09294/src/MAST_tools/metadata/signal_availability.csv'
FORBIDDEN_GROUPS={'thomson_scattering'}
FORBIDDEN_EXACT={'thomson_scattering-n_e','thomson_scattering-t_e'}
fs=s3fs.S3FileSystem(anon=True,client_kwargs={'endpoint_url':'https://s3.echo.stfc.ac.uk'})
meta=pd.read_csv(META_URL)

def trueish(v):
    if isinstance(v,(bool,np.bool_)): return bool(v)
    return str(v).strip().upper()=='TRUE'

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
    try:a=np.squeeze(np.asarray(ds[v].load().values,float))
    except Exception as e:return None,None,'LOAD_FAIL:'+type(e).__name__
    if a.ndim!=1 or len(a)!=len(t):return None,None,f'NON_1D:{list(np.shape(a))}'
    return t,a,'OK'

def interp(t,v,q):
    m=np.isfinite(t)&np.isfinite(v); t=np.asarray(t)[m];v=np.asarray(v)[m]
    if len(t)<2:return np.full(len(q),np.nan)
    o=np.argsort(t);t=t[o];v=v[o];t,ix=np.unique(t,return_index=True);v=v[ix]
    z=np.interp(q,t,v,left=np.nan,right=np.nan);z[(q<t[0])|(q>t[-1])]=np.nan
    return z

rows=[];recs=[];inventory={}
for sid in SHOTS:
    rec={'shot_id':sid,'te_loaded':False,'ne_loaded':False,'thomson_values_loaded':False,'unknown_is_zero':False,'metadata_commit':'1a200f4588addaad2ae3d53d438d9e1946c09294'}
    try:
        mr=meta.loc[meta['shot_id'].astype(int)==sid]
        if len(mr)!=1: raise ValueError(f'METADATA_ROW_COUNT={len(mr)}')
        mr=mr.iloc[0]
        available=[]
        for c in meta.columns:
            if c=='shot_id' or '-' not in c: continue
            if c in FORBIDDEN_EXACT: continue
            g,v=c.split('-',1)
            if g in FORBIDDEN_GROUPS: continue
            if trueish(mr[c]): available.append((g,v,c))
        mp=fs.get_mapper(f'mast/level2/shots/{sid}.zarr')
        th=xr.open_zarr(mp,group='thomson_scattering',consolidated=None)
        td=gt(th)  # clock only; no Thomson data_var is loaded.
        b=pd.DataFrame({'shot_id':sid,'time':td})
        cov={}; opened={}
        bygroup={}
        for g,v,c in available: bygroup.setdefault(g,[]).append((v,c))
        for g,items in sorted(bygroup.items()):
            try:
                ds=xr.open_zarr(mp,group=g,consolidated=None); opened[g]=ds
            except Exception as e:
                for v,c in items: cov[c]={'status':'GROUP_OPEN_FAIL:'+type(e).__name__,'coverage':0.0}; b[g+'.'+v]=np.nan
                continue
            for v,c in items:
                t,x,st=gs(ds,v); name=g+'.'+v
                if st!='OK': b[name]=np.nan; cov[c]={'status':st,'coverage':0.0}; continue
                z=interp(t,x,td); b[name]=z; cov[c]={'status':'OK','coverage':float(np.isfinite(z).mean())}
        rows.append(b)
        ok=[k for k,v in cov.items() if v['status']=='OK']
        rec.update({'status':'OK','rows':int(len(b)),'metadata_available_non_thomson':len(available),'one_d_ok':len(ok),'coverage':cov})
        inventory[str(sid)]={'metadata_available':[c for _,_,c in available],'one_d_ok':ok}
    except Exception as e:
        rec.update({'status':'FAILED','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()})
    recs.append(rec)

df=pd.concat(rows,ignore_index=True,sort=False) if rows else pd.DataFrame()
df.to_csv(OUT/f'P073_EXHAUSTIVE_STATE_SHARD_{SHARD}.csv',index=False)
(OUT/f'RECEIPTS_P073_STATE_{SHARD}.json').write_text(json.dumps(recs,indent=2,sort_keys=True)+'\n')
(OUT/f'INVENTORY_P073_STATE_{SHARD}.json').write_text(json.dumps(inventory,indent=2,sort_keys=True)+'\n')
print(json.dumps({'shard':SHARD,'shots':SHOTS,'ok':sum(r.get('status')=='OK' for r in recs),'failed':sum(r.get('status')!='OK' for r in recs),'te_loaded':False,'ne_loaded':False,'thomson_values_loaded':False}))
