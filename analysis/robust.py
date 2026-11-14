import json,math,bisect,collections
M=json.load(open("master.json"))
Q=["20223","20224","20231","20232","20243","20244","20251","20252","20253","20254","20261","20262"]
def dist(a,b):return math.hypot((a["lat"]-b["lat"])*111,(a["lon"]-b["lon"])*88.2)
g=lambda a,b:((a/b)**(1/3)-1)*100 if a and b and a>0 and b>0 else None
# district-level flags
for o in M:
    s=[o.get("q"+q,0) for q in Q]
    o["flag_cov"]= any(v==0 for v in s[:4]) and sum(s[8:])>2e8   # coverage started later
    jumps=[s[i]/s[i-1] for i in range(1,12) if s[i-1]>1e8]
    o["flag_jump"]= bool(jumps) and max(jumps)>1.6 and sum(s[8:])>8e8
    o["clean"]= not o["flag_cov"] and not o["flag_jump"]
C=[]
for c in M:
    if c["se"]=="전통시장": continue
    nb=[o for o in M if dist(c,o)<=1.0]; cl=[o for o in nb if o["clean"]]
    S=lambda key,L=nb:sum((o.get(key) or 0) for o in L)
    if S("now_amt")<60e8 or S("st_now")<25: continue
    r=dict(cd=c["cd"],nm=c["nm"],gu=c["gu"],dong=c["dong"],lat=c["lat"],lon=c["lon"],n=len(nb),sales=S("now_amt")/1e8,
      cf=g(S("now_cf_amt",cl),S("base_cf_amt",cl)),cagr=g(S("now_amt",cl),S("base_amt",cl)),cnt=g(S("now_cnt",cl),S("base_cnt",cl)),
      mom=(S("now_amt",cl)/S("mid_amt",cl)-1)*100 if S("mid_amt",cl) else 0,
      fl=g(S("fl_now"),S("fl_base")),wk=g(S("wk_now"),S("wk_base")),rp=g(S("rp_now"),S("rp_base")),
      wk_add=S("wk_now")-S("wk_base"),rp_add=S("rp_now")-S("rp_base"),wk_now=S("wk_now"),rp_now=S("rp_now"),fl_now=S("fl_now"),
      st=S("st_now"),stg=(S("st_now")/S("st_base")-1)*100 if S("st_base") else 0,sps=S("now_amt")/S("st_now")/1e8,
      flagged=[o["nm"] for o in nb if not o["clean"]],clean_share=S("now_amt",cl)/S("now_amt"))
    if None in (r["cf"],r["cnt"],r["cagr"],r["fl"],r["wk"],r["rp"]): continue
    r["mom"]=max(-20,min(20,r["mom"]))
    r["gap"]=r["cagr"]*3-r["stg"]
    C.append(r)
def pr(k):
    v=sorted(x[k] for x in C)
    for x in C: x["p_"+k]=bisect.bisect_left(v,x[k])/(len(v)-1)
for k in ["cf","cnt","mom","fl","wk","rp","wk_add","rp_add","gap","sps","cagr"]: pr(k)
for x in C:
    x["s_growth"]=0.35*x["p_cf"]+0.35*x["p_cnt"]+0.30*x["p_mom"]           # 실현 성장(카드매출)
    x["s_demand"]=0.30*x["p_wk"]+0.20*x["p_wk_add"]+0.25*x["p_rp"]+0.15*x["p_rp_add"]+0.10*x["p_fl"]   # 선행 수요
    x["s_room"]=0.6*x["p_gap"]+0.4*x["p_sps"]                               # 공급 여백
    x["score"]=round(100*(0.40*x["s_growth"]+0.40*x["s_demand"]+0.20*x["s_room"]),1)
C.sort(key=lambda x:-x["score"])
pick=[]
for x in C:
    if all(dist(x,p)>2.0 for p in pick): pick.append(x)
    if len(pick)>=25: break
for i,x in enumerate(C): x["rank"]=i+1
json.dump(dict(all=C,pick=pick),open("robust.json","w"),ensure_ascii=False)
print("clusters",len(C))
print(f"{'#':>2} {'점수':>4} {'중심':<16}{'구':<5} {'매출억':>5} {'커피':>5} {'건수':>5} {'모멘':>5} {'유동':>5} {'직장':>5} {'상주':>5} {'직장+':>6} {'상주+':>6} {'점포증':>5} {'점당':>4} 성장/수요/여백 clean")
for i,x in enumerate(pick):
    print(f"{i+1:>2} {x['score']:>4.0f} {x['nm'][:14]:<16}{x['gu']:<5} {x['sales']:>5.0f} {x['cf']:>5.1f} {x['cnt']:>5.1f} {x['mom']:>5.1f} {x['fl']:>5.1f} {x['wk']:>5.1f} {x['rp']:>5.1f} {x['wk_add']:>6.0f} {x['rp_add']:>6.0f} {x['stg']:>5.1f} {x['sps']:>4.1f} {x['s_growth']:.2f}/{x['s_demand']:.2f}/{x['s_room']:.2f} {x['clean_share']:.2f} {x['flagged'][:2]}")
