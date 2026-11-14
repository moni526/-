# 2-minute Answer-First pitch video: 1920x1080 @30fps, rendered with Pillow + ffmpeg.
# usage: python render.py <ffmpeg> <tmpdir> <out.mp4>
import sys, json, math, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from multiprocessing import Pool

W, H, FPS = 1920, 1080, 30
FF, TMP, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
TL = json.load(open(f"{TMP}/timeline.json"))
END_HOLD = 2.3
TOTAL = TL["total"] + END_HOLD
NF = int(TOTAL * FPS)

# ---------- palette ----------
WHITE = (255, 255, 255); NAVY = (8, 27, 51); INK = (30, 41, 56); GREY = (120, 130, 142); LG = (226, 230, 236); XLG = (243, 245, 248)
BLUE = (31, 91, 255); BLUE_L = (214, 226, 255); RED = (210, 67, 60); RED_L = (250, 226, 224); GREEN = (8, 132, 104); GREEN_L = (215, 240, 232)
COFFEE = (107, 74, 53); BAKERY = (214, 156, 58)

# ---------- fonts ----------
FP = "/System/Library/Fonts/AppleSDGothicNeo.ttc"; IDX = {"r": 0, "m": 2, "s": 4, "b": 6, "l": 8}
_fc = {}
def F(size, w="r"):
    k = (size, w)
    if k not in _fc: _fc[k] = ImageFont.truetype(FP, size, index=IDX[w])
    return _fc[k]

# ---------- easing / timing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def prog(t, t0, d=0.5): return eo((t - t0) / d)
def mix(c1, c2, a): return tuple(int(c1[i] + (c2[i] - c1[i]) * a) for i in range(3))

# ---------- drawing helpers (alpha-aware) ----------
class Canvas:
    def __init__(self):
        self.im = Image.new("RGBA", (W, H), WHITE + (255,)); self.d = ImageDraw.Draw(self.im)
    def layer(self, a, fn):
        if a <= 0.003: return
        if a >= 0.997: fn(self.d); return
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fn(ImageDraw.Draw(lay))
        arr = np.array(lay); arr[..., 3] = (arr[..., 3] * a).astype(np.uint8)
        self.im.alpha_composite(Image.fromarray(arr))
    def text(self, xy, s, size, w="r", fill=INK, a=1.0, anchor="la", dy=0):
        x, y = xy; self.layer(a, lambda d: d.text((x, y + dy), s, font=F(size, w), fill=fill, anchor=anchor))
    def rect(self, box, fill=None, outline=None, width=1, r=0, a=1.0):
        self.layer(a, lambda d: d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width) if r else d.rectangle(box, fill=fill, outline=outline, width=width))
    def line(self, pts, fill=INK, width=2, a=1.0):
        self.layer(a, lambda d: d.line(pts, fill=fill, width=width, joint="curve"))
    def circle(self, c, r, fill=None, outline=None, width=1, a=1.0):
        x, y = c; self.layer(a, lambda d: d.ellipse((x - r, y - r, x + r, y + r), fill=fill, outline=outline, width=width))

def tw(s, size, w="r"): return F(size, w).getlength(s)
def wrap(s, size, w, maxw):
    out, cur = [], ""
    for ch in s.split(" "):
        t = (cur + " " + ch).strip()
        if tw(t, size, w) <= maxw: cur = t
        else: out.append(cur); cur = ch
    if cur: out.append(cur)
    return out
def fmt(v, dec=0): return f"{v:,.{dec}f}"

# ---------- chrome ----------
SECTIONS = ["결론", "근거", "지표", "인사이트", "컨셉", "손익"]
SEC_OF = {"answer": 0, "pillars": 1, "market": 1, "metrics": 2, "insight1": 3, "economics": 3, "insight2": 3, "concept": 4, "menu": 4, "pnl": 5, "close": 5}
ML = 110

def chrome(c, sc, ts, idx, title, tracker, source):
    a = prog(ts, 0.0, 0.45)
    c.text((ML, 72), tracker, 22, "b", BLUE, a)
    # storyline tracker (top-right)
    x = W - ML
    for i in reversed(range(len(SECTIONS))):
        s = SECTIONS[i]; on = i == SEC_OF[sc]; done = i < SEC_OF[sc]
        wdt = tw(s, 19, "s" if on else "m") + 30; x -= wdt
        if on: c.rect((x, 62, x + wdt, 96), fill=NAVY, r=17)
        c.text((x + wdt / 2, 79), s, 19, "s" if on else "m", WHITE if on else (NAVY if done else GREY), 1, "mm")
        x -= 8
    lines = wrap(title, 50, "b", W - 2 * ML)
    for k, ln in enumerate(lines):
        c.text((ML, 118 + k * 64), ln, 50, "b", NAVY, a, dy=(1 - a) * 18)
    yb = 118 + len(lines) * 64 + 14
    c.rect((ML, yb, ML + (W - 2 * ML) * eo(ts / 0.7), yb + 3), fill=NAVY)
    # footer
    c.line([(ML, 1022), (W - ML, 1022)], LG, 2)
    c.text((ML, 1036), source, 19, "r", GREY)
    c.text((W - ML, 1036), f"{idx + 1:02d} / {len(TL['scenes']):02d}", 19, "m", GREY, 1, "ra")
    return yb + 30

def caption(c, t):
    for sc in TL["scenes"]:
        for cu in sc["cues"]:
            if cu["t"] - 0.05 <= t <= cu["t"] + cu["dur"] + 0.15:
                a = min(prog(t, cu["t"] - 0.05, 0.18), 1 - clamp((t - cu["t"] - cu["dur"]) / 0.15))
                lines = wrap(cu["text"], 30, "m", 1400)
                y0 = 990 - len(lines) * 40
                wmax = max(tw(l, 30, "m") for l in lines)
                c.rect((W / 2 - wmax / 2 - 22, y0 - 10, W / 2 + wmax / 2 + 22, y0 + len(lines) * 40 + 6), fill=(8, 27, 51, 225), r=10, a=a)
                for k, l in enumerate(lines): c.text((W / 2, y0 + k * 40 + 18), l, 30, "m", WHITE, a, "mm")
                return

def kpi(c, x, y, w, h, big, label, sub, a, color=NAVY, bigsize=64):
    c.rect((x, y, x + w, y + h), fill=XLG, r=14, a=a)
    c.rect((x, y, x + 8, y + h), fill=color, a=a)
    c.text((x + 34, y + 28), label, 25, "m", GREY, a)
    c.text((x + 32, y + 66), big, bigsize, "b", color, a)
    c.text((x + 34, y + h - 48), sub, 25 if h > 250 else 22, "r", INK, a)

def cue(sc, k):
    return sc["cues"][min(k, len(sc["cues"]) - 1)]["t"] - sc["start"]

# =============== scenes ===============
def s_answer(c, sc, ts, i):
    T = lambda k: cue(sc, k)
    y = chrome(c, "answer", ts, i, "결론: 삼성·영동대로에 ‘커피가 이끌고 빵이 따라가는’ 22평 그랩앤고 1호점을 연다", "ANSWER FIRST", "출처: 서울 열린데이터광장 상권분석서비스(2022.3Q–2026.2Q) 기반 자체 분석 · 금액 단위 원, 부가세 제외 순매출")
    a = prog(ts, T(1), .6)
    c.rect((ML, y + 10, W - ML, y + 280), fill=NAVY, r=18, a=a)
    c.text((ML + 54, y + 60), "1호점 입지", 28, "m", (160, 180, 210), a)
    c.text((ML + 54, y + 104), "봉은사역 ~ 코엑스 북문, 영동대로 변 1층 · 22평(72.7㎡)", 54, "b", WHITE, a)
    a2 = prog(ts, T(2), .6)
    c.text((ML + 54, y + 200), "업태", 28, "m", (160, 180, 210), a2)
    c.text((ML + 140, y + 194), "커피 주도 그랩앤고 + 베이크오프 빵 (음료 70 : 푸드 30)", 38, "s", WHITE, a2)
    a3 = [prog(ts, T(3) + k * .35, .55) for k in range(3)]
    ky = y + 320; kw = (W - 2 * ML - 60) / 3
    kpi(c, ML, ky, kw, 290, "5.4억 원", "정상 영업 연도 순매출 (2028)", "하루 158건 × 건당 9,900원", a3[0], NAVY, 92)
    kpi(c, ML + kw + 30, ky, kw, 290, "14.9%", "영업이익률 (2029, 환승센터 개통 후)", "영업이익 1.07억 원", a3[1], GREEN, 92)
    kpi(c, ML + 2 * (kw + 30), ky, kw, 290, "144건/일", "손익분기 거래량", "권역 평균 158건보다 9% 낮음", a3[2], BLUE, 92)

def s_pillars(c, sc, ts, i):
    T = lambda k: cue(sc, k)
    y = chrome(c, "pillars", ts, i, "이 결론을 받치는 근거는 세 가지다", "GOVERNING THOUGHT", "출처: 서울 열린데이터광장 상권분석서비스 추정매출·점포·직장인구(상권 단위, 2022.3Q–2026.2Q) · 성장률은 3년 비교")
    a0 = prog(ts, 0.2, .5)
    c.rect((W / 2 - 430, y + 10, W / 2 + 430, y + 110), fill=NAVY, r=14, a=a0)
    c.text((W / 2, y + 60), "삼성·영동대로 1호점 · 커피 주도 그랩앤고", 36, "b", WHITE, a0, "mm")
    bw = (W - 2 * ML - 60) / 3; by = y + 200
    items = [("①", "서울은 제로섬 시장", ["커피·제과 매출 연 +0.2%", "점포 21,888 → 20,996곳 (-892)", "→ 수요가 공급보다 빨리 느는 곳만"], NAVY),
             ("②", "이익이 나는 곳은 삼성뿐", ["점포당 하루 158건 (서울 60건의 2.6배)", "감당 임대료 ㎡당 14.2만 원", "영등포·마곡은 평균 점포가 적자"], BLUE),
             ("③", "커피 +35%, 빵 -33%", ["삼성 핵심 5개 상권, 3년 비교", "커피 779억 → 1,055억 원", "→ 커피 주도, 빵은 동반 구매"], GREEN)]
    for k, (n, h, bl, col) in enumerate(items):
        a = prog(ts, T(k + 1), .55); x = ML + k * (bw + 30)
        c.line([(W / 2, y + 110), (W / 2, y + 150), (x + bw / 2, y + 150), (x + bw / 2, by)], LG, 3, a)
        c.rect((x, by, x + bw, by + 480), fill=WHITE, outline=LG, width=2, r=14, a=a)
        c.rect((x, by, x + bw, by + 8), fill=col, a=a)
        c.text((x + 34, by + 44), n, 48, "b", col, a)
        c.text((x + 104, by + 50), h, 40, "b", NAVY, a)
        c.line([(x + 34, by + 130), (x + bw - 34, by + 130)], LG, 2, a)
        for j, b in enumerate(bl):
            c.text((x + 36, by + 168 + j * 92), b, 30, "b" if b.startswith("→") else "r", col if b.startswith("→") else INK, a)

def s_market(c, sc, ts, i):
    T = lambda k: cue(sc, k)
    y = chrome(c, "market", ts, i, "서울 커피·제과 시장은 3년째 제자리, 점포는 892곳 줄었다", "근거 ① 시장", "출처: 서울 열린데이터광장 상권분석서비스 추정매출·점포(커피-음료·제과점, 2022.3Q–2026.2Q) · 단위: 억 원(분기), 곳")
    q = [9154, 9051, 8619, 9105, 9004, 8913, 8160, 8975, 9341, 8959, 8514, 9288]
    a = prog(ts, 0.3, .5)
    cnt = eo((ts - 0.3) / 1.6)
    kpi(c, ML, y + 10, 520, 200, f"{3.61 * cnt:.2f}조 원", "연 매출 (최근 4개 분기)", "3년 연평균 +0.2%", a, NAVY, 70)
    kpi(c, ML, y + 240, 520, 200, f"-{int(892 * cnt)}곳", "커피·제과 점포 3년 증감", "21,888 → 20,996곳 (-4.1%)", prog(ts, 1.0, .5), RED, 70)
    # chart
    x0, x1, yt, yb = ML + 600, W - ML, y + 70, y + 440
    pos = [0, 1, 2, 3, 8, 9, 10, 11, 12, 13, 14, 15]; X = lambda p: x0 + 60 + p * (x1 - x0 - 90) / 15
    lo, hi = 0, 10000; Y = lambda v: yb - (v - lo) / (hi - lo) * (yb - yt)
    c.text((x0 + 50, yt - 52), "서울 커피·제과 분기 추정매출 (억 원)", 22, "m", GREY, a)
    for v in (0, 5000, 10000):
        c.line([(x0 + 50, Y(v)), (x1, Y(v))], LG, 1, a)
        if v < 10000: c.text((x0 + 40, Y(v)), fmt(v), 18, "r", GREY, a, "rm")
    gp = clamp((ts - 0.6) / 2.4)
    for k, v in enumerate(q):
        if k / 12 > gp: break
        bx = X(pos[k]); hh = (Y(0) - Y(v))
        c.rect((bx - 22, Y(v), bx + 22, Y(0)), fill=mix(NAVY, WHITE, .15) if k >= 8 else mix(NAVY, WHITE, .55), a=a)
        if k in (0, 11): c.text((bx, Y(v) - 14), fmt(v), 20, "s", NAVY, a, "mb")
    for p, l in [(0, "22.3Q"), (3, "23.2Q"), (8, "24.3Q"), (15, "26.2Q")]: c.text((X(p), yb + 22), l, 18, "r", GREY, a, "mm")
    c.text((X(5.5), Y(4800)), "미수집 구간", 18, "r", GREY, a * .8, "mm")
    a2 = prog(ts, T(1), .5)
    c.rect((ML, y + 480, W - ML, y + 560), fill=BLUE_L, r=12, a=a2)
    c.text((ML + 30, y + 520), "시사점  새 매장은 남의 매출을 가져와야 한다 → 수요가 공급보다 빨리 늘어나는 권역만 고른다", 30, "s", NAVY, a2, "lm")

def s_metrics(c, sc, ts, i):
    T = lambda k: cue(sc, k)
    y = chrome(c, "metrics", ts, i, "1,105개 권역을 상호 배타적인 세 질문으로 점수화했다", "지표 설계 · MECE", "출처: 서울 열린데이터광장 추정매출·직장인구·상주인구·길단위인구·점포 OpenAPI · 성장률 = 2025.3Q–26.2Q vs 2022.3Q–23.2Q 연평균")
    a = prog(ts, 0.2, .5); cnt = eo((ts - .2) / 1.4)
    c.rect((ML, y + 10, ML + 360, y + 150), fill=XLG, r=14, a=a)
    c.text((ML + 30, y + 40), "서울시 상권", 24, "m", GREY, a); c.text((ML + 30, y + 74), f"{int(1650 * cnt):,}곳", 52, "b", NAVY, a)
    c.text((ML + 395, y + 80), "→", 50, "b", GREY, a, "mm")
    c.rect((ML + 430, y + 10, ML + 820, y + 150), fill=NAVY, r=14, a=a)
    c.text((ML + 460, y + 40), "반경 1km 권역 (규모 필터 후)", 24, "m", (160, 180, 210), a); c.text((ML + 460, y + 74), f"{int(1105 * cnt):,}개", 52, "b", WHITE, a)
    qs = [("40%", "실현 성장", "이미 팔리고 있는가?", "커피 매출 CAGR 35 · 거래건수 CAGR 35 · 최근 1년 모멘텀 30", NAVY),
          ("40%", "선행 수요", "앞으로 살 사람이 늘고 있는가?", "직장인구 50 · 상주인구 40 · 유동인구 10 (증가율+증가 인원)", BLUE),
          ("20%", "공급 여백", "경쟁이 아직 비어 있는가?", "매출 증가율 - 점포 증가율 60 · 점포당 매출 40", GREEN)]
    for k, (wt, nm, qq, det, col) in enumerate(qs):
        ak = prog(ts, T(1) + k * .9, .5); yy = y + 190 + k * 118
        c.rect((ML, yy, ML + 1240, yy + 100), fill=WHITE, outline=LG, width=2, r=12, a=ak)
        c.rect((ML, yy, ML + 10, yy + 100), fill=col, a=ak)
        c.text((ML + 40, yy + 50), wt, 46, "b", col, ak, "lm")
        c.text((ML + 170, yy + 32), nm + "  ·  " + qq, 30, "b", NAVY, ak, "lm")
        c.text((ML + 170, yy + 72), det, 22, "r", GREY, ak, "lm")
    a3 = prog(ts, T(2), .5); bx = ML + 1280
    c.rect((bx, y + 10, W - ML, y + 545), fill=RED_L, r=14, a=a3)
    c.text((bx + 30, y + 46), "데이터 왜곡 제거", 30, "b", RED, a3)
    rows = [("집계 범위 변경", "마곡역 상권: 2025.2Q 전 매출 0원,", "커피 매출 미집계 → 매출 성장 제외"),
            ("계단식 급등", "잠실역: 제과 연 63억 → 289억 원", "한 분기 +60% 초과 → 매출 성장 제외"),
            ("규모 기준", "권역 연매출 60억 원 · 점포 25곳 이상", "전통시장 중심 권역 제외")]
    for k, (h, l1, l2) in enumerate(rows):
        yy = y + 110 + k * 140
        c.text((bx + 30, yy), h, 26, "b", NAVY, a3); c.text((bx + 30, yy + 42), l1, 22, "r", INK, a3); c.text((bx + 30, yy + 74), l2, 22, "r", INK, a3)

def s_insight1(c, sc, ts, i):
    T = lambda k: cue(sc, k)
    y = chrome(c, "insight1", ts, i, "‘뜨는’ 성수는 449위, 1위는 삼성·영동대로였다", "인사이트 ① 핫플 ≠ 성장 상권", "출처: 서울 열린데이터광장 상권분석서비스 기반 성장 점수(1,105개 권역) · 점포·거래 증감은 3년 비교, 커피-음료·제과점")
    a = prog(ts, 0.2, .5)
    x0, x1, yy = ML + 40, W - ML - 40, y + 230
    c.text((ML, y + 30), "1,105개 권역 성장 점수 순위", 26, "m", GREY, a)
    c.line([(x0, yy), (x1, yy)], LG, 6, a)
    X = lambda r: x0 + (r - 1) / 1104 * (x1 - x0)
    for r in (250, 500, 750, 1105): c.text((X(r), yy + 30), f"{r}위", 20, "r", GREY, a, "mt")
    pts = [(14, "마곡", NAVY, 1, 0.9, 14), (8, "영등포·문래", NAVY, 1, 0.8, 8), (1, "삼성·영동대로", BLUE, -1, T(2), 1), (449, "성수", RED, -1, T(1), 449), (974, "청량리", GREY, -1, 1.2, 974), (365, "잠실역 중심", GREY, 1, 1.1, 365)]
    for r, nm, col, side, t0, _ in pts:
        ap = prog(ts, t0, .5)
        if ap <= 0: continue
        big = nm in ("삼성·영동대로", "성수")
        c.circle((X(r), yy), 20 if big else 11, fill=col, a=ap)
        if r < 20:
            ly = {1: yy - 90, 8: yy + 80, 14: yy + 130}[r]
            c.line([(X(r), yy + (-20 if side < 0 else 12)), (X(r), ly + (20 if side < 0 else -18))], col, 2, ap)
            c.text((X(r) - 6, ly), f"{r}위 {nm}", 40 if big else 26, "b" if big else "s", col, ap, "lm")
            continue
        ly = yy - 90 if side < 0 else yy + 90
        c.line([(X(r), yy + (-20 if side < 0 else 12)), (X(r), ly + (24 if side < 0 else -20))], col, 2, ap)
        c.text((X(r), ly), f"{r}위 {nm}", 40 if big else 26, "b" if big else "s", col, ap, "mm")
    a2 = prog(ts, T(1) + .6, .5)
    bx, by = ML, y + 440
    cards = [("성수 · 449위", [("점포", "+8.0%"), ("거래건수", "-1.2%/년"), ("상주인구", "-6.1%/년"), ("점포당 매출", "1.1억")], RED, RED_L, a2),
             ("삼성·영동대로 · 1위", [("커피 매출", "+13.4%/년"), ("직장인구", "+12.8%/년"), ("점포", "+1.5%"), ("점포당 매출", "4.8억")], BLUE, BLUE_L, prog(ts, T(2), .5))]
    cw = (W - 2 * ML - 40) / 2
    for k, (h, kv, col, bg, ak) in enumerate(cards):
        x = bx + k * (cw + 40)
        c.rect((x, by, x + cw, by + 210), fill=bg, r=14, a=ak)
        c.text((x + 34, by + 38), h, 36, "b", col, ak)
        for j, (kk, vv) in enumerate(kv):
            xx = x + 34 + j * (cw - 68) / 4
            c.text((xx, by + 104), kk, 23, "m", GREY, ak); c.text((xx, by + 138), vv, 38, "b", NAVY, ak)

def s_economics(c, sc, ts, i):
    T = lambda k: cue(sc, k)
    y = chrome(c, "economics", ts, i, "결정을 가른 것은 ‘점포 하나가 버는 돈’이다", "인사이트 ② 유닛 이코노믹스", "출처: 서울 열린데이터광장 추정매출·점포(커피-음료, 2025.3Q–26.2Q, 권역 반경 1km) · 임대료: 한국부동산원 상업용부동산 임대동향(1층 기준) 인용")
    # left: txn per store per day
    a = prog(ts, T(1), .5); x0 = ML; cw = 800
    c.text((x0, y + 20), "점포당 하루 거래 건수 (건)", 28, "b", NAVY, a)
    bars = [("삼성·영동대로", 158.2, BLUE), ("영등포·문래", 72.9, GREY), ("마곡 (제과)", 60.6, GREY), ("서울 평균", 60.4, LG)]
    for k, (nm, v, col) in enumerate(bars):
        yy = y + 90 + k * 118; g = eo((ts - T(1) - k * .12) / .8); L = 230 + 0
        c.text((x0, yy + 36), nm, 27, "m", INK, a, "lm")
        c.rect((x0 + L, yy + 4, x0 + L + (cw - L - 120) * v / 170 * g, yy + 70), fill=col, r=6, a=a)
        c.text((x0 + L + (cw - L - 120) * v / 170 * g + 14, yy + 37), f"{v * g:.0f}", 34, "b", NAVY, a, "lm")
    c.text((x0, y + 590), "삼성 = 서울 평균의 2.6배", 36, "b", BLUE, prog(ts, T(1) + 1.2, .5))
    # right: affordable rent
    a2 = prog(ts, T(2), .5); rx = ML + 900; rw = W - ML - rx
    c.text((rx, y + 20), "같은 22평 매장이 감당할 수 있는 임대료 (㎡당 월, 만 원)", 28, "b", NAVY, a2)
    mx = 16.0; X = lambda v: rx + 200 + (rw - 260) * v / mx
    vals = [("삼성", 14.2, BLUE), ("마곡", 1.9, GREY), ("영등포", 0.0, RED)]
    for v, l in [(7.29, "테헤란로 1층 시세 7.29"), (2.67, "전국 평균 2.67")]:
        c.line([(X(v), y + 76), (X(v), y + 500)], (150, 160, 175) if v > 5 else LG, 2, a2)
        c.text((X(v) + 8, y + 520), l, 21, "s" if v > 5 else "m", NAVY if v > 5 else GREY, a2, "lm")
    for k, (nm, v, col) in enumerate(vals):
        yy = y + 100 + k * 140; g = eo((ts - T(2) - k * .15) / .8)
        c.text((rx, yy + 36), nm, 28, "m", INK, a2, "lm")
        c.rect((rx + 200, yy, max(rx + 204, X(v * g)), yy + 72), fill=col, r=6, a=a2)
        lx = max(rx + 204, X(v * g)) + 14
        if 0 < v < 4: lx = X(2.67) + 14
        lab = "0원 (임대료 전 적자)" if v == 0 else f"{v * g:.1f}"
        c.rect((lx - 6, yy + 16, lx + tw(lab, 32, "b") + 6, yy + 58), fill=WHITE, a=a2)
        c.text((lx, yy + 37), lab, 32, "b", col if v == 0 else NAVY, a2, "lm")
    c.text((rx, y + 590), "삼성은 시세의 약 2배까지 버틴다", 36, "b", BLUE, prog(ts, T(2) + 1.6, .5))

def s_insight2(c, sc, ts, i):
    T = lambda k: cue(sc, k)
    y = chrome(c, "insight2", ts, i, "삼성에서 커피는 +35%, 빵은 -33%: 업태를 커피 주도로 바꾼 발견", "인사이트 ③ 업종 디커플링", "출처: 서울 열린데이터광장 추정매출(삼성역·코엑스·강남MICE·포스코사거리·봉은사역 상권, 2022.3Q–2026.2Q) · 단위: 억 원(분기)")
    cf = [206.4, 198.9, 203.8, 170.1, 216.4, 200.5, 189.8, 210.9, 269.7, 271.9, 255.0, 258.6]
    bk = [81.9, 63.9, 63.0, 56.5, 62.5, 59.0, 50.6, 52.2, 57.4, 56.7, 33.3, 29.3]
    x0, x1, yt, yb = ML + 60, ML + 1000, y + 40, y + 520
    pos = [0, 1, 2, 3, 8, 9, 10, 11, 12, 13, 14, 15]; X = lambda p: x0 + p * (x1 - x0) / 15; Y = lambda v: yb - v / 300 * (yb - yt)
    a = prog(ts, 0.2, .5)
    for v in (0, 100, 200, 300):
        c.line([(x0, Y(v)), (x1, Y(v))], LG, 1, a); c.text((x0 - 12, Y(v)), str(v), 18, "r", GREY, a, "rm")
    for p, l in [(0, "22.3Q"), (3, "23.2Q"), (8, "24.3Q"), (15, "26.2Q")]: c.text((X(p), yb + 22), l, 18, "r", GREY, a, "mm")
    gp = clamp((ts - 0.4) / 3.2)
    for ser, col, nm in ((cf, COFFEE, "커피-음료"), (bk, BAKERY, "제과점")):
        n = max(1, int(gp * 12) + 1); pts = [(X(pos[k]), Y(ser[k])) for k in range(min(12, n))]
        if len(pts) >= 2:
            seg1 = [p for k, p in enumerate(pts) if k < 4]; seg2 = [p for k, p in enumerate(pts) if k >= 4]
            if len(seg1) >= 2: c.line(seg1, col, 6, a)
            if len(seg2) >= 2: c.line(seg2, col, 6, a)
        for p in pts: c.circle(p, 7, fill=col, a=a)
        if gp >= 1: c.text((X(15) + 16, Y(ser[11])), f"{nm} {ser[11]:.0f}억", 24, "b", col, a, "lm")
    a1 = prog(ts, 1.8, .5); bx = ML + 1300
    kpi(c, bx, y + 40, W - ML - bx, 210, "+35%", "커피 연매출 3년 비교", "779억 → 1,055억 원", a1, COFFEE, 72)
    kpi(c, bx, y + 280, W - ML - bx, 210, "-33%", "제과 연매출 3년 비교", "265억 → 177억 원", prog(ts, 2.6, .5), RED, 72)
    a2 = prog(ts, T(1), .5)
    c.rect((ML, y + 570, W - ML, y + 640), fill=BLUE_L, r=12, a=a2)
    c.text((ML + 30, y + 605), "So what  대형 베이커리 단독 업태(X)  →  커피가 이끌고 빵은 동반 구매로 따라가는 그랩앤고(O)", 29, "s", NAVY, a2, "lm")

def s_concept(c, sc, ts, i):
    T = lambda k: cue(sc, k)
    y = chrome(c, "concept", ts, i, "타깃의 하루 시간표가 공간 컨셉 ‘플랫폼’을 결정했다", "컨셉 ① 타깃 → 공간", "출처: 서울 열린데이터광장 직장인구·추정매출(삼성 권역, 2025.3Q–26.2Q) · 결제 건수 비중, 건당 금액 단위 원")
    # chain
    chain = ["타깃", "공간", "메뉴", "손익"]; cx = ML
    for k, s in enumerate(chain):
        on = k <= 1; a = prog(ts, 0.1 + k * .15, .4)
        c.rect((cx, y + 5, cx + 170, y + 55), fill=NAVY if on else XLG, r=27, a=a)
        c.text((cx + 85, y + 30), s, 24, "b", WHITE if on else GREY, a, "mm")
        if k < 3: c.text((cx + 195, y + 30), "→", 26, "b", GREY, a, "mm")
        cx += 220
    # left persona facts
    facts = [(T(0), "30~40대 54~57%", "권역 직장인 연령"), (T(0) + .4, "남성 59%", "커피 결제자 (서울 53%)"),
             (T(1), "아침 26.7% · 6,316원", "결제 건수 비중 · 건당 금액"), (T(1) + .5, "점심 35.8% · 10,113원", "팀 단위 주문 (서울보다 +19%)"), (T(1) + 1.0, "퇴근 제과 30.1%", "17~21시 빵 결제 비중")]
    for k, (t0, big, lab) in enumerate(facts):
        a = prog(ts, t0, .45); yy = y + 90 + k * 100
        c.rect((ML, yy, ML + 640, yy + 86), fill=XLG, r=10, a=a)
        c.text((ML + 26, yy + 30), big, 32, "b", NAVY, a, "lm"); c.text((ML + 26, yy + 64), lab, 21, "r", GREY, a, "lm")
    # right floor plan
    a = prog(ts, T(2), .6); px, py, s = ML + 760, y + 110, 84
    PW, PH = 11 * s * .92, 6.6 * s * .92; k = .92 * s
    c.text((px, y + 80), "플랫폼 · 22평 평면", 26, "b", NAVY, a)
    c.rect((px, py, px + PW, py + PH), outline=NAVY, width=4, a=a)
    zones = [(0, 0, 3.2, 3.0, "미팅 부스 8석", (232, 214, 194)), (3.2, 0, 4.6, 2.2, "바·제조", (222, 208, 198)), (7.8, 0, 3.2, 2.2, "베이크오프", LG),
             (3.2, 2.2, 3.0, 1.4, "주문", (222, 208, 198)), (6.2, 2.2, 1.6, 1.4, "빵 진열", (247, 226, 186)), (7.8, 2.2, 3.2, 1.4, "모바일 픽업", BLUE_L),
             (3.2, 3.6, 4.6, 1.6, "주문 현황판(출발 안내판)", XLG), (0, 5.2, 5.5, 1.4, "창가 바 10석", (232, 214, 194))]
    for zx, zy, zw, zh, nm, col in zones:
        c.rect((px + zx * k + 3, py + zy * k + 3, px + (zx + zw) * k - 3, py + (zy + zh) * k - 3), fill=col, r=6, a=a)
        c.text((px + (zx + zw / 2) * k, py + (zy + zh / 2) * k), nm, 20, "s", NAVY, a, "mm")
    a2 = prog(ts, T(2) + 1.6, .5)
    for dx, nm, col in [(5.0, "주문 입구", NAVY), (9.4, "픽업 입구", BLUE)]:
        c.rect((px + dx * k - 50, py + PH - 6, px + dx * k + 50, py + PH + 6), fill=col, a=a2)
        c.text((px + dx * k, py + PH + 30), nm, 22, "b", col, a2, "mm")
    c.text((px + PW, y + 80), "퇴근길 빵 수요(30.1%) → 출구 옆 진열", 22, "b", BAKERY, prog(ts, T(2) + 2.6, .5), "ra")

def s_menu(c, sc, ts, i):
    T = lambda k: cue(sc, k)
    y = chrome(c, "menu", ts, i, "메뉴 가격은 시간대별 결제 금액에서 거꾸로 설계했다", "컨셉 ② 메뉴", "출처: 서울 열린데이터광장 추정매출(삼성 권역 커피-음료·제과점, 2025.3Q–26.2Q) · 건당 금액 = 매출액 ÷ 결제 건수, 단위 원")
    x0, x1, ly = ML + 40, W - ML - 40, y + 140; a = prog(ts, 0.2, .5)
    c.line([(x0, ly), (x1, ly)], NAVY, 4, a)
    for hr in range(7, 21):
        X = x0 + (hr - 7) / 13 * (x1 - x0); c.line([(X, ly - 10), (X, ly + 10)], NAVY, 2, a); c.text((X, ly - 26), f"{hr}시", 20, "r", GREY, a, "mb")
    cards = [(8, "아침 세트", "6,500원", "아메리카노 + 버터롤", "아침 커피 건당 6,316원", "결제 건수의 26.7%", NAVY),
             (12.5, "팀 오더 4잔 캐리어", "17,000원", "8잔 32,000원 · 회의 박스", "점심 커피 건당 10,113원", "서울보다 +19%", BLUE),
             (18, "식사빵 박스", "13,500원", "캄파뉴·식빵 3종", "퇴근 제과 건당 13,613원", "빵 결제의 30.1%", BAKERY)]
    cw = 470
    for k, (hr, nm, pr, sub, ev, ev2, col) in enumerate(cards):
        ak = prog(ts, T(1) + k * 1.4, .5); X = x0 + (hr - 7) / 13 * (x1 - x0); cx = clamp(X - cw / 2, ML, W - ML - cw)
        c.circle((X, ly), 14, fill=col, a=ak); c.line([(X, ly + 14), (X, y + 220)], col, 2, ak)
        c.rect((cx, y + 220, cx + cw, y + 640), fill=WHITE, outline=LG, width=2, r=14, a=ak)
        c.rect((cx, y + 220, cx + cw, y + 228), fill=col, a=ak)
        c.text((cx + 32, y + 268), nm, 34, "b", NAVY, ak); c.text((cx + 32, y + 326), pr, 76, "b", col, ak)
        c.text((cx + 32, y + 434), sub, 26, "r", INK, ak)
        c.rect((cx + 20, y + 500, cx + cw - 20, y + 620), fill=XLG, r=10, a=ak)
        c.text((cx + 42, y + 536), "근거  " + ev, 26, "b", NAVY, ak, "lm"); c.text((cx + 42, y + 582), ev2, 24, "r", GREY, ak, "lm")
    a0 = prog(ts, T(0) + .3, .5)
    c.text((ML, y + 50), "음료 70 : 푸드 30 · 32개 품목 · 블렌디드 원가율 28.2% · 객단가 목표 9,900원 (권역 평균 8,982원)", 26, "m", INK, a0)

def s_pnl(c, sc, ts, i):
    T = lambda k: cue(sc, k)
    y = chrome(c, "pnl", ts, i, "손익분기는 하루 144건, 2029년 영업이익 1.07억 원(14.9%)", "손익 시뮬레이션", "출처: 추정매출 기반 자체 모델 · 임대료 ㎡당 72,900원(부동산원 집계 인용), 2027 최저임금 10,700원 → 시급 인력 15,000원/시간 · 부가세 제외")
    # BE gauge
    a = prog(ts, T(0), .5); gx0, gx1, gy = ML, ML + 760, y + 200
    c.text((ML, y + 30), "하루 거래 건수: 손익분기 vs 권역 평균", 26, "b", NAVY, a)
    X = lambda v: gx0 + (v - 80) / (220 - 80) * (gx1 - gx0)
    c.rect((gx0, gy - 14, gx1, gy + 14), fill=XLG, r=14, a=a)
    c.rect((gx0, gy - 14, X(144), gy + 14), fill=RED_L, r=14, a=a)
    c.rect((X(144), gy - 14, gx1, gy + 14), fill=GREEN_L, r=14, a=a)
    for v, l, col, up in [(144, "손익분기 144", RED, True), (158, "권역 평균 158", NAVY, False), (201, "삼성역 상권 201", GREEN, True)]:
        ak = prog(ts, T(0) + (0.3 if v == 144 else 0.8 if v == 158 else 1.3), .4)
        c.line([(X(v), gy - 40), (X(v), gy + 40)], col, 4, ak)
        c.text((X(v), gy - 54 if up else gy + 54), l, 26, "b", col, ak, "mb" if up else "mt")
    c.rect((ML, y + 330, ML + 760, y + 410), fill=RED_L, r=12, a=prog(ts, T(0) + 2, .5))
    c.text((ML + 26, y + 370), "여유는 9%뿐 → 동선·메뉴 설계 = 손익 설계", 32, "b", RED, prog(ts, T(0) + 2, .5), "lm")
    for j, (s_, t_) in enumerate([("초기 투자 1.82억 원 · 4-wall EBITDA 기준 회수 2.3년", 2.4), ("임대료 +30%에도 하루 180건이면 영업이익률 8.4%", 2.8), ("하루 130건이면 임대료를 깎아도 적자 → 거래량이 먼저", 3.2)]):
        c.text((ML, y + 450 + j * 52), "·  " + s_, 27, "r", INK, prog(ts, T(0) + t_, .5))
    # 3-year bars
    a2 = prog(ts, T(1), .5); bx0 = ML + 900; bx1 = W - ML; byb = y + 560; byt = y + 80
    c.text((bx0, y + 30), "3개년 전망 (억 원)", 26, "b", NAVY, a2)
    Y = lambda v: byb - (v + 1) / 9 * (byb - byt)
    c.line([(bx0, Y(0)), (bx1, Y(0))], GREY, 2, a2)
    data = [("2027", 4.59, -0.28, "오픈 · 85%"), ("2028", 5.40, 0.28, "기준안"), ("2029", 7.21, 1.07, "환승센터 개통 후")]
    gw = (bx1 - bx0) / 3
    for k, (yr, rev, op, note) in enumerate(data):
        g = eo((ts - T(1) - k * .5) / .7); cx = bx0 + gw * k + gw / 2
        c.rect((cx - 70, Y(rev * g), cx - 6, Y(0)), fill=mix(NAVY, WHITE, .65), r=4, a=a2)
        c.text((cx - 38, Y(rev * g) - 10), f"{rev:.1f}", 22, "m", GREY, a2 * g, "mb")
        col = GREEN if op >= 0 else RED
        y1, y2 = sorted([Y(op * g), Y(0)])
        c.rect((cx + 6, y1, cx + 70, y2 + (0 if op >= 0 else 0)), fill=col, r=4, a=a2)
        c.text((cx + 38, (Y(op * g) - 10) if op >= 0 else (Y(op * g) + 10), ), f"{op:+.2f}", 26, "b", col, a2 * g, "mb" if op >= 0 else "mt")
        c.text((cx, byb + 26), yr, 26, "b", NAVY, a2, "mm"); c.text((cx, byb + 58), note, 20, "r", GREY, a2, "mm")
    c.text((bx1, y + 34), "■ 순매출  ■ 영업이익", 20, "m", GREY, a2, "ra")

def s_close(c, sc, ts, i):
    T = lambda k: cue(sc, k)
    y = chrome(c, "close", ts, i, "2027년 상반기, 삼성·영동대로에서 시작한다", "NEXT STEPS", "출처: 본 분석 전체 · 개발 일정(GTX-A 삼성역·영동대로 복합환승센터 2028년 목표)은 공개 계획 기준으로 출점 전 재확인 필요")
    steps = [("2026.4Q", "후보 상가 3곳 실사", "임대료·보증금·권리금·배기·전기 용량"), ("2027.1Q", "보행량 실측·POS 검증", "봉은사역 출구·코엑스 북문, 07–09시·11–14시"), ("2027.상반기", "1호점 오픈", "1년 차 목표 하루 134건, 6개월 차 점검")]
    sw = (W - 2 * ML - 60) / 3
    for k, (when, h, d) in enumerate(steps):
        a = prog(ts, T(0) + k * .5, .5); x = ML + k * (sw + 30)
        c.rect((x, y + 20, x + sw, y + 290), fill=XLG, r=14, a=a)
        c.text((x + 32, y + 60), when, 28, "b", BLUE, a); c.text((x + 32, y + 112), h, 40, "b", NAVY, a); c.text((x + 32, y + 196), d, 24, "r", INK, a)
    a2 = prog(ts, T(1), .6)
    c.rect((ML, y + 340, W - ML, y + 600), fill=NAVY, r=18, a=a2)
    c.text((W / 2, y + 420), "삼성·영동대로 · 커피가 이끌고 빵이 따라가는 22평 그랩앤고", 48, "b", WHITE, a2, "mm")
    c.text((W / 2, y + 510), "순매출 5.4억  ·  손익분기 144건/일  ·  2029년 영업이익률 14.9%", 38, "s", (190, 205, 230), a2, "mm")

SCN = {"answer": s_answer, "pillars": s_pillars, "market": s_market, "metrics": s_metrics, "insight1": s_insight1, "economics": s_economics,
       "insight2": s_insight2, "concept": s_concept, "menu": s_menu, "pnl": s_pnl, "close": s_close}

def frame(n):
    t = n / FPS; c = Canvas()
    scs = TL["scenes"]; idx = 0
    for k, sc in enumerate(scs):
        if t >= sc["start"] - 0.25: idx = k
    sc = scs[idx]; ts = t - sc["start"] + 0.25
    SCN[sc["name"]](c, sc, ts, idx)
    caption(c, t)
    # scene fade from white + open/close fade
    fa = 1 - eo(ts / 0.35)
    if fa > 0: c.layer(fa, lambda d: d.rectangle((0, 0, W, H), fill=WHITE))
    if t > TOTAL - 1.0: c.layer(clamp((t - (TOTAL - 1.0)) / 1.0), lambda d: d.rectangle((0, 0, W, H), fill=NAVY))
    if t < 0.4: c.layer(1 - t / 0.4, lambda d: d.rectangle((0, 0, W, H), fill=WHITE))
    return c.im.convert("RGB").tobytes()

if __name__ == "__main__":
    only = os.environ.get("ONLY")
    if only:  # stills for QA: ONLY="12.0,30.5"
        for s in only.split(","):
            n = int(float(s) * FPS); Image.frombytes("RGB", (W, H), frame(n)).save(f"{TMP}/still_{float(s):06.1f}.png")
        sys.exit()
    p = subprocess.Popen([FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", f"{TMP}/mix.wav", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                          "-shortest", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    with Pool(max(2, os.cpu_count() - 1)) as pool:
        for k, fr in enumerate(pool.imap(frame, range(NF), chunksize=8)):
            p.stdin.write(fr)
            if k % 300 == 0: print(f"frame {k}/{NF}", flush=True)
    p.stdin.close(); p.wait(); print("done", OUT)
