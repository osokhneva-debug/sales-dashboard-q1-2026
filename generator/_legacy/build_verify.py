import csv,json,re
from collections import defaultdict

# ---- load current constants from index.html (ground truth) ----
s=open("index.html",encoding="utf-8").read()
def extract(name):
    key=f"const {name} = "; i=s.find(key)+len(key); j=s.find("\n",i)
    return json.loads(s[i:j].rstrip()[:-1])
CUR={"DATA":extract("DATA"),"DRILLDOWN":extract("DRILLDOWN"),"PARTNERS":extract("PARTNERS")}

MMAP={'января':'Январь','февраля':'Февраль','марта':'Март','апреля':'Апрель','мая':'Май','июня':'Июнь',
      'июля':'Июль','августа':'Август','сентября':'Сентябрь','октября':'Октябрь','ноября':'Ноябрь','декабря':'Декабрь'}
ORDER=['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']

rows=list(csv.reader(open("svod.csv",encoding="utf-8")))
H={h:i for i,h in enumerate(rows[0])}
def cell(r,k):
    i=H[k]; return r[i].strip() if i<len(r) else ""
def num(x):
    x=(x or "").replace("\xa0","").replace(" ","").replace("₽","").replace(",",".")
    if x in ("","#REF!","-"): return 0.0
    try: return float(x)
    except: return 0.0
def toks(v):
    if not v or v=="#REF!": return []
    return [t.strip() for t in v.split(",") if t.strip()]

present=set()
recs=[]
for r in rows[1:]:
    if not r or not r[0].strip(): continue
    m=MMAP.get(r[0].strip())
    if not m: continue
    present.add(m)
    recs.append((m,r))
MONTHS=[m for m in ORDER if m in present]
Z={mm:0 for mm in MONTHS}

tot={mm:{"gmv":0.0,"rev":0.0,"cnt":0.0} for mm in MONTHS}
dir_m=defaultdict(lambda:{mm:{"gmv":0.0,"rev":0.0,"cnt":0.0} for mm in MONTHS})
prof=defaultdict(lambda:defaultdict(lambda:{"rev":0.0,"cnt":0.0}))
skill=defaultdict(lambda:defaultdict(lambda:{"rev":0.0,"cnt":0.0}))
dd_prog=defaultdict(lambda:defaultdict(lambda:{mm:{"rev":0.0,"cnt":0.0} for mm in MONTHS}))
dd_part=defaultdict(lambda:defaultdict(lambda:{mm:{"rev":0.0,"cnt":0.0} for mm in MONTHS}))
p_month=defaultdict(lambda:{mm:{"rev":0.0,"cnt":0.0,"gmv":0.0} for mm in MONTHS})
p_dir_m=defaultdict(lambda:defaultdict(lambda:{mm:0.0 for mm in MONTHS}))

for m,r in recs:
    gmv=num(cell(r,"GMV")); rev=num(cell(r,"Ревевенью")); cnt=num(cell(r,"Количество продаж"))
    d=cell(r,"Направление"); d=None if d in("","#REF!") else d
    pn=cell(r,"Партнер"); pn=None if pn in("","#REF!") else pn
    prog=cell(r,"Программа"); prog=None if prog in("","#REF!") else prog
    tot[m]["gmv"]+=gmv; tot[m]["rev"]+=rev; tot[m]["cnt"]+=cnt
    if d:
        dir_m[d][m]["gmv"]+=gmv; dir_m[d][m]["rev"]+=rev; dir_m[d][m]["cnt"]+=cnt
    for t in toks(cell(r,"Профессия")): prof[t][m]["rev"]+=rev; prof[t][m]["cnt"]+=cnt
    for t in toks(cell(r,"Навык")): skill[t][m]["rev"]+=rev; skill[t][m]["cnt"]+=cnt
    if d and prog: dd_prog[d][prog][m]["rev"]+=rev; dd_prog[d][prog][m]["cnt"]+=cnt
    if d and pn: dd_part[d][pn][m]["rev"]+=rev; dd_part[d][pn][m]["cnt"]+=cnt
    if pn:
        p_month[pn][m]["rev"]+=rev; p_month[pn][m]["cnt"]+=cnt; p_month[pn][m]["gmv"]+=gmv
        if d: p_dir_m[pn][d][m]+=rev

R=lambda x:round(x,2)
# ---- build DATA ----
DATA={"months":MONTHS,
      "totals":{me:{mm:R(tot[mm][me]) for mm in MONTHS} for me in ("gmv","rev","cnt")},
      "directions":{me:{d:{mm:R(dir_m[d][mm][me]) for mm in MONTHS} for d in dir_m} for me in ("gmv","rev","cnt")},
      "professions":{me:{n:{mm:R(v[me]) for mm,v in mv.items()} for n,mv in prof.items()} for me in ("rev","cnt")},
      "skills":{me:{n:{mm:R(v[me]) for mm,v in mv.items()} for n,mv in skill.items()} for me in ("rev","cnt")}}
# ---- DRILLDOWN ----
DRILL={}
for d in set(list(dd_prog)+list(dd_part)):
    node={"programs":{},"partners":{}}
    for ent,mv in dd_prog.get(d,{}).items():
        node["programs"][ent]={mm:{"rev":R(mv[mm]["rev"]),"cnt":R(mv[mm]["cnt"])} for mm in MONTHS}
    for ent,mv in dd_part.get(d,{}).items():
        node["partners"][ent]={mm:{"rev":R(mv[mm]["rev"]),"cnt":R(mv[mm]["cnt"])} for mm in MONTHS}
    DRILL[d]=node
# ---- PARTNERS ----
first,last=MONTHS[0],MONTHS[-1]
PART={}
for pn in p_month:
    months={mm:{"rev":R(p_month[pn][mm]["rev"]),"cnt":R(p_month[pn][mm]["cnt"]),"gmv":R(p_month[pn][mm]["gmv"])} for mm in MONTHS}
    dirs={d:R(sum(p_dir_m[pn][d].values())) for d in p_dir_m[pn]}
    dj={d:R(p_dir_m[pn][d][first]) for d in p_dir_m[pn] if p_dir_m[pn][d][first]}
    da={d:R(p_dir_m[pn][d][last]) for d in p_dir_m[pn] if p_dir_m[pn][d][last]}
    PART[pn]={"months":months,"directions":dirs,"dir_jan":dj,"dir_apr":da}

NEW={"DATA":DATA,"DRILLDOWN":DRILL,"PARTNERS":PART}

# ---- COMPARE ----
def diffs(a,b,path="",out=None,tol=0.02):
    if out is None: out=[]
    if isinstance(a,dict) and isinstance(b,dict):
        ka,kb=set(a),set(b)
        for k in ka-kb: out.append(f"ONLY_NEW {path}/{k}")
        for k in kb-ka: out.append(f"ONLY_CUR {path}/{k}")
        for k in ka&kb: diffs(a[k],b[k],f"{path}/{k}",out,tol)
    elif isinstance(a,(int,float)) and isinstance(b,(int,float)):
        if abs(a-b)>tol: out.append(f"VAL {path}: new={a} cur={b}")
    elif isinstance(a,list) and isinstance(b,list):
        if a!=b: out.append(f"LIST {path}: {a} vs {b}")
    else:
        if a!=b: out.append(f"TYPE {path}: {a!r} vs {b!r}")
    return out

for name in ("DATA","DRILLDOWN","PARTNERS"):
    d=diffs(NEW[name],CUR[name])
    print(f"=== {name}: {len(d)} diffs ===")
    for x in d[:12]: print("  ",x)
    if len(d)>12: print(f"   ... +{len(d)-12} more")

print("\nMONTHS:",MONTHS)
print("June totals rebuilt:",{k:DATA['totals'][k]['Июнь'] for k in DATA['totals']})
json.dump(NEW,open("rebuilt_constants.json","w",encoding="utf-8"),ensure_ascii=False)
print("counts: dirs",len(DATA['directions']['rev']),"prof",len(DATA['professions']['rev']),"skills",len(DATA['skills']['rev']),"partners",len(PART),"drilldown",len(DRILL))
