#!/usr/bin/env python3
from __future__ import annotations
import json, math, os, random, hashlib, statistics, datetime as dt
from pathlib import Path

SCHEDULES=['free','hahn','cpmg_8','xy4x2_8','xy8_8','udd_8','ct_gridd_8']
CONTROLS=['cpmg_8','xy4x2_8','xy8_8','udd_8']
BASES=['X','Y']
FRACS=[0.05,0.10,0.20,0.35,0.55,0.80,1.10,1.50,2.00,2.60]
BLOCKS=8; SHOTS=512; ORDER_SEED=20260821; BOOT_REPS=10000; BOOT_SEED=20260821
PHI=(1+5**0.5)/2; SQRT2=2**0.5; SQRT3=3**0.5; LN5=math.log(5.0)

def cjson(o): return (json.dumps(o,sort_keys=True,separators=(',',':'))+'\n').encode()
def hobj(o): return hashlib.sha256(cjson(o)).hexdigest()
def frac(x): return x-math.floor(x)
def ct_axis(k): return int(math.floor(k*SQRT2)+math.floor(k*SQRT3)+math.floor(LN5*math.log(k+5.0)))%4

def sched(name):
    if name=='free': return [],[]
    if name=='hahn': return [0.5],[0]
    n=8
    if name=='cpmg_8': return [(k+.5)/n for k in range(n)],[0]*n
    if name=='xy4x2_8': return [(k+.5)/n for k in range(n)],[0,1,0,1]*2
    if name=='xy8_8': return [(k+.5)/n for k in range(n)],[0,1,0,1,1,0,1,0]
    if name=='udd_8': return [math.sin(math.pi*(k+1)/(2*n+2))**2 for k in range(n)],[0]*n
    if name=='ct_gridd_8':
        p=[(frac((k+1)/PHI),ct_axis(k)) for k in range(n)]; p.sort()
        return [x for x,_ in p],[a for _,a in p]
    raise KeyError(name)

def signs(ax):
    return (-1 if sum(a%2==1 for a in ax)%2 else 1, -1 if sum(a%2==0 for a in ax)%2 else 1)

def qgaps(total,pos,align):
    units=int(round(total/align)); edges=[0.0]+list(pos)+[1.0]
    raw=[(edges[i+1]-edges[i])*units for i in range(len(edges)-1)]
    u=[int(math.floor(x)) for x in raw]; rem=units-sum(u)
    order=sorted(range(len(raw)), key=lambda i:(-(raw[i]-u[i]),i))
    for i in order[:rem]: u[i]+=1
    return [x*align for x in u]

def qgrid(dtsec,t2,align):
    out=[]
    for f in FRACS:
        q=max(align,int(round((f*t2/dtsec)/align))*align)
        if out and q<=out[-1]: q=out[-1]+align
        out.append(q)
    return out

def imports():
    from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, transpile
    from qiskit.qasm3 import dumps as qasm3_dumps
    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
    return ClassicalRegister, QuantumCircuit, QuantumRegister, transpile, qasm3_dumps, QiskitRuntimeService, Sampler

def service(cls):
    tok=os.getenv('QISKIT_IBM_TOKEN')
    inst=os.getenv('QISKIT_IBM_INSTANCE') or None
    channel=os.getenv('QISKIT_IBM_CHANNEL','ibm_quantum_platform')
    if not tok: raise RuntimeError('QISKIT_IBM_TOKEN missing')
    kw={'channel':channel,'token':tok}
    if inst: kw['instance']=inst
    return cls(**kw)

def pick_backend(svc):
    preferred=os.getenv('IBM_BACKEND','ibm_fez')
    try:
        b=svc.backend(preferred)
        if getattr(b,'status',lambda:None)() and not b.status().operational: raise RuntimeError('not operational')
        return b
    except Exception:
        return svc.least_busy(operational=True,simulator=False,min_num_qubits=1)

def cal(backend, requested='auto'):
    props=backend.properties(); stamp=str(getattr(props,'last_update_date',None))
    dtsec=float(getattr(backend,'dt',None) or getattr(backend.target,'dt',None))
    try:
        tc=backend.target.timing_constraints(); align=int(getattr(tc,'delay_alignment',None) or getattr(tc,'pulse_alignment',None) or 1)
    except Exception: align=1
    align=max(1,align); n=int(getattr(backend,'num_qubits',None) or backend.target.num_qubits)
    cand=[]
    for q in range(n):
        try: t2=float(props.t2(q)); t1=float(props.t1(q)); ro=float(props.readout_error(q))
        except Exception: continue
        if math.isfinite(t2) and t2>0 and math.isfinite(t1) and t1>0:
            cand.append((t2/(1+20*max(ro,0.0)),q,t2,t1,ro))
    if not cand: raise RuntimeError('no calibrated qubit')
    cand.sort(reverse=True)
    if requested=='auto': _,q,t2,t1,ro=cand[0]
    else:
        q=int(requested); found=[x for x in cand if x[1]==q]
        if not found: raise RuntimeError('requested qubit invalid')
        _,q,t2,t1,ro=found[0]
    return {'stamp':stamp,'dt':dtsec,'align':align,'q':q,'t2':t2,'t1':t1,'ro':ro,'n':n}

def precommit(backend,c):
    sm={}
    for s in SCHEDULES:
        pos,ax=sched(s); sx,sy=signs(ax)
        sm[s]={'pulse_count':len(ax),'normalized_positions':pos,'axis_classes_0X_1Y_2mX_3mY':ax,'frame_sign_X':sx,'frame_sign_Y':sy}
    p={'schema':'CT_GRIDD_HARDWARE_PRECOMMIT_V2','protocol_freeze':'2026-08-21','backend':backend.name,'qubit':c['q'],
       'calibration_timestamp':c['stamp'],'dt_seconds':c['dt'],'t2_ref_seconds_from_pre_run_calibration':c['t2'],
       'delay_alignment_dt':c['align'],'pulse_budget':8,'blocks':BLOCKS,'shots_per_basis':SHOTS,'measurement_bases':BASES,
       'delay_fractions_t2':FRACS,'delay_grid_dt':qgrid(c['dt'],c['t2'],c['align']),'schedules':sm,
       'execution':{'randomized_interleaved_order':True,'order_seed':ORDER_SEED,'one_job_per_block':True,'same_backend_qubit_calibration_window':True,'transpile_optimization_level':0,'all_pi_pulses_share_physical_X_gate_with_virtual_Z_phase':True},
       'frozen_comparator':'cpmg_8','equal_budget_controls':CONTROLS,'diagnostic_schedules_not_primary':['free','hahn'],
       'backend_metadata':{'selection_rule':'max pre-run T2/(1+20*readout_error), outcome-blind','pre_run_t1_seconds':c['t1'],'pre_run_t2_seconds':c['t2'],'pre_run_readout_error':c['ro'],'prepared_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'hardware_credit':0}}
    p['precommit_sha256']=hobj(p); return p

def phase(qc,q,a):
    ph=(a%4)*math.pi/2
    if abs(ph)>1e-15: qc.rz(ph,q)
    qc.x(q)
    if abs(ph)>1e-15: qc.rz(-ph,q)

def build(pre,s,d,basis,QReg,CReg,QC):
    qr=QReg(1,'q'); cr=CReg(1,'meas'); qc=QC(qr,cr,name=f'{s}_d{d}_{basis}'); q=qr[0]
    qc.h(q); pos,ax=sched(s); gaps=qgaps(d,pos,int(pre['delay_alignment_dt']))
    for i,a in enumerate(ax):
        if gaps[i]>0: qc.delay(gaps[i],q,unit='dt')
        phase(qc,q,a)
    if gaps[-1]>0: qc.delay(gaps[-1],q,unit='dt')
    if basis=='X': qc.h(q)
    else: qc.sdg(q); qc.h(q)
    qc.measure(q,cr[0]); return qc,len(ax),gaps

def counts01(counts):
    c0=c1=0
    for k,v in counts.items():
        ks=str(k).replace(' ','')
        if ks in ('0','0x0','0b0'): c0+=int(v)
        elif ks in ('1','0x1','0b1'): c1+=int(v)
    return c0,c1

def auc(t,y):
    a=sum(.5*(y[i-1]+y[i])*(t[i]-t[i-1]) for i in range(1,len(t))); return a/(t[-1]-t[0])

def linreg(x,y):
    mx,my=statistics.fmean(x),statistics.fmean(y); den=sum((v-mx)**2 for v in x)
    m=sum((a-mx)*(b-my) for a,b in zip(x,y))/den; return my-m*mx,m

def fit_t2(t,y):
    y=[max(0,min(1.5,float(v))) for v in y]; ym=min(y); bs=[0.0] if ym<=1e-8 else [ym*i/256 for i in range(257)]; best=None
    for b in bs:
        ix=[i for i,v in enumerate(y) if v-b>1e-8]
        if len(ix)<4: continue
        try: inter,m=linreg([t[i] for i in ix],[math.log(y[i]-b) for i in ix])
        except Exception: continue
        if m>=-1e-15: continue
        T=-1/m; A=math.exp(inter); pred=[A*math.exp(-u/T)+b for u in t]; sse=sum((u-v)**2 for u,v in zip(y,pred)); cand=(sse,T,A,b)
        if best is None or cand<best: best=cand
    return float('nan') if best is None else float(best[1])

def pct(v,q):
    p=(len(v)-1)*q; lo=int(math.floor(p)); hi=int(math.ceil(p)); return v[lo] if lo==hi else v[lo]*(hi-p)+v[hi]*(p-lo)

def boot(vals,seed):
    r=random.Random(seed); n=len(vals); z=sorted(sum(vals[r.randrange(n)] for _ in range(n))/n for __ in range(BOOT_REPS)); return [pct(z,.025),pct(z,.975)]

def score(rec,pre):
    times=[d*pre['dt_seconds'] for d in pre['delay_grid_dt']]; bm={}; block_metrics=[]
    for bl in rec['blocks']:
        ix={(e['schedule'],e['delay_dt'],e['basis']):e for e in bl['entries']}
        for s in SCHEDULES:
            coh=[]
            for d in pre['delay_grid_dt']:
                q={}
                for basis in BASES:
                    c0,c1=counts01(ix[(s,d,basis)]['raw_counts']); raw=(c0-c1)/(c0+c1); q[basis]=pre['schedules'][s]['frame_sign_'+basis]*raw
                coh.append(min(1.0,math.sqrt(q['X']**2+q['Y']**2)))
            row={'block_index':bl['block_index'],'schedule':s,'auc':auc(times,coh),'t2_seconds':fit_t2(times,coh),'final_coherence':coh[-1],'coherence_by_delay':coh}; bm[(bl['block_index'],s)]=row; block_metrics.append(row)
    comp={}
    for base in ['free','hahn']+CONTROLS:
        da=[bm[(b,'ct_gridd_8')]['auc']-bm[(b,base)]['auc'] for b in range(BLOCKS)]
        dt2=[bm[(b,'ct_gridd_8')]['t2_seconds']-bm[(b,base)]['t2_seconds'] for b in range(BLOCKS)]
        ca=boot(da,BOOT_SEED+sum(map(ord,base))); ct=boot(dt2,BOOT_SEED+1000+sum(map(ord,base)))
        comp[base]={'mean_auc_delta':statistics.fmean(da),'auc_delta_ci95':ca,'mean_t2_delta_seconds':statistics.fmean(dt2),'t2_delta_ci95_seconds':ct,'joint_positive_ci':ca[0]>0 and ct[0]>0}
    if all(comp[x]['joint_positive_ci'] for x in CONTROLS): st='PASS_SUPERIORITY'
    elif comp['cpmg_8']['joint_positive_ci']: st='PASS_FROZEN_ONLY'
    elif comp['free']['joint_positive_ci']: st='MITIGATION_ONLY'
    else: st='FAIL'
    return {'schema':'CT_GRIDD_MATCHED_HARDWARE_SCORE_V2','status':st,'hardware_terminal_closed':True,'scientific_hardware_credit':1,'backend':pre['backend'],'qubit':pre['qubit'],'precommit_sha256':pre['precommit_sha256'],'comparisons_vs_ct':comp,'block_metrics':block_metrics,'errors':[]}

def main():
    CReg,QC,QReg,transpile,qasm3_dumps,QRS,Sampler=imports(); svc=service(QRS); backend=pick_backend(svc); c=cal(backend,'auto'); pre=precommit(backend,c)
    out=Path('HARDWARE_RUN'); out.mkdir(exist_ok=True); (out/'PRECOMMIT_V2.json').write_bytes(cjson(pre)); (out/'PRECOMMIT_SHA256.txt').write_text(pre['precommit_sha256']+'\n')
    c2=cal(backend,str(pre['qubit']))
    if c2['stamp']!=pre['calibration_timestamp'] or abs(c2['dt']-pre['dt_seconds'])>1e-18: raise RuntimeError('calibration changed between freeze and run')
    rec={'schema':'CT_GRIDD_MATCHED_HARDWARE_RECEIPT_V2','precommit_sha256':pre['precommit_sha256'],'backend':pre['backend'],'qubit':pre['qubit'],'calibration_timestamp':pre['calibration_timestamp'],'dt_seconds':pre['dt_seconds'],'pulse_budget':8,'shots_per_basis':SHOTS,'run_started_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'blocks':[]}
    sampler=Sampler(mode=backend)
    for bi in range(BLOCKS):
        desc=[(s,d,b) for s in SCHEDULES for d in pre['delay_grid_dt'] for b in BASES]; random.Random(ORDER_SEED+bi).shuffle(desc)
        circuits=[]; meta=[]
        for oi,(s,d,b) in enumerate(desc):
            qc,n,gaps=build(pre,s,d,b,QReg,CReg,QC); tq=transpile(qc,backend=backend,initial_layout=[pre['qubit']],optimization_level=0,seed_transpiler=0)
            qasm=qasm3_dumps(tq); xcnt=int(tq.count_ops().get('x',0))
            if xcnt!=n: raise RuntimeError(f'X count mismatch {s}: {xcnt}!={n}')
            meta.append({'schedule':s,'delay_dt':d,'basis':b,'physical_dd_pulse_count':n,'quantized_gap_dt':gaps,'circuit_sha256':hashlib.sha256(qasm.encode()).hexdigest(),'order_index':oi}); circuits.append(tq)
        job=sampler.run(circuits,shots=SHOTS); result=job.result()
        entries=[]
        for r,m in zip(result,meta):
            mm=dict(m); mm['raw_counts']={str(k):int(v) for k,v in r.data.meas.get_counts().items()}; entries.append(mm)
        rec['blocks'].append({'block_index':bi,'job_id':str(job.job_id()),'entries':entries}); (out/'HARDWARE_RECEIPT_V2.json').write_bytes(cjson(rec)); print('block',bi+1,'job',job.job_id(),flush=True)
    rec['run_completed_utc']=dt.datetime.now(dt.timezone.utc).isoformat(); (out/'HARDWARE_RECEIPT_V2.json').write_bytes(cjson(rec)); sc=score(rec,pre); (out/'HARDWARE_SCORE_V2.json').write_bytes(cjson(sc)); print('STATUS='+sc['status'])

if __name__=='__main__': main()
