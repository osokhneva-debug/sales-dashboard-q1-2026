s=open("index_new.html",encoding="utf-8").read()

# ---- 1) Fix chPartTop chart (unreadable grouped 6-mo bars -> clean total bar) + heading ----
OLD_TOP='''const top15 = [...rows].sort((a,b)=>b.total-a.total).slice(0,15);
  if(partTopChart) partTopChart.destroy();
  partTopChart = new Chart(document.getElementById('chPartTop'),{
    type:'bar',
    data:{
      labels: top15.map(r=>r.name),
      datasets: MONTHS.map((m,i)=>({
        label:m,
        data: top15.map(r=>r.byMonth[i]),
        backgroundColor: ['#93c5fd','#a78bfa','#6ee7b7','#fcd34d','#fb7185'][i]
      }))
    },
    options:{
      indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins:{legend:{position:'top',labels:{boxWidth:12}},tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${unit==='₽'?fmtR(c.parsed.x):fmtN(c.parsed.x)}`}}},
      scales:{x:{ticks:{callback:v=>unit==='₽'?fmtR(v):fmtN(v)}},y:{grid:{display:false}}}
    }
  });'''
NEW_TOP='''const top15 = [...rows].sort((a,b)=>b.total-a.total).slice(0,15);
  if(partTopChart) partTopChart.destroy();
  partTopChart = new Chart(document.getElementById('chPartTop'),{
    type:'bar',
    data:{labels: top15.map(r=>r.name), datasets:[{label:'Итого за период', data: top15.map(r=>r.total), backgroundColor:'#6366f1', borderRadius:6}]},
    options:{indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`${unit==='₽'?fmtR(c.parsed.x):fmtN(c.parsed.x)}`}}},
      scales:{x:{ticks:{callback:v=>unit==='₽'?fmtR(v):fmtN(v)}},y:{grid:{display:false}}}}
  });'''
assert s.count(OLD_TOP)==1,("chPartTop",s.count(OLD_TOP)); s=s.replace(OLD_TOP,NEW_TOP,1)
s=s.replace('<h3>Топ-15 школ — общий объём и тренд <span class="badge" id="partChartLbl">Ревеню</span></h3>',
            '<h3>Топ-15 школ — общий объём за период <span class="badge" id="partChartLbl">Ревеню</span></h3>',1)
# stale "в апреле" text on drilldown/partners
s=s.replace('перестал продавать в апреле','перестал продавать в последнем месяце')

# ---- 2) Overrides for drilldown deltas (MoM + QoQ), Total direction, insights ----
OV=r'''
// ===== Drilldown redesign: MoM abs + QoQ %, Total direction, insights =====
function buildEntityRows(entityDict){
  const n=MONTHS.length, qOf=i=>Math.floor(i/3), lastQ=qOf(n-1), prevQ=lastQ-1;
  return Object.keys(entityDict).map(k=>{
    const rec=entityDict[k];
    const byMonth=MONTHS.map(m=>rec[m][ddMetric]);
    const total=byMonth.reduce((a,b)=>a+b,0);
    const first=byMonth[0], last=byMonth[n-1], prev=n>1?byMonth[n-2]:0;
    const mom=last-prev, momPct=prev>0?mom/prev:null;
    let q1=0,q2=0; byMonth.forEach((v,i)=>{const q=qOf(i); if(q===prevQ)q1+=v; else if(q===lastQ)q2+=v;});
    const qoqPct=(prevQ>=0&&q1>0)?(q2-q1)/q1:null;
    let status='normal';
    if(prev>0&&last===0)status='killed'; else if(prev===0&&last>0)status='new';
    else if(mom<0)status='down'; else if(mom>0)status='up';
    return {name:k,byMonth,total,first,last,prev,drop:mom,dropPct:momPct,qoqPct,q1,q2,status};
  }).filter(r=>r.total>0);
}
function renderDrilldownTable(tableId, rows, unit, labelCol){
  const fmt=unit==='₽'?fmtR:fmtN;
  const sort=tableSort[tableId]||{col:'drop',dir:'asc'};
  const val=(r,col)=>{ if(col==='name')return (r.name||'').toLowerCase(); if(col==='total')return r.total||0;
    if(col==='drop')return r.drop||0; if(col==='qoq')return (r.qoqPct==null?-Infinity:r.qoqPct);
    if(col==='status'){const o={killed:0,down:1,flat:2,up:3,new:4};return o[r.status]!=null?o[r.status]:2;} return r.byMonth[+col]||0; };
  const srt=rows.slice().sort((a,b)=>{const va=val(a,sort.col),vb=val(b,sort.col); if(typeof va==='string')return sort.dir==='asc'?va.localeCompare(vb):vb.localeCompare(va); return sort.dir==='asc'?va-vb:vb-va;});
  const lastM=MONTHS[MONTHS.length-1], prevM=MONTHS[MONTHS.length-2]||'';
  const th=(col,lbl,cls='')=>{const sc=String(sort.col)===String(col)?(sort.dir==='asc'?'sort-asc':'sort-desc'):'';return `<th data-sort="${col}" class="${sc} ${cls}" style="cursor:pointer;user-select:none">${lbl}</th>`;};
  let html=`<thead><tr><th>#</th>${th('name',labelCol)}${MONTHS.map((m,i)=>th(i,m,'num')).join('')}${th('total','Итого','num')}${th('drop','Δ '+lastM+'−'+prevM,'num')}${th('qoq','Δ QoQ %','num')}${th('status','Статус')}</tr></thead><tbody>`;
  srt.forEach((r,idx)=>{
    const rankCls=idx===0?'top1':idx===1?'top2':idx===2?'top3':'';
    const dcol=r.drop<0?'#991b1b':r.drop>0?'#065f46':'#64748b';
    const st=r.status==='killed'?`<span class="kill-tag">⚠️ перестал</span>`:r.status==='new'?`<span class="new-tag">🆕 новый</span>`:r.status==='down'?`<span class="trend-down">↘ падение</span>`:r.status==='up'?`<span class="trend-up">↗ рост</span>`:`<span class="trend-flat">— стаб.</span>`;
    html+=`<tr><td><span class="rank ${rankCls}">${idx+1}</span></td><td class="cat-cell" title="${r.name}">${r.name}${r.school?`<div style="font-size:11px;color:#64748b;font-weight:400">🏫 ${r.school}</div>`:''}</td>${r.byMonth.map(v=>`<td class="num">${fmt(v)}</td>`).join('')}<td class="num"><strong>${fmt(r.total)}</strong></td><td class="num" style="color:${dcol};font-weight:600">${r.drop>=0?'+':''}${fmt(r.drop).replace(' ₽','')}${unit==='₽'?' ₽':''}</td><td class="num ${r.qoqPct==null?'trend-flat':(r.qoqPct>=0?'trend-up':'trend-down')}">${r.qoqPct==null?'—':fmtPct(r.qoqPct)}</td><td>${st}</td></tr>`;
  });
  document.getElementById(tableId).innerHTML=html+'</tbody>';
  document.querySelectorAll(`#${tableId} th[data-sort]`).forEach(h=>{h.onclick=()=>{const col=h.dataset.sort;const cur=tableSort[tableId]||{col:'drop',dir:'asc'};if(String(cur.col)===String(col))cur.dir=cur.dir==='asc'?'desc':'asc';else{cur.col=col;cur.dir=(col==='name')?'asc':'desc';}tableSort[tableId]=cur;renderDrilldownTable(tableId,rows,unit,labelCol);};});
}
function populateDirectionSelector(){
  const n=MONTHS.length;
  const dirs=Object.keys(DRILLDOWN).map(k=>{const parts=DRILLDOWN[k].partners;let last=0,prev=0,tot=0;
    Object.values(parts).forEach(p=>{const bm=MONTHS.map(m=>p[m].rev);last+=bm[n-1];prev+=bm[n-2]||0;tot+=bm.reduce((a,b)=>a+b,0);});
    return {name:k,mom:last-prev,momPct:prev>0?(last-prev)/prev*100:0,total:tot};}).filter(d=>d.total>0);
  dirs.sort((a,b)=>a.mom-b.mom);
  const sel=document.getElementById('ddDirection');
  const opt=d=>{const a=d.mom<0?'↘':d.mom>0?'↗':'—';return `<option value="${d.name}">${a} ${d.name}  (${d.mom>=0?'+':''}${Math.round(d.mom).toLocaleString('ru-RU')} ₽, ${d.momPct.toFixed(0)}%)</option>`;};
  sel.innerHTML=`<option value="__ALL__">📊 Все направления (Total)</option>`+dirs.map(opt).join('');
}
function rerenderDrilldown(){
  const dir=document.getElementById('ddDirection').value; if(!dir)return;
  const unit=ddMetric==='cnt'?'':'₽', fmt=unit==='₽'?fmtR:fmtN;
  const sortMode=document.getElementById('ddSort').value;
  document.getElementById('ddPartnerBadge').textContent=ddMetric==='rev'?'Ревеню':'Кол-во продаж';
  let partSrc,progSrc;
  if(dir==='__ALL__'){partSrc={};progSrc={};
    const merge=(dst,src)=>{for(const k in src){if(!dst[k]){dst[k]={};MONTHS.forEach(m=>dst[k][m]={rev:0,cnt:0});}MONTHS.forEach(m=>{dst[k][m].rev+=src[k][m].rev;dst[k][m].cnt+=src[k][m].cnt;});}};
    Object.values(DRILLDOWN).forEach(nd=>{merge(partSrc,nd.partners);merge(progSrc,nd.programs);});
  } else {if(!DRILLDOWN[dir])return; partSrc=DRILLDOWN[dir].partners; progSrc=DRILLDOWN[dir].programs;}
  const partnerRows=buildEntityRows(partSrc), programRows=buildEntityRows(progSrc);
  let progSch; if(dir==='__ALL__'){progSch={};Object.values(DRILLDOWN).forEach(nd=>Object.assign(progSch,nd.prog_schools||{}));}else{progSch=DRILLDOWN[dir].prog_schools||{};}
  programRows.forEach(r=>{r.school=progSch[r.name]||'';});
  const sortFn=sortMode==='drop'?(a,b)=>a.drop-b.drop:sortMode==='growth'?(a,b)=>b.drop-a.drop:(a,b)=>b.total-a.total;
  partnerRows.sort(sortFn); programRows.sort(sortFn);
  const n=MONTHS.length, lastM=MONTHS[n-1], prevM=MONTHS[n-2]||'';
  const lastSum=partnerRows.reduce((s,r)=>s+r.last,0), prevSum=partnerRows.reduce((s,r)=>s+r.prev,0);
  const mom=lastSum-prevSum, momPct=prevSum>0?mom/prevSum*100:0;
  const q1=partnerRows.reduce((s,r)=>s+r.q1,0), q2=partnerRows.reduce((s,r)=>s+r.q2,0), qoqPct=q1>0?(q2-q1)/q1*100:0;
  const killed=partnerRows.filter(r=>r.status==='killed'), killedLoss=killed.reduce((s,r)=>s+r.prev,0);
  const worst=[...partnerRows].filter(r=>r.drop<0).sort((a,b)=>a.drop-b.drop)[0];
  const best=[...partnerRows].filter(r=>r.drop>0).sort((a,b)=>b.drop-a.drop)[0];
  const worstProg=[...programRows].filter(r=>r.drop<0).sort((a,b)=>a.drop-b.drop)[0];
  const dirName=dir==='__ALL__'?'по всем направлениям':`«${dir}»`;
  const li=[];
  li.push(`Выручка ${lastM}: <b>${fmt(lastSum)}</b>, к ${prevM}: <b style="color:${mom<0?'#dc2626':'#16a34a'}">${mom>=0?'+':''}${fmt(mom).replace(' ₽','')} ${unit}</b> (${momPct>=0?'+':''}${momPct.toFixed(1)}%); квартал к кварталу <b style="color:${qoqPct<0?'#dc2626':'#16a34a'}">${qoqPct>=0?'+':''}${qoqPct.toFixed(1)}%</b>.`);
  if(worst)li.push(`Сильнее всех просела: <b>${worst.name}</b> (${fmt(worst.drop).replace(' ₽','')} ${unit} за месяц) — сюда копать.`);
  if(best)li.push(`Драйвер роста: <b>${best.name}</b> (+${fmt(best.drop).replace(' ₽','')} ${unit}).`);
  if(killed.length)li.push(`Перестали продавать в ${lastM}: <b>${killed.length}</b> (потеря ${fmt(killedLoss)}).`);
  if(worstProg)li.push(`Программа-просадка: <b>${worstProg.name.length>44?worstProg.name.slice(0,44)+'…':worstProg.name}</b>${progSch[worstProg.name]?' · 🏫 '+progSch[worstProg.name]:''} (${fmt(worstProg.drop).replace(' ₽','')} ${unit}).`);
  const ins=`<div class="card grid-1" style="border-left:4px solid #6366f1;background:#f5f3ff;margin-bottom:14px"><div style="font-weight:700;margin-bottom:6px">🔍 Что копать — ${dirName} · ${lastM} к ${prevM}</div><ul style="margin:0;padding-left:18px;line-height:1.6;color:#334155;font-size:14px">${li.map(x=>`<li>${x}</li>`).join('')}</ul></div>`;
  const nn=MONTHS.length;
  const fatal=programRows.map(r=>{const a=r.byMonth[nn-3]||0,m2=r.byMonth[nn-2]||0,j=r.byMonth[nn-1]||0,amAvg=(a+m2)/2;return {r,amAvg,j,dp:amAvg>0?(j-amAvg)/amAvg:0};}).filter(x=>x.amAvg>=50000&&x.j<=x.amAvg*0.4).sort((a,b)=>b.amAvg-a.amAvg).slice(0,12);
  const fatalHtml=fatal.length?`<div class="card grid-1" style="border-left:4px solid #ef4444;background:#fef2f2;margin-bottom:14px"><div style="font-weight:700;margin-bottom:6px">🔴 Курсы, обвалившиеся в ${lastM} — были сильны в ${MONTHS[nn-3]}–${MONTHS[nn-2]}, привязаны к школе</div><ul style="margin:0;padding-left:18px;line-height:1.65;color:#334155;font-size:14px">`+fatal.map(x=>`<li><b>${x.r.name.length>52?x.r.name.slice(0,52)+'…':x.r.name}</b>${x.r.school?' · 🏫 '+x.r.school:''} — ${MONTHS[nn-3]}–${MONTHS[nn-2]} ≈ ${fmt(x.amAvg)}/мес → ${lastM}: <b style="color:#dc2626">${fmt(x.j)}</b> (${(x.dp*100).toFixed(0)}%)</li>`).join('')+`</ul></div>`:'';
  document.getElementById('ddSummary').innerHTML=fatalHtml+ins+`<div class="dd-summary"><div class="dd-summary-card"><div class="lbl">Выручка ${prevM}</div><div class="v">${fmt(prevSum)}</div></div><div class="dd-summary-card"><div class="lbl">Выручка ${lastM}</div><div class="v">${fmt(lastSum)}</div></div><div class="dd-summary-card ${mom<0?'alert':'success'}"><div class="lbl">Δ ${lastM} к ${prevM}</div><div class="v">${mom>=0?'+':''}${fmt(mom).replace(' ₽','')} ${unit}</div><div class="d ${mom<0?'down':'up'}">${momPct>=0?'+':''}${momPct.toFixed(1)}%</div></div><div class="dd-summary-card ${qoqPct<0?'alert':'success'}"><div class="lbl">Квартал к кварталу</div><div class="v">${qoqPct>=0?'+':''}${qoqPct.toFixed(1)}%</div><div class="d">Q2 vs Q1</div></div><div class="dd-summary-card ${killed.length?'alert':''}"><div class="lbl">Перестали в ${lastM}</div><div class="v">${killed.length} шт.</div><div class="d down">потеря ${fmt(killedLoss)}</div></div></div>`;
  renderDrilldownTable('ddPartnerTable',partnerRows,unit,'Партнёр');
  renderDrilldownTable('ddProgramTable',programRows,unit,'Программа');
  const topPart=[...partnerRows].sort((a,b)=>Math.abs(b.drop)-Math.abs(a.drop)).slice(0,8);
  const topProg=[...programRows].sort((a,b)=>Math.abs(b.drop)-Math.abs(a.drop)).slice(0,8);
  const barCfg=rows=>({type:'bar',data:{labels:rows.map(r=>r.name.length>45?r.name.slice(0,45)+'…':r.name),datasets:[{label:`Δ ${lastM}−${prevM}`,data:rows.map(r=>r.drop),backgroundColor:rows.map(r=>r.drop<0?'#ef4444':r.drop>0?'#10b981':'#94a3b8'),borderRadius:6}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{title:it=>rows[it[0].dataIndex].name,label:c=>{const r=rows[c.dataIndex];return [`${prevM}: ${fmt(r.prev)}`,`${lastM}: ${fmt(r.last)}`,`Δ: ${r.drop>=0?'+':''}${fmt(r.drop).replace(' ₽','')} ${unit}`];}}}},scales:{x:{ticks:{callback:v=>unit==='₽'?fmtR(v):fmtN(v)}},y:{grid:{display:false}}}}});
  if(ddPartChart)ddPartChart.destroy(); ddPartChart=new Chart(document.getElementById('chDdPartners'),barCfg(topPart));
  if(ddProgChart)ddProgChart.destroy(); ddProgChart=new Chart(document.getElementById('chDdPrograms'),barCfg(topProg));
  const lineCfg=rows=>({type:'line',data:{labels:MONTHS,datasets:rows.slice(0,6).map((r,i)=>({label:r.name.length>40?r.name.slice(0,40)+'…':r.name,data:r.byMonth,borderColor:PALETTE[i%PALETTE.length],backgroundColor:PALETTE[i%PALETTE.length]+'22',tension:0.3,borderWidth:2,pointRadius:3}))},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:10,font:{size:9}}},tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${unit==='₽'?fmtR(c.parsed.y):fmtN(c.parsed.y)}`}}},scales:{x:{grid:{display:false}},y:{ticks:{callback:v=>unit==='₽'?fmtR(v):fmtN(v)}}}}});
  if(ddPartLineChart)ddPartLineChart.destroy(); ddPartLineChart=new Chart(document.getElementById('chDdPartnersLine'),lineCfg(topPart));
  if(ddProgLineChart)ddProgLineChart.destroy(); ddProgLineChart=new Chart(document.getElementById('chDdProgramsLine'),lineCfg(topProg));
}
'''
assert s.count("// INIT\n")==1
s=s.replace("// INIT\n", OV+"\n// INIT\n", 1)
open("index_new.html","w",encoding="utf-8").write(s)
print("OK drilldown redesign injected;",len(s),"bytes")
