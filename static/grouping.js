async function requestGrouping(){
  proposal=await post('/api/grouping/proposals',{source_run:currentRun.id});
  renderProposal();$('#proposal-section').scrollIntoView({behavior:'smooth'});
}

function renderGroupingResult(){
  const x=currentRun.result,g=x.grouping,s=g.selected,score=n=>Number(n).toFixed(3);
  const shared=g.strategies.find(r=>r.model_count===1),separate=g.strategies.find(r=>r.model_count===g.products.length);
  const representatives=[shared,separate,s].filter((r,i,rows)=>r&&rows.findIndex(t=>t?.id===r.id)===i);
  $('#result').innerHTML=`<div id="grouping-summary"><p><strong>학습할 제품 그룹 구성 비교</strong> · ${esc(x.dataset.name)}</p>
    <h3>Validation 선택: ${esc(s.name)} · 모델 ${s.model_count}개</h3>
    <p class="explanation">${esc(name(g.algorithm))}와 전처리·불균형 설정을 고정했습니다.<br>${g.fitted_group_count}개 학습 묶음을 재사용해 ${g.evaluated_partition_count}/${g.partitions.length}개 구성을 비교했습니다.</p>
    <p>제품별 정상 오판 한도 → 모든 제품 검출 목표 → 전체 Recall·F1 → 동률이면 적은 모델 순입니다.</p>
    <div id="grouping-validation"><h3>같은 Validation에서 대표 구성 비교</h3>
    ${table(['제품 담당 그룹','모델 수','Recall','F1','정상 오판률'],representatives.map(r=>[esc(r.name),r.model_count,pct(r.validation.recall),score(r.validation.f1),pct(r.validation.fpr)]))}</div></div>
    <div id="grouping-test"><h3>선택 후 같은 Test 확인</h3>
    ${table(['제품 담당 그룹','불량 발견','정상 오판','Recall','F1'],g.tested_baselines.map(r=>[esc(r.name),`${r.test.tp}/${r.test.positive_count}`,`${r.test.fp}/${r.test.tn+r.test.fp}`,pct(r.test.recall),score(r.test.f1)]))}
    <p class="${x.gate.passed?'neutral':'warning'}"><strong>${x.gate.passed?'시연 전체 목표 충족 · 현장 검증 필요':'판단: 적용 보류 · 추가 검증 필요'}</strong><br>${x.gate.reasons.map(esc).join('<br>')}<br>Test를 보고 그룹 구성을 다시 고르지 않습니다. 기존 Test 재사용 탐색이며 양산 승인 결과가 아닙니다.</p></div>
    <details><summary>모든 ${g.partitions.length}개 그룹 구성과 점수</summary>
    ${table(['그룹 구성','모델 수','Validation Recall','F1','정상 오판률'],g.ranked.map(r=>[esc(r.name),r.model_count,pct(r.validation.recall),score(r.validation.f1),pct(r.validation.fpr)]))}
    <a href="/api/runs/${currentRun.id}/export.csv">전체 그룹 구성 CSV 내려받기</a></details>
    <details><summary>선택 구성의 제품별 검출률·오판·표본 확인</summary>
    ${table(['제품','담당 모델 학습 제품','Validation Recall','정상 오판률','Test Recall','정상 오판률','Test 불량 수'],g.products.map(p=>[esc(p),esc(s.groups.find(group=>group.includes(p)).join('+')),pct(s.per_product[p].recall),pct(s.per_product[p].fpr),pct(g.per_product_test[p].recall),pct(g.per_product_test[p].fpr),g.per_product_test[p].positive_count]))}
    <p>제품별 표본이 작으면 높은 비율도 불확실합니다. 현재 비교는 그룹 구성과 판정 기준의 탐색이며 앙상블 비율까지 동시에 최적화한 결과가 아닙니다.</p></details>
    <button id="back-to-models">개별 모델 비교 결과로 돌아가기</button>`;
  $('#back-to-models').onclick=safe(()=>watch(g.source_run));
  $('#management-features').hidden=true;$('#discovery-features').hidden=true;
}
