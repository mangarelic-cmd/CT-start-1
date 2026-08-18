import os,json,traceback,re
from pathlib import Path
import s3fs,zarr
SHARD=int(os.environ['SHARD']); NS=10; OUT=Path(f'p075e-catalog-{SHARD}'); OUT.mkdir(exist_ok=True)
ALL=[26993,17746,20727,12779,24198,18826,29159,16738,17822,14281,27613,17930,22785,17792,30410,25008,27446,21338,27500,23288,16374,25009,12989,30022,15060,15094,30419,21725,26790,24668]
SHOTS=[s for i,s in enumerate(ALL) if i%NS==SHARD]
fs=s3fs.S3FileSystem(anon=True,client_kwargs={'endpoint_url':'https://s3.echo.stfc.ac.uk'})
KWS=['neutron','fusion','isotope','deuter','trit','fuel','species','branch','calib','efficien','geometry','solid_angle','charge_exchange','t_i','ion_temperature','temperature','whmd','stored','thermal','energy','confin','tau','transport','loss','disrupt','mhd','stabil','actuator','control','wall','divert','heat','particle','material','limit','bolom','radiat','power','nbi','alpha','fast_ion']
def keep(s):
 s=s.lower(); return any(k in s for k in KWS)
def safe(x):
 try:
  if isinstance(x,(str,int,float,bool)) or x is None:return x
  if hasattr(x,'tolist'): return x.tolist()
  return str(x)
 except:return '<UNSERIALIZABLE>'
recs=[]
for sid in SHOTS:
 rec={'shot_id':sid,'status':'OPEN','matches':[],'group_count':0,'array_count':0,'unknown_is_zero':False,'data_values_loaded':False}
 try:
  mapper=fs.get_mapper(f'mast/level2/shots/{sid}.zarr')
  root=zarr.open_group(store=mapper,mode='r')
  def walk(g,path=''):
   rec['group_count']+=1
   try:gattrs={k:safe(v) for k,v in dict(g.attrs).items()}
   except:gattrs={}
   if keep(path+' '+json.dumps(gattrs,sort_keys=True)):
    rec['matches'].append({'kind':'group','path':path or '/','attrs':gattrs})
   for name in g.array_keys():
    rec['array_count']+=1
    try:
     a=g[name]; attrs={k:safe(v) for k,v in dict(a.attrs).items()}; shape=list(a.shape); dtype=str(a.dtype); chunks=safe(a.chunks)
    except Exception as e:
     attrs={};shape=[];dtype='ERROR:'+type(e).__name__;chunks=None
    blob=' '.join([path,name,json.dumps(attrs,sort_keys=True)])
    if keep(blob): rec['matches'].append({'kind':'array','path':('/'.join([path,name])).strip('/'),'shape':shape,'dtype':dtype,'chunks':chunks,'attrs':attrs})
   for name in g.group_keys():
    try: walk(g[name],('/'.join([path,name])).strip('/'))
    except Exception as e: rec['matches'].append({'kind':'group_open_error','path':('/'.join([path,name])).strip('/'),'error':type(e).__name__+':'+str(e)})
  walk(root,'')
  rec['status']='OK'
 except Exception as e:
  rec.update({'status':'FAILED','error_type':type(e).__name__,'error':str(e),'traceback':traceback.format_exc()})
 recs.append(rec)
(OUT/f'CATALOG_P075E_{SHARD}.json').write_text(json.dumps(recs,indent=2,sort_keys=True)+'\n')
print(json.dumps({'shard':SHARD,'shots':SHOTS,'ok':sum(r['status']=='OK' for r in recs),'failed':sum(r['status']!='OK' for r in recs),'matches':sum(len(r.get('matches',[])) for r in recs),'data_values_loaded':False,'unknown_is_zero':False}))