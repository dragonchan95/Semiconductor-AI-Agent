"""Install official CPU-only Ollama files and a small local Qwen for an 8GB laptop.

Reads selected files from the official release ZIP with HTTP ranges, so unused
CUDA libraries are not downloaded. Model weights stay in ignored var/.
"""
import io
import json
import os
from pathlib import Path
import subprocess
import time
import zipfile
from functools import lru_cache

import httpx

ROOT=Path(__file__).resolve().parent.parent
RUNTIME=ROOT/'var/runtime/ollama'
MODEL='qwen2.5:1.5b'


class ReleaseZip(io.RawIOBase):
    def __init__(self,client,url):
        self.client=client;self.pos=0;self.downloaded=0
        with client.stream('GET',url,headers={'Range':'bytes=0-0'}) as r:
            r.raise_for_status()
            if r.status_code!=206:raise RuntimeError('Official release server does not support range downloads.')
            self.url=str(r.url);self.size=int(r.headers['content-range'].split('/')[-1])
    def seekable(self):return True
    def readable(self):return True
    def tell(self):return self.pos
    def seek(self,offset,whence=0):
        self.pos=offset if whence==0 else self.pos+offset if whence==1 else self.size+offset
        return self.pos
    @lru_cache(maxsize=2)
    def block(self,index):
        start=index*4*1024*1024;end=min(self.size,start+4*1024*1024)-1
        with self.client.stream('GET',self.url,headers={'Range':f'bytes={start}-{end}'}) as r:
            r.raise_for_status()
            if r.status_code!=206:raise RuntimeError('Partial download was not honored.')
            data=r.read()
        if len(data)!=end-start+1:raise RuntimeError('Incomplete release download.')
        self.downloaded+=len(data)
        return data
    def read(self,n=-1):
        if n<0:n=self.size-self.pos
        n=min(n,self.size-self.pos);parts=[]
        while n>0:
            index,offset=divmod(self.pos,4*1024*1024)
            block=self.block(index);part=block[offset:offset+n]
            if not part:break
            parts.append(part);self.pos+=len(part);n-=len(part)
        return b''.join(parts)


def main():
    RUNTIME.mkdir(parents=True,exist_ok=True)
    exe=RUNTIME/'ollama.exe'
    with httpx.Client(follow_redirects=True,timeout=90) as client:
        if not exe.exists():
            release=client.get('https://api.github.com/repos/ollama/ollama/releases/latest');release.raise_for_status()
            asset=next(a for a in release.json()['assets'] if a['name']=='ollama-windows-amd64.zip')
            remote=ReleaseZip(client,asset['browser_download_url'])
            with zipfile.ZipFile(remote) as archive:
                members=[x for x in archive.infolist() if not x.is_dir() and
                    (x.filename=='ollama.exe' or x.filename.startswith('lib/ollama/')) and
                    not any(word in x.filename.lower() for word in ['cuda','vulkan','rocm','hipblas','cublas','cudnn'])]
                assert any(m.filename=='ollama.exe' for m in members)
                print('Official release',release.json()['tag_name'],'CPU files',len(members),flush=True)
                for item in members:
                    destination=(RUNTIME/item.filename).resolve()
                    assert destination.is_relative_to(RUNTIME.resolve())
                    destination.parent.mkdir(parents=True,exist_ok=True)
                    destination.write_bytes(archive.read(item))
                    print('Installed',item.filename,flush=True)
            print('Downloaded release MB',round(remote.downloaded/1e6),flush=True)
        env={**os.environ,'OLLAMA_HOST':'127.0.0.1:11434','OLLAMA_MODELS':str(ROOT/'var/qwen-models'),
             'OLLAMA_NO_CLOUD':'1','OLLAMA_MAX_LOADED_MODELS':'1','OLLAMA_NUM_PARALLEL':'1','OLLAMA_CONTEXT_LENGTH':'4096'}
        local=httpx.Client(base_url='http://127.0.0.1:11434',timeout=150,trust_env=False)
        try:ready=local.get('/api/tags').status_code==200
        except httpx.HTTPError:ready=False
        if not ready:
            log=(ROOT/'var/ollama-server.log').open('ab')
            process=subprocess.Popen([str(exe),'serve'],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
            (ROOT/'var/ollama.pid').write_text(str(process.pid),encoding='ascii')
            for _ in range(30):
                try:
                    if local.get('/api/tags').status_code==200:break
                except httpx.HTTPError:pass
                time.sleep(1)
            else:raise RuntimeError('Ollama did not start. See var/ollama-server.log.')
        tags=local.get('/api/tags').json()
        if not any(m['name']==MODEL for m in tags.get('models',[])):
            previous=-1
            with local.stream('POST','/api/pull',json={'model':MODEL,'stream':True},timeout=None) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line:continue
                    event=json.loads(line)
                    if event.get('error'):raise RuntimeError(event['error'])
                    percent=int(100*event.get('completed',0)/event['total']) if event.get('total') else None
                    if percent is not None and percent//10!=previous:
                        previous=percent//10;print('Model download',percent,'%',flush=True)
        result=local.post('/api/chat',json={'model':MODEL,'stream':False,'think':False,
            'options':{'num_ctx':4096,'num_predict':40,'temperature':0},
            'messages':[{'role':'user','content':'Reply with exactly: LOCAL_QWEN_OK'}]})
        result.raise_for_status()
        print('Local Qwen reply:',result.json()['message']['content'],flush=True)
        from dotenv import set_key
        settings=ROOT/'.env'
        set_key(settings,'SEMI_LLM_ENABLED','1')
        set_key(settings,'SEMI_LLM_MODEL',MODEL)
        set_key(settings,'SEMI_DENSE_ENABLED','0')
        set_key(settings,'SEMI_LLM_TIMEOUT','150')
        print('Configured local Qwen. Retrieval remains TF-IDF; no paid inference API.',flush=True)


if __name__=='__main__':main()
