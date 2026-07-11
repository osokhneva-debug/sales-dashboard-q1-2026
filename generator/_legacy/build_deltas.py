s=open("index_new.html",encoding="utf-8").read()

def rep(old,new,label):
    assert s.count(old)==1, (label, s.count(old))
    return s.replace(old,new,1)

# ---- string fixes ----
s=rep('<label>Фильтр по тренду (Янв→Июнь)</label>','<label>Фильтр по тренду (мес)</label>','filter-label')
# rerenderPartners summary -> MoM
s=rep('const jan = rows.reduce((s,r)=>s+r.first,0);\n  const apr = rows.reduce((s,r)=>s+r.last,0);',
      'const jan = rows.reduce((s,r)=>s+r.prev,0);\n  const apr = rows.reduce((s,r)=>s+r.last,0);','part-summary-calc')
s=rep('Янв → Апр (все школы)','${MONTHS[MONTHS.length-2]} → ${MONTHS[MONTHS.length-1]} (все школы)','part-summary-lbl')
# KPI deltas -> MoM (from build_streams2 override)
s=rep('const fR=STREAMS.total[SM[0]]||0,lR=STREAMS.total[lastM]||0,deltaRev=(lR-fR)/fR;',
      'const fR=STREAMS.total[SM[SM.length-2]]||0,lR=STREAMS.total[lastM]||0,deltaRev=fR?(lR-fR)/fR:0;','kpi-rev-calc')
s=rep('delta:`Янв→${lastM}: ${fmtPct(deltaRev)}`','delta:`${SM[SM.length-2]}→${lastM}: ${fmtPct(deltaRev)}`','kpi-rev-lbl')
s=rep('const firstGmv=t.gmv[MONTHS[0]]||0,lastGmv=t.gmv[MONTHS[MONTHS.length-1]]||0,deltaGmv=(lastGmv-firstGmv)/firstGmv;',
      'const firstGmv=t.gmv[MONTHS[MONTHS.length-2]]||0,lastGmv=t.gmv[MONTHS[MONTHS.length-1]]||0,deltaGmv=firstGmv?(lastGmv-firstGmv)/firstGmv:0;','kpi-gmv-calc')
s=rep('delta:`Янв→${MONTHS[MONTHS.length-1]}: ${fmtPct(deltaGmv)}`','delta:`${MONTHS[MONTHS.length-2]}→${MONTHS[MONTHS.length-1]}: ${fmtPct(deltaGmv)}`','kpi-gmv-lbl')

# ---- overrides (before // INIT, last decl wins) ----
OV=r'''
// ===== Consistent MoM abs + QoQ % across all pivot/partner tables =====
function buildPivotTable(tableId, dataDict, metricLabel){
  const n=MONTHS.length, qOf=i=>Math.floor(i/3), lastQ=qOf(n-1), prevQ=lastQ-1;
  return Object.keys(dataDict).map(k=>{
    const byMonth=MONTHS.map(m=>dataDict[k][m]||0);
    const total=byMonth.reduce((a,b)=>a+b,0);
    const last=byMonth[n-1], prev=n>1?byMonth[n-2]:0;
    const momAbs=last-prev, momPct=prev>0?(last-prev)/prev:null;
    let q1=0,q2=0; byMonth.forEach((v,i)=>{const q=qOf(i); if(q===prevQ)q1+=v; else if(q===lastQ)q2+=v;});
    const qoqPct=(prevQ>=0&&q1>0)?(q2-q1)/q1:null;
    const trend=momAbs>0?'up':momAbs<0?'down':'flat';
    return {name:k, byMonth, total, momAbs, momPct, qoqPct, trend, delta:momPct};
  });
}
function renderTable(tableId, rows, metricLabel, unit, opts){
  opts=opts||{}; const filter=opts.filter||'', trendFilter=opts.trendFilter||'all', limit=opts.limit||999999;
  let filtered=rows.filter(r=>r.name.toLowerCase().includes(filter.toLowerCase()));
  if(trendFilter!=='all') filtered=filtered.filter(r=>r.trend===trendFilter);
  const sort=tableSort[tableId]||{col:'total',dir:'desc'};
  filtered.sort((a,b)=>{ if(sort.col==='name')return sort.dir==='asc'?a.name.localeCompare(b.name):b.name.localeCompare(a.name);
    let av,bv;
    if(sort.col==='total'){av=a.total;bv=b.total;}
    else if(sort.col==='mom'){av=a.momAbs;bv=b.momAbs;}
    else if(sort.col==='qoq'){av=a.qoqPct==null?-Infinity:a.qoqPct;bv=b.qoqPct==null?-Infinity:b.qoqPct;}
    else {const i=parseInt(sort.col);av=a.byMonth[i]||0;bv=b.byMonth[i]||0;}
    return sort.dir==='asc'?av-bv:bv-av; });
  filtered=filtered.slice(0,limit);
  const minMax=MONTHS.map((m,i)=>{const vals=filtered.map(r=>r.byMonth[i]).filter(v=>v>0);return {min:vals.length?Math.min(...vals):0,max:vals.length?Math.max(...vals):1};});
  const fmt=unit==='₽'?fmtR:fmtN; const lastM=MONTHS[MONTHS.length-1], prevM=MONTHS[MONTHS.length-2]||'';
  const th=(col,lbl,cls='')=>{const sc=sort.col===col?(sort.dir==='asc'?'sort-asc':'sort-desc'):'';return `<th data-sort="${col}" class="${sc} ${cls}">${lbl}</th>`;};
  let html=`<thead><tr><th>#</th>${th('name','Категория')}${MONTHS.map((m,i)=>th(i,m,'num')).join('')}${th('total','Итого','num')}${th('mom','Δ '+lastM+'−'+prevM,'num')}${th('qoq','Δ QoQ %','num')}<th>Тренд</th></tr></thead><tbody>`;
  filtered.forEach((r,idx)=>{
    const rankCls=idx===0?'top1':idx===1?'top2':idx===2?'top3':'';
    const dcol=r.momAbs<0?'#991b1b':r.momAbs>0?'#065f46':'#64748b';
    html+=`<tr><td><span class="rank ${rankCls}">${idx+1}</span></td><td class="cat-cell" title="${r.name}">${r.name}</td>${r.byMonth.map((v,i)=>`<td class="num"><span class="heatmap-cell" style="background:${heatColor(v,minMax[i].min,minMax[i].max)};color:${heatTextColor(v,minMax[i].min,minMax[i].max)}">${fmt(v)}</span></td>`).join('')}<td class="num"><strong>${fmt(r.total)}</strong></td><td class="num" style="color:${dcol};font-weight:600">${r.momAbs>=0?'+':''}${fmt(r.momAbs).replace(' ₽','')}${unit==='₽'?' ₽':''}</td><td class="num ${r.qoqPct==null?'trend-flat':(r.qoqPct>=0?'trend-up':'trend-down')}">${r.qoqPct==null?'—':fmtPct(r.qoqPct)}</td><td>${r.trend==='up'?'<span class="trend-up">↗ рост</span>':r.trend==='down'?'<span class="trend-down">↘ падение</span>':'<span class="trend-flat">— стаб.</span>'}</td></tr>`;
  });
  document.getElementById(tableId).innerHTML=html+'</tbody>';
  document.querySelectorAll(`#${tableId} th[data-sort]`).forEach(th=>{th.onclick=()=>{const col=th.dataset.sort;const cur=tableSort[tableId]||{col:'total',dir:'desc'};if(cur.col===col)cur.dir=cur.dir==='asc'?'desc':'asc';else{cur.col=col;cur.dir='desc';}tableSort[tableId]=cur;opts.rerender&&opts.rerender();};});
}
function buildPartnerRows(){
  const n=MONTHS.length, qOf=i=>Math.floor(i/3), lastQ=qOf(n-1), prevQ=lastQ-1;
  return Object.keys(PARTNERS).map(k=>{
    const rec=PARTNERS[k];
    const byMonth=MONTHS.map(m=>rec.months[m][partMetric]);
    const total=byMonth.reduce((a,b)=>a+b,0);
    const first=byMonth[0], last=byMonth[n-1], prev=n>1?byMonth[n-2]:0;
    const drop=last-prev, dropPct=prev>0?drop/prev:null;
    let q1=0,q2=0; byMonth.forEach((v,i)=>{const q=qOf(i); if(q===prevQ)q1+=v; else if(q===lastQ)q2+=v;});
    const qoqPct=(prevQ>=0&&q1>0)?(q2-q1)/q1:null;
    let status='normal';
    if(prev>0&&last===0)status='killed'; else if(prev===0&&last>0)status='new';
    else if(drop<0)status='down'; else if(drop>0)status='up';
    const dirs=Object.entries(rec.directions).sort((a,b)=>b[1]-a[1]).slice(0,3);
    return {name:k,byMonth,total,first,last,prev,drop,dropPct,qoqPct,status,topDirs:dirs,dirJan:rec.dir_jan,dirApr:rec.dir_apr};
  }).filter(r=>r.total>0);
}
function renderPartnerTable(rows, unit){
  const fmt=unit==='₽'?fmtR:fmtN;
  const lastM=MONTHS[MONTHS.length-1], prevM=MONTHS[MONTHS.length-2]||'';
  const sort=tableSort['partTable'];
  const val=(r,col)=>{ if(col==='name')return (r.name||'').toLowerCase(); if(col==='total')return r.total||0; if(col==='drop')return r.drop||0; if(col==='qoq')return (r.qoqPct==null?-Infinity:r.qoqPct); if(col==='status'){const o={killed:0,down:1,flat:2,up:3,new:4};return o[r.status]!=null?o[r.status]:2;} return r.byMonth[+col]||0; };
  let srt=rows.slice();
  if(sort){srt.sort((a,b)=>{const va=val(a,sort.col),vb=val(b,sort.col); if(typeof va==='string')return sort.dir==='asc'?va.localeCompare(vb):vb.localeCompare(va); return sort.dir==='asc'?va-vb:vb-va;});}
  const maxAbs=Math.max(...srt.map(r=>Math.abs(r.drop)),1);
  const th=(col,lbl,cls='')=>{const sc=sort&&String(sort.col)===String(col)?(sort.dir==='asc'?'sort-asc':'sort-desc'):'';return `<th data-sort="${col}" class="${sc} ${cls}" style="cursor:pointer;user-select:none">${lbl}</th>`;};
  let html=`<thead><tr><th>#</th>${th('name','Школа')}${MONTHS.map((m,i)=>th(i,m,'num')).join('')}${th('total','Итого','num')}${th('drop','Δ '+lastM+'−'+prevM,'num')}${th('qoq','Δ QoQ %','num')}${th('status','Статус')}<th>Топ-3 направления</th></tr></thead><tbody>`;
  srt.forEach((r,idx)=>{
    const rankCls=idx===0?'top1':idx===1?'top2':idx===2?'top3':'';
    const intensity=Math.min(Math.abs(r.drop)/maxAbs,1);
    const diffBg=r.drop<0?`rgba(239, 68, 68, ${0.15+0.5*intensity})`:r.drop>0?`rgba(16, 185, 129, ${0.15+0.5*intensity})`:'#f8fafc';
    const diffColor=intensity>0.7?'white':(r.drop<0?'#991b1b':r.drop>0?'#065f46':'#64748b');
    const statusTag=r.status==='killed'?`<span class="kill-tag">⚠️ перестала</span>`:r.status==='new'?`<span class="new-tag">🆕 новая</span>`:r.status==='down'?`<span class="trend-down">↘ падение</span>`:r.status==='up'?`<span class="trend-up">↗ рост</span>`:`<span class="trend-flat">— стаб.</span>`;
    const topDirsStr=r.topDirs.map(([d,v])=>{const jv=r.dirJan[d]||0,av=r.dirApr[d]||0,dd=av-jv;const arrow=dd<0?'<span style="color:#ef4444">↘</span>':dd>0?'<span style="color:#10b981">↗</span>':'—';return `<div style="font-size:11px;line-height:1.5">${arrow} ${d}: <strong>${fmt(v)}</strong></div>`;}).join('');
    html+=`<tr><td><span class="rank ${rankCls}">${idx+1}</span></td><td class="cat-cell" title="${r.name}">${r.name}</td>${r.byMonth.map(v=>`<td class="num">${fmt(v)}</td>`).join('')}<td class="num"><strong>${fmt(r.total)}</strong></td><td class="num"><span class="heatmap-cell" style="background:${diffBg};color:${diffColor}">${r.drop>=0?'+':''}${fmt(r.drop).replace(' ₽','')}${unit==='₽'?' ₽':''}</span></td><td class="num ${r.qoqPct==null?'trend-flat':(r.qoqPct>=0?'trend-up':'trend-down')}">${r.qoqPct==null?'—':fmtPct(r.qoqPct)}</td><td>${statusTag}</td><td style="max-width:320px">${topDirsStr}</td></tr>`;
  });
  document.getElementById('partTable').innerHTML=html+'</tbody>';
  document.querySelectorAll('#partTable th[data-sort]').forEach(h=>{h.onclick=()=>{const col=h.dataset.sort;const cur=tableSort['partTable']||{col:'total',dir:'desc'};if(String(cur.col)===String(col))cur.dir=cur.dir==='asc'?'desc':'asc';else{cur.col=col;cur.dir=(col==='name')?'asc':'desc';}tableSort['partTable']=cur;renderPartnerTable(rows,unit);};});
}
'''
assert s.count("// INIT\n")==1
s=s.replace("// INIT\n", OV+"\n// INIT\n", 1)
open("index_new.html","w",encoding="utf-8").write(s)
print("OK deltas unified;",len(s),"bytes")
