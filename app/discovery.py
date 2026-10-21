"""Live official-document retrieval, grounded proposals and durable candidate history.
The provider searches scikit-learn's official API index. Two reviewed local adapters
can be trained; other names remain discoverable metadata, never downloaded code.
"""
import html
import re
import uuid
from html.parser import HTMLParser
from urllib.parse import urljoin

import httpx
from .catalog import TABULAR, EXTERNAL
from .store import digest, now
from .metrics import selection_key

INDEX = 'https://scikit-learn.org/stable/api/index.html'
BASE = 'https://scikit-learn.org/stable/'


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(); self.hidden=0; self.parts=[]; self.article=False
    def handle_starttag(self, tag, attrs):
        if tag=='article': self.article=True
        if tag in {'script','style','nav'}: self.hidden+=1
        if tag in {'p','div','section','dt','dd','h1','h2','li'}: self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in {'script','style','nav'}: self.hidden=max(0,self.hidden-1)
    def handle_data(self, text):
        if self.article and not self.hidden: self.parts.append(text)


def fetch(url, client):
    # URLs come exclusively from the official index and a fixed origin/path.
    if not url.startswith(BASE) or '..' in url: raise ValueError('공식 문서 주소만 조회합니다')
    response=client.get(url, follow_redirects=False)
    response.raise_for_status()
    if len(response.content)>2_000_000: raise ValueError('문서가 너무 큽니다')
    return response.text


def discover(wb, dataset_id, question='', client=None):
    dataset=wb.store.dataset(dataset_id)
    if dataset['modality']!='tabular': raise ValueError('현재 외부 모델 실험 연결은 숫자 센서 분류를 지원합니다')
    owned=client is None
    client=client or httpx.Client(timeout=20)
    try:
        index=fetch(INDEX,client)
    except (httpx.HTTPError,ValueError) as exc:
        if owned:client.close()
        raise ValueError('공식 모델 목록을 가져오지 못했습니다. 네트워크 확인 후 다시 검색하세요') from exc
    links={urljoin(INDEX,html.unescape(x.split('#')[0])) for x in re.findall(r'href=[\"\']([^\"\']+)[\"\']',index)}
    links=sorted(x for x in links if x.startswith(BASE+'modules/generated/sklearn.') and x.endswith('.html'))
    # Only binary-classifier adapters reviewed in this repository can create models.
    found=[]; errors=[]
    for code,meta in EXTERNAL.items():
        url=meta[3]
        if url not in links: continue
        try:
            raw=fetch(url,client); parser=VisibleText();parser.feed(raw)
            text=re.sub(r'[ \t]+',' ',''.join(parser.parts))
            # Start at the actual estimator definition, past the API navigation.
            marker=meta[4]; start=text.find(marker)
            if start<0: raise ValueError('모델 정의를 확인하지 못했습니다')
            text=text[start:];end=text.find('Parameters:')
            description=text[:end] if end>0 else text[:5000]
            chunks=[description[i:i+650] for i in range(0,min(len(description),3900),500) if description[i:i+650].strip()]
            found.append({'model':code,'title':meta[0],'url':url,'chunks':chunks,'document_hash':digest(raw),'adapter':'reviewed_local','fetched_at':now()})
        except (httpx.HTTPError,ValueError) as exc: errors.append({'model':code,'error':type(exc).__name__})
    if owned:client.close()
    if not found: raise ValueError('공식 목록과 모델 본문을 확인한 새 후보가 없습니다')
    query=(question[:1500]+' binary classification numerical tabular sensor non linear class imbalance random trees gaussian conditional independence')
    chunks=[{'id':f'{d["model"]}-{i}','model':d['model'],'url':d['url'],'text':t}
            for d in found for i,t in enumerate(d['chunks'])]
    retrieved=wb.knowledge.search_documents(chunks,query,len(chunks))
    retrieval_status=dict(wb.knowledge.last_status)
    evidence=[]
    for d in found:
        matches=[c for c in retrieved if c['model']==d['model']][:2]
        if not matches: raise ValueError('모델 문서의 관련 근거를 검색하지 못했습니다')
        evidence.append({'id':'external-'+d['model'],'model':d['model'],'title':d['title'],'url':d['url'],
                         'text':'\n'.join(c['text'] for c in matches),'score':max(c['score'] for c in matches),
                         'document_hash':d['document_hash'],'fetched_at':d['fetched_at']})
    evidence.sort(key=lambda d:d['score'],reverse=True)
    audit=dataset['audit'];choices={e['model']:EXTERNAL[e['model']][2] for e in evidence}
    advice=wb.advisor.advise('ModelDiscoveryAgent',{'modality':'tabular','features':audit['features'],'missing_ratio':audit['missing_ratio'],'defect_ratio':audit['defect_ratio']},choices,evidence)
    records=[]
    for e in evidence:
        code=e['model']
        records.append({'model':code,'title':e['title'],'source':e['url'],'status':'발굴됨 · 승인 전',
            'reason':EXTERNAL[code][2], 'preprocessing':'Train 중앙값 결측 대체·상수 제거'+('·Scaling'if EXTERNAL[code][1]=='scaled'else''),
            'evidence_id':e['id'],'retrieval_score':e['score'],'adapter':'reviewed_local'})
    return wb.store.save_discovery({'id':'discovery-'+uuid.uuid4().hex[:12],'created_at':now(),
        'dataset_id':dataset_id,'dataset_sha256':dataset['sha256'],'question':question[:1500],
        'provider':'scikit-learn official API index','index_url':INDEX,'index_hash':digest(index),
        'index_api_entry_count':len(links),'models':records,'evidence':evidence,'agent':advice,'errors':errors,
        'retrieval':'official HTML chunks + '+retrieval_status['mode']+'; local LLM grounded code selection or explicit rule fallback',
        'retrieval_status':retrieval_status,
        'scope':'공식 API 목록에서 기존 교육12종 밖의 ExtraTrees·GaussianNB를 찾고 검토된 adapter로 실험. 임의 웹 모델 코드 생성·설치는 지원하지 않음',
        'privacy':'원본 센서 행·제품명·사용자 질문을 외부 서버로 전송하지 않음. 공식 문서 GET만 수행',
        'summary':'숫자 센서 이진 분류에 연결 가능한 새 후보를 공식 문서에서 찾았습니다. 문서 근거는 실험 적합성 가설이며 성능 우위를 보장하지 않습니다.'})


def propose_discovery(wb, discovery_id, source_run):
    from .planner import ProposalRequest
    d=wb.store.discovery(discovery_id);run=wb.store.run(source_run)
    if run['status']!='completed' or run['result']['dataset']['id']!=d['dataset_id']: raise ValueError('같은 데이터의 완료된 기준 실험이 필요합니다')
    source=wb.store.proposal(run['proposal_id'])['plan'];winner=run['result']['winner']
    if winner['model']not in TABULAR: raise ValueError('기존 교육 모델 실험을 기준으로 선택하세요')
    candidates=[x['model']for x in d['models']if x['model']in EXTERNAL]
    if not candidates: raise ValueError('학습에 연결 가능한 후보가 없습니다')
    return wb.propose(ProposalRequest(dataset_id=d['dataset_id'],question='공식 외부 문서 근거로 새 후보를 기존 모델과 비교',
        models=[winner['model'],*candidates],cohort_mode='all',training_products=winner['products'],
        target_products=source['target_products'],balance=['none','weighted'],preprocessing=['auto'],
        policy=source['policy'],discovery_id=discovery_id,discovery_source_run=source_run))


def register_results(wb, proposal, run_id, result):
    ident=proposal['plan'].get('discovery_id')
    if not ident:return
    d=wb.store.discovery(ident)
    rows=[]
    for code in [m['model']for m in d['models']]:
        complete=[t for t in result['trials']if t['model']==code and t['status']=='completed']
        best=max(complete,key=lambda t:(*selection_key(t['validation'],proposal['plan']['policy']),t['id'])) if complete else None
        record={'model':code,'title':EXTERNAL[code][0],'discovery_id':ident,'run_id':run_id,'dataset_id':d['dataset_id'],
            'source':EXTERNAL[code][3],'updated_at':now(),'status':('Validation 목표 충족'if best['validation_feasible']else'Validation 목표 미달')if best else'학습 실패',
            'validation':best['validation']if best else None,'selected':result['winner']['model']==code,
            'production_deployed':False,'split_hash':proposal['plan']['split_hash']}
        wb.store.update_candidate(record);rows.append(record)
    result['discovery']={'id':ident,'source_run':proposal['plan']['discovery_source_run'],'registry_updates':rows,
        'note':'기존에 확인한 Test를 재사용한 탐색 비교입니다. 독립 기간 검증 없이 현장 적용을 확정하지 않습니다.'}
