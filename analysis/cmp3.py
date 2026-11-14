import json,math,collections
M=json.load(open("master.json"));by={o["cd"]:o for o in M}
def dist(a,b):return math.hypot((a["lat"]-b["lat"])*111,(a["lon"]-b["lon"])*88.2)
NOW=["20253","20254","20261","20262"]
rows=collections.defaultdict(list)
for q in NOW:
    for x in json.load(open(f"raw/VwsmTrdarSelngQq_{q}.json")): rows[x["TRDAR_CD"]].append(x)
st={}
for x in json.load(open("raw/VwsmTrdarStorQq_20262.json")): st[(x["TRDAR_CD"],x["SVC_INDUTY_CD"])]=x
def agg(cds,ind):
    A=collections.defaultdict(float)
    for cd in cds:
        for x in rows.get(cd,[]):
            if x["SVC_INDUTY_CD"]!=ind: continue
            for k,v in x.items():
                if isinstance(v,(int,float)): A[k]+=v
        s=st.get((cd,ind))
        if s: A["stores"]+=s["STOR_CO"]; A["frc"]+=s["FRC_STOR_CO"]
    return A
# Seoul-wide by industry
allc=list(rows.keys())
out={}
cent={"samseong":"3120223","magok":"3110643","yeongdeungpo":"3120145"}
sites={"samseong":["3120221","3120222","3001496","3120215","3120218"],"magok":["3120118","3120119","3110648"],"yeongdeungpo":["3120137","3110792","3120145","3120140"]}
def summarize(A):
    if not A.get("THSMON_SELNG_CO"): return None
    amt=A["THSMON_SELNG_AMT"];cnt=A["THSMON_SELNG_CO"]
    r=dict(amt_eok=round(amt/1e8,1),cnt=int(cnt),ticket=round(amt/cnt),stores=int(A["stores"]),frc=int(A["frc"]),
      sps=round(amt/max(1,A["stores"])/1e8,2),txn_store_day=round(cnt/max(1,A["stores"])/365,1),
      wkend=round(A["WKEND_SELNG_AMT"]/amt*100,1),
      tz={t:round(A[f"TMZON_{t}_SELNG_AMT"]/amt*100,1) for t in ["00_06","06_11","11_14","14_17","17_21","21_24"]},
      tzc={t:round(A[f"TMZON_{t}_SELNG_CO"]/cnt*100,1) for t in ["06_11","11_14","14_17","17_21","21_24"]},
      tick_tz={t:round(A[f"TMZON_{t}_SELNG_AMT"]/max(1,A[f"TMZON_{t}_SELNG_CO"])) for t in ["06_11","11_14","14_17","17_21","21_24"]},
      tick_wd=round(A["MDWK_SELNG_AMT"]/max(1,A["MDWK_SELNG_CO"])),tick_we=round(A["WKEND_SELNG_AMT"]/max(1,A["WKEND_SELNG_CO"])),
      dow={d:round(A[f"{d}_SELNG_AMT"]/amt*100,1) for d in ["MON","TUES","WED","THUR","FRI","SAT","SUN"]},
      age={a:round(A[f"AGRDE_{a}_SELNG_AMT"]/amt*100,1) for a in ["10","20","30","40","50","60_ABOVE"]},
      fml=round(A["FML_SELNG_AMT"]/amt*100,1))
    return r
res={}
res["seoul"]={ind:summarize(agg(allc,ind)) for ind in ["CS100010","CS100005"]}
for k,c in cent.items():
    cds=[o["cd"] for o in M if dist(by[c],o)<=1.0]
    res[k]={"catch":{ind:summarize(agg(cds,ind)) for ind in ["CS100010","CS100005"]},
            "sites":{cd:{"nm":by[cd]["nm"],**{ind:summarize(agg([cd],ind)) for ind in ["CS100010","CS100005"]}} for cd in sites[k]}}
json.dump(res,open("cmp3.json","w"),ensure_ascii=False)
def p(name,r):
    if not r: print("   ",name,"-");return
    print(f"    {name}: {r['amt_eok']}억 ticket {r['ticket']}원 stores {r['stores']} frc {r['frc']} sps {r['sps']}억 txn/st/day {r['txn_store_day']} 주말 {r['wkend']}% tz {r['tz']} tick평일/주말 {r['tick_wd']}/{r['tick_we']} age {r['age']} 여 {r['fml']}")
for k in ["seoul"]: 
    print("SEOUL");p("커피",res[k]["CS100010"]);p("제과",res[k]["CS100005"])
for k in cent:
    print("==",k);print("  catchment");p("커피",res[k]["catch"]["CS100010"]);p("제과",res[k]["catch"]["CS100005"])
    for cd,v in res[k]["sites"].items(): print("  site",v["nm"]);p("커피",v["CS100010"]);p("제과",v["CS100005"])
