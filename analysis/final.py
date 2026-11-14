import json,math
M=json.load(open("master.json"));by={o["cd"]:o for o in M};R=json.load(open("robust.json"));RA={x["cd"]:x for x in R["all"]}
Qs=["20223","20224","20231","20232","20243","20244","20251","20252","20253","20254","20261","20262"]
for o in M:
    v=[o.get("q"+q,0) for q in Qs]
    cov=any(x==0 for x in v[:4]) and sum(v[8:])>2e8
    j=[v[i]/v[i-1] for i in range(1,12) if v[i-1]>1e8]
    o["clean"]=not cov and not (bool(j) and max(j)>1.6 and sum(v[8:])>8e8)
def dist(a,b):return math.hypot((a["lat"]-b["lat"])*111,(a["lon"]-b["lon"])*88.2)
Q=["20223","20224","20231","20232","20243","20244","20251","20252","20253","20254","20261","20262"]
AREAS=[("samseong","3120223"),("magok","3110643"),("yeongdeungpo","3120145"),("jamsilnaru","3111011"),("yongsan","3120044"),("seongsu","3120052"),("cheongnyangni","3120063")]
out={}
for key,cd in AREAS:
    c=by[cd];nb=[o for o in M if dist(c,o)<=1.0];S=lambda k:sum((o.get(k) or 0) for o in nb)
    tz={t:S("n_TMZON_"+t+"_SELNG_AMT") for t in ["06_11","11_14","14_17","17_21","21_24"]};tt=sum(tz.values()) or 1
    ag={a:S(f"n_AGRDE_{a}_SELNG_AMT") for a in ["20","30","40","50","60_ABOVE"]};at=sum(ag.values()) or 1
    r=RA[cd]
    out[key]=dict(center=c["nm"],gu=c["gu"],lat=c["lat"],lon=c["lon"],rank=r["rank"],N=len(R["all"]),score=r["score"],g=round(r["s_growth"]*100),d=round(r["s_demand"]*100),room=round(r["s_room"]*100),
      sales=round(S("now_amt")/1e8),cf=round(r["cf"],1),cnt=round(r["cnt"],1),wk=round(r["wk"],1),rp=round(r["rp"],1),fl=round(r["fl"],1),wk_now=int(S("wk_now")),rp_now=int(S("rp_now")),wk_add=int(r["wk_add"]),rp_add=int(r["rp_add"]),
      st=int(S("st_now")),st_base=int(S("st_base")),stg=round(r["stg"],1),sps=round(r["sps"],2),frc=round(S("frc_now")/max(1,S("st_now"))*100),
      tz={t:round(v/tt*100,1) for t,v in tz.items()},age={a:round(v/at*100,1) for a,v in ag.items()},
      wkend=round(S("n_WKEND_SELNG_AMT")/max(1,S("n_WKEND_SELNG_AMT")+S("n_MDWK_SELNG_AMT"))*100,1),
      fml=round(S("n_FML_SELNG_AMT")/max(1,S("n_FML_SELNG_AMT")+S("n_ML_SELNG_AMT"))*100,1),
      bk=round(S("now_bk_amt")/max(1,S("now_amt"))*100,1),
      q=[round(S("q"+q)/1e8,1) for q in Q],flagged=r["flagged"])
    print(key,{k:out[key][k] for k in ["center","rank","score","sales","cf","cnt","wk","rp","stg","sps","frc","wkend","fml","bk"]},out[key]["tz"],out[key]["age"])
# site-level
SITES=["3120221","3120215","3001496","3110648","3120118","3110792","3120137","3111011","3111013","3120045","3110068","3120119","3120222"]
sites={}
for cd in SITES:
    o=by[cd];g=lambda a,b:round(((a/b)**(1/3)-1)*100,1) if a and b else None
    sites[cd]=dict(nm=o["nm"],se=o["se"],gu=o["gu"],dong=o["dong"],lat=o["lat"],lon=o["lon"],sales=round(o.get("now_amt",0)/1e8,1),sales_g=g(o.get("now_amt"),o.get("base_amt")) if o["clean"] else None,clean=o["clean"],
      st=int(o.get("st_now",0)),st_base=int(o.get("st_base",0)),sps=round(o.get("now_amt",0)/max(1,o.get("st_now",0))/1e8,2),wk_base=o.get("wk_base"),wk=o.get("wk_now"),rp_base=o.get("rp_base"),rp=o.get("rp_now"),fl=round(o.get("fl_now",0)),ix=o.get("ix_now"),opn=o.get("opn"),cls=o.get("cls"))
    print(cd,sites[cd])
# Seoul context
T=json.load(open("clusters.json"))["tot"]
seoul=dict(now=T["now_amt"],base=T["base_amt"],cf_now=T["now_cf_amt"],bk_now=T["now_bk_amt"],cf_base=T["base_cf_amt"],bk_base=T["base_bk_amt"],st_now=T["st_now"],st_base=T["st_base"],wk_now=T["wk_now"],wk_base=T["wk_base"],rp_now=T["rp_now"],rp_base=T["rp_base"],fl_now=T["fl_now"],fl_base=T["fl_base"],cnt_now=T["now_cnt"],cnt_base=T["base_cnt"],
   q=[round(sum(o.get("q"+q,0) for o in M)/1e8) for q in Q])
# map points: all districts + scores
pts=[[o["lat"],o["lon"],round(RA[o["cd"]]["score"]) if o["cd"] in RA else -1] for o in M]
top=[dict(nm=x["nm"],gu=x["gu"],score=x["score"],lat=x["lat"],lon=x["lon"],cf=round(x["cf"],1),wk=round(x["wk"],1),rp=round(x["rp"],1),stg=round(x["stg"],1)) for x in R["pick"][:15]]
json.dump(dict(areas=out,sites=sites,seoul=seoul,pts=pts,top=top),open("report_data.json","w"),ensure_ascii=False)
print("seoul",{k:(round(v/1e8) if isinstance(v,float) and v>1e7 else v) for k,v in seoul.items()})
