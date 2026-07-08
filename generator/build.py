import csv,json,re
from collections import defaultdict

SVOD="svod.csv"; TEMPLATE="template.html"; OUT="index_new.html"

CANON={
 "Eduson Academy":"Академия Эдюсон",
 "Moscow Business Academy":"Московская Бизнес Академия",
 "City Business School":"Сити Бизнес Скул - City Business School",
 "Сити Бизнес Скул":"Сити Бизнес Скул - City Business School",
}
MMAP={'января':'Январь','февраля':'Февраль','марта':'Март','апреля':'Апрель','мая':'Май','июня':'Июнь',
      'июля':'Июль','августа':'Август','сентября':'Сентябрь','октября':'Октябрь','ноября':'Ноябрь','декабря':'Декабрь'}
ORDER=['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']

rows=list(csv.reader(open(SVOD,encoding="utf-8")))
H={h:i for i,h in enumerate(rows[0])}
def cell(r,k):
    i=H[k]; return r[i].strip() if i<len(r) else ""
def num(x):
    x=(x or "").replace("\xa0","").replace(" ","").replace("₽","").replace(",",".")
    try: return float(x) if x not in("","#REF!","-") else 0.0
    except: return 0.0
def toks(v):
    return [t.strip() for t in v.split(",") if t.strip()] if v and v!="#REF!" else []

recs=[]; present=set()
for r in rows[1:]:
    if not r or not r[0].strip(): continue
    m=MMAP.get(r[0].strip())
    if not m: continue
    present.add(m); recs.append((m,r))
MONTHS=[m for m in ORDER if m in present]
first,last=MONTHS[0],MONTHS[-1]

tot={mm:{"gmv":0.0,"rev":0.0,"cnt":0.0} for mm in MONTHS}
dir_m=defaultdict(lambda:{mm:{"gmv":0.0,"rev":0.0,"cnt":0.0} for mm in MONTHS})
prof=defaultdict(lambda:defaultdict(lambda:{"rev":0.0,"cnt":0.0}))
skill=defaultdict(lambda:defaultdict(lambda:{"rev":0.0,"cnt":0.0}))
dd_prog=defaultdict(lambda:defaultdict(lambda:{mm:{"rev":0.0,"cnt":0.0} for mm in MONTHS}))
dd_part=defaultdict(lambda:defaultdict(lambda:{mm:{"rev":0.0,"cnt":0.0} for mm in MONTHS}))
p_month=defaultdict(lambda:{mm:{"rev":0.0,"cnt":0.0,"gmv":0.0} for mm in MONTHS})
p_dir_m=defaultdict(lambda:defaultdict(lambda:{mm:0.0 for mm in MONTHS}))
tag_prof=defaultdict(float); tag_skill=defaultdict(float)   # GMV by tag (mutually exclusive)
dd_prog_sch=defaultdict(lambda:defaultdict(lambda:defaultdict(float)))  # dir->prog->school->rev

for m,r in recs:
    gmv=num(cell(r,"GMV")); rev=num(cell(r,"Ревевенью")); cnt=num(cell(r,"Количество продаж"))
    hp=bool(toks(cell(r,"Профессия"))); hn=bool(toks(cell(r,"Навык")))
    if hp: tag_prof[m]+=gmv
    elif hn: tag_skill[m]+=gmv
    d=cell(r,"Направление"); d=None if d in("","#REF!") else d
    pn=cell(r,"Партнер"); pn=None if pn in("","#REF!") else CANON.get(pn,pn)
    prog=cell(r,"Программа"); prog=None if prog in("","#REF!") else prog
    tot[m]["gmv"]+=gmv; tot[m]["rev"]+=rev; tot[m]["cnt"]+=cnt
    if d:
        for me,val in (("gmv",gmv),("rev",rev),("cnt",cnt)): dir_m[d][m][me]+=val
    for t in toks(cell(r,"Профессия")): prof[t][m]["rev"]+=rev; prof[t][m]["cnt"]+=cnt
    for t in toks(cell(r,"Навык")): skill[t][m]["rev"]+=rev; skill[t][m]["cnt"]+=cnt
    if d and prog: dd_prog[d][prog][m]["rev"]+=rev; dd_prog[d][prog][m]["cnt"]+=cnt
    if d and prog and pn: dd_prog_sch[d][prog][pn]+=rev
    if d and pn: dd_part[d][pn][m]["rev"]+=rev; dd_part[d][pn][m]["cnt"]+=cnt
    if pn:
        p_month[pn][m]["rev"]+=rev; p_month[pn][m]["cnt"]+=cnt; p_month[pn][m]["gmv"]+=gmv
        if d: p_dir_m[pn][d][m]+=rev

R=lambda x:round(x,2)
DATA={"months":MONTHS,
 "totals":{me:{mm:R(tot[mm][me]) for mm in MONTHS} for me in("gmv","rev","cnt")},
 "directions":{me:{d:{mm:R(dir_m[d][mm][me]) for mm in MONTHS} for d in dir_m} for me in("gmv","rev","cnt")},
 "professions":{me:{n:{mm:R(v[me]) for mm,v in mv.items()} for n,mv in prof.items()} for me in("rev","cnt")},
 "skills":{me:{n:{mm:R(v[me]) for mm,v in mv.items()} for n,mv in skill.items()} for me in("rev","cnt")}}
DRILL={}
for d in set(list(dd_prog)+list(dd_part)):
    prog_schools={}
    for prog,schm in dd_prog_sch.get(d,{}).items():
        sl=sorted(schm.items(),key=lambda x:-x[1])
        if sl: prog_schools[prog]=sl[0][0]+(f" +{len(sl)-1}" if len(sl)>1 else "")
    DRILL[d]={"programs":{ent:{mm:{"rev":R(mv[mm]["rev"]),"cnt":R(mv[mm]["cnt"])} for mm in MONTHS} for ent,mv in dd_prog.get(d,{}).items()},
              "partners":{ent:{mm:{"rev":R(mv[mm]["rev"]),"cnt":R(mv[mm]["cnt"])} for mm in MONTHS} for ent,mv in dd_part.get(d,{}).items()},
              "prog_schools":prog_schools}
PART={}
for pn in p_month:
    PART[pn]={"months":{mm:{"rev":R(p_month[pn][mm]["rev"]),"cnt":R(p_month[pn][mm]["cnt"]),"gmv":R(p_month[pn][mm]["gmv"])} for mm in MONTHS},
              "directions":{d:R(sum(p_dir_m[pn][d].values())) for d in p_dir_m[pn]},
              "dir_jan":{d:R(p_dir_m[pn][d][first]) for d in p_dir_m[pn] if p_dir_m[pn][d][first]},
              "dir_apr":{d:R(p_dir_m[pn][d][last]) for d in p_dir_m[pn] if p_dir_m[pn][d][last]}}
TAGSTATS={"months":MONTHS,"prof":{mm:R(tag_prof[mm]) for mm in MONTHS},"skill":{mm:R(tag_skill[mm]) for mm in MONTHS},"total":{mm:R(tot[mm]["gmv"]) for mm in MONTHS}}

# ---- write back into template ----
s=open(TEMPLATE,encoding="utf-8").read()
def replace_const(text,name,obj):
    key=f"const {name} = "; i=text.find(key)+len(key); j=text.find("\n",i)
    assert text[i:j].rstrip().endswith(";")
    return text[:i]+json.dumps(obj,ensure_ascii=False)+";"+text[j:]
out=s
for nm,obj in (("DATA",DATA),("DRILLDOWN",DRILL),("PARTNERS",PART)):
    out=replace_const(out,nm,obj)
out=out.replace("const DATA = ","const TAGSTATS = "+json.dumps(TAGSTATS,ensure_ascii=False)+";\nconst DATA = ",1)
# dynamic month-range labels (title/subtitle) so the header updates each month
out=out.replace("Январь–Июнь 2026",MONTHS[0]+"–"+MONTHS[-1]+" 2026").replace("Январь – Июнь 2026",MONTHS[0]+" – "+MONTHS[-1]+" 2026")
open(OUT,"w",encoding="utf-8").write(out)

print("WROTE",OUT,len(out),"bytes | months:",MONTHS)
print("partners:",len(PART),"| directions:",len(DATA['directions']['rev']),"| prof:",len(DATA['professions']['rev']),"| skills:",len(DATA['skills']['rev']))
print("dupes gone:", all(x not in PART for x in ("Eduson Academy","Moscow Business Academy","City Business School","Сити Бизнес Скул")))
print("Академия Эдюсон total rev:", round(sum(PART['Академия Эдюсон']['months'][mm]['rev'] for mm in MONTHS),0))
print("Московская Бизнес Академия total rev:", round(sum(PART['Московская Бизнес Академия']['months'][mm]['rev'] for mm in MONTHS),0))
print("June totals:",{k:DATA['totals'][k]['Июнь'] for k in DATA['totals']})
print("all-months rev:",{mm:DATA['totals']['rev'][mm] for mm in MONTHS})
