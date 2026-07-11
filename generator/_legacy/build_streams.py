import csv,json,re

# ---- parse Факт2025-2026 -> STREAMS ----
rows=list(csv.reader(open("fakt.csv",encoding="utf-8")))
def num(x):
    x=(x or "").replace("\xa0","").replace(" ","").replace("₽","").replace(",",".")
    try: return float(x) if x not in("","#REF!","-") else None
    except: return None
years,mon=rows[0],rows[1]
cols=[i for i,y in enumerate(years) if y.strip()=="2026"]
MEN={'JAN':'Январь','FEB':'Февраль','MAR':'Март','APR':'Апрель','MAY':'Май','JUNE':'Июнь','JUN':'Июнь',
     'JULY':'Июль','AUG':'Август','SEPT':'Сентябрь','OCT':'Октябрь','NOV':'Ноябрь','DEC':'Декабрь'}
LAB={"GMV":"gmv","Кол-во покупок":"purchases","Revenue CPA":"cpa","Revenue CPС":"cpc","Revenue Fix":"fix",
     "Revenue c Рекламы":"adv","Total Revenue EdTech":"total","Клики_total":"clicks"}
def frow(lbl):
    for r in rows:
        if r and r[0].strip()==lbl: return r
STREAMS={}
for lbl,key in LAB.items():
    r=frow(lbl); s={}
    for i in cols:
        m=MEN.get(mon[i].strip().upper()); v=num(r[i]) if r and i<len(r) else None
        if m and v is not None: s[m]=round(v,2)
    STREAMS[key]=s
ORDER=['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']
STREAMS["months"]=[m for m in ORDER if m in STREAMS["total"]]
print("STREAMS months:",STREAMS["months"],"| June total:",STREAMS["total"].get("Июнь"))

# ---- load index_new.html (already has rebuilt CPA constants) ----
s=open("index_new.html",encoding="utf-8").read()

TABBTN='  <button class="tab" data-tab="directions">🎯 Направления</button>'
SECTION_ANCHOR='<div class="tab-content active" id="overview">'
NOTE_OLD='✅ Период январь–май 2026 (данные за май добавлены из дополнительного файла)'
INIT_ANCHOR='// INIT\nrenderKPI();\nrenderOverview();'
for a,cnt in [(TABBTN,1),(SECTION_ANCHOR,1),('const DATA = ',1),(INIT_ANCHOR,1)]:
    assert s.count(a)==cnt, (a[:40], s.count(a))

SECTION='''<div class="tab-content" id="streams">
  <div class="kpi-grid" id="streamsKpi" style="margin-bottom:16px"></div>
  <div class="card grid-1">
    <h3 style="margin:0 0 12px">Выручка по потокам, помесячно (₽)</h3>
    <div style="position:relative;height:360px"><canvas id="chStreamsStack"></canvas></div>
    <div class="note">CPA — партнёрская выручка (ядро) · CPC — оплата за клик · Fix — фикс-размещение · Реклама — платка. Источник: «Факт2025-2026».</div>
  </div>
  <div class="card grid-1">
    <h3 style="margin:0 0 12px">Доля потоков · последний месяц</h3>
    <div style="position:relative;height:300px"><canvas id="chStreamsShare"></canvas></div>
  </div>
  <div class="card grid-1">
    <h3 style="margin:0 0 12px">Потоки × месяцы</h3>
    <div class="table-wrap"><table id="streamsTable"></table></div>
    <div class="note">«Покупки» здесь — платные; в «Обзоре» считаются все продажи, включая БП.</div>
  </div>
</div>

'''

RENDER='''// ====== STREAMS (revenue by monetization stream) ======
const STREAM_DEFS=[['cpa','CPA','#3b82f6'],['cpc','CPC','#10b981'],['fix','Fix','#f59e0b'],['adv','Реклама','#8b5cf6']];
let stStack, stShare;
function renderStreams(){
  const M=STREAMS.months, lm=M[M.length-1], total=STREAMS.total[lm]||0;
  const kpis=[{l:'Total EdTech · '+lm,v:total,c:'#0f172a'}].concat(STREAM_DEFS.map(d=>({l:d[1]+' · '+lm,v:STREAMS[d[0]][lm]||0,c:d[2]})));
  document.getElementById('streamsKpi').innerHTML=kpis.map(k=>`<div class="kpi-card"><div style="font-size:13px;color:#64748b;margin-bottom:6px">${k.l}</div><div style="font-size:24px;font-weight:700;color:${k.c}">${fmtR(k.v)}</div></div>`).join('');
  if(stStack) stStack.destroy();
  stStack=new Chart(document.getElementById('chStreamsStack'),{type:'bar',
    data:{labels:M,datasets:STREAM_DEFS.map(d=>({label:d[1],data:M.map(m=>STREAMS[d[0]][m]||0),backgroundColor:d[2],borderRadius:4,stack:'s'}))},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,position:'bottom'},tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${fmtR(c.parsed.y)}`}}},scales:{x:{stacked:true,grid:{display:false}},y:{stacked:true,ticks:{callback:v=>fmtR(v)}}}}});
  if(stShare) stShare.destroy();
  stShare=new Chart(document.getElementById('chStreamsShare'),{type:'doughnut',
    data:{labels:STREAM_DEFS.map(d=>d[1]),datasets:[{data:STREAM_DEFS.map(d=>STREAMS[d[0]][lm]||0),backgroundColor:STREAM_DEFS.map(d=>d[2])}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom'},tooltip:{callbacks:{label:c=>`${c.label}: ${fmtR(c.parsed)}`}}}}});
  const defs=STREAM_DEFS.concat([['total','Total EdTech','#0f172a']]);
  let h=`<thead><tr><th>Поток</th>${M.map(m=>`<th class="num">${m}</th>`).join('')}<th class="num">Доля ${lm}</th></tr></thead><tbody>`;
  defs.forEach(d=>{const val=STREAMS[d[0]][lm]||0;const sh=d[0]==='total'?100:(total?val/total*100:0);
    h+=`<tr><td><span style="display:inline-block;width:10px;height:10px;border-radius:3px;background:${d[2]};margin-right:8px"></span>${d[1]}</td>${M.map(m=>`<td class="num">${fmtR(STREAMS[d[0]][m]||0)}</td>`).join('')}<td class="num">${d[0]==='total'?'100%':sh.toFixed(0)+'%'}</td></tr>`;});
  document.getElementById('streamsTable').innerHTML=h+`</tbody>`;
}
'''

s=s.replace(TABBTN,'  <button class="tab" data-tab="streams">💰 Выручка</button>\n'+TABBTN,1)
s=s.replace(SECTION_ANCHOR,SECTION+SECTION_ANCHOR,1)
s=s.replace('const DATA = ','const STREAMS = '+json.dumps(STREAMS,ensure_ascii=False)+';\nconst DATA = ',1)
s=s.replace(INIT_ANCHOR,RENDER+'\n'+INIT_ANCHOR.replace('renderOverview();','renderOverview();\nrenderStreams();'),1)
if NOTE_OLD in s: s=s.replace(NOTE_OLD,'✅ Период январь–июнь 2026 · +таб «Выручка» (4 потока монетизации)',1)

open("index_new.html","w",encoding="utf-8").write(s)
print("OK, wrote index_new.html",len(s),"bytes")
