/* Weight search is an approved experiment; scores and ranking come from the API. */
async function requestEnsemble(){
  proposal=await post('/api/ensemble/proposals',{source_run:currentRun.id,grid_percent:5});
  renderProposal();$('#proposal-section').scrollIntoView({behavior:'smooth'});
}

function ensembleWeights(weights,members){
  return weights.map((w,i)=>`${name(members[i].model)} ${(100*w).toFixed(w===1/3?1:0)}%`).join(' + ');
}

async function renderEnsembleResult(){
  const x=currentRun.result,e=x.ensemble,s=e.selected,m=s.validation,b=e.best_single;
  const approvedPolicy=(await api(`/api/proposals/${currentRun.proposal_id}`)).plan.policy;
  const score=n=>Number(n).toFixed(3);
  const weights=r=>esc(ensembleWeights(r.weights,e.members));
  const comparison=[['최선 단일',b],['균등 혼합',e.equal],['최선 혼합',e.best_mixed]];
  $('#result').innerHTML=`<div id="ensemble-recommendation">
    <p><strong>모델 예측 확률을 섞는 앙상블</strong> · ${esc(x.dataset.name)}</p>
    <h3>${e.selected_uses_multiple_models?'추천 혼합 비율':'탐색 결론: 단일 모델 유지'}</h3>
    <div class="ensemble-weights">${e.members.map((member,i)=>`<div class="ensemble-weight"><strong>${esc(name(member.model))}</strong><span>${pct(s.weights[i])}</span><div class="ensemble-bar"><i style="width:${100*s.weights[i]}%"></i></div></div>`).join('')}</div>
    <p class="explanation">정상 오판률 ${pct(approvedPolicy.max_fpr)} 이하 → Recall 최대 → 동률이면 F1 우선<br>
    선택 Validation: Recall <strong>${pct(m.recall)}</strong> · F1 <strong>${score(m.f1)}</strong> · 정상 오판률 <strong>${pct(m.fpr)}</strong></p>
    <p>${e.grid_percent}% 간격과 균등 비율의 <strong>${e.weight_count}개 비율</strong>을 비교했습니다. 각 비율의 판정 기준도 Validation에서 골랐습니다.<br>
    동일 성능 비율 ${e.tied_best_count}개 중 ${s.active_models}개 모델을 사용하는 구성을 택했습니다. 이 범위 안의 최선이며 현장 최적을 보장하지 않습니다.</p>
    <div id="ensemble-validation"><h3>왜 이 비율인가요? 같은 Validation 비교</h3>
    ${table(['비교','비율','Recall','F1','정상 오판률'],comparison.map(([label,row])=>[label,weights(row),pct(row.validation.recall),score(row.validation.f1),pct(row.validation.fpr)]))}
    </div>${!e.selected_uses_multiple_models?'<p class="warning">이번에는 섞어도 단일 모델보다 선택 기준이 좋아지지 않아 단일 모델을 유지했습니다.</p>':''}
    </div>
    <div id="ensemble-test"><h3>비율 선택 후, 같은 Test에서 확인</h3>
    ${table(['Test 지표',`최선 단일: ${esc(name(e.best_single_model))}`,'선택한 비율'],[
      ['불량 발견 / 전체 불량',`${x.baseline_test.tp} / ${x.baseline_test.positive_count}`,`${x.test.tp} / ${x.test.positive_count}`],
      ['정상 오판 / 전체 정상',`${x.baseline_test.fp} / ${x.baseline_test.tn+x.baseline_test.fp}`,`${x.test.fp} / ${x.test.tn+x.test.fp}`],
      ['Recall',pct(x.baseline_test.recall),pct(x.test.recall)],['Precision',pct(x.baseline_test.precision),pct(x.test.precision)],
      ['F1',score(x.baseline_test.f1),score(x.test.f1)],['정상 오판률',pct(x.baseline_test.fpr),pct(x.test.fpr)]] )}
    <p class="${x.gate.passed?'neutral':'warning'}">${x.gate.passed?'설정한 시연 목표 충족 · 새 독립 데이터로 검증 필요':x.gate.reasons.map(esc).join('<br>')}<br>비율 선택에는 Test를 쓰지 않았습니다. 기존 프로젝트에서 이미 확인한 Test의 추가 탐색 결과이며 양산 승인 결과가 아닙니다.</p></div>
    <details><summary>비율별 점수와 계산 근거</summary><p>${esc(e.selection_reason)}</p>
    <p>불량 확률 = ${esc(e.weights_description)}의 가중 평균. 선택 판정 기준 ${Number(e.threshold).toFixed(5)} 이상이면 불량으로 판단합니다.</p>
    ${table(['비율','Recall','F1','정상 오판률','판정 기준'],e.top_weights.map(r=>[weights(r),pct(r.validation.recall),score(r.validation.f1),pct(r.validation.fpr),r.validation.threshold.toFixed(5)]))}
    <a href="/api/runs/${currentRun.id}/export.csv">전체 비율 비교 CSV 내려받기</a></details>
    <button id="back-to-models">개별 모델 비교 결과로 돌아가기</button>`;
  $('#back-to-models').onclick=safe(()=>watch(e.source_run));
  $('#management-features').hidden=true;$('#discovery-features').hidden=true;
}
