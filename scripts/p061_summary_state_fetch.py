import os,json,traceback
from pathlib import Path
import numpy as np,pandas as pd,xarray as xr,s3fs
SHARD=int(os.environ['SHARD']); NSHARD=16; OUT=Path(f'p061-summary-{SHARD}'); OUT.mkdir(exist_ok=True)
ENDPOINT='https://s3.echo.stfc.ac.uk'
CAL=[13038,16195,17664,20880,22308,24143,25365]
N100=[12088,12202,12228,12474,12901,12931,12964,13093,13108,13274,13430,13557,13583,13644,13742,13766,14017,14520,14583,15113,15153,15279,15507,15703,15898,15993,16036,16151,16731,16828,16862,17712,17768,17901,17964,17999,18328,18496,18531,20428,20465,20495,20514,20570,20651,20862,21344,21517,21771,21785,21797,22162,22215,22287,22300,22309,22382,22430,22526,23143,23485,23489,23598,23667,24004,24474,24514,24528,24665,24717,25696,25697,26004,26163,26463,26651,26867,26953,27050,27125,27169,27198,27401,27450,27601,27640,27740,27822,28178,28267,28811,28816,28860,28997,29047,29077,29229,29440,29488,30048]
ALL=CAL+N100; assert len(set(ALL))==107
SHOTS=[s for i,s in enumerate(ALL) if i%NSHARD==SHARD]
VARS=['ip','line_average_n_e','power_nbi','power_radiated','greenwald_density']
fs=s3fs.S3FileSystem(anon=True,client_kwargs={'endpoint_url':ENDPOINT})
def gettime(ds):
    if 'time' in ds.coords:return np.asarray(ds.coords['time'].load().values,float).reshape(-1)
    if 'time' in ds:return np.asarray(ds['time'].load().values,float).reshape(-1)
    for c in ds.coords:
        if 'time' in c.lower():return np.asarray(ds.coords[c].load().values,float).reshape(-1)
    raise KeyError('NO_TIME')
def interp(t,v,q):
    m=np.isfinite(t)&np.isfinite(v);t=np.asarray(t)[m];v=np.asarray(v)[m]
    if len(t)<2:return np.full(len(q),np.nan)
    o=np.argsort(t);t=t[o];v=v[o];t,idx=np.unique(t,return_index=True);v=v[idx]
    z=np.interp(q,t,v,left=np.nan,right=np.nan);z[(q<t[0])|(q>t[-1])]=np.nan;return z
rows=[];receipts=[]
for sid in SHOTS:
    split='CAL7' if sid in CAL else 'N100';key=f'mast/level2/shots/{sid}.zarr';rec={'shot_id':sid,'split':split,'te_loaded':False,'ne_loaded':False,'unknown_is_zero':False}
    try:
        mp=fs.get_mapper(key);th=xr.open_zarr(mp,group='thomson_scattering',consolidated=None);td=np.asarray(th.coords['time'].load().values,float).reshape(-1)
        ds=xr.open_zarr(mp,group='summary',consolidated=None);st=gettime(ds);b=pd.DataFrame({'shot_id':sid,'split':split,'time':td});cov={}
        for v in VARS:
            c='summary.'+v
            if v not in ds:b[c]=np.nan;cov[c]={'status':'ABSENT_VAR','coverage':0.0};continue
            a=np.squeeze(np.asarray(ds[v].load().values,float))
            if a.ndim!=1 or len(a)!=len(st):b[c]=np.nan;cov[c]={'status':'NON_1D','coverage':0.0};continue
            z=interp(st,a,td);b[c]=z;cov[c]={'status':'OK','coverage':float(np.isfinite(z).mean()),'source_points':int(len(st))}
        den=b['summary.line_average_n_e'].to_numpy(float);gw=b['summary.greenwald_density'].to_numpy(float);b['derived.f_greenwald']=np.where(np.isfinite(den)&np.isfinite(gw)&(gw!=0),den/gw,np.nan)
        pn=b['summary.power_nbi'].to_numpy(float);pr=b['summary.power_radiated'].to_numpy(float);b['derived.p_nbi_minus_prad']=np.where(np.isfinite(pn)&np.isfinite(pr),pn-pr,np.nan)
        rows.append(b);rec.update({'status':'OK','thomson_times':int(len(td)),'coverage':cov,'te_variable_present_but_not_loaded':bool('t_e' in th),'ne_variable_present_but_not_loaded':bool('n_e' in th)})
    except Exception as e:rec.update({'status':'FAILED','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()})
    receipts.append(rec)
df=pd.concat(rows,ignore_index=True) if rows else pd.DataFrame();df.to_csv(OUT/f'TRAINING_STATE_SHARD_{SHARD}_P061.csv',index=False)
s={'authority_candidate':'P061_SUMMARY16','shard':SHARD,'nshard':NSHARD,'requested_shots':len(SHOTS),'requested_ids':SHOTS,'successful_shots':sum(r['status']=='OK' for r in receipts),'failed_shots':sum(r['status']!='OK' for r in receipts),'rows':int(len(df)),'te_loaded_anywhere':False,'ne_loaded_anywhere':False,'unknown_is_zero':False,'open_providers':['equilibrium','magnetics','pulse_schedule']}
(OUT/f'STATE_RECEIPTS_SHARD_{SHARD}_P061.json').write_text(json.dumps(receipts,indent=2,sort_keys=True)+'\n');(OUT/f'STATE_SUMMARY_SHARD_{SHARD}_P061.json').write_text(json.dumps(s,indent=2,sort_keys=True)+'\n');print(json.dumps(s))