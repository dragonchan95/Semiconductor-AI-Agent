"""Read/propose MCP tools. Engineer approval is deliberately not an AI tool."""
from fastmcp import FastMCP
from app.config import STATE_DIR
from app.workbench import Workbench
from app.catalog import TABULAR, IMAGE, pipeline_reason

workbench = Workbench(STATE_DIR)
mcp = FastMCP("semiconductor-experiment-copilot")


@mcp.tool()
def list_datasets() -> list[dict]:
    """등록된 데이터 품질 및 제품 범위를 확인합니다."""
    return [{k: v for k, v in d.items() if k != "path"} for d in workbench.store.datasets()]


@mcp.tool()
def propose_experiment(dataset_id: str, question: str, cohort_mode: str = "all") -> dict:
    """근거와 승인 대기 계획을 만듭니다. 학습 실행이나 승인은 하지 않습니다."""
    return workbench.propose({"dataset_id": dataset_id, "question": question, "cohort_mode": cohort_mode})


@mcp.tool()
def get_experiment_result(run_id: str) -> dict:
    """엔지니어가 승인한 분석의 실측 결과를 조회합니다."""
    return workbench.store.run(run_id)


@mcp.tool()
def explain_model_candidates(modality: str = 'tabular') -> list[dict]:
    """데이터 종류에 맞는 교육 모델과 실제 전처리·선정 근거를 조회합니다."""
    if modality not in {'tabular', 'image'}:
        raise ValueError('센서 tabular 또는 image만 실제 학습 지원')
    return [pipeline_reason(n, 'gray' if modality == 'image' else 'auto') for n in (IMAGE if modality == 'image' else TABULAR)]


@mcp.resource("semiconductor://knowledge/{topic}")
def get_knowledge(topic: str) -> str:
    """검증·전처리·제품 범위 비교에 관한 근거 문서를 조회합니다."""
    doc = next((d for d in workbench.knowledge.docs if d["id"] == topic), None)
    if doc is None:
        raise ValueError("등록되지 않은 지식 문서입니다")
    return f"# {doc['title']}\n{doc['text']}\nSource: {doc['source']}\n{doc.get('url') or ''}"


if __name__ == "__main__":
    mcp.run(show_banner=False)
