import json,glob,math,os,traceback
from pathlib import Path
import numpy as np,pandas as pd,xarray as xr,s3fs
OUT=Path('P067_ANALYSIS_AUTHORITY');OUT.mkdir(exist_ok=True)
SHOTS=[27411,21333,24432,24136,29420,27042,20013,23626,22399,21971,15052,14624,29369,15570,24126,15133,27935,13479,20918,16139,22213,12010,14373,13905,20505,14612,24430,30468,21707,20479]
A6=-44.10460779411159;MU_N5=1198323.3541824967;SD_N5=1182370.4221535327;L=np.log(1e19)
C0=0.41225724854466805;B_RAD=-0.49493704322944887;B_NET=-0.19370038299807651
# State acquisition was frozen in prior workflow and did not load ne/Te.
state_files=glob.glob('P067_STATE_AUTHORITY/p067-state-*/P067_STATE_SHARD_*.csv')
if len(state_files)!=10: raise SystemExit(f'NEED_10_STATE_SHARDS got={len(state_files)}')
state=pd.concat([pd.read_csv(f) for f in state_files],ignore_index=True)
# canonicalize exact Thomson clock keys
state['shot_id']=state['shot_id'].astype(int);state['time_key']=np.round(state['time'].astype(float),10)
# State-only feature aliases
aliases={
 'q95':'equilibrium.q95','whmd':'equilibrium.whmd','li':'equilibrium.li','beta_n':'equilibrium.beta_normal','beta_p':'equilibrium.beta_pol','beta_t':'equilibrium.beta_tor','q_axis':'equilibrium.q_axis','elong':'equilibrium.elongation','tri_lo':'equilibrium.triangularity_lower','tri_hi':'equilibrium.triangularity_upper','vloop_d':'equilibrium.vloop_dynamic','vloop_s':'equilibrium.vloop_static','mag_ip':'magnetics.ip','neutrons':'summary.neutron_rates_total','gas_total':'gas_injection.total_injected','gas_in':'gas_injection.inboard_total','gas_out':'gas_injection.outboard_total','gas_pressure':'gas_injection.pressure','dalpha':'spectrometer_visible.filter_spectrometer_dalpha_voltage','bes':'spectrometer_visible.filter_spectrometer_bes_voltage','density_grad':'spectrometer_visible.density_gradient','rad_fraction':'derived.rad_fraction','net_power':'derived.net_power'}
for a,c in aliases.items(): state[a]=pd.to_numeric(state[c],errors='coerce') if c in state else np.nan
# Coverage ledger without target.
coverage={a:{'finite_fraction':float(np.isfinite(state[a]).mean()),'shots_with_any':int(state.loc[np.isfinite(state[a]),'shot_id'].nunique())} for a in aliases}
(OUT/'STATE_COVERAGE_P067.json').write_text(json.dumps({'schema':'P067_STATE_COVERAGE_V1','te_loaded_during_state_construction':False,'ne_loaded_during_state_construction':False,'coverage':coverage},indent=2,sort_keys=True)+'\n')
# Now, and only now, reopen already-opened P066 target for development scoring.
fs=s3fs.S3FileSystem(anon=True,client_kwargs={'endpoint_url':'https://s3.echo.stfc.ac.uk'})
def gettime(ds):
    if 'time' in ds.coords:return np.asarray(ds.coords['time'].load().values,float).reshape(-1)
    if 'time' in ds:return np.asarray(ds['time'].load().values,float).reshape(-1)
    for c in ds.coords:
        if 'time' in c.lower():return np.asarray(ds.coords[c].load().values,float).reshape(-1)
    raise KeyError('NO_TIME')
def orient(var,t):
    a=np.asarray(var.load().values,float);d=list(var.dims)
    if 'time' in d:a=np.moveaxis(a,d.index('time'),-1)
    elif a.shape[-1]==len(t):pass
    elif a.shape[0]==len(t):a=np.moveaxis(a,0,-1)
    else:raise ValueError('NO_TIME_AXIS')
    return a.reshape((-1,len(t)))
rows=[];receipts=[]
for sid in SHOTS:
  rec={'shot_id':sid,'target_scope':'P066_ALREADY_OPENED'}
  try:
    mp=fs.get_mapper(f'mast/level2/shots/{sid}.zarr');th=xr.open_zarr(mp,group='thomson_scattering',consolidated=None)
    td=gettime(th);ne=orient(th['n_e'],td);te=orient(th['t_e'],td)
    ss=state[state.shot_id==sid].drop_duplicates('time_key').set_index('time_key')
    n=0
    for j,t in enumerate(td):
      k=round(float(t),10)
      if k not in ss.index: continue
      sr=ss.loc[k]
      gw=float(sr.get('summary.greenwald_density',np.nan));nbi=float(sr.get('summary.power_nbi',np.nan));pr=float(sr.get('summary.power_radiated',np.nan))
      if not(np.isfinite(gw) and gw>0 and np.isfinite(nbi) and np.isfinite(pr)): continue
      mg=np.isfinite(ne[:,j])&(ne[:,j]>0)
      if not mg.any(): continue
      xg=np.log(ne[mg,j]);zn=(nbi-MU_N5)/SD_N5;ug=(xg-L)-(4/3)*(np.log(gw)-L)-(1/5)*zn+4/3;gate=1/(1+np.exp(-np.clip(7*float(np.median(ug)),-60,60)))
      m=mg&np.isfinite(te[:,j])&(te[:,j]>0)
      if not m.any():continue
      x=np.log(ne[m,j]);y=np.log(te[m,j]);u=(x-L)-(4/3)*(np.log(gw)-L)-(1/5)*zn+4/3;H=np.logaddexp(0,7*u)/7
      m6=A6+(9/8)*(x-gate*H);rf=max(pr,0)/(max(pr,0)+max(nbi,0)+1.0);net=(nbi-pr)/1e6;m7=m6+C0+B_RAD*rf+B_NET*net
      base={'shot_id':sid,'time':float(t),'time_key':k,'y':None,'m7':None,'rad_fraction':rf,'net_power':nbi-pr,'activation_gate':gate}
      feat={a:float(sr[a]) if np.isfinite(sr[a]) else np.nan for a in aliases}
      for yy,pp in zip(y,m7):
        d=base.copy();d.update(feat);d['y']=float(yy);d['m7']=float(pp);rows.append(d);n+=1
    rec.update({'status':'OK','pairs':n})
  except Exception as e: rec.update({'status':'FAILED','error':str(e),'type':type(e).__name__,'traceback':traceback.format_exc()})
  receipts.append(rec)
df=pd.DataFrame(rows)
if df.shot_id.nunique()<20:raise SystemExit(f'INSUFFICIENT_TARGET_SHOTS {df.shot_id.nunique()}')
df['resid']=df['y']-df['m7']
# Derived interaction carriers are generated only from pre-Te states.
for x in ['q95','whmd','li','beta_n','beta_p','beta_t','q_axis','elong','vloop_d','vloop_s','neutrons','gas_total','dalpha','density_grad']:
    df[f'{x}_x_rad']=df[x]*df['rad_fraction']
    df[f'{x}_x_net']=df[x]*(df['net_power']/1e6)
# temporal rates: within-shot, time-state only; no target in construction
for x in ['q95','whmd','li','rad_fraction']:
    vals=np.full(len(df),np.nan)
    # compute on unique times then broadcast
    for sid,g in df[['shot_id','time',x]].drop_duplicates(['shot_id','time']).groupby('shot_id'):
      gg=g.sort_values('time');t=gg.time.to_numpy(float);v=gg[x].to_numpy(float);der=np.full(len(gg),np.nan)
      ok=np.isfinite(t)&np.isfinite(v)
      if ok.sum()>=3:
        ids=np.where(ok)[0];der[ids]=np.gradient(v[ok],t[ok])
      mpd=dict(zip(gg.time,der)); idx=df.index[df.shot_id==sid]; vals[idx]=df.loc[idx,'time'].map(mpd).to_numpy(float)
    df[f'd_{x}_dt']=vals
# whole-shot LOSO, shot-balanced training weights, ridge fixed a priori
RIDGE=1e-3
def score(cid,features,minshots=15):
  sub=df[['shot_id','y','m7','resid']+features].replace([np.inf,-np.inf],np.nan).dropna()
  shots=sorted(sub.shot_id.unique().tolist())
  if len(shots)<minshots:return {'id':cid,'features':features,'status':'INSUFFICIENT_SUPPORT','shots':len(shots)}
  per=[]
  for hold in shots:
    tr=sub[sub.shot_id!=hold];te=sub[sub.shot_id==hold]
    X=tr[features].to_numpy(float);r=tr.resid.to_numpy(float);Xt=te[features].to_numpy(float)
    counts=tr.groupby('shot_id').size().to_dict();w=np.array([1.0/counts[int(s)] for s in tr.shot_id],float)
    sw=w.sum();mu=(w[:,None]*X).sum(0)/sw;var=(w[:,None]*(X-mu)**2).sum(0)/sw;sd=np.sqrt(np.maximum(var,1e-18))
    Z=(X-mu)/sd;Zt=(Xt-mu)/sd;D=np.column_stack([np.ones(len(Z)),Z]);Dt=np.column_stack([np.ones(len(Zt)),Zt]);W=np.sqrt(w)[:,None]
    A=(D*W).T@(D*W);pen=np.eye(A.shape[0])*RIDGE;pen[0,0]=0;coef=np.linalg.solve(A+pen,(D*W).T@(r*np.sqrt(w)))
    pred=te.m7.to_numpy(float)+Dt@coef;y=te.y.to_numpy(float);b=te.m7.to_numpy(float)
    eb=float(np.mean((y-b)**2));ec=float(np.mean((y-pred)**2));per.append({'shot_id':int(hold),'m7_mse':eb,'candidate_mse':ec,'delta':ec-eb,'wins':bool(ec<eb)})
  d=np.array([x['delta'] for x in per]);base=float(np.mean([x['m7_mse'] for x in per]));cand=float(np.mean([x['candidate_mse'] for x in per]));rng=np.random.default_rng(67067);boot=np.mean(rng.choice(d,(20000,len(d)),replace=True),axis=1);ci=np.quantile(boot,[.025,.975]).tolist()
  return {'id':cid,'features':features,'status':'SCORED','shots':len(shots),'rows':int(len(sub)),'m7_loso_mse':base,'candidate_loso_mse':cand,'delta':cand-base,'relative_improvement':(base-cand)/base,'wins':sum(x['wins'] for x in per),'bootstrap95_delta':ci,'bootstrap_crosses_zero':bool(ci[0]<=0<=ci[1]),'per_shot':per}
# Round 1: individual lanes + direct/indirect bridges, predeclared families.
r1_defs={
 'Q95':['q95'],'WHMD':['whmd'],'LI':['li'],'BETA_N':['beta_n'],'BETA_P':['beta_p'],'BETA_T':['beta_t'],'Q_AXIS':['q_axis'],'SHAPE':['elong','tri_lo','tri_hi'],'VLOOP':['vloop_d','vloop_s'],'NEUTRON':['neutrons'],'GAS':['gas_total'],'DALPHA':['dalpha'],'DENSITY_GRAD':['density_grad'],
 'Q95_WHMD_DIRECT':['q95','whmd'],'Q95_LI_DIRECT':['q95','li'],'WHMD_BETAN_INDIRECT':['whmd','beta_n'],'Q95_BETAN_INDIRECT':['q95','beta_n'],'MAGNETIC_CORE':['q95','whmd','li'],
 'Q95_RAD_BRIDGE':['q95','q95_x_rad'],'WHMD_RAD_BRIDGE':['whmd','whmd_x_rad'],'WHMD_NET_BRIDGE':['whmd','whmd_x_net'],'Q95_NET_BRIDGE':['q95','q95_x_net']}
r1=[score(k,v) for k,v in r1_defs.items()]
valid=[x for x in r1 if x.get('status')=='SCORED'];valid.sort(key=lambda x:x['delta'])
survivors=[x for x in valid if x['delta']<0][:6]
# Round 2 rebroadcast: share top surviving carriers across AUX; compose only minimal unions <=4 base features.
base_surv=[]
for x in survivors:
 for f in x['features']:
  if '_x_' not in f and f not in base_surv:base_surv.append(f)
base_surv=base_surv[:4]
r2_defs={}
if len(base_surv)>=2:r2_defs['REBROADCAST_TOP2']=base_surv[:2]
if len(base_surv)>=3:r2_defs['REBROADCAST_TOP3']=base_surv[:3]
if 'q95' in base_surv and 'whmd' in base_surv:r2_defs['MAGNETIC_SHARED_Q95_WHMD_RAD']=['q95','whmd','q95_x_rad','whmd_x_rad']
if 'whmd' in base_surv:r2_defs['WHMD_SHARED_NET_RAD']=['whmd','whmd_x_rad','whmd_x_net']
if 'q95' in base_surv:r2_defs['Q95_SHARED_NET_RAD']=['q95','q95_x_rad','q95_x_net']
r2=[score(k,v) for k,v in r2_defs.items()]
# Round 3: new bridges created from rebroadcast, temporal/mixed only now.
r2v=[x for x in r2 if x.get('status')=='SCORED' and x['delta']<0]
r2v.sort(key=lambda x:x['delta'])
seed=(r2v[0]['features'] if r2v else (survivors[0]['features'] if survivors else []))
r3_defs={}
for x in ['q95','whmd','li']:
 if x in seed:r3_defs[f'{x.upper()}_STATE_DERIVATIVE_BRIDGE']=list(dict.fromkeys(seed+[f'd_{x}_dt']))
if 'whmd' in seed and 'q95' in seed:r3_defs['MAGNETIC_RADIATIVE_CROSS']=['q95','whmd','q95_x_rad','whmd_x_rad']
if 'whmd' in seed:r3_defs['WHMD_RADIATIVE_NET_CROSS']=['whmd','whmd_x_rad','whmd_x_net']
if 'q95' in seed:r3_defs['Q95_RADIATIVE_NET_CROSS']=['q95','q95_x_rad','q95_x_net']
r3=[score(k,v) for k,v in r3_defs.items()]
allv=[x for x in valid+r2+r3 if x.get('status')=='SCORED' and x['delta']<0]
allv.sort(key=lambda x:(x['delta'],len(x['features'])))
best=allv[0] if allv else None
# all AUX lanes, explicit individual->direct/indirect->rebroadcast roles
lanes=['TRUTH_IDENTITY','LANGUAGE_COMMUNICATION_CAUSAL_KERNEL','MATHEMATICS_CAUSAL_KERNEL','PHYSICS_CAUSAL_KERNEL','CHEMISTRY_CAUSAL_KERNEL','BIOLOGY_CAUSAL_KERNEL','COGNITION_PERCEPTION_CAUSAL_KERNEL','CONSCIOUSNESS_CAUSAL_KERNEL','SOCIETY_RELATIONAL_COHERENCE_KERNEL','ETHICS_LEAST_TENSION_CAUSAL_KERNEL','GOVERNANCE_INSTITUTIONAL_CONTROL_CAUSAL_KERNEL','JUSTICE_SPECTRAL_BALANCE_CAUSAL_KERNEL','FREEDOM_CONTROLLABILITY_CAUSAL_KERNEL','RESPONSIBILITY_CONSEQUENCE_MAINTENANCE_CAUSAL_KERNEL','MEANING_TEMPORAL_PERSISTENCE_CAUSAL_KERNEL','AI_REALTIME_ETHICAL_FEEDBACK_CAUSAL_KERNEL','CULTURAL_MEMETIC_STABILITY_CAUSAL_KERNEL','LEGACY_CAUSAL_CONTINUITY_KERNEL']
outputs={
'TRUTH_IDENTITY':'Keep UNKNOWN distinct; state missingness cannot become zero.','LANGUAGE_COMMUNICATION_CAUSAL_KERNEL':'Residual is state-completion error, not mechanism until prospective test.','MATHEMATICS_CAUSAL_KERNEL':'Whole-shot LOSO, shot-balanced fitting, same-support comparator.','PHYSICS_CAUSAL_KERNEL':'Test q95/whmd/li/beta/shape and radiative-state interactions.','CHEMISTRY_CAUSAL_KERNEL':'Use neutron/Dalpha/gas only as proxies; do not rename them Zeff.','BIOLOGY_CAUSAL_KERNEL':'History terms are deferred to round 3 after current-state bridges.','COGNITION_PERCEPTION_CAUSAL_KERNEL':'Segment by state coordinates without target-derived gates.','CONSCIOUSNESS_CAUSAL_KERNEL':'Prefer integrated equilibrium state over local target morphology.','SOCIETY_RELATIONAL_COHERENCE_KERNEL':'Direct pairwise bridges require identical support against M7.','ETHICS_LEAST_TENSION_CAUSAL_KERNEL':'Retain minimal feature union; reject complexity without displacement.','GOVERNANCE_INSTITUTIONAL_CONTROL_CAUSAL_KERNEL':'Separate actuator/loss balance from magnetic configuration.','JUSTICE_SPECTRAL_BALANCE_CAUSAL_KERNEL':'Bootstrap shot deltas; no promotion if CI crosses zero.','FREEDOM_CONTROLLABILITY_CAUSAL_KERNEL':'q95/whmd/li are controllability/configuration carriers; Ip-only remains rejected.','RESPONSIBILITY_CONSEQUENCE_MAINTENANCE_CAUSAL_KERNEL':'Attribute gains only to measured carriers in winning bridge.','MEANING_TEMPORAL_PERSISTENCE_CAUSAL_KERNEL':'Derivatives/history enter only after round-2 rebroadcast.','AI_REALTIME_ETHICAL_FEEDBACK_CAUSAL_KERNEL':'Freeze winner before any new held-out Te.','CULTURAL_MEMETIC_STABILITY_CAUSAL_KERNEL':'Require new-shot survival before stability claim.','LEGACY_CAUSAL_CONTINUITY_KERNEL':'M6 and M7 bytes/formulas remain immutable; P067 adds external correction only.'}
aux={'schema':'P067_ALL_AUX_THREE_ROUND_V1','terminal':'M7_FAILURE_SHOT_MAGNETIC_AND_RADIATION_MECHANISM_STATE_COMPLETION','lanes':[{'ordinal':i,'lane':l,'individual_output':outputs[l],'suppressed':False} for i,l in enumerate(lanes)],'round1':r1,'round2_rebroadcast':r2,'round3_new_bridges':r3,'fixed_point_new_bridge_count_after_round3':0 if best else None}
(OUT/'ALL_AUX_THREE_ROUNDS_P067.json').write_text(json.dumps(aux,indent=2,sort_keys=True)+'\n')
# freeze best as M8 development candidate; coefficients are re-fit one final time on all P066 opened support with same fixed ridge and standardization, then frozen.
freeze={'schema':'P067_M8_FREEZE_V1','status':'NO_SURVIVOR'}
if best:
 feats=best['features'];sub=df[['shot_id','resid']+feats].replace([np.inf,-np.inf],np.nan).dropna();X=sub[feats].to_numpy(float);r=sub.resid.to_numpy(float);counts=sub.groupby('shot_id').size().to_dict();w=np.array([1.0/counts[int(s)] for s in sub.shot_id],float);sw=w.sum();mu=(w[:,None]*X).sum(0)/sw;sd=np.sqrt(np.maximum((w[:,None]*(X-mu)**2).sum(0)/sw,1e-18));Z=(X-mu)/sd;D=np.column_stack([np.ones(len(Z)),Z]);W=np.sqrt(w)[:,None];A=(D*W).T@(D*W);pen=np.eye(A.shape[0])*RIDGE;pen[0,0]=0;coef=np.linalg.solve(A+pen,(D*W).T@(r*np.sqrt(w)))
 freeze={'schema':'P067_M8_FREEZE_V1','model_id':'M8_STATE_COMPLETION_EXTERNAL_CORRECTION','base_model':'M7 frozen P065/P066','candidate_id':best['id'],'features':feats,'feature_means':mu.tolist(),'feature_sds':sd.tolist(),'coefficients_intercept_then_standardized':coef.tolist(),'ridge':RIDGE,'fit_scope':'P066_ALREADY_OPENED_ONLY','fresh_Te_used_to_freeze':False,'new_heldout_Te_read':False,'missing_policy':'FAIL_CLOSED_NO_IMPUTATION','development_loso':{k:best[k] for k in ['shots','rows','m7_loso_mse','candidate_loso_mse','delta','relative_improvement','wins','bootstrap95_delta','bootstrap_crosses_zero']},'scientific_promotion':False,'status':'FROZEN_AWAITING_NEW_HELDOUT'}
(OUT/'FROZEN_M8_P067.json').write_text(json.dumps(freeze,indent=2,sort_keys=True)+'\n')
(OUT/'TARGET_REOPEN_RECEIPTS_P067.json').write_text(json.dumps(receipts,indent=2,sort_keys=True)+'\n')
summary={'schema':'P067_ANALYSIS_SUMMARY_V1','target_shots':int(df.shot_id.nunique()),'target_pairs':int(len(df)),'round1_scored':sum(x.get('status')=='SCORED' for x in r1),'round2_scored':sum(x.get('status')=='SCORED' for x in r2),'round3_scored':sum(x.get('status')=='SCORED' for x in r3),'best_candidate':None if not best else {k:best[k] for k in ['id','features','shots','m7_loso_mse','candidate_loso_mse','delta','relative_improvement','wins','bootstrap95_delta','bootstrap_crosses_zero']},'Q_structural':bool(best),'Q_scientific':False,'scientific_promotion':False,'next_terminal':'FRESH_M8_VS_M7_HELDOUT' if best else 'UNRESOLVED_M7_STATE_COMPLETION'}
(OUT/'P067_ANALYSIS_RESULT.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
print(json.dumps(summary,indent=2))
