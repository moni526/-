import json, sys, os, urllib.request, time
from concurrent.futures import ThreadPoolExecutor
K=os.environ["SEOUL_API_KEY"]  # 서울 열린데이터광장 인증키 (환경변수로 전달)
B=f"http://openapi.seoul.go.kr:8088/{K}/json"
def get(svc,a,b,q=""):
    url=f"{B}/{svc}/{a}/{b}/{q}"
    for i in range(5):
        try:
            d=json.load(urllib.request.urlopen(url,timeout=60))
            if svc in d: return d[svc]
            if d.get("RESULT",{}).get("CODE")=="INFO-200": return {"list_total_count":0,"row":[]}
        except Exception as e: pass
        time.sleep(1+i*2)
    raise RuntimeError(url)
def pull(svc,q="",keep=None):
    fn=f"raw/{svc}_{q or 'all'}.json"
    if os.path.exists(fn): return
    n=get(svc,1,1,q)["list_total_count"]
    rng=[(i,min(i+999,n)) for i in range(1,n+1,1000)]
    with ThreadPoolExecutor(8) as ex: parts=list(ex.map(lambda r:get(svc,r[0],r[1],q)["row"],rng))
    rows=[x for p in parts for x in p]
    if keep: rows=[x for x in rows if keep(x)]
    json.dump(rows,open(fn,"w"),ensure_ascii=False); print(svc,q,n,len(rows),flush=True)
Q=["20223","20224","20231","20232","20243","20244","20251","20252","20253","20254","20261","20262"]
F=lambda x:x["SVC_INDUTY_CD"] in("CS100010","CS100005")
for q in Q: pull("VwsmTrdarSelngQq",q,F)
for q in Q: pull("VwsmTrdarFlpopQq",q)
for q in ["20232","20262","20252"]: pull("VwsmTrdarStorQq",q,F)
pull("VwsmTrdarIxQq","20262"); pull("VwsmTrdarIxQq","20232")
pull("TbgisTrdarRelm")
pull("VwsmTrdarWrcPopltnQq"); pull("VwsmTrdarRepopQq"); pull("VwsmTrdarFcltyQq")
