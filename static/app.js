const $=s=>document.querySelector(s);
let datasets=[], selected=null, proposal=null, polling=null;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct=v=>v==null?'—':(v*100).toFixed(1)+'%';
const num=v=>v==null?'—':Number(v).toLocaleString('ko-KR',{maximumFractionDigits:0});
async function api(path,options={}){
  const headers={...(options.body instanceof FormData?{}:{'Content-Type':'application/json'}),...(options.headers||{})};
  if($('#token').value)headers['X-Engineer-Token']=$('#token').value;
  const r=await fetch(path,{...options,headers});
  let body;try{body=await r.json()}catch{throw Error('서버 응답을 읽지 못했습니다')}
  if(!r.ok)throw Error(typeof body.detail==='string'?body.detail:JSON.stringify(body.detail||body));
  return body;
}
function notify(message){$('#notice').textContent=message;setTimeout(()=>$('#notice').textContent='',9000)}
async function refresh(){
  datasets=await api('/api/datasets');
  if(!selected&&datasets.length)selected=datasets.find(d=>d.synthetic&&d.modality==='tabular')?.id||datasets[0].id;
  $('#datasets').innerHTML=datasets.map(d=>`<button class="dataset ${selected===d.id?'selected':''}" data-dataset="${esc(d.id)}"><span class="type ${d.synthetic?'synthetic':''}">${d.synthetic?'합성 데모':'공개 / 업로드 데이터'} · ${d.modality==='image'?'이미지':'공정 센서'}</span><h3>${esc(d.name)}</h3><p class="numbers">${num(d.audit.rows)} <small>samples</small></p><p>불량 ${num(d.audit.defects)}개 (${pct(d.audit.defect_ratio)}) · 제품 ${Object.keys(d.audit.products).length}개</p></button>`).join('');
  document.querySelectorAll('[data-dataset]').forEach(el=>el.onclick=()=>{selected=el.dataset.dataset;refresh().catch(e=>notify(e.message))});
  const d=datasets.find(d=>d.id===selected);
  if(d){
    const old=$('#target').value;
    $('#target').innerHTML='<option value="all">전체 제품 (모든 후보에 동일)</option>'+Object.keys(d.audit.products).map(p=>`<option value="${esc(p)}">${esc(p)} 제품만 평가</option>`).join('');
    if([...$('#target').options].some(x=>x.value===old))$('#target').value=old;
    $('#model-hint').textContent=d.modality==='image'?'비교 모델: ResNetSmall, VGGSmall, 정상 전용 Autoencoder. 전체 부분집합은 gray 전처리, 통합 학습은 gray·contrast를 비교합니다.':'비교 모델: Logistic Regression, Extra Trees. 단일 제품은 HistGradientBoosting도 비교합니다. none·class-weight 불균형 정책을 비교합니다.';
  }
  const history=await api('/api/runs');
  $('#history').innerHTML=history.length?history.map(r=>`<div class="history-row"><span>${esc(r.id)} · ${esc(r.status)}</span><button data-run="${esc(r.id)}">결과 보기</button></div>`).join(''):'<p class="hint">승인 후 실행한 분석이 여기에 기록됩니다.</p>';
  document.querySelectorAll('[data-run]').forEach(el=>el.onclick=()=>watch(el.dataset.run));
}
$('#examples').onclick=async()=>{const b=$('#examples');b.disabled=true;try{await api('/api/examples',{method:'POST'});await refresh();notify('공개 SECOM과 합성 공정·이미지 데모를 준비했습니다. 데이터 출처를 확인해 선택하세요.')}catch(e){notify(e.message)}finally{b.disabled=false}};
$('#upload').onchange=async()=>{if(!$('#upload').files[0])return;try{const body=new FormData();body.append('file',$('#upload').files[0]);const d=await api('/api/datasets',{method:'POST',body});selected=d.id;await refresh();notify('등록 전 품질 검사를 통과했습니다.')}catch(e){notify(e.message)}finally{$('#upload').value=''}};
$('#token').onchange=()=>refresh().catch(e=>notify(e.message));
$('#proposal-form').onsubmit=async e=>{
  e.preventDefault();if(!selected)return notify('데이터를 먼저 준비하고 선택하세요.');
  const b=e.submitter;b.disabled=true;
  try{
    proposal=await api('/api/proposals',{method:'POST',body:JSON.stringify({dataset_id:selected,question:$('#question').value,cohort_mode:$('#cohorts').value,target_products:$('#target').value==='all'?null:[$('#target').value],policy:{min_precision:Number($('#precision').value),max_fpr:Number($('#fpr').value),miss_cost:Number($('#miss-cost').value),false_alarm_cost:Number($('#false-cost').value)}})});
    renderProposal();$('#proposal-section').scrollIntoView({behavior:'smooth'});
  }catch(e){notify(e.message)}finally{b.disabled=false}
};
function renderProposal(){
  const p=proposal;$('#proposal-section').hidden=false;
  $('#approve').disabled=p.status!=='awaiting_approval';$('#reject').disabled=p.status!=='awaiting_approval';
  $('#proposal').innerHTML=`<h3>${esc(p.dataset_name)} ${p.synthetic?'(합성 데모)':''}</h3><p>${p.status==='awaiting_approval'?'승인 대기':p.status==='rejected'?'반려':'승인 완료'} · 최대 <strong>${p.plan.trial_budget}개</strong> 실험 · 평가 제품 <strong>${p.plan.target_products.map(esc).join(', ')}</strong></p><ul>${p.reasons.map(x=>`<li>${esc(x)}</li>`).join('')}</ul><details><summary>학습 범위와 데이터 분할</summary><p>${p.plan.cohorts.map(c=>esc(c.join('+'))).join(' / ')}</p><p>${esc(p.plan.models.join(', '))}</p><pre>${esc(JSON.stringify(p.split,null,2))}</pre></details><h3>제안 근거</h3>${p.evidence.map(d=>`<div class="evidence"><h4>${esc(d.title)}</h4><p>${esc(d.text)}</p><p>${d.url?`<a target="_blank" rel="noopener" href="${esc(d.url)}">${esc(d.source)}</a>`:esc(d.source)}</p></div>`).join('')}<p class="meta">승인할 계획 SHA-256: ${esc(p.plan_hash)}</p>`;
}
async function decision(accepted){
  if(!proposal)return;$('#approve').disabled=true;$('#reject').disabled=true;
  try{const r=await api(`/api/proposals/${proposal.id}/decision`,{method:'POST',body:JSON.stringify({accepted,engineer:$('#engineer').value,plan_hash:proposal.plan_hash})});proposal=r.proposal;renderProposal();if(r.run_id)watch(r.run_id);else notify('계획을 반려했습니다. 학습은 실행하지 않았습니다.')}catch(e){notify(e.message);$('#approve').disabled=false;$('#reject').disabled=false}
}
$('#approve').onclick=()=>decision(true);$('#reject').onclick=()=>decision(false);
async function watch(id){
  if(polling)clearInterval(polling);$('#result-section').hidden=false;$('#result').innerHTML='';$('#progress').textContent='승인한 실험을 실행 중입니다. 동일 계획의 중복 실행은 차단합니다.';$('#result-section').scrollIntoView({behavior:'smooth'});
  const tick=async()=>{try{const r=await api(`/api/runs/${id}`);if(r.status==='completed'){clearInterval(polling);polling=null;$('#progress').textContent=`완료 · ${id}`;renderResult(r);refresh()}else if(r.status==='failed'){clearInterval(polling);polling=null;$('#progress').textContent='실행 중단';$('#result').innerHTML=`<div class="warning">${esc(r.result.error)}</div>`;refresh()}}catch(e){clearInterval(polling);notify(e.message)}};
  await tick();if(!$('#result').innerHTML)polling=setInterval(tick,1200);
}
function renderResult(r){
 const x=r.result,t=x.test,b=x.baseline_test,w=x.winner;
 const comparison=[['불량 Recall',pct(b.recall),pct(t.recall)],['Precision',pct(b.precision),pct(t.precision)],['정상 오탐률',pct(b.fpr),pct(t.fpr)],['Average Precision',Number(b.average_precision).toFixed(3),Number(t.average_precision).toFixed(3)],['미탐 / 오탐',`${b.fn} / ${b.fp}`,`${t.fn} / ${t.fp}`],['1만 건당 손실 가정 (원)',num(b.assumed_cost_per_10000),num(t.assumed_cost_per_10000)]];
 $('#result').innerHTML=`<p>${esc(x.dataset.name)} · ${x.dataset.synthetic?'합성 데이터':'공개 / 업로드 데이터'} · 최종 test ${t.n}개 / 불량 ${t.positive_count}개</p><div class="${x.gate.passed?'neutral':'warning'}"><strong>${esc(x.gate.action)}</strong>${x.gate.reasons.length?'<br>'+x.gate.reasons.map(esc).join(' · '):''}<br>운영 배포는 자동 실행하지 않습니다.</div><div class="summary"><div class="metric"><span>불량 Recall</span><strong>${pct(t.recall)}</strong></div><div class="metric"><span>정상 오탐률</span><strong>${pct(t.fpr)}</strong></div><div class="metric"><span>Recall 95% Wilson 구간</span><strong>${pct(t.recall_wilson95[0])}–${pct(t.recall_wilson95[1])}</strong></div><div class="metric"><span>실행 시간</span><strong>${x.elapsed_seconds.toFixed(1)}초</strong></div></div><h3>선택 결과</h3><p>${esc(w.model)} · 학습 ${esc(w.products.join('+'))} · ${esc(w.preprocessing)} · ${esc(w.balance)} · threshold ${t.threshold.toFixed(4)}</p><p class="hint">후보 선택은 validation 기준입니다. 아래 test 수치는 선택 후에만 계산했습니다. ${esc(x.architecture_note||'')}</p><h3>같은 test 표본의 Before / After</h3><div class="table-wrap"><table><thead><tr><th>지표</th><th>사전 정의 baseline</th><th>선택한 분석 절차</th></tr></thead><tbody>${comparison.map(v=>'<tr>'+v.map(c=>`<td>${esc(c)}</td>`).join('')+'</tr>').join('')}</tbody></table></div><p class="hint">${esc(x.economic_note)}</p><h3>Validation 실험 비교</h3><p class="hint">여러 번 실험할수록 validation 과적합 위험이 있습니다. test 결과를 보고 모델을 다시 고르지 마세요.</p><div class="table-wrap"><table><thead><tr><th>후보</th><th>모델</th><th>학습 제품</th><th>전처리</th><th>불균형 정책</th><th>Recall</th><th>Precision</th><th>AP</th><th>상태</th></tr></thead><tbody>${x.trials.map(row=>`<tr><td>${esc(row.id)}</td><td>${esc(row.model)}</td><td>${esc((row.products||[]).join('+'))}</td><td>${esc(row.preprocessing)}</td><td>${esc(row.balance)}</td><td>${pct(row.validation?.recall)}</td><td>${pct(row.validation?.precision)}</td><td>${row.validation?row.validation.average_precision.toFixed(3):'—'}</td><td>${esc(row.status)}</td></tr>`).join('')}</tbody></table></div><a href="/api/runs/${esc(r.id)}/export.csv" id="export-results">검증 비교표 CSV 다운로드</a><details><summary>원본 결과 JSON과 데이터 분할</summary><pre>${esc(JSON.stringify(x,null,2))}</pre></details>`;
 $('#export-results').onclick=async e=>{e.preventDefault();try{const headers={};if($('#token').value)headers['X-Engineer-Token']=$('#token').value;const resp=await fetch(e.target.href,{headers});if(!resp.ok)throw Error('CSV 다운로드 실패');const url=URL.createObjectURL(await resp.blob());const a=document.createElement('a');a.href=url;a.download=`${r.id}.csv`;a.click();URL.revokeObjectURL(url)}catch(err){notify(err.message)}};
}
refresh().catch(e=>notify(e.message));
