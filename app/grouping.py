"""Approved exhaustive product partitions; fixed estimator, Validation-only choice."""
import itertools
import json
from pathlib import Path

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

from .catalog import TABULAR, EXTERNAL
from .data import META, load_frame, split_frame
from .ensemble import probability
from .experiments import fit_estimator
from .metrics import measure, operational_gate, meets_goals
from .store import digest


def partitions(products):
    """Each canonical partition covers each product exactly once. Bell(4)=15."""
    products=sorted(products)
    if len(products)!=len(set(products)) or not 1<=len(products)<=4:
        raise ValueError('서로 다른 제품1~4개가 필요합니다')
    def visit(items):
        if not items:yield [];return
        first,*rest=items
        for groups in visit(rest):
            yield [[first]]+[g[:] for g in groups]
            for i in range(len(groups)):
                yield [sorted(g+[first]) if j==i else g[:] for j,g in enumerate(groups)]
    normalized={tuple(sorted(tuple(g) for g in groups)) for groups in visit(products)}
    return [[list(g) for g in groups] for groups in sorted(normalized,key=lambda p:(len(p),p))]


def group_name(groups):return ' / '.join('+'.join(g) for g in groups)


def route_metrics(y,scores,thresholds):
    decision=np.asarray(scores)>=np.asarray(thresholds)
    m=measure(y,decision.astype(float),.5)
    # Raw probability scales/thresholds differ by route; a pooled AUC is misleading.
    m['roc_auc']=None;m['threshold']=None
    return m


def choose_group_threshold(y,scores,products,policy):
    y=np.asarray(y);scores=np.asarray(scores);products=np.asarray(products)
    if not np.isfinite(scores).all() or ((scores<0)|(scores>1)).any():raise ValueError('확률 범위 오류')
    thresholds=np.unique(np.r_[scores,np.nextafter(scores.max(),np.inf)])
    predicted=scores[None,:]>=thresholds[:,None]
    pos=y==1;neg=~pos;tp=predicted[:,pos].sum(axis=1);fp=predicted[:,neg].sum(axis=1)
    fn=pos.sum()-tp
    recall=tp/pos.sum();f1=2*tp/(2*tp+fp+fn)
    fpr=fp/neg.sum();worst_fpr=np.zeros(len(thresholds))
    for product in sorted(set(products)):
        mask=(products==product)&neg
        if not mask.any():raise ValueError('제품별 Validation 정상 표본이 필요합니다')
        worst_fpr=np.maximum(worst_fpr,predicted[:,mask].mean(axis=1))
    best=max(range(len(thresholds)),key=lambda i:(worst_fpr[i]<=policy['max_fpr'],
        -max(0,worst_fpr[i]-policy['max_fpr']),recall[i],f1[i],-fpr[i],thresholds[i]))
    return float(thresholds[best])


def partition_key(row,policy):
    per=list(row['per_product'].values());m=row['validation']
    return (all(p['fpr']<=policy['max_fpr'] for p in per),
            all(p['recall']>=policy['min_recall'] for p in per),
            m['recall'],m['f1'],min(p['recall'] for p in per),-row['model_count'],-m['fpr'],row['name'])


class ProductRoutedModel:
    """Product metadata is required: never route a plain feature array implicitly."""
    def __init__(self,groups,models,thresholds,features):
        self.groups=groups;self.models=models;self.thresholds=thresholds;self.features=features

    def predict_frame(self,frame):
        labels=frame['product'].astype(str).to_numpy()
        scores=np.empty(len(frame));limits=np.empty(len(frame));covered=np.zeros(len(frame),dtype=bool)
        for group in self.groups:
            key=tuple(group);mask=np.isin(labels,group)
            if (covered&mask).any():raise ValueError('제품 담당 그룹 중복')
            if mask.any():scores[mask]=probability(self.models[key],frame.loc[mask,self.features].to_numpy(dtype=float))
            limits[mask]=self.thresholds[key];covered|=mask
        if not covered.all():raise ValueError('등록되지 않은 제품은 별도 검증이 필요합니다')
        return scores,limits,scores>=limits


def propose_grouping(wb,source_run):
    source=wb.store.run(source_run)
    if source['status']!='completed' or source['result'].get('ensemble') or source['result'].get('grouping'):
        raise ValueError('완료된 개별 모델 비교 결과를 기준으로 요청하세요')
    result=source['result'];ds=wb.store.dataset(result['dataset']['id'])
    if ds['modality']!='tabular':raise ValueError('제품 그룹 비교는 센서 분류를 지원합니다')
    frame=load_frame(ds);parts,split=split_frame(frame);products=sorted(frame['product'].astype(str).unique())
    if len(products)<2:raise ValueError('서로 다른 제품2개 이상이 필요합니다')
    original=wb.store.proposal(source['proposal_id']);fixed=result['winner']
    if digest(split)!=original['plan']['split_hash']:raise ValueError('원본 데이터 분할 변경')
    if fixed['model'] not in TABULAR and fixed['model'] not in EXTERNAL:raise ValueError('지원하지 않는 기준 알고리즘')
    for product in products:
        val=frame.iloc[parts['validation']];val=val[val['product'].astype(str)==product]
        if val.label.nunique()!=2 or int(val.label.sum())<3:
            raise ValueError(f'{product} Validation의 정상·불량 표본을 보강해 주세요')
        test=frame.iloc[parts['test']];test=test[test['product'].astype(str)==product]
        if test.label.nunique()!=2:
            raise ValueError(f'{product} Test에 정상·불량 표본이 모두 필요합니다. 그룹 선택 전 평가 가능 여부만 확인합니다')
    configs=partitions(products)
    groups=[list(c) for n in range(1,len(products)+1) for c in itertools.combinations(products,n)]
    spec={'source_run':source_run,'source_result_hash':digest(result),'products':products,'partitions':configs,
        'training_groups':groups,'algorithm':fixed['model'],'preprocessing':fixed['preprocessing'],'balance':fixed['balance'],
        'objective':'per_product_fpr_limit_then_all_product_recall_goal_then_aggregate_recall_f1_model_count',
        'selection_rule':'제품별 정상 오판 한도 준수 → 모든 제품 검출 목표 충족 → 전체 Recall·F1 → 동률이면 적은 모델',
        'declared_test_baselines':['all_shared','all_separate']}
    plan={**original['plan'],'models':[fixed['model']],'cohorts':groups,'target_products':products,
          'trial_budget':len(groups),'search_strategy':'product_partitions','grouping':spec}
    for key in ['discovery_id','discovery_source_run','discovery_incumbent','management_source_run']:
        plan.pop(key,None)
    explanation={'data_summary':f'제품 {"·".join(products)}를 나누는 {len(configs)}개 구성을 모두 비교합니다.',
        'preprocessing_evidence':f'알고리즘과 전처리·불균형 설정을 {fixed["model"]}으로 고정하고 학습 제품 묶음만 바꿉니다.',
        'imbalance_reason':f'비어 있지 않은 학습 그룹{len(groups)}개를 한 번씩 학습해 재사용합니다. 그룹별 판정값과 구성은 Validation에서만 선택합니다.',
        'candidates':[{'title':fixed['model'],'model_reason':'학습 제품 묶음의 영향을 비교하기 위해 고정한 기준 알고리즘',
                       'preprocessing_reason':fixed['preprocessing']+' / '+fixed['balance']}]}
    return wb.store.add_proposal(plan,{'dataset_name':ds['name'],'synthetic':ds['synthetic'],'audit':ds['audit'],
        'split':split,'explanation':explanation,'agent_outputs':[],
        'reasons':[spec['selection_rule'],'선택 후 공통·전용 기준 구성과 같은 Test에서 확인합니다. 기존 Test 재사용 탐색입니다.'],
        'evidence':original.get('evidence',[])})


def execute_grouping(wb,dataset,plan,artifact_dir,on_event=lambda e:None):
    spec=plan['grouping'];source=wb.store.run(spec['source_run'])
    if source['status']!='completed' or digest(source['result'])!=spec['source_result_hash']:
        raise ValueError('승인한 원본 실험이 변경됐습니다')
    frame=load_frame(dataset);parts,split=split_frame(frame)
    if digest(split)!=plan['split_hash']:raise ValueError('승인한 분할이 변경됐습니다')
    features=[c for c in frame if c not in META];products=frame['product'].astype(str).to_numpy()
    x=frame[features].to_numpy(dtype=float);y=frame.label.to_numpy(dtype=int);val=parts['validation']
    models={};limits={};cached={};failed=[]
    with threadpool_limits(limits=1):
        for group in spec['training_groups']:
            key=tuple(group);train=parts['train'][np.isin(products[parts['train']],group)]
            idx=val[np.isin(products[val],group)]
            if len(train)<30 or y[train].sum()<4 or len(np.unique(y[train]))!=2:
                failed.append({'group':group,'reason':'Train 정상·불량 표본 부족'});continue
            model=fit_estimator(spec['algorithm'],spec['preprocessing'],spec['balance'],x[train],y[train])
            score=probability(model,x[idx]);threshold=choose_group_threshold(y[idx],score,products[idx],plan['policy'])
            models[key]=model;limits[key]=threshold;cached[key]={'indices':idx,'scores':score,'train_n':len(train)}
            on_event({'type':'ProductGroupFitted','group':group})
        rows=[]
        for i,groups in enumerate(spec['partitions'],1):
            if any(tuple(g) not in models for g in groups):continue
            scores=np.empty(len(frame));thresholds=np.empty(len(frame))
            for g in groups:
                key=tuple(g);idx=cached[key]['indices'];scores[idx]=cached[key]['scores'];thresholds[idx]=limits[key]
            per={p:measure(y[idx],scores[idx],limits[tuple(next(g for g in groups if p in g))],plan['policy'])
                 for p in spec['products'] for idx in [val[products[val]==p]]}
            m=route_metrics(y[val],scores[val],thresholds[val])
            rows.append({'id':f'partition-{i:03d}','name':group_name(groups),'groups':groups,'model_count':len(groups),
                'validation':m,'per_product':per,'validation_feasible':all(meets_goals(v,plan['policy']) for v in per.values()),
                'validation_fingerprint':digest(sorted(map(int,val)))})
        if not rows:raise ValueError('실행 가능한 제품 그룹 구성 없음')
        ranked=sorted(rows,key=lambda row:partition_key(row,plan['policy']),reverse=True);selected=ranked[0]
        on_event({'type':'ProductPartitionSelected','groups':selected['groups']})
        # Only now access Test for the frozen choice and two declared baselines.
        test=parts['test'];tested={}
        shared=next((r for r in rows if r['model_count']==1),None)
        separate=next((r for r in rows if r['model_count']==len(spec['products'])),None)
        for row in [selected,shared,separate]:
            if row is None or row['id'] in tested:continue
            keys=[tuple(g) for g in row['groups']]
            routed=ProductRoutedModel(row['groups'],{k:models[k] for k in keys},{k:limits[k] for k in keys},features)
            scores,thresholds,decisions=routed.predict_frame(frame.iloc[test].reset_index(drop=True))
            per={p:measure(y[idx],scores[mask],float(thresholds[mask][0]),plan['policy'])
                 for p in spec['products'] for mask in [products[test]==p] for idx in [test[mask]]}
            tested[row['id']]={'name':row['name'],'groups':row['groups'],'test':route_metrics(y[test],scores,thresholds),
                'per_product':per,'model_count':row['model_count']}
    chosen=tested[selected['id']];gate=operational_gate(chosen['test'],plan['policy'])
    if any(not meets_goals(m,plan['policy']) for m in chosen['per_product'].values()):
        gate['passed']=False;gate['reasons'].append('일부 제품의 Test 검출률 또는 정상 오판률이 목표 미달')
    if any(m['positive_count']<plan['policy'].get('min_test_defects',20) for m in chosen['per_product'].values()):
        gate['passed']=False;gate['reasons'].append('제품별 Test 불량 표본이 작아 추가 검증 필요')
    if not gate['passed']:gate['action']='제품별 목표·표본 재검증 전 적용 보류'
    keys=[tuple(g) for g in selected['groups']]
    routed=ProductRoutedModel(selected['groups'],{k:models[k] for k in keys},{k:limits[k] for k in keys},features)
    directory=Path(artifact_dir);directory.mkdir(parents=True,exist_ok=True);joblib.dump(routed,directory/'product-routing.joblib')
    trials=[{**row,'model':'product_routing','products':spec['products'],'status':'completed',
        'preprocessing':spec['preprocessing'],'balance':spec['balance']} for row in rows]
    winner=next(row for row in trials if row['id']==selected['id']);winner['train_n']=len(parts['train'])
    baseline=tested[shared['id']] if shared else chosen
    reason=f'{len(rows)}/{len(spec["partitions"])}개 구성을 같은 제품 Validation에서 비교. '+spec['selection_rule']+f'. 선택: {selected["name"]} ({selected["model_count"]}개 모델).'
    result={'dataset':{k:dataset[k] for k in ['id','name','source','synthetic','sha256']},'split':split,
        'winner':winner,'winner_id':winner['id'],'trials':trials,'test':chosen['test'],'baseline_test':baseline['test'],
        'selection_feasible':selected['validation_feasible'],'gate':gate,'test_fingerprint':digest(sorted(map(int,test))),
        'grouping':{**spec,'selected':selected,'strategies':rows,'ranked':ranked,'tested_baselines':list(tested.values()),
            'per_product_test':chosen['per_product'],'fitted_group_count':len(models),'failed_groups':failed,
            'evaluated_partition_count':len(rows),'selection_reason':reason,'selection_uses_test':False,
            'thresholds':{'+'.join(k):limits[k] for k in keys},
            'limitations':['Fixed algorithm and settings; not joint optimization of algorithms, groupings and ensemble weights.',
                'Repeated Validation and previously inspected project Test; new independent-period validation required.',
                'Product-level small defect counts; no production approval or performance guarantee.']},
        'explanation':{'selection_reason':reason,'preprocessing_reason':'동일 전처리·알고리즘을 각 그룹 Train에만 적합',
            'balance_method':spec['balance'],'search_note':'제품을 중복·누락 없이 나누는 모든 구성 비교','source':'제품 그룹 구성 실측'},
        'test_note':'Validation에서 그룹과 판정 기준 고정 후, 선택 구성·사전 선언한 공통/전용 기준만 Test 확인'}
    (directory/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    return result
