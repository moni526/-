import json
# ---- assumptions (all KRW) ----
AREA_PY=22; M2=AREA_PY*3.3058
RENT_M2=72900      # 테헤란로 상권 중대형상가 1층 기준 (부동산원 집계 인용, 2026Q1)
MGMT_M2=12000      # 관리비 가정
HOURLY=15000       # 2027 최저임금 10,700 + 주휴(20%) + 사업주 4대보험(~10%) + 퇴직충당(8.3%)
MGR=50_000_000     # 점장 1명 연 인건비(4대보험 포함)
VAT=1.1
SC={
 "보수":dict(txn=110,ticket=9000,b2b=0.00,hourly_h=140,mkt=0.03),
 "기준":dict(txn=158,ticket=9900,b2b=0.04,hourly_h=154,mkt=0.02),
 "낙관":dict(txn=201,ticket=10300,b2b=0.05,hourly_h=185,mkt=0.02),
}
MIX_BEV=0.70; COGS_BEV=0.24; COGS_FOOD=0.38
CAPEX=dict(interior=AREA_PY*3_500_000,equip=65_000_000,sign_furn=23_000_000)
CAPEX["contingency"]=round(sum(CAPEX.values())*0.10)
CAPEX_T=sum(CAPEX.values()); DEP=CAPEX_T/5
DEPOSIT=RENT_M2*M2*10
def run(s,rent_m2=RENT_M2,txn=None,ticket=None):
    t=txn or s["txn"]; tk=ticket or s["ticket"]
    gross=t*tk*365; net_store=gross/VAT; b2b=net_store*s["b2b"]; net=net_store+b2b
    cogs=net*(MIX_BEV*COGS_BEV+(1-MIX_BEV)*COGS_FOOD)
    pack=net*0.035
    labor=MGR+s["hourly_h"]*52*HOURLY
    rent=rent_m2*M2*12; mgmt=MGMT_M2*M2*12
    card=gross*0.013
    util=net*0.028; mkt=net*s["mkt"]; other=net*0.02
    ebitda=net-cogs-pack-labor-rent-mgmt-card-util-mkt-other
    hq=net*0.03; op=ebitda-hq-DEP
    return dict(gross=gross,net=net,b2b=b2b,cogs=cogs,pack=pack,labor=labor,rent=rent,mgmt=mgmt,card=card,util=util,mkt=mkt,other=other,ebitda=ebitda,hq=hq,dep=DEP,op=op)
R={k:run(v) for k,v in SC.items()}
for k,r in R.items():
    print(k,"매출(순) %.2f억"%(r["net"]/1e8),"4-wall EBITDA %.2f억 (%.1f%%)"%(r["ebitda"]/1e8,r["ebitda"]/r["net"]*100),"영업이익 %.2f억 (%.1f%%)"%(r["op"]/1e8,r["op"]/r["net"]*100),"labor %.1f%% rent+mgmt %.1f%% cogs %.1f%%"%(r["labor"]/r["net"]*100,(r["rent"]+r["mgmt"])/r["net"]*100,r["cogs"]/r["net"]*100),"payback yrs",round(CAPEX_T/max(1,r["ebitda"]),1) if r["ebitda"]>0 else None)
# break-even txn/day (op=0) under base ticket
s=SC["기준"]
lo,hi=10,400
for _ in range(60):
    mid=(lo+hi)/2
    if run(s,txn=mid)["op"]>0: hi=mid
    else: lo=mid
be_op=hi
lo,hi=10,400
for _ in range(60):
    mid=(lo+hi)/2
    if run(s,txn=mid)["ebitda"]>0: hi=mid
    else: lo=mid
be_eb=hi
print("BE txn/day OP",round(be_op),"EBITDA",round(be_eb),"capex",CAPEX_T,CAPEX,"deposit",round(DEPOSIT))
# sensitivity grid: txn x rent
grid=[[round(run(s,rent_m2=rm,txn=t)["op"]/run(s,rent_m2=rm,txn=t)["net"]*100,1) for rm in (55000,65000,72900,85000,95000)] for t in (110,130,158,180,201)]
print(grid)
# 3-year ramp: 2027 (85% of base, 1st-year mkt 4%), 2028 base, 2029 optimistic (catalyst)
y27=run(dict(SC["기준"],mkt=0.04),txn=158*0.85); y28=R["기준"]; y29=R["낙관"]
yrs={"2027":y27,"2028":y28,"2029":y29}
for y,r in yrs.items(): print(y,round(r["net"]/1e8,2),round(r["op"]/1e8,2))
json.dump(dict(R=R,SC=SC,yrs=yrs,be_op=be_op,be_eb=be_eb,capex=CAPEX,capex_t=CAPEX_T,deposit=DEPOSIT,grid=grid,assump=dict(AREA_PY=AREA_PY,M2=M2,RENT_M2=RENT_M2,MGMT_M2=MGMT_M2,HOURLY=HOURLY,MGR=MGR,MIX_BEV=MIX_BEV,COGS_BEV=COGS_BEV,COGS_FOOD=COGS_FOOD)),open("pnl.json","w"),ensure_ascii=False)
