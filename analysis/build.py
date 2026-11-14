import json,math,statistics as stt,collections
L=lambda f:json.load(open("raw/"+f))
NOW=["20253","20254","20261","20262"];MID=["20243","20244","20251","20252"];BASE=["20223","20224","20231","20232"]
relm={x["TRDAR_CD"]:x for x in L("TbgisTrdarRelm_all.json")}
D=collections.defaultdict(lambda:collections.defaultdict(float))
for grp,qs in (("now",NOW),("mid",MID),("base",BASE)):
    for q in qs:
        for x in L(f"VwsmTrdarSelngQq_{q}.json"):
            d=D[x["TRDAR_CD"]];ind="cf" if x["SVC_INDUTY_CD"]=="CS100010" else "bk"
            d[f"{grp}_amt"]+=x["THSMON_SELNG_AMT"];d[f"{grp}_cnt"]+=x["THSMON_SELNG_CO"];d[f"{grp}_{ind}_amt"]+=x["THSMON_SELNG_AMT"]
            if grp=="now":
                for k in ["MDWK_SELNG_AMT","WKEND_SELNG_AMT","TMZON_06_11_SELNG_AMT","TMZON_11_14_SELNG_AMT","TMZON_14_17_SELNG_AMT","TMZON_17_21_SELNG_AMT","TMZON_21_24_SELNG_AMT","TMZON_00_06_SELNG_AMT","ML_SELNG_AMT","FML_SELNG_AMT","AGRDE_10_SELNG_AMT","AGRDE_20_SELNG_AMT","AGRDE_30_SELNG_AMT","AGRDE_40_SELNG_AMT","AGRDE_50_SELNG_AMT","AGRDE_60_ABOVE_SELNG_AMT"]:
                    d["n_"+k]+=x[k]
        # quarterly series for sparkline
for q in ["20223","20224","20231","20232","20243","20244","20251","20252","20253","20254","20261","20262"]:
    for x in L(f"VwsmTrdarSelngQq_{q}.json"): D[x["TRDAR_CD"]]["q"+q]+=x["THSMON_SELNG_AMT"]
for grp,qs in (("now",NOW),("base",BASE),("mid",MID)):
    for q in qs:
        for x in L(f"VwsmTrdarFlpopQq_{q}.json"):
            D[x["TRDAR_CD"]][f"fl_{grp}"]+=x["TOT_FLPOP_CO"]/4
            if grp=="now":
                for k in ["AGRDE_20_FLPOP_CO","AGRDE_30_FLPOP_CO","TMZON_06_11_FLPOP_CO","SAT_FLPOP_CO","SUN_FLPOP_CO"]: D[x["TRDAR_CD"]]["fln_"+k]+=x[k]/4
for f,key,col in (("VwsmTrdarWrcPopltnQq_all.json","wk","TOT_WRC_POPLTN_CO"),("VwsmTrdarRepopQq_all.json","rp","TOT_REPOP_CO")):
    for x in L(f):
        if x["STDR_YYQU_CD"]=="20262": D[x["TRDAR_CD"]][key+"_now"]=x[col]
        if x["STDR_YYQU_CD"]=="20232": D[x["TRDAR_CD"]][key+"_base"]=x[col]
        if key=="rp" and x["STDR_YYQU_CD"]=="20262": D[x["TRDAR_CD"]]["apt_hh"]=x["APT_HSHLD_CO"];D[x["TRDAR_CD"]]["hh"]=x["TOT_HSHLD_CO"]
for q,g in (("20262","now"),("20232","base")):
    for x in L(f"VwsmTrdarStorQq_{q}.json"):
        d=D[x["TRDAR_CD"]];d[f"st_{g}"]+=x["STOR_CO"];d[f"frc_{g}"]+=x["FRC_STOR_CO"]
        if g=="now": d["opn"]+=x["OPBIZ_STOR_CO"];d["cls"]+=x["CLSBIZ_STOR_CO"]
for x in L("VwsmTrdarStorQq_20252.json"):
    pass
for q,g in (("20262","now"),("20232","base")):
    for x in L(f"VwsmTrdarIxQq_{q}.json"): D[x["TRDAR_CD"]]["ix_"+g]=x["TRDAR_CHNGE_IX_NM"]
for x in L("VwsmTrdarFcltyQq_all.json"):
    if x["STDR_YYQU_CD"]=="20262":
        d=D[x["TRDAR_CD"]];d["subway"]=x["SUBWAY_STATN_CO"];d["viatr"]=x["VIATR_FCLTY_CO"];d["univ"]=x["UNIV_CO"];d["hosp"]=x["GNRL_HSPTL_CO"]
# TM(EPSG:5181) -> WGS84
def tm2ll(X,Y):
    a=6378137.0;f=1/298.257222101;e2=f*(2-f);k0=1;lon0=math.radians(127);lat0=math.radians(38);FE=200000;FN=500000
    def M(p):return a*((1-e2/4-3*e2**2/64-5*e2**3/256)*p-(3*e2/8+3*e2**2/32+45*e2**3/1024)*math.sin(2*p)+(15*e2**2/256+45*e2**3/1024)*math.sin(4*p)-(35*e2**3/3072)*math.sin(6*p))
    m=M(lat0)+(Y-FN)/k0;mu=m/(a*(1-e2/4-3*e2**2/64-5*e2**3/256));e1=(1-math.sqrt(1-e2))/(1+math.sqrt(1-e2))
    p1=mu+(3*e1/2-27*e1**3/32)*math.sin(2*mu)+(21*e1**2/16-55*e1**4/32)*math.sin(4*mu)+(151*e1**3/96)*math.sin(6*mu)
    ep2=e2/(1-e2);C=ep2*math.cos(p1)**2;T=math.tan(p1)**2;N=a/math.sqrt(1-e2*math.sin(p1)**2);R=a*(1-e2)/(1-e2*math.sin(p1)**2)**1.5;Dd=(X-FE)/(N*k0)
    lat=p1-(N*math.tan(p1)/R)*(Dd**2/2-(5+3*T+10*C-4*C**2-9*ep2)*Dd**4/24)
    lon=lon0+(Dd-(1+2*T+C)*Dd**3/6)/math.cos(p1)
    return round(math.degrees(lat),5),round(math.degrees(lon),5)
out=[]
for cd,r in relm.items():
    d=D.get(cd,{});la,lo=tm2ll(float(r["XCNTS_VALUE"]),float(r["YDNTS_VALUE"]))
    o=dict(cd=cd,nm=r["TRDAR_CD_NM"],se=r["TRDAR_SE_CD_NM"],gu=r["SIGNGU_CD_NM"],dong=r["ADSTRD_CD_NM"],ar=float(r["RELM_AR"]),lat=la,lon=lo)
    o.update({k:v for k,v in d.items()})
    out.append(o)
json.dump(out,open("master.json","w"),ensure_ascii=False)
print(len(out)); import random; print(out[0]["nm"],out[0]["lat"],out[0]["lon"])
