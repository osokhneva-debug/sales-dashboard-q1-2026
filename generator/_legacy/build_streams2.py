import csv,json
rows=list(csv.reader(open("fakt.csv",encoding="utf-8")))
def num(x):
    x=(x or "").replace("\xa0","").replace(" ","").replace("₽","").replace(",",".")
    try: return float(x) if x not in("","#REF!","-") else None
    except: return None
years,mon=rows[0],rows[1]
cols=[i for i,y in enumerate(years) if y.strip()=="2026"]
MEN={'JAN':'Январь','FEB':'Февраль','MAR':'Март','APR':'Апрель','MAY':'Май','JUNE':'Июнь','JUN':'Июнь','JULY':'Июль','AUG':'Август','SEPT':'Сентябрь','OCT':'Октябрь','NOV':'Ноябрь','DEC':'Декабрь'}
LAB={"GMV":"gmv","Кол-во покупок":"purchases","Revenue CPA":"cpa","Revenue CPС":"cpc","Revenue Fix":"fix","Revenue c Рекламы":"adv","Total Revenue EdTech":"total","Клики_total":"clicks"}
def frow(l):
    for r in rows:
        if r and r[0].strip()==l: return r
STREAMS={}
for l,k in LAB.items():
    r=frow(l); s={}
    for i in cols:
        m=MEN.get(mon[i].strip().upper()); v=num(r[i]) if r and i<len(r) else None
        if m and v is not None: s[m]=round(v,2)
    STREAMS[k]=s
ORDER=['Январь','Февраль','Март','Апрель','Май','Июнь','Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь']
STREAMS["months"]=[m for m in ORDER if m in STREAMS["total"]]
LAST=STREAMS["months"][-1]

s=open("index_new.html",encoding="utf-8").read()
TABBTN='  <button class="tab" data-tab="directions">🎯 Направления</button>'
SEC_ANCHOR='<div class="tab-content active" id="overview">'
INIT_ANCHOR='// INIT\nrenderKPI();\nrenderOverview();'
NOTE_OLD='✅ Период январь–май 2026 (данные за май добавлены из дополнительного файла)'
for a in (TABBTN,SEC_ANCHOR,'const DATA = ',INIT_ANCHOR): assert s.count(a)==1,(a[:30],s.count(a))

INSIGHTS='<ul style="margin:6px 0 0;padding-left:20px;line-height:1.65;color:#334155;font-size:14px">\
<li><b>Тотал выручки ~97 млн за H1 растёт, но тянет его платка.</b> Реклама Мар→Июнь удвоилась (4,7→6,1 млн), а CPA-ядро стоит/падает (Янв 10,6 → Июнь 9,3 млн).</li>\
<li><b>Q2 к Q1: +7,9%</b> — прирост почти весь из рекламы, не из ядра.</li>\
<li><b>Куда копать: CPA.</b> В июле план режет платку вдвое и требует от CPA +47% при флэте кликов — рост обязан прийти из RpC и конверсии, а не трафика. Главный риск.</li>\
<li><b>Fix недобирает</b> (0,52 млн в июне против плана 1,27) — механику пересобрать под гарантию трафика.</li>\
<li><b>Выручка концентрируется в топ-школах</b> (Skypro, Эдюсон, Нетология) — держать их ДРР под контролем (у Нетологии уже 59%).</li></ul>'

INSIGHTS_LOG=json.load(open("insights.json",encoding="utf-8"))
INSIGHTS_SECTION=('<div class="tab-content" id="insights">\n'
 '  <div class="note" style="margin-bottom:14px">Аналитический журнал: основные выводы месяца и гипотезы по точкам роста. Накапливается месяц к месяцу (новые — сверху), обновляется ежемесячно.</div>\n'
 '  <div id="insightsLog"></div>\n</div>\n\n')

SECTION=('<div class="tab-content" id="streams">\n'
 '  <div class="kpi-grid" id="streamsQuarters" style="margin-bottom:16px"></div>\n'
 '  <div class="kpi-grid" id="streamsKpi" style="margin-bottom:16px"></div>\n'
 '  <div class="card grid-1"><h3 style="margin:0 0 12px">Выручка по потокам, помесячно (₽)</h3>\n'
 '    <div style="position:relative;height:360px"><canvas id="chStreamsStack"></canvas></div>\n'
 '    <div class="note">CPA — партнёрская выручка (ядро) · CPC — оплата за клик · Fix — фикс-размещение · Реклама — платка. Источник: «Факт2025-2026».</div></div>\n'
 '  <div class="card grid-1"><h3 style="margin:0 0 12px">Потоки × месяцы + накопленный итог</h3>\n'
 '    <div class="table-wrap"><table id="streamsTable"></table></div>\n'
 '    <div class="note">«Покупки» здесь — платные; в «Выручке по CPA» считаются все продажи, включая БП.</div></div>\n'
 '  <div class="card grid-1"><h3 style="margin:0 0 12px">GMV: профессии vs навыки, помесячно</h3>\n'
 '    <div class="table-wrap"><table id="tagStatsTable"></table></div>\n'
 '    <div class="note">Каждая продажа отнесена либо к профессии, либо к навыку (пересечений нет). «Доля навыков» = навыки ÷ всего GMV — реальная доля без двойного счёта мультитегов из таба «Навыки».</div></div>\n'
 '</div>\n\n')

JS='''
// ====== KPI (overridden: total revenue from all streams + top-3 schools) ======
function renderKPI(){
  const t=DATA.totals;
  const totGmv=MONTHS.reduce((s,m)=>s+(t.gmv[m]||0),0);
  const totCnt=MONTHS.reduce((s,m)=>s+(t.cnt[m]||0),0);
  const cpaRev=MONTHS.reduce((s,m)=>s+(t.rev[m]||0),0);
  const SM=STREAMS.months, lastM=SM[SM.length-1];
  const totRev=SM.reduce((s,m)=>s+(STREAMS.total[m]||0),0);
  const fR=STREAMS.total[SM[0]]||0,lR=STREAMS.total[lastM]||0,deltaRev=(lR-fR)/fR;
  const firstGmv=t.gmv[MONTHS[0]]||0,lastGmv=t.gmv[MONTHS[MONTHS.length-1]]||0,deltaGmv=(lastGmv-firstGmv)/firstGmv;
  const arpu=cpaRev/totCnt;
  const cards=[
    {label:'Общий Ревеню (все потоки)',value:fmtR(totRev),delta:`Янв→${lastM}: ${fmtPct(deltaRev)}`,deltaCls:deltaRev>=0?'up':'down'},
    {label:'Общий GMV',value:fmtR(totGmv),delta:`Янв→${MONTHS[MONTHS.length-1]}: ${fmtPct(deltaGmv)}`,deltaCls:deltaGmv>=0?'up':'down'},
    {label:'Комиссия CPA (ревеню/GMV)',value:(cpaRev/totGmv*100).toFixed(1)+'%',delta:'CPA-ревеню ÷ GMV',deltaCls:''},
    {label:'Кол-во продаж',value:fmtN(totCnt),delta:`Средний чек: ${fmtR(arpu)}`,deltaCls:''},
    {label:'Топ-направление',value:topByPeriod(DATA.directions.rev,1)[0].name,delta:fmtR(topByPeriod(DATA.directions.rev,1)[0].total),deltaCls:''},
    {label:'Топ-профессия',value:topByPeriod(DATA.professions.rev,1)[0].name,delta:fmtR(topByPeriod(DATA.professions.rev,1)[0].total),deltaCls:''},
  ];
  document.getElementById('kpiGrid').innerHTML=cards.map(c=>`<div class="kpi-card"><div class="kpi-label">${c.label}</div><div class="kpi-value">${c.value}</div><div class="kpi-delta ${c.deltaCls}">${c.delta}</div></div>`).join('');
}
// ====== STREAMS tab ======
const STREAM_DEFS=[['cpa','CPA','#3b82f6'],['cpc','CPC','#10b981'],['fix','Fix','#f59e0b'],['adv','Реклама','#8b5cf6']];
let stStack;
function renderStreams(){
  const M=STREAMS.months,lm=M[M.length-1],total=STREAMS.total[lm]||0,grand=M.reduce((s,m)=>s+(STREAMS.total[m]||0),0);
  const kpis=[{l:'Total EdTech · '+lm,v:total,c:'#0f172a'}].concat(STREAM_DEFS.map(d=>({l:d[1]+' · '+lm,v:STREAMS[d[0]][lm]||0,c:d[2]})));
  document.getElementById('streamsKpi').innerHTML=kpis.map(k=>`<div class="kpi-card"><div style="font-size:13px;color:#64748b;margin-bottom:6px">${k.l}</div><div style="font-size:24px;font-weight:700;color:${k.c}">${fmtR(k.v)}</div></div>`).join('');
  const QDEF=[['Q1',['Январь','Февраль','Март']],['Q2',['Апрель','Май','Июнь']],['Q3',['Июль','Август','Сентябрь']],['Q4',['Октябрь','Ноябрь','Декабрь']]];
  const qv=QDEF.map(([q,ms])=>({q,v:ms.reduce((s,m)=>s+(STREAMS.total[m]||0),0),has:ms.some(m=>M.includes(m))})).filter(x=>x.has);
  let qh=qv.map((x,i)=>{const p=i>0?qv[i-1].v:null;const qoq=p?`<div style="font-size:12px;margin-top:4px;color:${x.v>=p?'#10b981':'#ef4444'}">${x.v>=p?'▲ +':'▼ '}${((x.v/p-1)*100).toFixed(1)}% к пред. кв.</div>`:'<div style="font-size:12px;margin-top:4px;color:#94a3b8">старт</div>';return `<div class="kpi-card"><div style="font-size:13px;color:#64748b">${x.q} · выручка</div><div style="font-size:22px;font-weight:700">${fmtR(x.v)}</div>${qoq}</div>`;}).join('');
  qh+=`<div class="kpi-card" style="background:#0f172a"><div style="font-size:13px;color:#cbd5e1">Итого выручка (весь период)</div><div style="font-size:22px;font-weight:700;color:#fff">${fmtR(grand)}</div><div style="font-size:12px;margin-top:4px;color:#94a3b8">${M[0]}–${lm}</div></div>`;
  document.getElementById('streamsQuarters').innerHTML=qh;
  if(stStack)stStack.destroy();
  stStack=new Chart(document.getElementById('chStreamsStack'),{type:'bar',data:{labels:M,datasets:STREAM_DEFS.map(d=>({label:d[1],data:M.map(m=>STREAMS[d[0]][m]||0),backgroundColor:d[2],borderRadius:4,stack:'s'}))},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:true,position:'bottom'},tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${fmtR(c.parsed.y)}`}}},scales:{x:{stacked:true,grid:{display:false}},y:{stacked:true,ticks:{callback:v=>fmtR(v)}}}}});
  const defs=STREAM_DEFS.concat([['total','Total EdTech','#0f172a']]);
  let h=`<thead><tr><th>Поток</th>${M.map(m=>`<th class="num">${m}</th>`).join('')}<th class="num">Итого 6 мес</th><th class="num">Доля ${lm}</th></tr></thead><tbody>`;
  defs.forEach(d=>{const val=STREAMS[d[0]][lm]||0,sh=d[0]==='total'?100:(total?val/total*100:0);const rowT=M.reduce((s,m)=>s+(STREAMS[d[0]][m]||0),0);h+=`<tr${d[0]==='total'?' style="border-top:2px solid #cbd5e1;font-weight:700"':''}><td><span style="display:inline-block;width:10px;height:10px;border-radius:3px;background:${d[2]};margin-right:8px"></span>${d[1]}</td>${M.map(m=>`<td class="num">${fmtR(STREAMS[d[0]][m]||0)}</td>`).join('')}<td class="num"><strong>${fmtR(rowT)}</strong></td><td class="num">${d[0]==='total'?'100%':sh.toFixed(0)+'%'}</td></tr>`;});
  let cum=0;const cs=M.map(m=>{cum+=STREAMS.total[m]||0;return cum;});
  h+=`<tr style="border-top:2px solid #6366f1;color:#4f46e5;font-weight:700"><td>Накопленный итог</td>${cs.map(v=>`<td class="num">${fmtR(v)}</td>`).join('')}<td class="num"><strong>${fmtR(grand)}</strong></td><td class="num">—</td></tr>`;
  document.getElementById('streamsTable').innerHTML=h+`</tbody>`;
}
// ====== GMV: professions vs skills (deduped tag stats) ======
function renderTagStats(){
  const M=TAGSTATS.months,last=M[M.length-1];
  const rd=[['prof','Профессии','#3b82f6'],['skill','Навыки','#f59e0b']];
  let h=`<thead><tr><th>GMV</th>${M.map(m=>`<th class="num">${m}</th>`).join('')}<th class="num">Δ Янв→${last}</th></tr></thead><tbody>`;
  rd.forEach(d=>{const f=TAGSTATS[d[0]][M[0]]||0,l=TAGSTATS[d[0]][last]||0,dl=f?(l-f)/f:0;
    h+=`<tr><td><span style="display:inline-block;width:10px;height:10px;border-radius:3px;background:${d[2]};margin-right:8px"></span>${d[1]}</td>${M.map(m=>`<td class="num">${fmtR(TAGSTATS[d[0]][m]||0)}</td>`).join('')}<td class="num ${dl>=0?'trend-up':'trend-down'}">${fmtPct(dl)}</td></tr>`;});
  const ft=TAGSTATS.total[M[0]]||0,lt=TAGSTATS.total[last]||0,dt=ft?(lt-ft)/ft:0;
  h+=`<tr style="border-top:2px solid #cbd5e1;font-weight:700"><td>Всего GMV</td>${M.map(m=>`<td class="num">${fmtR(TAGSTATS.total[m]||0)}</td>`).join('')}<td class="num ${dt>=0?'trend-up':'trend-down'}">${fmtPct(dt)}</td></tr>`;
  h+=`<tr style="border-top:2px solid #f59e0b;color:#b45309;font-weight:700"><td>Доля навыков в GMV</td>${M.map(m=>{const ssh=TAGSTATS.total[m]?TAGSTATS.skill[m]/TAGSTATS.total[m]*100:0;return `<td class="num">${ssh.toFixed(1)}%</td>`;}).join('')}<td class="num">—</td></tr>`;
  document.getElementById('tagStatsTable').innerHTML=h+`</tbody>`;
}
// ====== Insights journal (accumulating monthly) ======
function renderInsights(){
  document.getElementById('insightsLog').innerHTML=INSIGHTS_LOG.map(e=>`<div class="card grid-1" style="border-left:4px solid #6366f1;margin-bottom:16px"><h3 style="margin:0 0 4px">🗓 ${e.month}</h3>${e.note?`<div style="font-size:12px;color:#64748b;margin-bottom:12px">${e.note}</div>`:'<div style="margin-bottom:12px"></div>'}<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:22px"><div><div style="font-weight:700;color:#334155;margin-bottom:8px">📊 Основные выводы</div><ul style="margin:0;padding-left:18px;line-height:1.6;color:#334155;font-size:14px">${e.findings.map(x=>`<li style="margin-bottom:5px">${x}</li>`).join('')}</ul></div><div><div style="font-weight:700;color:#334155;margin-bottom:8px">🚀 Гипотезы по точкам роста</div><ul style="margin:0;padding-left:18px;line-height:1.6;color:#334155;font-size:14px">${e.hypotheses.map(x=>`<li style="margin-bottom:5px">${x}</li>`).join('')}</ul></div></div></div>`).join('');
}
'''

s=s.replace('const DATA = ','const STREAMS = '+json.dumps(STREAMS,ensure_ascii=False)+';\nconst DATA = ',1)
s=s.replace('const DATA = ','const INSIGHTS_LOG = '+json.dumps(INSIGHTS_LOG,ensure_ascii=False)+';\nconst DATA = ',1)
s=s.replace(TABBTN,'  <button class="tab" data-tab="streams">💰 Выручка</button>\n'+TABBTN,1)
s=s.replace(SEC_ANCHOR,SECTION+INSIGHTS_SECTION+SEC_ANCHOR,1)
s=s.replace(INIT_ANCHOR,JS+'\n'+INIT_ANCHOR.replace('renderOverview();','renderOverview();\nrenderStreams();\nrenderTagStats();\nrenderInsights();'),1)
if NOTE_OLD in s: s=s.replace(NOTE_OLD,'✅ Период январь–июнь 2026 · «Обзор» = вся выручка (~97 млн, 4 потока) · «Выручка по CPA» = детализация',1)

# ---- reorder + rename tabs: streams->Обзор (1st, active); overview->Выручка по CPA (2nd) ----
PAIR_OLD='  <button class="tab active" data-tab="overview">📈 Обзор</button>\n  <button class="tab" data-tab="streams">💰 Выручка</button>'
assert s.count(PAIR_OLD)==1, ("pair",s.count(PAIR_OLD))
s=s.replace(PAIR_OLD,'  <button class="tab active" data-tab="streams">📊 Обзор</button>\n  <button class="tab" data-tab="overview">💰 Выручка по CPA</button>',1)
s=s.replace('<div class="tab-content active" id="overview">','<div class="tab-content" id="overview">',1)
s=s.replace('<div class="tab-content" id="streams">','<div class="tab-content active" id="streams">',1)

# ---- add "Выводы месяца" tab LAST (after partners) ----
PART_BTN='  <button class="tab" data-tab="partners">🏢 Сводно по школам</button>'
assert s.count(PART_BTN)==1
s=s.replace(PART_BTN, PART_BTN+'\n  <button class="tab" data-tab="insights">📝 Выводы месяца</button>',1)

open("index_new.html","w",encoding="utf-8").write(s)
print("OK",len(s),"bytes | last month:",LAST)
