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
GROUPS = "skill_groups.json"  # skill -> enlarged group dictionary (hand-kept)
FAKT = "fakt.csv"          # revenue streams: «Факт2025-2026»
INSIGHTS = "insights.json" # monthly conclusions journal (newest first)
OUT = "../data.js"

# Укрупнённые группы навыков. Порядок ключей в файле = приоритет при равенстве
# числа навыков, поэтому группа курса не зависит от частот и не прыгает от месяца
# к месяцу. Пополняется руками по отчёту «в Прочее ушло …» в конце сборки.
SKILL_GROUPS = json.load(open(GROUPS, encoding="utf-8"))
SKILL2GROUP = {s: g for g, ss in SKILL_GROUPS.items() for s in ss}
GROUP_PRIO = {g: i for i, g in enumerate(SKILL_GROUPS)}
OTHER = "Прочее"

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
other_rev = defaultdict(float); other_skills = defaultdict(float)  # courses no group covers
PROF_KEY = {}   # sorted profession set -> display label (keeps the sheet's own order)
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
    # Одна строка свода = один курс. Если курс размечен на несколько профессий,
    # он идёт ОДНОЙ строкой с профессиями через запятую, а не начисляется каждой
    # профессии отдельно: иначе продажи двоятся (август 2026: 15,0 млн вместо
    # 9,54 по вкладке, +57%). Правило Оли от 02.09.2026.
    pts = toks(cell(r, "Профессия"))
    if pts:
        seen = set(); ordered = [t for t in pts if not (t in seen or seen.add(t))]
        canon = PROF_KEY.setdefault(tuple(sorted(ordered)), ", ".join(ordered))
        prof[canon][m]["rev"] += rev; prof[canon][m]["cnt"] += cnt
    # Навыки: курс относится ровно к ОДНОЙ укрупнённой группе - той, где у него
    # больше всего навыков; при равенстве к той, что выше в skill_groups.json.
    # Начислять каждому навыку отдельно нельзя: курс с 3 навыками попадал в три
    # строки целиком, и август показывал 13,97 млн руб. охвата вместо 2,51 млн
    # реальной выручки. Правило Оли от 02.09.2026.
    sts = toks(cell(r, "Навык"))
    if sts:
        hits = defaultdict(int)
        for t in sts:
            g = SKILL2GROUP.get(t)
            if g: hits[g] += 1
        if hits:
            grp = min(hits, key=lambda g: (-hits[g], GROUP_PRIO[g]))
        else:
            grp = OTHER
            other_rev[m] += rev
            for t in sts: other_skills[t] += rev
        skill[grp][m]["rev"] += rev; skill[grp][m]["cnt"] += cnt
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
# dict.fromkeys, not set(): keeps CSV order and makes output deterministic across runs
for d in dict.fromkeys(list(dd_prog) + list(dd_part)):
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
# A month is real only if at least one revenue stream has data for it. A lone
# "Total Revenue EdTech" value is a plan stub (incident 03.08.2026: 20.6M copied
# into Jul-Dec as plan), not a fact — never let it become the "latest month".
STREAMS["months"] = [m for m in ORDER if any(m in STREAMS[k] for k in ("cpa", "cpc", "fix", "adv"))]
for k in LAB.values():
    STREAMS[k] = {m: v for m, v in STREAMS[k].items() if m in STREAMS["months"]}

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
# skill groups: one course = one group, so the column is money and sums up
_sr = DATA['skills']['rev']
_sg = {g: round(sum(_sr[g].values()), 2) for g in _sr}
print(f"skill groups: {len(_sg)} | {last} sum:", round(sum(_sr[g].get(last, 0) for g in _sg), 2))
for g, v in sorted(_sg.items(), key=lambda x: -x[1]):
    print(f"   {_sr[g].get(last, 0):12,.0f} {last} | {v:12,.0f} год | {g}")
_ot = round(sum(other_rev.values()), 2)
_os_top = sorted(other_skills.items(), key=lambda x: -x[1])[:15]
print(f"в Прочее ушло {_ot:,.0f} руб., навыки: " +
      (", ".join(f"{s} ({v:,.0f})" for s, v in _os_top) if _os_top else "нет"))
print("last month totals:", {k: DATA['totals'][k][last] for k in DATA['totals']})

# stamp index.html so browsers fetch the fresh data.js instead of a cached copy
# (the tag had no version, so an updated dashboard could still show old numbers).
import re as _re, time as _time, os as _os
_idx = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "index.html")
_html = open(_idx, encoding="utf-8").read()
_stamped = _re.sub(r'<script src="data\.js(?:\?v=\d+)?"></script>',
                   f'<script src="data.js?v={_time.strftime("%Y%m%d%H%M")}"></script>', _html, count=1)
if _stamped != _html:
    open(_idx, "w", encoding="utf-8").write(_stamped)
    print("STAMPED index.html with data.js version")
