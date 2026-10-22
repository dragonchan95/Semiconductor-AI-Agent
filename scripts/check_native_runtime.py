"""Native FAISS / 12 classifiers / Torch coexistence smoke check.\nRun: LANGSMITH_TRACING=false .venv/bin/python -m scripts.check_native_runtime\nEmbeddings are deterministic mocked vectors; this does not evaluate LLM/RAG quality."""
import app
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import faiss
from sklearn.datasets import make_classification
from app.experiments import fit_estimator
from app.catalog import TABULAR
from app.retrieval import FaissRetriever
import httpx,json

def embed(request):
    rows=json.loads(request.content)['input']
    return httpx.Response(200,json={'embeddings':[[1.,0.,1.,0.] for _ in rows]})
retriever=FaissRetriever(client=httpx.Client(transport=httpx.MockTransport(embed)))
x,y=make_classification(n_samples=180,n_features=8,n_informative=5,random_state=45)
def run():
    for repeat in range(3):
        retriever.search([{'id':'a','text':'sensor test'}],'sensor')
        for name in TABULAR:
            model=fit_estimator(name,'scaled','none',x,y)
            assert np.isfinite(model.predict_proba(x[:10])).all()
        print('RAG + all12 models cycle',repeat+1,flush=True)
    import torch
    torch.set_num_threads(1)
    net=torch.nn.Linear(8,1)
    net(torch.from_numpy(x[:8].astype('float32'))).sum().backward()
    retriever.search([{'id':'a','text':'sensor test'}],'sensor')
    print('Torch + FAISS passed',flush=True)
with ThreadPoolExecutor(max_workers=1) as executor:executor.submit(run).result()
print('native smoke finished normally',flush=True)
