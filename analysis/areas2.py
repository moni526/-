import json,math,bisect
M=json.load(open("master.json"));CL=json.load(open("clusters.json"));C=CL["allc"]
by={o["cd"]:o for o in M}
def dist(a,b):return math.hypot((a["lat"]-b["lat"])*111,(a["lon"]-b["lon"])*88.2)
g=lambda a,b:((a/b)**(1/3)-1)*100 if a and b else None
A={"잠실":"3120227","마곡":"3120118","삼성·코엑스":"3120222","용산":"3120044","성수":"3120052","영등포":"3120145","이문·휘경":"3110220","둔촌·고덕":"3120245","고덕":"3120249","상봉":"3120069","연신내·불광":"3120090","청량리":"3120063","광운대":"3110420","여의도":"3120146" if "3120146" in by else None}
cpos={x["cd"]:i for i,x in enumerate(C)}
res={}
for k,cd in A.items():
    if not cd or cd not in by: continue
    c=by[cd]; nb=[o for o in M if dist(c,o)<=1.0]
    S=lambda key:sum((o.get(key) or 0) for o in nb)
    r=dict(center=c["nm"],n=len(nb),sales=S("now_amt")/1e8,cagr=g(S("now_amt"),S("base_amt")),cagr_cnt=g(S("now_cnt"),S("base_cnt")),mom=(S("now_amt")/S("mid_amt")-1)*100,
      fl=g(S("fl_now"),S("fl_base")),wk=g(S("wk_now"),S("wk_base")),rp=g(S("rp_now"),S("rp_base")),wk_now=S("wk_now"),rp_now=S("rp_now"),fl_now=S("fl_now"),
      st=S("st_now"),stg=(S("st_now")/S("st_base")-1)*100,sps=S("now_amt")/S("st_now")/1e8,frc=S("frc_now")/max(1,S("st_now"))*100)
    tz={t:S("n_TMZON_"+t+"_SELNG_AMT") for t in ["06_11","11_14","14_17","17_21","21_24"]};tt=sum(tz.values())
    r["tz"]={t:round(v/tt*100,1) for t,v in tz.items()}
    r["wkend"]=S("n_WKEND_SELNG_AMT")/(S("n_WKEND_SELNG_AMT")+S("n_MDWK_SELNG_AMT"))*100
    ag={a:S(f"n_AGRDE_{a}_SELNG_AMT") for a in ["10","20","30","40","50","60_ABOVE"]};at=sum(ag.values());r["age"]={a:round(v/at*100,1) for a,v in ag.items()}
    r["fml"]=S("n_FML_SELNG_AMT")/(S("n_FML_SELNG_AMT")+S("n_ML_SELNG_AMT"))*100
    r["bk_share"]=S("now_bk_amt")/S("now_amt")*100
    r["bk_cagr"]=g(S("now_bk_amt"),S("base_bk_amt")); r["cf_cagr"]=g(S("now_cf_amt"),S("base_cf_amt"))
    r["q"]=[round(S("q"+q)/1e8,1) for q in ["20223","20224","20231","20232","20243","20244","20251","20252","20253","20254","20261","20262"]]
    r["cl_rank"]=None
    if cd in cpos: r["cl_score"]=round(C[cpos[cd]]["score"],1); r["cl_pct"]=round(100*(1-cpos[cd]/len(C)))
    subs=[o for o in nb if o.get("now_amt",0)>3e8 and o.get("base_amt")]
    for o in subs: o["_g"]=g(o["now_amt"],o["base_amt"]); o["_sps"]=o["now_amt"]/max(1,o.get("st_now",0))/1e8
    r["subs"]=[dict(cd=o["cd"],nm=o["nm"],se=o["se"],sales=round(o["now_amt"]/1e8,1),g=round(o["_g"],1),st=int(o.get("st_now",0)),sps=round(o["_sps"],2),wk=o.get("wk_now"),rp=o.get("rp_now"),ix=o.get("ix_now"),lat=o["lat"],lon=o["lon"]) for o in sorted(subs,key=lambda o:-o["now_amt"])[:10]]
    r["lat"],r["lon"]=c["lat"],c["lon"]
    res[k]=r
json.dump(res,open("areas.json","w"),ensure_ascii=False)
print(f"{'권역':<8}{'n':>3} {'매출억':>6} {'CAGR':>6} {'건수':>6} {'모멘':>6} {'유동':>5} {'직장':>5} {'상주':>5} {'점포':>5} {'점포증':>6} {'점당':>4} {'주말':>5} {'제과비':>5} {'군집pct':>6}")
for k,r in res.items():
    print(f"{k:<8}{r['n']:>3} {r['sales']:>6.0f} {r['cagr']:>6.1f} {r['cagr_cnt']:>6.1f} {r['mom']:>6.1f} {r['fl']:>5.1f} {r['wk']:>5.1f} {r['rp']:>5.1f} {r['st']:>5.0f} {r['stg']:>6.1f} {r['sps']:>4.1f} {r['wkend']:>5.1f} {r['bk_share']:>5.1f} {r.get('cl_pct','')!s:>6}")
