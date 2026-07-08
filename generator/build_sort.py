s=open("index_new.html",encoding="utf-8").read()
assert s.count("// INIT\n")==1

DD='''// ====== Drilldown tables: sortable columns (override) ======
function renderDrilldownTable(tableId, rows, unit, labelCol){
  const fmt = unit==='₽'?fmtR:fmtN;
  const sort = tableSort[tableId] || {col:'drop',dir:'asc'};
  const val=(r,col)=>{
    if(col==='name') return (r.name||'').toLowerCase();
    if(col==='total') return r.total||0;
    if(col==='drop') return r.drop||0;
    if(col==='dropPct') return (r.dropPct==null?-Infinity:r.dropPct);
    if(col==='status'){const o={killed:0,down:1,flat:2,up:3,new:4};return (o[r.status]!=null?o[r.status]:2);}
    return r.byMonth[+col]||0;
  };
  const srt=rows.slice().sort((a,b)=>{const va=val(a,sort.col),vb=val(b,sort.col);
    if(typeof va==='string') return sort.dir==='asc'?va.localeCompare(vb):vb.localeCompare(va);
    return sort.dir==='asc'?va-vb:vb-va;});
  const drops=srt.map(r=>r.drop);const maxAbs=Math.max(...drops.map(Math.abs),1);
  const th=(col,lbl,cls='')=>{const sc=String(sort.col)===String(col)?(sort.dir==='asc'?'sort-asc':'sort-desc'):'';return `<th data-sort="${col}" class="${sc} ${cls}" style="cursor:pointer;user-select:none">${lbl}</th>`;};
  let html=`<thead><tr><th>#</th>${th('name',labelCol)}${MONTHS.map((m,i)=>th(i,m,'num')).join('')}${th('total','Итого','num')}${th('drop','Δ Янв→'+MONTHS[MONTHS.length-1],'num')}${th('dropPct','Δ %','num')}${th('status','Статус')}</tr></thead><tbody>`;
  srt.forEach((r,idx)=>{
    const rankCls=idx===0?'top1':idx===1?'top2':idx===2?'top3':'';
    const intensity=Math.min(Math.abs(r.drop)/maxAbs,1);
    const diffBg=r.drop<0?`rgba(239, 68, 68, ${0.15+0.5*intensity})`:r.drop>0?`rgba(16, 185, 129, ${0.15+0.5*intensity})`:'#f8fafc';
    const diffColor=(r.drop<0&&intensity>0.7)||(r.drop>0&&intensity>0.7)?'white':(r.drop<0?'#991b1b':r.drop>0?'#065f46':'#64748b');
    const statusTag=r.status==='killed'?`<span class="kill-tag">⚠️ обнулился</span>`:r.status==='new'?`<span class="new-tag">🆕 новый</span>`:r.status==='down'?`<span class="trend-down">↘ падение</span>`:r.status==='up'?`<span class="trend-up">↗ рост</span>`:`<span class="trend-flat">— стаб.</span>`;
    html+=`<tr><td><span class="rank ${rankCls}">${idx+1}</span></td><td class="cat-cell" title="${r.name}">${r.name}</td>${r.byMonth.map(v=>`<td class="num">${fmt(v)}</td>`).join('')}<td class="num"><strong>${fmt(r.total)}</strong></td><td class="num"><span class="heatmap-cell" style="background:${diffBg};color:${diffColor}">${r.drop>=0?'+':''}${fmt(r.drop).replace(' ₽','')}${unit==='₽'?' ₽':''}</span></td><td class="num ${r.dropPct==null?'trend-flat':(r.dropPct>=0?'trend-up':'trend-down')}">${r.dropPct==null?'—':fmtPct(r.dropPct)}</td><td>${statusTag}</td></tr>`;
  });
  html+='</tbody>';
  document.getElementById(tableId).innerHTML=html;
  document.querySelectorAll(`#${tableId} th[data-sort]`).forEach(h=>{h.onclick=()=>{const col=h.dataset.sort;const cur=tableSort[tableId]||{col:'drop',dir:'asc'};if(String(cur.col)===String(col))cur.dir=cur.dir==='asc'?'desc':'asc';else{cur.col=col;cur.dir=(col==='name')?'asc':'desc';}tableSort[tableId]=cur;renderDrilldownTable(tableId,rows,unit,labelCol);};});
}
'''
s=s.replace("// INIT\n", DD+"\n// INIT\n", 1)
open("index_new.html","w",encoding="utf-8").write(s)
print("OK, DD sortable override injected;",len(s),"bytes")
