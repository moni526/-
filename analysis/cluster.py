import json,math,collections
M=json.load(open("master.json"))
tot=collections.defaultdict(float)
for o in M:
    for k in ["now_amt","base_amt","mid_amt","now_cnt","base_cnt","now_cf_amt","now_bk_amt","base_cf_amt","base_bk_amt","st_now","st_base","fl_now","fl_base","wk_now","wk_base","rp_now","rp_base"]:
        tot[k]+=o.get(k,0) or 0
g=lambda a,b:((a/b)**(1/3)-1)*100
print("서울 커피+제과 연매출(조)",round(tot["now_amt"]/1e12,2),"base",round(tot["base_amt"]/1e12,2),"CAGR",round(g(tot["now_amt"],tot["base_amt"]),1),"건수CAGR",round(g(tot["now_cnt"],tot["base_cnt"]),1))
print("커피 CAGR",round(g(tot["now_cf_amt"],tot["base_cf_amt"]),1),"제과 CAGR",round(g(tot["now_bk_amt"],tot["base_bk_amt"]),1), "커피/제과 now(억)",round(tot["now_cf_amt"]/1e8),round(tot["now_bk_amt"]/1e8))
print("점포",tot["st_base"],tot["st_now"],"유동",round(g(tot["fl_now"],tot["fl_base"]),2),"직장",round(g(tot["wk_now"],tot["wk_base"]),2),"상주",round(g(tot["rp_now"],tot["rp_base"]),2))
# quarterly seoul series
Q=["20223","20224","20231","20232","20243","20244","20251","20252","20253","20254","20261","20262"]
print("Q series(억)",[round(sum(o.get("q"+q,0) for o in M)/1e8) for q in Q])
# cluster: radius 1.0km around each district, sum metrics
def dist(a,b):return math.hypot((a["lat"]-b["lat"])*111,(a["lon"]-b["lon"])*88.2)
C=[]
for c in M:
    nb=[o for o in M if dist(c,o)<=1.0]
    s={k:sum((o.get(k) or 0) for o in nb) for k in ["now_amt","base_amt","mid_amt","now_cnt","base_cnt","st_now","st_base","fl_now","fl_base","wk_now","wk_base","rp_now","rp_base","apt_hh"]}
    if s["now_amt"]<80e8 or s["base_amt"]<=0 or s["st_now"]<20: continue
    r=dict(cd=c["cd"],nm=c["nm"],gu=c["gu"],lat=c["lat"],lon=c["lon"],n=len(nb),**s)
    r["cagr"]=g(s["now_amt"],s["base_amt"]);r["cagr_cnt"]=g(s["now_cnt"],s["base_cnt"]);r["mom"]=(s["now_amt"]/s["mid_amt"]-1)*100
    r["fl"]=g(s["fl_now"],s["fl_base"]);r["wk"]=g(s["wk_now"],s["wk_base"]);r["rp"]=g(s["rp_now"],s["rp_base"])
    r["stg"]=(s["st_now"]/s["st_base"]-1)*100 if s["st_base"] else 0;r["sps"]=s["now_amt"]/s["st_now"]/1e8
    C.append(r)
import bisect
def pr(k,rev=False):
    v=sorted(x[k] for x in C)
    for x in C: p=bisect.bisect_left(v,x[k])/(len(v)-1); x["p_"+k]=1-p if rev else p
for k in ["cagr","cagr_cnt","mom","fl","wk","rp","sps"]: pr(k)
for x in C: x["gap"]=( (x["now_amt"]/x["base_amt"]-1)*100 - x["stg"])
pr("gap")
for x in C:
    x["score"]=100*(0.20*x["p_cagr_cnt"]+0.15*x["p_cagr"]+0.10*x["p_mom"]+0.15*x["p_wk"]+0.15*x["p_rp"]+0.10*x["p_fl"]+0.10*x["p_gap"]+0.05*x["p_sps"])
C.sort(key=lambda x:-x["score"])
# greedy non-overlapping clusters (centers ≥2km apart)
pick=[]
for x in C:
    if all(dist(x,p)>2.0 for p in pick): pick.append(x)
    if len(pick)>=30: break
json.dump(dict(clusters=pick,allc=C,tot=tot),open("clusters.json","w"),ensure_ascii=False)
print(f"{'#':>2} {'점수':>4} {'중심상권':<18}{'구':<5}{'n':>3} {'매출억':>5} {'CAGR':>6} {'건수':>6} {'모멘':>6} {'유동':>5} {'직장':>5} {'상주':>5} {'점포':>4} {'점포증':>6} {'점당':>4}")
for i,x in enumerate(pick):
    print(f"{i+1:>2} {x['score']:>4.0f} {x['nm'][:16]:<18}{x['gu']:<5}{x['n']:>3} {x['now_amt']/1e8:>5.0f} {x['cagr']:>6.1f} {x['cagr_cnt']:>6.1f} {x['mom']:>6.1f} {x['fl']:>5.1f} {x['wk']:>5.1f} {x['rp']:>5.1f} {int(x['st_now']):>4} {x['stg']:>6.1f} {x['sps']:>4.1f}")
