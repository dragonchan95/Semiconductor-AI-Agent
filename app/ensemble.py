"""Approved soft-voting weight/threshold search using Validation only."""
import json
from pathlib import Path

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

from .catalog import TABULAR, EXTERNAL
from .data import META, load_frame, split_frame
from .experiments import fit_estimator
from .metrics import measure, meets_goals, operational_gate
from .store import digest


def weight_grid(count, units=20):
    if count not in (2,3) or units not in (10,20):
        raise ValueError('2~3개 모델과 5% 또는 10% 간격을 지원합니다')
    if count==2:
        rows=[(a/units,(units-a)/units) for a in range(units+1)]
    else:
        rows=[(a/units,b/units,(units-a-b)/units)
              for a in range(units+1) for b in range(units-a+1)]
    equal=tuple([1/count]*count)
    if not any(np.allclose(row,equal,rtol=0,atol=1e-12) for row in rows):rows.append(equal)
    return rows


def ensemble_key(metrics, policy):
    """False-positive ceiling first; maximize Recall, then F1. Recall target is a gate."""
    excess=max(0,metrics['fpr']-policy['max_fpr'])
    return (metrics['fpr']<=policy['max_fpr'],-excess,metrics['recall'],metrics['f1'],-metrics['fpr'])


def choose_ensemble_threshold(y, scores, policy):
    """Enumerate every distinct Validation decision boundary without sklearn loops."""
    y=np.asarray(y,dtype=int);scores=np.asarray(scores,dtype=float)
    if y.ndim!=1 or scores.shape!=y.shape or set(np.unique(y))!={0,1}:
        raise ValueError('정상·불량 Validation 라벨과 같은 길이의 확률이 필요합니다')
    if not np.isfinite(scores).all() or ((scores<0)|(scores>1)).any():
        raise ValueError('모델 확률은 유한한 0~1 값이어야 합니다')
    thresholds=np.unique(np.r_[scores,np.nextafter(scores.max(),np.inf)])
    predicted=scores[None,:]>=thresholds[:,None]
    positive=y==1;negative=~positive
    tp=predicted[:,positive].sum(axis=1);fp=predicted[:,negative].sum(axis=1)
    fn=positive.sum()-tp
    recall=tp/positive.sum();fpr=fp/negative.sum()
    f1=np.divide(2*tp,2*tp+fp+fn,out=np.zeros(len(tp),dtype=float),where=(2*tp+fp+fn)!=0)
    within_limit=fpr<=policy['max_fpr']
    excess=np.maximum(0,fpr-policy['max_fpr'])
    best=max(range(len(thresholds)),key=lambda i:(bool(within_limit[i]),-excess[i],recall[i],f1[i],-fpr[i],thresholds[i]))
    return measure(y,scores,float(thresholds[best]),policy)


def search_weights(y_validation, validation_scores, policy, units=20):
    """This function has no Test inputs. One-hot weights include single-model baselines."""
    scores=np.asarray(validation_scores,dtype=float)
    if scores.ndim!=2 or scores.shape[1]!=len(y_validation):
        raise ValueError('모델별 동일 Validation 행의 확률이 필요합니다')
    if not np.isfinite(scores).all() or ((scores<0)|(scores>1)).any():
        raise ValueError('잘못된 예측 확률입니다')
    rows=[]
    for i,weights in enumerate(weight_grid(len(scores),units),1):
        metrics=choose_ensemble_threshold(y_validation,np.clip(np.asarray(weights)@scores,0,1),policy)
        rows.append({'id':f'weight-{i:03d}','weights':list(weights),'validation':metrics,
                     'active_models':sum(w>0 for w in weights),'validation_feasible':meets_goals(metrics,policy)})
    def key(row):
        return (*ensemble_key(row['validation'],policy),-row['active_models'],row['validation']['threshold'],tuple(row['weights']))
    ranked=sorted(rows,key=key,reverse=True)
    singles=[r for r in ranked if r['active_models']==1]
    mixed=[r for r in ranked if r['active_models']>=2]
    equal=next(r for r in rows if np.allclose(r['weights'],1/len(scores),rtol=0,atol=1e-12))
    winner=ranked[0]
    tied=sum(ensemble_key(r['validation'],policy)==ensemble_key(winner['validation'],policy) for r in rows)
    return {'rows':rows,'ranked':ranked,'winner':winner,'best_single':singles[0],
            'best_mixed':mixed[0],'equal':equal,'tied_best_count':tied}


def probability(model,x):
    classes=list(model.classes_)
    if set(classes)!={0,1}:raise ValueError('정상0·불량1 모델만 혼합합니다')
    return model.predict_proba(x)[:,classes.index(1)]


class WeightedProbabilityModel:
    def __init__(self,models,weights,feature_names):
        self.models=models;self.weights=np.asarray(weights,dtype=float);self.feature_names=feature_names
        self.classes_=np.asarray([0,1])

    def predict_proba(self,x):
        p=np.clip(self.weights@np.asarray([probability(m,x) for m in self.models]),0,1)
        return np.column_stack([1-p,p])


def propose_ensemble(wb,source_run,grid_percent=5):
    if grid_percent not in (5,10):raise ValueError('비율 탐색 간격은 5% 또는 10%입니다')
    source=wb.store.run(source_run)
    if source['status']!='completed' or source['result'].get('ensemble'):
        raise ValueError('완료된 개별 모델 비교 결과에서 앙상블을 제안하세요')
    result=source['result'];dataset=wb.store.dataset(result['dataset']['id'])
    if dataset['modality']!='tabular':raise ValueError('현재 확률 혼합은 센서 이진 분류를 지원합니다')
    original=wb.store.proposal(source['proposal_id'])
    _,split=split_frame(load_frame(dataset))
    if digest(split)!=original['plan']['split_hash'] or dataset['sha256']!=result['dataset']['sha256']:
        raise ValueError('기존 실험과 데이터·분할이 다릅니다')
    complete=[r for r in result['trials'] if r['status']=='completed']
    scope=max(len(r['products']) for r in complete)
    products=sorted(next(r['products'] for r in complete if len(r['products'])==scope))
    available=[r for r in complete if sorted(r['products'])==products]
    best={}
    for row in available:
        code=row['model']
        if code not in TABULAR and code not in EXTERNAL:continue
        key=lambda r:(*ensemble_key(r['validation'],original['plan']['policy']),r['id'])
        if code not in best or key(row)>key(best[code]):best[code]=row
    selected=sorted(best.values(),key=lambda r:(*ensemble_key(r['validation'],original['plan']['policy']),r['model']),reverse=True)[:3]
    if len(selected)<2:raise ValueError('서로 다른 알고리즘 2개 이상의 완료 결과가 필요합니다')
    members=[{k:r[k] for k in ['id','model','products','preprocessing','balance']} for r in selected]
    units=100//grid_percent;count=len(weight_grid(len(members),units))
    plan={**original['plan'],'models':[m['model'] for m in members],'cohorts':[products],
          'target_products':original['plan']['target_products'],'trial_budget':len(members),
          'search_strategy':'weighted_soft_voting','ensemble':{
              'source_run':source_run,'source_result_hash':digest(result),'members':members,
              'grid_units':units,'grid_percent':grid_percent,'weight_count':count,
              'objective':'fpr_ceiling_then_recall_then_f1','member_selection':'Top three distinct algorithms by stored Validation Recall then F1 within FPR limit, on identical training products',
              'selection_rule':'정상 오판률 한도 준수 → Validation Recall 최대 → 동률이면 F1·정상 오판·적은 모델 순',
              'tie_rule':'동일 성능이면 적은 모델을 사용하며 단일 모델도 허용합니다.'}}
    for key in ['discovery_id','discovery_source_run','discovery_incumbent','management_source_run']:
        plan.pop(key,None)
    explanation={'data_summary':f'동일 학습 제품 {"+".join(products)}에서 정상 오판 한도 안의 Validation Recall·F1 상위 {len(members)}개 알고리즘을 선정했습니다.',
        'preprocessing_evidence':'각 모델의 전처리는 Train에서만 다시 적합합니다. 예측 확률에 비율을 곱해 합칩니다.',
        'imbalance_reason':f'{grid_percent}% 간격의 모든 합계100% 비율과 균등 비율을 포함해 {count}개를 비교합니다. 비율과 판정 기준은 Validation에서만 선택합니다.',
        'candidates':[{'title':m['model'],'model_reason':'기존 동일 학습 범위에서 정상 오판 한도 안의 Recall·F1 상위 알고리즘',
                       'preprocessing_reason':f'{m["preprocessing"]} / {m["balance"]}'} for m in members]}
    return wb.store.add_proposal(plan,{'dataset_name':dataset['name'],'synthetic':dataset['synthetic'],
        'split':split,'audit':dataset['audit'],'explanation':explanation,'agent_outputs':[],
        'reasons':[plan['ensemble']['selection_rule'],'비율 탐색에 Test는 사용하지 않습니다. 기존 Test 재사용이므로 새 독립 데이터 검증이 필요합니다.'],
        'evidence':original.get('evidence',[])+[{'id':'soft-voting','title':'Weighted soft voting','text':'각 모델의 불량 확률에 비율을 곱해 합칩니다. 합계는100%이며 평균 확률의 판정 기준도 Validation에서 선택합니다.',
                    'url':'https://scikit-learn.org/stable/modules/ensemble.html#voting-classifier'}]})


def execute_ensemble(wb,dataset,plan,artifact_dir,on_event=lambda e:None):
    spec=plan['ensemble'];source=wb.store.run(spec['source_run'])
    if source['status']!='completed' or digest(source['result'])!=spec['source_result_hash']:
        raise ValueError('승인한 원본 실험 기록이 변경됐습니다')
    df=load_frame(dataset);parts,split=split_frame(df)
    if digest(split)!=plan['split_hash']:raise ValueError('승인한 분할과 다릅니다')
    targets=plan['target_products']
    val=parts['validation'][np.isin(df.iloc[parts['validation']]['product'].astype(str),targets)]
    features=[c for c in df if c not in META];x=df[features].to_numpy(dtype=float);y=df.label.to_numpy(dtype=int)
    if set(np.unique(y[val]))!={0,1}:raise ValueError('대상 Validation에 정상·불량이 필요합니다')
    models=[];scores=[];train_sizes=[]
    with threadpool_limits(limits=1):
        for m in spec['members']:
            idx=parts['train'][np.isin(df.iloc[parts['train']]['product'].astype(str),m['products'])]
            model=fit_estimator(m['model'],m['preprocessing'],m['balance'],x[idx],y[idx])
            models.append(model);scores.append(probability(model,x[val]));train_sizes.append(len(idx))
            on_event({'type':'EnsembleMemberFitted','model':m['model']})
        search=search_weights(y[val],scores,plan['policy'],spec['grid_units'])
        selected=search['winner'];single=search['best_single'];equal=search['equal']
        # The weight/threshold decision is now frozen, before any Test predictions.
        on_event({'type':'EnsembleWeightsSelected','weights':selected['weights'],'validation_f1':selected['validation']['f1']})
        test=parts['test'][np.isin(df.iloc[parts['test']]['product'].astype(str),targets)]
        combined=WeightedProbabilityModel(models,selected['weights'],features)
        test_scores=combined.predict_proba(x[test])[:,1]
        test_metrics=measure(y[test],test_scores,selected['validation']['threshold'],plan['policy'])
        single_index=single['weights'].index(1.0)
        single_test=measure(y[test],probability(models[single_index],x[test]),single['validation']['threshold'],plan['policy'])
    members=[{**m,'train_n':n,'weight':weight} for m,n,weight in zip(spec['members'],train_sizes,selected['weights'])]
    threshold=selected['validation']['threshold']
    artifact_dir=Path(artifact_dir);artifact_dir.mkdir(parents=True,exist_ok=True)
    joblib.dump(combined,artifact_dir/'champion.joblib')
    description=' + '.join(f'{m["model"]} {100*m["weight"]:.0f}%' for m in members)
    feasible=sum(row['validation_feasible'] for row in search['rows'])
    gain=selected['validation']['f1']-single['validation']['f1']
    reason=(f'{spec["weight_count"]}개 비율 중 두 목표 충족 {feasible}개. '+spec['selection_rule']+
            f'. 선택 Validation Recall {selected["validation"]["recall"]:.1%}, F1 {selected["validation"]["f1"]:.4f}, 정상 오판률 {selected["validation"]["fpr"]:.1%}. '+
            f'최선 단일의 Recall {single["validation"]["recall"]:.1%}, F1 {single["validation"]["f1"]:.4f}. '+
            f'동일 우선 성능 비율 {search["tied_best_count"]}개. 탐색 범위 안의 최선이며 유일한 전역 최적을 뜻하지 않습니다.')
    rows=[{**row,'model':'weighted_soft_voting','products':spec['members'][0]['products'],
           'status':'completed','preprocessing':'member_train_only','balance':'member_specific',
           'explanation':{'preprocessing':'각 구성 모델의 Train 전처리'}} for row in search['rows']]
    winner=next(row for row in rows if row['id']==selected['id'])
    winner.update({'train_n':max(train_sizes),'train_defects':int(y[parts['train']].sum()),
                   'explanation':{'preprocessing':'각 모델의 Train 적합 전처리 후 예측 확률 혼합'}})
    result={'dataset':{k:dataset[k] for k in ['id','name','source','synthetic','sha256']},
        'split':split,'trials':rows,'winner':winner,'winner_id':winner['id'],
        'test':test_metrics,'baseline_test':single_test,'gate':operational_gate(test_metrics,plan['policy']),
        'selection_feasible':bool(feasible),'test_fingerprint':digest(sorted(map(int,test))),
        'test_predictions':[{'sample_index':int(i),'label':int(y[i]),'score':float(p)} for i,p in zip(test,test_scores)],
        'ensemble':{**spec,'members':members,'weights_description':description,'threshold':threshold,
            'false_positive_limit':plan['policy']['max_fpr'],'recall_goal':plan['policy']['min_recall'],
            'selection_reason':reason,'selected':selected,'best_single':single,'equal':equal,'best_mixed':search['best_mixed'],
            'best_single_model':members[single_index]['model'],'best_single_test':single_test,
            'validation_f1_gain_over_single':gain,'feasible_weight_count':feasible,
            'tied_best_count':search['tied_best_count'],'top_weights':search['ranked'][:10],
            'selected_uses_multiple_models':selected['active_models']>1,
            'selection_uses_test':False,'objective_matches_original_run':False,
            'limitations':['Best within approved member models, weight grid and Validation thresholds, not a global or production optimum.',
                'Members and weights reuse Validation; this is exploratory selection, not an independent benchmark.',
                'The existing project Test has previously been inspected. New independent-period Test data is required.',
                'Member probabilities are not separately calibrated; weight values are not feature importance or causal contributions.']},
        'explanation':{'selection_reason':reason,'preprocessing_reason':'구성 모델의 전처리는 Train에서만 적합',
            'balance_method':'각 모델의 기존 설정 유지','search_note':'Validation 가중 평균 확률·판정 기준 전수 비교',
            'source':'scikit-learn voting classifier documentation'},
        'scope_note':'가중치는 정상 오판률 한도 안에서 Validation Recall 우선·동률 F1 기준으로 선택합니다. Recall 목표는 별도 달성 여부를 표시합니다.',
        'test_note':'비율·판정 기준 선택 후 동일 Test에서 최선 단일 후보와 선택 조합만 확인. 기존 Test 재사용 탐색.'}
    if not feasible:
        result['gate']={'passed':False,'reasons':['Validation에서 두 목표를 충족한 비율 없음. 탐색 참고 결과'],
                        'auto_deploy':False,'action':'후보 재검토'}
    (artifact_dir/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    return result
