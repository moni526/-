import json,math,statistics as S
M=json.load(open("master.json"))
def g(a,b,yrs=3):
    return (a/b)**(1/yrs)-1 if a and b and a>0 and b>0 else None
rows=[]
for o in M:
    if not o.get("now_amt") or not o.get("base_amt"): continue
    o["sales_now"]=o["now_amt"]; o["cagr_amt"]=g(o["now_amt"],o["base_amt"]); o["cagr_cnt"]=g(o["now_cnt"],o["base_cnt"])
    o["mom"]=o["now_amt"]/o["mid_amt"]-1 if o.get("mid_amt") else None
    o["fl_g"]=g(o.get("fl_now"),o.get("fl_base"))
    o["wk_g"]=g(o.get("wk_now"),o.get("wk_base")); o["rp_g"]=g(o.get("rp_now"),o.get("rp_base"))
    o["st_g"]=(o.get("st_now",0)-o.get("st_base",0))
    o["sps"]=o["now_amt"]/o["st_now"] if o.get("st_now") else None
    o["sales_per_fl"]=o["now_amt"]/o["fl_now"] if o.get("fl_now") else None
    rows.append(o)
print("rows",len(rows))
amts=sorted(r["sales_now"] for r in rows); print("annual sales pct (억)",[round(amts[int(len(amts)*p)]/1e8,1) for p in (.25,.5,.75,.9)])
# scale filter: annual coffee+bakery ≥ 20억, stores ≥ 5
U=[r for r in rows if r["sales_now"]>=20e8 and r.get("st_now",0)>=5 and r["cagr_amt"] is not None]
print("universe",len(U))
def pr(key,lst,rev=False):
    v=sorted(x[key] for x in lst if x.get(key) is not None)
    for x in lst:
        if x.get(key) is None: x["p_"+key]=0.5; continue
        import bisect; p=bisect.bisect_left(v,x[key])/max(1,len(v)-1); x["p_"+key]=1-p if rev else p
for k in ["cagr_amt","cagr_cnt","mom","fl_g","wk_g","rp_g","sps","sales_now"]: pr(k,U)
med_sps=S.median(x["sps"] for x in U if x.get("sps"))
for x in U:
    # demand-supply gap: sales growth vs store growth
    sg=(x.get("st_now",0)/x["st_base"]-1) if x.get("st_base") else 0
    x["gap"]=(x["now_amt"]/x["base_amt"]-1)-sg
pr("gap",U)
IX={"상권확장":1.0,"다이나믹":0.75,"정체":0.4,"상권축소":0.1}
for x in U:
    growth=0.45*x["p_cagr_cnt"]+0.30*x["p_cagr_amt"]+0.25*x["p_mom"]
    demand=0.40*x["p_fl_g"]+0.35*x["p_wk_g"]+0.25*x["p_rp_g"]
    room=0.55*x["p_gap"]+0.45*x["p_sps"]
    struct=IX.get(x.get("ix_now"),0.4)
    x["s_growth"],x["s_demand"],x["s_room"],x["s_struct"]=growth,demand,room,struct
    x["score"]=round(100*(0.40*growth+0.25*demand+0.20*room+0.15*struct),1)
U.sort(key=lambda x:-x["score"])
json.dump(U,open("scored.json","w"),ensure_ascii=False)
f=lambda v:"" if v is None else f"{v*100:+.1f}%"
print(f"{'#':>3} {'score':>5} {'상권':<22}{'구':<5}{'구분':<5} {'매출억':>6} {'매출CAGR':>8} {'건수CAGR':>8} {'모멘텀':>7} {'유동':>7} {'직장':>7} {'상주':>7} {'점포':>4} {'점당억':>5} 지표")
for i,x in enumerate(U[:60]):
    print(f"{i+1:>3} {x['score']:>5} {x['nm'][:20]:<22}{x['gu']:<5}{x['se'][:4]:<5} {x['sales_now']/1e8:>6.0f} {f(x['cagr_amt']):>8} {f(x['cagr_cnt']):>8} {f(x['mom']):>7} {f(x['fl_g']):>7} {f(x['wk_g']):>7} {f(x['rp_g']):>7} {int(x.get('st_now',0)):>4} {x['sps']/1e8:>5.1f} {x.get('ix_now')}")
