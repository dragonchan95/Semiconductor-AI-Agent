# 공식 문서 근거를 연결하는 RAG

5주차 `knowledge_asset_demo_faiss_bge_m3.ipynb`의 **BGE-M3 → 정규화 → FAISS IndexFlatIP → 검색 문서를 Qwen에 전달** 구조를 참고했습니다. 수업은 SentenceTransformer를 사용했고 현재 Windows는 BGE-M3를 로컬 Ollama로 실행합니다. 수업 원본 파일은 공개 저장소에 재배포하지 않습니다.

14주차 `AI캠퍼스_생성형 AI_4. Vector DB.pdf`도 확인했습니다. PDF6쪽은 BGE-M3와FAISS 기초에서 Qdrant·Hybrid·재순위화로 확장하는 흐름, 35~36쪽은 FAISS 라이브러리와 Qdrant 서버·메타데이터 기능의 차이를 설명합니다. 이번 작은 로컬 문서 묶음은 FAISS를 사용하고 서버형 DB·필터·Hybrid·재순위화 확장은 수행하지 않았습니다.

## 역할과 적용 위치

- **BGE-M3**: 문서와 질문을 의미 벡터로 변환합니다.
- **FAISS**: 정규화한 벡터에서 cosine 유사도가 높은 문서를 검색합니다. 벡터 파일과 문서·출처 JSON을 로컬 저장하고 내용·모델 설정이 바뀌면 새 인덱스를 만듭니다.
- **Qwen2.5**: 검색한 근거와 데이터 요약을 받아 허용된 후보·근거 코드를 응답합니다. 학습 수치 계산과 승인 권한은 실험 엔진에 있습니다.

내부 교육 근거14개 검색과 외부 공식 모델 문서 검색에 같은 검색기를 사용합니다. 외부 탐색은 공식 API 목록과 사전 검토한 ExtraTrees·GaussianNB 문서를 수집해 청크로 나눕니다. 관련 청크를 검색해 로컬 Qwen에 주입하고 후보 근거를 제시합니다. 이후 비교 계획과 엔지니어 승인을 거쳐 실제 모델 학습에 연결합니다.

FAISS는 로컬 벡터 인덱스 라이브러리이며 이 구현은 출처 JSON을 결합한 작은 벡터 저장소입니다. 다중 사용자·트랜잭션을 지원하는 별도 서버형 Vector DB를 운영한다고 주장하지 않습니다. 임의 웹 모델 코드를 다운로드해 실행하는 기능도 아닙니다.

## 현재 설정과 재현

프로젝트 의존성의 `faiss-cpu`를 설치하고 로컬 Ollama에서 `ollama pull bge-m3`로 모델을 준비합니다. 이 작업 노트북에는 설치·다운로드를 완료했습니다. 공개 저장소에는 모델 가중치나 개인 설정을 포함하지 않습니다.

```dotenv
SEMI_DENSE_ENABLED=1
SEMI_RETRIEVER=bge_m3_faiss
SEMI_EMBED_MODEL=bge-m3
OLLAMA_URL=http://127.0.0.1:11434
```

8GB 환경을 고려해 문서를4개씩 임베딩하고 각 요청 후 임베딩 모델을 해제합니다. 원본 센서 행과 이미지 대신 문서·질문만 로컬 임베딩 서비스에 전달합니다. 외부에는 공식 문서 GET만 수행합니다. 초기 인덱스 계산과 CPU 추론은 시간이 걸릴 수 있습니다.

`scripts/verify_vector_rag.py`는 실제 BGE-M3·FAISS 내부 검색, 공식 문서 검색, Qwen의 근거 코드 응답을 확인하며 학습을 승인하지 않습니다. [실제 기록](evaluation/vector_rag.json)은 고정 개발 질문의 결과이고 독립적인 검색 성능 평가가 아닙니다. 이전 Mac의 Qwen 임베딩·cosine 결과는 [이전 기록](evaluation/agent_integration.json)으로 보존합니다.

고정13질의에서 Hit@3는13/13, MRR@3는0.923입니다. 과거 TF-IDF의 같은 개발 질의 MRR@3는0.9615였으므로 임베딩 도입으로 검색 품질이 향상됐다고 주장하지 않습니다. 의미 검색 구조와 출처 주입이 실제 실행됐는지를 확인한 기록입니다. 외부 공식 문서4개 청크의 검색과Qwen 근거 응답도 성공했으며 모델 성능 향상 실적과는 별개입니다.

의존성·모델·임베딩 응답 실패 시 TF-IDF 대체 검색을 사용하고 `tfidf_fallback` 상태를 기록·표시합니다. TF-IDF로 대체된 실행을 의미 임베딩 성공이라고 표시하지 않습니다.

구현: [retrieval.py](../app/retrieval.py), [planner.py](../app/planner.py), [discovery.py](../app/discovery.py). 참고: [BGE-M3 모델](https://huggingface.co/BAAI/bge-m3), [Ollama BGE-M3](https://ollama.com/library/bge-m3), [FAISS 정규화와 cosine](https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances).
