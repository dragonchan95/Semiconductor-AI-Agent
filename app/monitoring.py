"""Labeled batch review and automatically prepared per-product training plans.
Only the new batch's train partition informs retraining advice. Its held-out
test is reserved for the approved training experiment. Advice is heuristic.
"""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from .data import load_frame, split_frame, META
from .metrics import measure, operational_gate, meets_goals, selection_key
from .store import digest


def prepare_changed_demo(wb):
    name = '새로 수집된 공정 데이터 (변화 합성 데모)'
    found = next((d for d in wb.store.datasets() if d['name'] == name), None)
    if found:
        return found
    rng = np.random.default_rng(1045)
    records = []
    for lot in range(480):
        product = 'ABCD'[lot % 4]
        for j in range(8):
            x = rng.normal(size=8)
            # Changed defect mechanism, not measurements from a factory.
            label = int(x[4]+.7*x[5]+.45*x[2]**2+rng.normal(0,.4) > 1.5)
            x[3] += (lot % 4)*.8
            records.append({'sample_id': f'new-{lot}-{j}', 'product': product,
                'lot_id': f'new-lot-{lot}', 'timestamp': f'2026-02-{1+lot//20:02d}',
                'label': label, **{f'sensor_{i}': float(v) for i,v in enumerate(x)}})
    path = wb.directory / 'examples/changed/process.csv'
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_csv(path,index=False)
    return wb.register(path,name,'독립 seed 1045, 결함 발생 규칙을 바꾼 합성 후속 배치. 실제 생산 데이터 아님.',True)


def assess(wb, source_run, dataset_id):
    run = wb.store.run(source_run)
    if run['status'] != 'completed':
        raise ValueError('완료된 공정 모델을 선택하세요')
    result = run['result']
    old_ds = wb.store.dataset(result['dataset']['id'])
    new_ds = wb.store.dataset(dataset_id)
    if old_ds['modality'] != 'tabular' or new_ds['modality'] != 'tabular':
        raise ValueError('이번 재학습 점검은 공정 센서 모델을 지원합니다')
    old, new = load_frame(old_ds), load_frame(new_ds)
    features = [c for c in old if c not in META]
    if set(features) != set(c for c in new if c not in META):
        raise ValueError('기존 모델과 새 데이터의 센서 열이 같아야 합니다')
    old_hash = pd.util.hash_pandas_object(old[features], index=False)
    new_hash = pd.util.hash_pandas_object(new[features], index=False)
    if new_hash.isin(set(old_hash)).any():
        raise ValueError('이전 데이터와 중복된 표본이 있습니다. 독립적인 새 배치를 등록하세요')
    parts, split = split_frame(new)
    idx = parts['train']
    checked = new.iloc[idx]
    policy = wb.store.proposal(run['proposal_id'])['plan']['policy']
    model = joblib.load(wb.directory / 'runs' / source_run / 'champion.joblib')
    scores = model.predict_proba(checked[features].to_numpy(dtype=float))[:,1]
    m = measure(checked.label.to_numpy(), scores, result['test']['threshold'], policy)
    # Compare an unchanged model + threshold on the SAME product. A product
    # omitted from the training cohort may still have been an evaluation target.
    parts_old,_=split_frame(old)
    target_products=wb.store.proposal(run['proposal_id'])['plan']['target_products']
    same_product=[]
    reasons=[]
    for product in sorted(set(checked['product'].astype(str)) & set(target_products)):
        old_rows=old.iloc[parts_old['test']]
        old_rows=old_rows[old_rows['product'].astype(str)==product]
        new_rows=checked[checked['product'].astype(str)==product]
        before=measure(old_rows.label,model.predict_proba(old_rows[features].to_numpy(dtype=float))[:,1],result['test']['threshold'])
        after=measure(new_rows.label,model.predict_proba(new_rows[features].to_numpy(dtype=float))[:,1],result['test']['threshold'])
        sufficient=after['positive_count']>=20
        needs=sufficient and (not meets_goals(after,policy) or after['recall']<before['recall']-.10)
        same_product.append({'product':product,'previous':before,'current':after,
            'needs_retraining':needs,'previous_small_sample':before['positive_count']<20,
            'status':'재학습 비교 제안' if needs else '표본 보강' if not sufficient else '유지 관찰'})
        if needs:
            reasons.append(f"{product}: 기존 모델의 새 데이터 불량 검출률 {after['recall']:.1%}, 정상 오판률 {after['fpr']:.1%}. 데모 목표 미달 또는 검출률 10%p 하락")
    unseen = set(new['product'].astype(str))-set(target_products)
    if unseen:
        reasons.append('기존 평가 대상에 없던 새 제품: '+', '.join(sorted(unseen))+' — 새 제품 모델 검증을 별도로 진행')
    verdict = '재학습 필요' if any(r['needs_retraining'] for r in same_product) else '판단 보류' if not same_product or all(r['current']['positive_count']<20 for r in same_product) else '현재 모델 유지'
    return wb.store.save_review({'source_run':source_run,'dataset_id':dataset_id,
        'dataset_name':new_ds['name'],'dataset_sha256':new_ds['sha256'],
        'synthetic':new_ds['synthetic'], 'verdict':verdict,'reasons':reasons,
        'previous_recall':result['test']['recall'],'current':m,'split':split,'same_product':same_product,
        'source_model':result['winner']['model'],'new_products':sorted(unseen),
        'products':sorted(new['product'].astype(str).unique()),
        'note':'같은 제품·같은 모델·같은 판정 경계값으로 새 배치의 학습 구간을 점검. 10%p 하락·불량 20개는 교육용 점검 규칙이며 회사 기준·통계적 확증이 아님. 과거 제품별 표본이 작으면 하락 폭도 탐색적 해석. 새 Validation/Test는 점검에 사용하지 않음.'})


def product_plans(wb, review_id):
    review = wb.store.review(review_id)
    if review['verdict'] != '재학습 필요':
        raise ValueError('재학습 필요 판정을 받은 점검에서만 계획을 생성합니다')
    ds = wb.store.dataset(review['dataset_id'])
    if ds['sha256'] != review['dataset_sha256']:
        raise ValueError('점검한 데이터 버전이 변경됐습니다')
    df = load_frame(ds)
    parts, _ = split_frame(df)
    policy = wb.store.proposal(wb.store.run(review['source_run'])['proposal_id'])['plan']['policy']
    source=wb.store.run(review['source_run'])['result']['winner']
    plans = [wb.propose({'dataset_id':ds['id'],'question':'모든 제품을 합친 공통 모델과 제품별 전용 모델을 비교해줘',
        'target_products':review['products'],'training_products':review['products'],'cohort_mode':'all',
        'models':[source['model']],'preprocessing':[source['preprocessing']],'balance':['none','weighted'],
        'policy':policy,'management_source_run':review['source_run']})]
    skipped = []
    for product in review['products']:
        enough = all(int(df.iloc[idx].loc[df.iloc[idx]['product'].astype(str)==product,'label'].sum())>=3
                     and df.iloc[idx].loc[df.iloc[idx]['product'].astype(str)==product,'label'].nunique()==2
                     for idx in parts.values())
        if not enough:
            skipped.append({'product':product,'reason':'제품별 구간에 정상·불량 표본 부족'})
            continue
        plans.append(wb.propose({'dataset_id':ds['id'],'question':f'{product} 제품 재학습 후보를 생성해줘',
            'target_products':[product],'training_products':[product],'cohort_mode':'all',
            'models':[source['model']],'preprocessing':[source['preprocessing']],'balance':['none','weighted'],
            'management_source_run':review['source_run'],'policy':policy}))
    return {'proposals':plans,'skipped':skipped,'note':'기존과 같은 알고리즘을 사용해 여러 제품을 합쳐 재학습할지, 제품마다 따로 재학습할지 비교하는 계획입니다. 승인 전에는 학습하지 않습니다.'}


def select_strategy(candidates, policy):
    """Select on validation only. Held-out test never participates in ranking."""
    feasible = [c for c in candidates if meets_goals(c['validation'],policy)]
    selected=max(candidates,key=lambda c:(*selection_key(c['validation'],policy),c['strategy']=='shared'))
    return selected['strategy'], bool(feasible)


def compare_strategies(wb, run_ids):
    if len(run_ids) < 2 or len(run_ids) != len(set(run_ids)):
        raise ValueError('서로 다른 공통·제품별 완료 실행이 필요합니다')
    runs = [wb.store.run(r) for r in run_ids]
    if any(r['status'] != 'completed' for r in runs):
        raise ValueError('모든 비교 학습이 완료되어야 합니다')
    plans = [wb.store.proposal(r['proposal_id'])['plan'] for r in runs]
    reference = plans[0]
    keys = ['dataset_id','dataset_sha256','split_hash','policy','management_source_run']
    if not reference.get('management_source_run') or any(
        any(p[k] != reference[k] for k in keys) for p in plans):
        raise ValueError('동일한 데이터·분할·기준·관리 원본의 실행만 비교합니다')
    ds = wb.store.dataset(reference['dataset_id'])
    df = load_frame(ds)
    products = sorted(df['product'].astype(str).unique())
    pooled = [r for r,p in zip(runs,plans) if p['cohorts']==[products] and sorted(p['target_products'])==products]
    separate = {}
    for r,p in zip(runs,plans):
        if len(p['target_products'])==1 and p['cohorts']==[p['target_products']]:
            product=p['target_products'][0]
            if product in separate:
                raise ValueError('제품별 후보가 중복되었습니다')
            separate[product]=r
    if len(pooled)!=1 or not separate or len(runs)!=len(separate)+1:
        raise ValueError('공통 모델 1개와 서로 다른 제품별 후보를 선택하세요')
    parts,_=split_frame(df)
    features=[c for c in df if c not in META]
    x=df[features].to_numpy(dtype=float)
    policy=reference['policy']
    rows=[]
    for product, individual in sorted(separate.items()):
        candidates=[]
        for strategy,record in [('shared',pooled[0]),('separate',individual)]:
            result=record['result']
            model=joblib.load(wb.directory/'runs'/record['id']/'champion.joblib')
            metrics={}
            fingerprints={}
            for split in ['validation','test']:
                idx=parts[split][df.iloc[parts[split]]['product'].astype(str).to_numpy()==product]
                metrics[split]=measure(df.iloc[idx].label.to_numpy(),model.predict_proba(x[idx])[:,1],result['test']['threshold'],policy)
                fingerprints[split]=digest(sorted(map(int,idx)))
            candidates.append({'strategy':strategy,'run_id':record['id'],'model':result['winner']['model'],
                'selection_feasible':result['selection_feasible'],**metrics,'fingerprints':fingerprints})
        chosen,feasible=select_strategy(candidates,policy)
        selected=next(c for c in candidates if c['strategy']==chosen)
        gate=operational_gate(selected['test'],policy)
        allowed=feasible and gate['passed']
        rows.append({'product':product,'candidates':candidates,'selected_strategy':chosen,
            'validation_feasible':feasible,'test_gate':gate,
            'recommendation':('여러 제품을 합쳐 학습한 후보' if chosen=='shared' else '이 제품만 학습한 후보') if allowed else '추가 데이터로 재확인 필요',
            'reason':('같은 제품 Validation에서 데모 목표 충족 여부, 불량 검출률, 정상 오판률 순으로 비교. 완전 동률은 관리할 모델 수가 적은 합친 학습을 선택. ' if feasible else
                       '같은 제품 Validation에서 두 방식 모두 데모 목표 미달. 참고 후보만 표시. ')+
                      ('Test 데모 목표도 충족. 회사 적용 승인은 별개.' if allowed else 'Test 목표 또는 표본 수 부족. 회사 적용 승인은 별개.'),
            'selected_run':selected['run_id']})
    frozen=wb.store.run(reference['management_source_run'])['result']
    frozen_model=joblib.load(wb.directory/'runs'/reference['management_source_run']/'champion.joblib')
    held=parts['test']
    pooled_result=pooled[0]['result']
    old_on_new=measure(df.iloc[held].label,frozen_model.predict_proba(x[held])[:,1],frozen['test']['threshold'])
    output={'dataset_id':ds['id'],'dataset_sha256':ds['sha256'],'run_ids':run_ids,'products':rows,
        'source_run':reference['management_source_run'],
        'same_model_retraining':{'model':frozen['winner']['model'],'before':old_on_new,'after':pooled_result['test'],
            'test_fingerprint':digest(sorted(map(int,held))),
            'note':'기존 모델과 같은 알고리즘을 새 학습 데이터로 다시 학습한 모델을 새 배치의 동일 Test에서 비교. Test는 재학습 필요 판단·후보 선택에 사용하지 않음.'},
        'policy':policy,'selection_basis':'같은 제품의 validation으로 방식 선택. test는 순위 선택에 사용하지 않고 최종 확인과 보류에만 사용.',
        'training_scope':'새로 등록한 한 배치의 여러 제품을 합친 학습과 제품별 학습 비교. 과거 배치 파일을 자동 병합하지 않음.',
        'note':'단일 합성 배치의 결과. 제품별 우월성을 일반화할 수 없고 반복 validation 비교의 낙관 편향 가능. 자동 배포 없음.'}
    return wb.store.save_comparison(output)
