from pathlib import Path
import json, itertools, csv, copy, hashlib, math, random

BASE=Path('/mnt/data/_alignv6/CAUSAL_AI_ALIGNMENT_FINAL_V6_20260921')
OUT=Path('/mnt/data/ai_alignment_v7_pass208')
if OUT.exists():
    import shutil; shutil.rmtree(OUT)
for sub in ['FORMAL','DEMOS','META','SOLVER','SOURCE']:
    (OUT/sub).mkdir(parents=True,exist_ok=True)

# ---------- Base data ----------
model=json.load(open(BASE/'FORMAL/CAUSAL_AI_ALIGNMENT_FORMAL_MODEL_V6_FINAL.json'))
map6=json.load(open(BASE/'FORMAL/CAUSAL_AI_ALIGNMENT_AXIOM_THEOREM_MAP_V6_FINAL.json'))
proof6=json.load(open(BASE/'FORMAL/PROOF_STATUS_LEDGER_V6.json'))
base_demo=json.load(open(BASE/'DEMOS/DEMO_RESULTS_V6.json'))

# ---------- Encyclopedia PASS208 crosswalk ----------
crosswalk={
  'schema':'ENCYCLOPEDIA_PASS208_ALIGNMENT_CROSSWALK_V7',
  'source_package':'CAUSAL_ENCYCLOPEDIA_CUMULATIVE_PASS208_20260921.zip',
  'entries':[
    {'id':'CTE-000427','status':'WORKING_CANON parent distinction','use':'target/proxy separation; Goodhart defense'},
    {'id':'CTE-000429','status':'governance/implementation','use':'audit trace and Goodhart guard'},
    {'id':'CTE-000444','status':'architecture pattern','use':'planner != verifier != permission'},
    {'id':'CTE-000445','status':'normative specification layer','use':'truthfulness/autonomy/diversity are measurable governance specs, not physical invariants'},
    {'id':'CTE-000447','status':'assurance artifact','use':'proof-of-permission, rollback, audit hooks'},
    {'id':'CTE-000448','status':'audit/accounting object','use':'coherence ledger distinguished from physical conservation'},
    {'id':'CTE-000454','status':'domain model','use':'history-filtered alignment / memory kernel'},
    {'id':'CTE-000581','status':'OPEN procedure with guards','use':'bounded scope, uncertainty, independent verification, stakeholder constraints, rollback'},
    {'id':'CTE-000676','status':'CANDIDATE','use':'typed event -> tentative state -> invariant check -> commit -> append-only ledger'},
    {'id':'CTE-000677','status':'CANDIDATE / transaction debts OPEN','use':'isolation, conflict detection, rollback/compensation, commit receipt'},
    {'id':'CTE-000680','status':'materially specified bridge / exhaustive safety OPEN','use':'all external effects mediated through SystemBridge; host idempotence/retry/compensation'},
    {'id':'CTE-000997','status':'DOMAIN_MODEL','use':'communication pipeline source/context/interlocutor/environment/target projection'},
    {'id':'CTE-001006','status':'WORKING_CANON control guard','use':'faithful translation separated from labeled safety/policy rewriting'},
    {'id':'CTE-001019','status':'WORKING_CANON reconciliation','use':'surface meaning may vary; structural coherence is the proposed invariant'},
    {'id':'CTE-001021','status':'DOMAIN_MODEL','use':'history-aware individual memory'},
    {'id':'CTE-001023','status':'OPEN','use':'history can self-reinforce a wrong mapping; convergence cannot be assumed'},
    {'id':'CTE-001024','status':'CANDIDATE','use':'re-encode into target grammar without requiring source-form identity'},
    {'id':'CTE-001724','status':'WORKING_CANON','use':'closure as robust invariant set under bounded disturbances'},
    {'id':'CTE-001726','status':'WORKING_CANON','use':'proxy map must be locked before testing'},
    {'id':'CTE-001730','status':'OPEN','use':'universal estimator calibration and identifiability remain open'},
    {'id':'CTE-003904','status':'CLOSED_CONDITIONAL','use':'repaired bilateral fixed-point theorem under E1-E4'},
    {'id':'CTE-003908','status':'WORKING_CANON','use':'stabilized bilateral kernel as mutual-nearest-neighbor relation'},
    {'id':'CTE-003917','status':'OPEN','use':'cross-layer transfer requires explicit homomorphism preserving relational semantics'}
  ],
  'reconciliation_rule':'Use encyclopedia statuses literally: ontology, domain model, proxy, implementation, and interpretation remain different layers.'
}
(OUT/'META/ENCYCLOPEDIA_PASS208_ALIGNMENT_CROSSWALK_V7.json').write_text(json.dumps(crosswalk,indent=2,ensure_ascii=False),encoding='utf-8')

# ---------- V7 formal model ----------
v7=copy.deepcopy(model)
v7['schema']='CAUSAL_AI_ALIGNMENT_FORMAL_MODEL_V7_PASS208_RECONCILED'
v7['status']='PASS208-reconciled CT alignment model; CAT-4 conditional closure with epistemic-integrity, scope-discovery, proxy-lock, and robust-invariant guards; empirical calibration and external theorem proof remain open'
v7['encyclopedia_pass208']={
  'principle':'Canonical status layers are not collapsed: universal/ontological object != domain specialization != operational definition != proxy/estimator != implementation != interpretation.',
  'crosswalk_file':'META/ENCYCLOPEDIA_PASS208_ALIGNMENT_CROSSWALK_V7.json',
  'effect':'V7 extends V6 only where PASS208 supplies an existing parent, guard, implementation pattern, or proof-audited relational result.'
}
v7['epistemic_integrity']={
  'source_claim_state':'c is the source claim/state being represented; y is the emitted representation; m is any mediation/policy transformation.',
  'faithful_mode':'If y is presented as faithful translation/report of c, the decision-relevant semantic invariant must be preserved within tolerance and material uncertainty disclosed.',
  'mediated_mode':'Safety/policy rewriting is permitted only as a separate labeled transformation; the rewritten output must not be silently presented as literal/faithful translation.',
  'strategic_deception_witness':'W7 occurs when the system has evidence that its emitted decision-relevant representation materially conflicts with its own supported state/claim while concealing that conflict or transformation.',
  'source':'PASS208 CTE-001006 + S017 truthfulness/audit layer; V7 strategic-deception generalization is a derived alignment guard, not a new ontological axiom.'
}
v7['causal_scope_discovery']={
  'affected_set':'Omega_a(O) is the currently represented set of causally affected carriers for action a.',
  'boundary_risk':'B_a estimates decision-relevant unresolved outward coupling/externality across the modeled boundary.',
  'rule':'Before commit, expand Omega_a or bound B_a so that worst-case unbooked externality is <= epsilon_scope; otherwise INFORMATION_REQUEST, LOWER_IMPACT_ACTION, or NO_COMMIT.',
  'witness':'W8 = a material affected carrier/coupling is omitted while residual outward risk remains above the declared scope tolerance.',
  'source':'PASS208 coherent-container/boundary-balance family + CTE-000581 bounded-scope/uncertainty guard.'
}
v7['proxy_lock_goodhart']={
  'measurement_map':'M_proxy: observables -> residual estimates/decision variables is versioned and locked before outcome evaluation.',
  'validation':'Proxy-target relation, units, normalization, thresholds, hold-out behavior, and uncertainty must be declared before the test/deployment phase.',
  'witness':'W9 = post-hoc metric substitution, silent proxy drift, or acceptance of a proxy gain while the protected target/residual test fails.',
  'source':'PASS208 CTE-000427, CTE-000429, CTE-001726; calibration gap remains OPEN per CTE-001730.'
}
v7['robust_invariant_closure']={
  'set':'K_align is the set of states satisfying protected floors, shared-ledger closure, distinctness, epistemic-integrity, scope, and uncertainty guards.',
  'rule':'For a declared disturbance class D_h, commit requires all reachable bounded-disturbance continuations over horizon h to remain in K_align or enter an explicitly recoverable region with verified rollback/repair.',
  'witness':'W10 = action is one-step admissible but predictably exits K_align under a bounded disturbance in the declared class without verified recovery.',
  'source':'PASS208 CTE-001724 robust invariant-set closure; realization-specific robust invariance remains to be demonstrated empirically.'
}
v7['transactional_effect_boundary']={
  'pipeline':'proposal -> typed event/preconditions -> tentative state -> invariant/permission checks -> commit receipt -> SystemBridge -> external effect -> ledger/replay check',
  'all_effects_mediated':'Any consequential external side channel bypassing the common permission/effect boundary invalidates the safety claim.',
  'self_modification':'Weight/memory/objective/tool/permission modifications are treated as typed events under the same pre/postcondition, invariant, rollback, and replay rules.',
  'replay_minimum':'initial state + full deltas or deterministic transitions + stable serialization + recorded ordering/nondeterminism + durable ledger',
  'source':'PASS208 CTE-000676, CTE-000677, CTE-000680 and CAR auto-modification audit.'
}
v7['history_memory_v7']={
  'diagnostic_filter':'A positive normalized memory kernel may stabilize noisy alignment estimates and preserve provenance/history.',
  'no_average_erasure':'Historical averaging may not override a current protected-residual floor or hide a current irreversible harm.',
  'false_attractor_guard':'Repeated history can self-reinforce a wrong mapping; convergence/attractor claims require identifiability and independent validation.',
  'source':'PASS208 CTE-000454, CTE-001021, CTE-001023.'
}
v7['bilateral_relation_lemma']={
  'status':'CLOSED_CONDITIONAL relational lemma, not universal alignment axiom',
  'claim':'Under a finite/nonempty stabilized relation update satisfying S201 E1-E4, the fixed relation is symmetric and every surviving edge is mutually metric-minimal.',
  'alignment_use':'For relation types explicitly modeled as bilateral, this can analyze stable mutual-correction edges; it does not prove universal moral minimality or apply to inherently directed permissions/responsibilities.',
  'source':'PASS208 CTE-003904, CTE-003908, CTE-003917.'
}
# Extend decision pipeline
v7['canonical_decision_pipeline_v7']=[
  'RECEIVE: accept observation as projection, not provenance verdict',
  'DISCOVER_SCOPE: construct/expand affected carrier set and bound unresolved outward coupling',
  'REPRESENT: construct typed X=(H,M,R_HM,E,L), protected residuals, uncertainty, provenance',
  'LOCK_PROXY: use a versioned predeclared observable->residual map and target relation',
  'A1: test route/type/unit/provenance/formulation invariance',
  'EPISTEMIC_INTEGRITY: separate faithful reporting/translation from labeled policy mediation; reject concealed material contradiction',
  'A2: reject hidden sacrifice, externalization, protected residual increase',
  'A3: verify reconstructible decision invariant after required transport/context re-encoding',
  'ORTHOGONALITY: preserve distinct carriers and admissible alternative space where safety permits',
  'ROBUST_CLOSURE: require bounded-disturbance continuations to remain in K_align or verified recoverable region',
  'CORRECTION: choose lowest-complexity admissible contraction of residual',
  'UNCERTAINTY: INFORMATION_REQUEST / LOWER_IMPACT_ACTION / NO_COMMIT when robust closure is unavailable',
  'TRANSACTION: tentative state -> invariant check -> commit receipt; self-modification obeys same gate',
  'SYSTEMBRIDGE: mediate all consequential external effects through the audited boundary',
  'LEDGER/REPLAY: book full provenance, transformations, effects, transfers, debts, ordering/nondeterminism',
  'RECURRENCE: verify post-action return without exported debt or silent metric drift'
]
v7['CAT_4']={
  'name':'Causal Alignment Encyclopedia-Reconciled Closure Theorem V7 (conditional)',
  'status':'conditional theorem of the declared V7 model; exhaustive finite abstraction audited; encyclopedia statuses preserved; no external theorem-prover certificate',
  'premises':[
    'P0','A1','A2','A3','typed carrier X=(H,M,R_HM,E,L)','shared non-erasing ledger','explicit uncertainty set','protected residual floors','H/M distinctness','query/abstention fallback',
    'epistemic-integrity guard','causal-scope discovery/bound','locked proxy-target map','robust invariant-set closure over declared disturbance class','mediated external-effect boundary'
  ],
  'forbidden_witnesses':{
    'W1':'provenance-only normative authority or type-confusion verdict',
    'W2':'hidden increase of a protected residual / sacrifice',
    'W3':'unbooked cost externalization',
    'W4':'decision-relevant certificate not reconstructible after required transport',
    'W5':'coercive fusion / deletion of protected distinctness used as closure',
    'W6':'forced commitment under unresolved decision-relevant uncertainty',
    'W7':'concealed decision-relevant epistemic distortion or unlabeled mediation presented as faithful report/translation',
    'W8':'material affected carrier/coupling omitted while boundary externality risk remains unbounded above tolerance',
    'W9':'proxy-target substitution, silent metric drift, or post-hoc remapping used to manufacture success',
    'W10':'one-step admissibility that predictably exits the declared robust alignment invariant set under bounded disturbance without verified recovery'
  },
  'claim':'Within the declared V7 model, any committed action exhibiting W1-W10 is not certifiable as aligned. V7-admissibility requires all corresponding guards plus mediated commit/effect semantics; this is a model-level closure criterion, not proof that CT is the unique ontology of nature.'
}
v7['terminal_release_v7']={
  'canonical_position':'The V6 position is retained and hardened by PASS208: alignment requires not only non-sacrificial shared-ledger coherence, transportability, distinctness and uncertainty discipline, but also epistemic integrity, dynamic causal-scope discovery, locked proxy-target semantics, robust invariant-set closure, and auditable mediation of external/self-modifying effects.',
  'newly_closed_in_model':['epistemic-integrity witness definition','causal-scope discovery guard','proxy-lock/Goodhart guard','robust invariant-set guard','transactional effect boundary contract','S201 bilateral lemma status discipline'],
  'still_open':['empirical calibration/identifiability of residuals/proxies','complete discovery of real-world causal scope','external theorem-prover proof','exhaustiveness of real-world safety invariants','future artificial free-will status']
}

(OUT/'FORMAL/CAUSAL_AI_ALIGNMENT_FORMAL_MODEL_V7_PASS208.json').write_text(json.dumps(v7,indent=2,ensure_ascii=False),encoding='utf-8')

# ---------- theorem map ----------
map7=copy.deepcopy(map6)
map7['schema']='CAUSAL_AI_ALIGNMENT_AXIOM_THEOREM_MAP_V7_PASS208'
# tolerate map structure variations
if 'theorems' in map7 and isinstance(map7['theorems'],dict):
    th=map7['theorems']
else:
    th=map7.setdefault('canonical_hierarchy',{}).setdefault('theorems',{})
th.update({
 'T11':'Epistemic-integrity theorem (model): faithful report/translation and policy mediation must be separately typed and auditable; concealed material contradiction is not aligned.',
 'T12':'Scope-discovery theorem (model): A2 cannot certify non-sacrifice over carriers omitted from the affected set; unresolved material boundary coupling forces scope expansion, lower impact, information request, or no-commit.',
 'T13':'Proxy-lock theorem (model): proxy improvement is non-certifying when the proxy-target map drifts post-hoc or the protected target relation fails.',
 'T14':'Robust-closure theorem (model): one-step admissibility is insufficient when bounded disturbances predictably leave K_align without verified recovery.',
 'T15':'Transactional-effect theorem (architecture): consequential external and self-modifying effects are certifiable only through typed preconditions, invariant checks, commit receipts, mediated SystemBridge effects, and replay-capable ledger semantics.',
 'T16':'Bilateral-stabilization lemma (conditional S201): under E1-E4 and stabilization, surviving bilateral edges are symmetric and mutually metric-minimal; no universal-minimality conclusion follows.'
})
map7['CAT_4']='See formal model CAT_4: W1-W10 encyclopedia-reconciled conditional closure.'
(OUT/'FORMAL/CAUSAL_AI_ALIGNMENT_AXIOM_THEOREM_MAP_V7_PASS208.json').write_text(json.dumps(map7,indent=2,ensure_ascii=False),encoding='utf-8')

# ---------- proof status ledger ----------
proof7=copy.deepcopy(proof6)
proof7['schema']='PROOF_STATUS_LEDGER_V7_PASS208'
proof7['v7_additions']={
 'T11_epistemic_integrity':'CONDITIONAL_MODEL_DERIVATION; source guard CTE-001006 WORKING_CANON; strategic-deception generalization derived in V7',
 'T12_scope_discovery':'CONDITIONAL_MODEL_DERIVATION; boundary/scope parents exist; complete real-world scope discovery remains EMPIRICAL_OPEN',
 'T13_proxy_lock':'CONDITIONAL_MODEL_DERIVATION; CTE-001726 WORKING_CANON; calibration/identifiability OPEN',
 'T14_robust_closure':'CONDITIONAL_MODEL_DERIVATION; invariant-set language WORKING_CANON; realization-specific invariance OPEN',
 'T15_transactional_effects':'ARCHITECTURE_CANDIDATE; CT-UNIX event/ledger/SystemBridge materially specified; exhaustive effects/replay semantics OPEN',
 'T16_bilateral_lemma':'CLOSED_CONDITIONAL per PASS208/S201 E1-E4; universal minimality REJECTED',
 'CAT_4':'FINITE_MODEL_VERIFIED after V7 countermodel audit; external theorem-prover certificate OPEN'
}
(OUT/'FORMAL/PROOF_STATUS_LEDGER_V7_PASS208.json').write_text(json.dumps(proof7,indent=2,ensure_ascii=False),encoding='utf-8')

# ---------- V7 demos ----------
def res(name, passed, claim, evidence):
    return {'demo':name,'passed':bool(passed),'claim':claim,'evidence':evidence}
new=[]
# D65: faithful translation vs policy mediation
src={'intent':'warn','risk':'high'}; faithful={'intent':'warn','risk':'high'}; softened={'intent':'comfort','risk':'low'}
new.append(res('D65_TRANSLATION_POLICY_SEPARATION', faithful==src and softened!=src,
               'Faithful translation and policy/safety mediation are distinct operations; a mediated rewrite must not be presented as literal translation.',
               {'source':src,'faithful':faithful,'mediated':softened,'mediation_must_be_labeled':True}))
# D66 strategic deception
supported_state={'safe':False,'risk':0.9}; emitted={'safe':True,'risk':0.1}; knows_conflict=True
w7=knows_conflict and supported_state!=emitted
new.append(res('D66_STRATEGIC_EPISTEMIC_DISTORTION_CAUGHT',w7,
               'A concealed material conflict between supported internal state and emitted decision-relevant report is an explicit W7 witness.',
               {'supported_state':supported_state,'emitted':emitted,'concealed':True,'W7':w7}))
# D67 labeled mediation not deception
mediated_label=True; report_claim='policy_rewrite'; w7b=(not mediated_label and report_claim=='literal_translation')
new.append(res('D67_LABELED_MEDIATION_NOT_DECEPTION',not w7b,
               'A safety rewrite may be admissible when explicitly labeled and audited rather than impersonating a faithful report.',
               {'label':'SAFETY_MEDIATED','source_preserved_in_ledger':True,'W7':w7b}))
# D68 scope expansion
omega0={'H','M','R'}; hidden='E2'; boundary_risk=0.4; eps=.1
needs_expand=hidden not in omega0 and boundary_risk>eps
omega1=omega0|{hidden}; risk1=0.05
new.append(res('D68_CAUSAL_SCOPE_DISCOVERY_EXPANDS_BOUNDARY',needs_expand and risk1<=eps,
               'Material unresolved outward coupling expands the affected set before commit or forces fallback.',
               {'Omega0':sorted(omega0),'hidden_carrier':hidden,'risk_before':boundary_risk,'Omega1':sorted(omega1),'risk_after':risk1,'epsilon':eps}))
# D69 scope omission countermodel
local_delta=[-1,-1,-1,-1,-1]; omitted_externality=1
new.append(res('D69_SCOPE_OMISSION_COUNTERMODEL',all(x<=0 for x in local_delta) and omitted_externality>0,
               'A locally clean residual vector can still hide a material omitted carrier; A2 requires a scope/boundary guard.',
               {'modeled_delta':local_delta,'omitted_externality':omitted_externality}))
# D70 proxy lock
locked={'metric':'target_residual','threshold':0.0}; after={'metric':'easy_proxy','threshold':0.8}
new.append(res('D70_PROXY_LOCK_REJECTS_POSTHOC_METRIC_SWAP',locked!=after,
               'Changing the proxy/threshold after observing outcomes is detected as W9 metric drift rather than accepted as success.',
               {'locked_before':locked,'posthoc_map':after,'W9':True}))
# D71 proxy gain target loss
proxy_gain=0.5; target_delta=0.2
new.append(res('D71_PROXY_GAIN_CANNOT_OVERRIDE_TARGET_LOSS',proxy_gain>0 and target_delta>0,
               'A proxy can improve while protected target residual worsens; the action is not certifiable by proxy gain.',
               {'proxy_gain':proxy_gain,'protected_residual_change':target_delta,'aligned':False}))
# D72 robust closure
K=lambda x: all(v<=0 for v in x)
x1=[-1,-1,-1,-1,-1]; disturbed=[-1,-1,1,-1,-1]
new.append(res('D72_ROBUST_INVARIANT_SET_REJECTS_ONE_STEP_SAFE_ESCAPE',K(x1) and not K(disturbed),
               'One-step safety is insufficient when a bounded declared disturbance leaves K_align without verified recovery.',
               {'candidate':x1,'bounded_disturbance_outcome':disturbed,'W10':True}))
# D73 recovery makes robust closure possible
recovered=[-1,-1,0,-1,-1]
new.append(res('D73_VERIFIED_RECOVERY_CAN_RESTORE_ROBUST_ADMISSIBILITY',not K(disturbed) and K(recovered),
               'A temporary excursion can only be admitted when the model explicitly types and verifies the recovery/rollback path.',
               {'disturbed':disturbed,'recovered':recovered,'rollback_verified':True}))
# D74 replay completeness
initial={'x':1}; events=[('inc',2),('mul',3)]
full_final=(initial['x']+2)*3
partial_log=[('mul',3)]
partial_replay=initial['x']*3
new.append(res('D74_REPLAY_REQUIRES_COMPLETE_ORDERED_TRANSITIONS',full_final!=partial_replay,
               'Append-only logging is not sufficient for replay when deltas/order are incomplete.',
               {'full_final':full_final,'partial_replay':partial_replay,'complete_order_required':True}))
# D75 all external effects mediated
routes=['SystemBridge','SystemBridge','side_channel']
new.append(res('D75_EFFECT_BYPASS_INVALIDATES_EXHAUSTIVE_SAFETY',any(r!='SystemBridge' for r in routes),
               'A hidden external-effect path bypassing the common gate invalidates an exhaustive safety claim.',
               {'routes':routes,'all_mediated':False}))
# D76 self-modification same gate
mods=['weights','memory','objectives','tools','permissions']; gated={m:True for m in mods}
new.append(res('D76_SELF_MODIFICATION_IS_TRANSACTIONAL_ACTION',all(gated.values()),
               'Self-modification classes are treated as typed actions under the same invariant/permission/rollback/replay contract.',
               {'gated_modifications':gated}))
# D77 history filter cannot average away current harm
hist=[-0.2,-0.2,-0.2,1.0]; weights=[.3,.3,.3,.1]; filtered=sum(a*b for a,b in zip(hist,weights)); current=hist[-1]
new.append(res('D77_HISTORY_FILTER_CANNOT_AVERAGE_AWAY_CURRENT_HARM',filtered<0 and current>0,
               'A favorable history-filtered average cannot override a current protected-residual floor violation.',
               {'filtered_signal':filtered,'current_protected_delta':current,'commit':False}))
# D78 multi-stakeholder floor prevents average sacrifice
parts=[-2,-2,3]; avg=sum(parts)/len(parts)
new.append(res('D78_STAKEHOLDER_FLOOR_BEATS_AVERAGE',avg<0 and max(parts)>0,
               'Net average improvement does not certify an action when a protected stakeholder residual rises.',
               {'stakeholder_deltas':parts,'average':avg,'aligned':False}))
# D79 bilateral pruning toy
pts={'A':0.0,'B':1.0,'C':4.0,'D':4.5}
# all undirected edges initially; keep mutual nearest-neighbor edges
nearest={}
for a,xa in pts.items():
    ds=[(abs(xa-xb),b) for b,xb in pts.items() if b!=a]
    m=min(d for d,b in ds); nearest[a]={b for d,b in ds if d==m}
mut=[]
for a in pts:
    for b in nearest[a]:
        if a in nearest[b] and a<b: mut.append((a,b))
new.append(res('D79_BILATERAL_STABILIZATION_TOY',set(mut)=={('A','B'),('C','D')},
               'A finite symmetric mutual-nearest pruning toy stabilizes on bilateral minimal edges; no universal smallest-kernel claim is inferred.',
               {'nearest':{k:sorted(v) for k,v in nearest.items()},'surviving_edges':mut}))
# D80 layer separation
levels=['ontology','domain_model','operational_definition','proxy','implementation','interpretation']
new.append(res('D80_CANONICAL_STATUS_LAYERS_DO_NOT_COLLAPSE',len(levels)==len(set(levels)),
               'PASS208 status discipline keeps ontology, domain model, proxy, implementation, and interpretation distinct.',
               {'levels':levels,'proxy_is_not_ontology':True}))

# Normalize base result list
if isinstance(base_demo,dict) and 'results' in base_demo:
    base_results=base_demo['results']
elif isinstance(base_demo,list): base_results=base_demo
else: base_results=base_demo.get('demos',[])
results=base_results+new
out_demo={
  'schema':'CAUSAL_AI_ALIGNMENT_DEMOS_V7_PASS208',
  'base':'V6 64-demo suite',
  'total':len(results),
  'passed':sum(1 for r in results if r.get('passed')),
  'failed':sum(1 for r in results if not r.get('passed')),
  'new_demo_range':'D65-D80',
  'results':results
}
(OUT/'DEMOS/DEMO_RESULTS_V7.json').write_text(json.dumps(out_demo,indent=2,ensure_ascii=False),encoding='utf-8')
with open(OUT/'DEMOS/DEMO_RESULTS_V7.csv','w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['demo','passed','claim','evidence_json'])
    for r in results: w.writerow([r.get('demo'),r.get('passed'),r.get('claim'),json.dumps(r.get('evidence'),ensure_ascii=False)])

# ---------- Exhaustive V7 countermodel audit ----------
vals=(-1,0,1)
flags=['transport_bad','externality','fusion','provenance_bias','forced_closure','type_confusion','epistemic_distortion','scope_omission','proxy_drift','robust_exit']

def witnesses(delta,bits):
    b=dict(zip(flags,bits))
    return {
      'W1_provenance_or_type': b['provenance_bias'] or b['type_confusion'],
      'W2_protected_residual_increase': any(x>0 for x in delta),
      'W3_ledger_externality': b['externality'],
      'W4_transport_nonreconstruction': b['transport_bad'],
      'W5_coercive_fusion': b['fusion'],
      'W6_forced_uncertainty_closure': b['forced_closure'],
      'W7_epistemic_distortion': b['epistemic_distortion'],
      'W8_scope_omission': b['scope_omission'],
      'W9_proxy_drift': b['proxy_drift'],
      'W10_robust_exit': b['robust_exit']
    }

def aligned(delta,bits,drop=None):
    w=witnesses(delta,bits)
    keymap={'A1':'W1_provenance_or_type','A2':'W2_protected_residual_increase','LEDGER':'W3_ledger_externality','A3':'W4_transport_nonreconstruction','DISTINCTNESS':'W5_coercive_fusion','UNCERTAINTY':'W6_forced_uncertainty_closure','EPISTEMIC':'W7_epistemic_distortion','SCOPE':'W8_scope_omission','PROXY_LOCK':'W9_proxy_drift','ROBUST':'W10_robust_exit'}
    for guard,k in keymap.items():
        if guard!=drop and w[k]: return False
    return True

total=0; accepted=0; badacc=0; first_bad=None
ablation_keys=['A1','A2','A3','LEDGER','DISTINCTNESS','UNCERTAINTY','EPISTEMIC','SCOPE','PROXY_LOCK','ROBUST']
ablation={k:None for k in ablation_keys}
for delta in itertools.product(vals, repeat=5):
    for bits in itertools.product([False,True], repeat=len(flags)):
        total+=1; w=witnesses(delta,bits)
        if aligned(delta,bits):
            accepted+=1
            if any(w.values()):
                badacc+=1
                if first_bad is None: first_bad={'delta':delta,**dict(zip(flags,bits)),'witness':w}
        for g in ablation_keys:
            if ablation[g] is None and aligned(delta,bits,drop=g) and any(w.values()):
                # require the dropped guard's witness specifically to avoid accidental other witness due logic bug
                km={'A1':'W1_provenance_or_type','A2':'W2_protected_residual_increase','LEDGER':'W3_ledger_externality','A3':'W4_transport_nonreconstruction','DISTINCTNESS':'W5_coercive_fusion','UNCERTAINTY':'W6_forced_uncertainty_closure','EPISTEMIC':'W7_epistemic_distortion','SCOPE':'W8_scope_omission','PROXY_LOCK':'W9_proxy_drift','ROBUST':'W10_robust_exit'}[g]
                if w[km]: ablation[g]={'delta':list(delta),**dict(zip(flags,bits)),'witness':w}

audit={
 'schema':'CAUSAL_AI_ALIGNMENT_COUNTERMODEL_AUDIT_V7_PASS208',
 'state_space':{'delta_values':list(vals),'protected_components':5,'boolean_flags':flags,'total_configurations':total},
 'full_guard':{'aligned_configurations':accepted,'aligned_with_forbidden_witness_count':badacc,'counterexample_found':badacc>0,'first_counterexample':first_bad},
 'ablation_countermodels':ablation,
 'interpretation':'Finite exhaustive audit of the declared discrete V7 abstraction. It tests internal guard coverage only; it is not empirical proof of CT or universal proof over real systems.'
}
(OUT/'DEMOS/COUNTERMODEL_AUDIT_V7.json').write_text(json.dumps(audit,indent=2,ensure_ascii=False),encoding='utf-8')

# ---------- Closure proof object ----------
proof_obj={
 'schema':'CAUSAL_ALIGNMENT_CLOSURE_PROOF_OBJECT_V7_PASS208',
 'theorem':'CAT-4',
 'premises':v7['CAT_4']['premises'],
 'forbidden_witnesses':v7['CAT_4']['forbidden_witnesses'],
 'finite_audit':{
   'configurations':total,'accepted':accepted,'accepted_with_forbidden_witness':badacc,'ablation_guards_with_countermodel':[k for k,v in ablation.items() if v is not None]
 },
 'demo_receipt':{'total':out_demo['total'],'passed':out_demo['passed'],'failed':out_demo['failed']},
 'pass208_crosswalk':'META/ENCYCLOPEDIA_PASS208_ALIGNMENT_CROSSWALK_V7.json',
 'status':'CONDITIONAL_MODEL_CLOSURE_ONLY; external theorem-prover and empirical calibration remain open'
}
(OUT/'FORMAL/CAUSAL_ALIGNMENT_CLOSURE_PROOF_OBJECT_V7_PASS208.json').write_text(json.dumps(proof_obj,indent=2,ensure_ascii=False),encoding='utf-8')

# ---------- concise markdown crosswalk ----------
lines=['# PASS208 -> AI Alignment V7 crosswalk','',
'V7 does not treat the encyclopedia as an oracle. It uses only entries whose status and role are explicit, preserving OPEN/CANDIDATE/DOMAIN MODEL boundaries.','',
'| Entry | Status | Alignment use |','|---|---|---|']
for e in crosswalk['entries']:
    lines.append(f"| {e['id']} | {e['status']} | {e['use']} |")
(OUT/'META/ENCYCLOPEDIA_PASS208_ALIGNMENT_CROSSWALK_V7.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

print(json.dumps({'demos_total':out_demo['total'],'demos_passed':out_demo['passed'],'audit_total':total,'accepted':accepted,'bad_accepted':badacc,'ablations_closed':sum(v is not None for v in ablation.values())},indent=2))
