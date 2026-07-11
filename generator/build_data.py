#!/usr/bin/env python3
"""Single build step: read svod.csv + fakt.csv + insights.json, emit ../data.js.

Replaces the old 5-script patch chain (build.py, build_streams2.py, build_extras.py,
build_drilldown.py, build_deltas.py). All layout/render code now lives permanently
in ../index.html (the shell); this script only recomputes the data constants.

Usage: fetch CSVs first (see README), then `python3 build_data.py`.
"""
import csv, json
from collections import defaultdict

SVOD = "svod.csv"          # sales detail: «Сводная всех месяцев»
FAKT = "fakt.csv"          # revenue streams: «Факт2025-2026»
INSIGHTS = "insights.json" # monthly conclusions journal (newest first)
OUT = "../data.js"

# School name canon (dedupe EN/RU duplicates) — keep in sync with dashboard history
CANON = {
    "Eduson Academy": "Академия Эдюсон",
    "Moscow Business Academy": "Московская Бизнес Академия",
    "City Business School": "Сити Бизнес Скул - City Business School",
    "Сити Бизнес Скул": "Сити Бизнес Скул - City Business School",
}
MMAP = {'января':'Январь','февраля':'Февраль','марта':'Март','апреля':'Апрель','мая':'Май','июня':'Июнь',
        'июля':'Июль','августа':'Август','сентября':'Сентябрь','октября':'Октябрь','ноября':'Ноябрь','декабря':'Декабрь'}
ORDER = ['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']

# ---------- svod.csv → DATA / DRILLDOWN / PARTNERS / TAGSTATS ----------
rows = list(csv.reader(open(SVOD, encoding="utf-8")))
H = {h: i for i, h in enumerate(rows[0])}

def cell(r, k):
    i = H[k]; return r[i].strip() if i < len(r) else ""

def num(x):
    x = (x or "").replace("\xa0", "").replace(" ", "").replace("₽", "").replace(",", ".")
    try: return float(x) if x not in ("", "#REF!", "-") else 0.0
    except: return 0.0

def toks(v):
    return [t.strip() for t in v.split(",") if t.strip()] if v and v != "#REF!" else []

recs = []; present = set()
for r in rows[1:]:
    if not r or not r[0].strip(): continue
    m = MMAP.get(r[0].strip())
    if not m: continue
    present.add(m); recs.append((m, r))
MONTHS = [m for m in ORDER if m in present]
first, last = MONTHS[0], MONTHS[-1]

tot = {mm: {"gmv": 0.0, "rev": 0.0, "cnt": 0.0} for mm in MONTHS}
dir_m = defaultdict(lambda: {mm: {"gmv": 0.0, "rev": 0.0, "cnt": 0.0} for mm in MONTHS})
prof = defaultdict(lambda: defaultdict(lambda: {"rev": 0.0, "cnt": 0.0}))
skill = defaultdict(lambda: defaultdict(lambda: {"rev": 0.0, "cnt": 0.0}))
dd_prog = defaultdict(lambda: defaultdict(lambda: {mm: {"rev": 0.0, "cnt": 0.0} for mm in MONTHS}))
dd_part = defaultdict(lambda: defaultdict(lambda: {mm: {"rev": 0.0, "cnt": 0.0} for mm in MONTHS}))
p_month = defaultdict(lambda: {mm: {"rev": 0.0, "cnt": 0.0, "gmv": 0.0} for mm in MONTHS})
p_dir_m = defaultdict(lambda: defaultdict(lambda: {mm: 0.0 for mm in MONTHS}))
tag_prof = defaultdict(float); tag_skill = defaultdict(float)   # GMV by tag (mutually exclusive)
dd_prog_sch = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))  # dir->prog->school->rev

for m, r in recs:
    gmv = num(cell(r, "GMV")); rev = num(cell(r, "Ревевенью")); cnt = num(cell(r, "Количество продаж"))
    hp = bool(toks(cell(r, "Профессия"))); hn = bool(toks(cell(r, "Навык")))
    if hp: tag_prof[m] += gmv
    elif hn: tag_skill[m] += gmv
    d = cell(r, "Направление"); d = None if d in ("", "#REF!") else d
    pn = cell(r, "Партнер"); pn = None if pn in ("", "#REF!") else CANON.get(pn, pn)
    prog = cell(r, "Программа"); prog = None if prog in ("", "#REF!") else prog
    tot[m]["gmv"] += gmv; tot[m]["rev"] += rev; tot[m]["cnt"] += cnt
    if d:
        for me, val in (("gmv", gmv), ("rev", rev), ("cnt", cnt)): dir_m[d][m][me] += val
    for t in toks(cell(r, "Профессия")): prof[t][m]["rev"] += rev; prof[t][m]["cnt"] += cnt
    for t in toks(cell(r, "Навык")): skill[t][m]["rev"] += rev; skill[t][m]["cnt"] += cnt
    if d and prog: dd_prog[d][prog][m]["rev"] += rev; dd_prog[d][prog][m]["cnt"] += cnt
    if d and prog and pn: dd_prog_sch[d][prog][pn] += rev
    if d and pn: dd_part[d][pn][m]["rev"] += rev; dd_part[d][pn][m]["cnt"] += cnt
    if pn:
        p_month[pn][m]["rev"] += rev; p_month[pn][m]["cnt"] += cnt; p_month[pn][m]["gmv"] += gmv
        if d: p_dir_m[pn][d][m] += rev

R = lambda x: round(x, 2)
DATA = {"months": MONTHS,
 "totals": {me: {mm: R(tot[mm][me]) for mm in MONTHS} for me in ("gmv", "rev", "cnt")},
 "directions": {me: {d: {mm: R(dir_m[d][mm][me]) for mm in MONTHS} for d in dir_m} for me in ("gmv", "rev", "cnt")},
 "professions": {me: {n: {mm: R(v[me]) for mm, v in mv.items()} for n, mv in prof.items()} for me in ("rev", "cnt")},
 "skills": {me: {n: {mm: R(v[me]) for mm, v in mv.items()} for n, mv in skill.items()} for me in ("rev", "cnt")}}

DRILL = {}
for d in set(list(dd_prog) + list(dd_part)):
    prog_schools = {}
    for prog, schm in dd_prog_sch.get(d, {}).items():
        sl = sorted(schm.items(), key=lambda x: -x[1])
        if sl: prog_schools[prog] = sl[0][0] + (f" +{len(sl)-1}" if len(sl) > 1 else "")
    DRILL[d] = {"programs": {ent: {mm: {"rev": R(mv[mm]["rev"]), "cnt": R(mv[mm]["cnt"])} for mm in MONTHS} for ent, mv in dd_prog.get(d, {}).items()},
                "partners": {ent: {mm: {"rev": R(mv[mm]["rev"]), "cnt": R(mv[mm]["cnt"])} for mm in MONTHS} for ent, mv in dd_part.get(d, {}).items()},
                "prog_schools": prog_schools}

PART = {}
for pn in p_month:
    PART[pn] = {"months": {mm: {"rev": R(p_month[pn][mm]["rev"]), "cnt": R(p_month[pn][mm]["cnt"]), "gmv": R(p_month[pn][mm]["gmv"])} for mm in MONTHS},
                "directions": {d: R(sum(p_dir_m[pn][d].values())) for d in p_dir_m[pn]},
                "dir_jan": {d: R(p_dir_m[pn][d][first]) for d in p_dir_m[pn] if p_dir_m[pn][d][first]},
                "dir_apr": {d: R(p_dir_m[pn][d][last]) for d in p_dir_m[pn] if p_dir_m[pn][d][last]}}

TAGSTATS = {"months": MONTHS, "prof": {mm: R(tag_prof[mm]) for mm in MONTHS},
            "skill": {mm: R(tag_skill[mm]) for mm in MONTHS}, "total": {mm: R(tot[mm]["gmv"]) for mm in MONTHS}}

# ---------- fakt.csv → STREAMS ----------
frows = list(csv.reader(open(FAKT, encoding="utf-8")))

def fnum(x):
    x = (x or "").replace("\xa0", "").replace(" ", "").replace("₽", "").replace(",", ".")
    try: return float(x) if x not in ("", "#REF!", "-") else None
    except: return None

years, mon = frows[0], frows[1]
cols = [i for i, y in enumerate(years) if y.strip() == "2026"]
MEN = {'JAN':'Январь','FEB':'Февраль','MAR':'Март','APR':'Апрель','MAY':'Май','JUNE':'Июнь','JUN':'Июнь',
       'JULY':'Июль','JUL':'Июль','AUG':'Август','SEPT':'Сентябрь','SEP':'Сентябрь','OCT':'Октябрь','NOV':'Ноябрь','DEC':'Декабрь'}
LAB = {"GMV":"gmv","Кол-во покупок":"purchases","Revenue CPA":"cpa","Revenue CPС":"cpc",
       "Revenue Fix":"fix","Revenue c Рекламы":"adv","Total Revenue EdTech":"total","Клики_total":"clicks"}

def frow(l):
    for r in frows:
        if r and r[0].strip() == l: return r

STREAMS = {}
for l, k in LAB.items():
    r = frow(l); s = {}
    for i in cols:
        m = MEN.get(mon[i].strip().upper()); v = fnum(r[i]) if r and i < len(r) else None
        if m and v is not None: s[m] = round(v, 2)
    STREAMS[k] = s
STREAMS["months"] = [m for m in ORDER if m in STREAMS["total"]]

# ---------- insights.json → INSIGHTS_LOG ----------
INSIGHTS_LOG = json.load(open(INSIGHTS, encoding="utf-8"))

# ---------- emit data.js ----------
parts = []
for name, obj in (("TAGSTATS", TAGSTATS), ("STREAMS", STREAMS), ("INSIGHTS_LOG", INSIGHTS_LOG),
                  ("DATA", DATA), ("DRILLDOWN", DRILL), ("PARTNERS", PART)):
    parts.append(f"const {name} = " + json.dumps(obj, ensure_ascii=False) + ";")
open(OUT, "w", encoding="utf-8").write("// Generated by generator/build_data.py — do not edit by hand\n" + "\n".join(parts) + "\n")

# ---------- report ----------
print("WROTE", OUT, "| months:", MONTHS, "| streams months:", STREAMS["months"])
print("partners:", len(PART), "| directions:", len(DATA['directions']['rev']),
      "| prof:", len(DATA['professions']['rev']), "| skills:", len(DATA['skills']['rev']))
print("dupes gone:", all(x not in PART for x in CANON))
print("monthly CPA rev:", {mm: DATA['totals']['rev'][mm] for mm in MONTHS})
print("last month totals:", {k: DATA['totals'][k][last] for k in DATA['totals']})
