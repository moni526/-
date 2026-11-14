import json,math
M=json.load(open("master.json"));CL=json.load(open("clusters.json"));C=CL["allc"]
byname={o["nm"]:o for o in M}
def find(s): return [o for o in M if s in o["nm"]]
for s in ["잠실나루","잠실역","발산역","마곡","코엑스","삼성역","휘문","삼각지","신용산","성수","영등포역","외대앞","경희대","둔촌","고덕","상봉","망우","연신내","불광","이문","휘경","청량리","광운","한강진","남영"]:
    print(s, [(o["cd"],o["nm"],o["se"]) for o in find(s)][:8])
