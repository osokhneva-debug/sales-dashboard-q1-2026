s=open("index_new.html",encoding="utf-8").read()

# 1) CSS: full height for dir/prof/skill tables + csv button
CSS_ANCHOR='.table-wrap{max-height:600px;overflow-y:auto;border-radius:10px;border:1px solid var(--border)}'
assert s.count(CSS_ANCHOR)==1
EXTRA_CSS=CSS_ANCHOR+'\n.table-wrap:has(#dirTable),.table-wrap:has(#profTable),.table-wrap:has(#skillTable){max-height:none}\n.csv-btn{margin-left:auto;font-size:12px;font-weight:600;padding:5px 12px;border-radius:8px;border:1px solid var(--border);background:#fff;color:#4f46e5;cursor:pointer}\n.csv-btn:hover{background:#eef2ff}'
s=s.replace(CSS_ANCHOR,EXTRA_CSS,1)

# 2) CSV buttons in headings
repl=[
 ('<h3>Полная таблица направлений <span class="badge">кликни на заголовок для сортировки</span></h3>',
  '<h3 style="display:flex;align-items:center;gap:10px">Полная таблица направлений <span class="badge">кликни на заголовок для сортировки</span><button class="csv-btn" onclick="downloadCSV(\'dirTable\',\'направления.csv\')">⬇ Скачать CSV</button></h3>'),
 ('<h3>Таблица профессий</h3>',
  '<h3 style="display:flex;align-items:center;gap:10px">Таблица профессий<button class="csv-btn" onclick="downloadCSV(\'profTable\',\'профессии.csv\')">⬇ Скачать CSV</button></h3>'),
 ('<h3>Таблица навыков <span class="badge">навыки разделены из мультизначных ячеек</span></h3>',
  '<h3 style="display:flex;align-items:center;gap:10px">Таблица навыков <span class="badge">навыки разделены из мультизначных ячеек</span><button class="csv-btn" onclick="downloadCSV(\'skillTable\',\'навыки.csv\')">⬇ Скачать CSV</button></h3>'),
]
for a,b in repl:
    assert s.count(a)==1,(a[:40],s.count(a)); s=s.replace(a,b,1)

# 3) downloadCSV function before // INIT
assert s.count("// INIT\n")==1
FN='''function downloadCSV(tableId,filename){
  const trs=[...document.querySelectorAll('#'+tableId+' tr')];
  const csv=trs.map(tr=>[...tr.querySelectorAll('th,td')].map(c=>{let t=(c.innerText||'').replace(/\\s+/g,' ').trim().replace(/"/g,'""');return '"'+t+'"';}).join(',')).join('\\n');
  const blob=new Blob(['\\uFEFF'+csv],{type:'text/csv;charset=utf-8'});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=filename;document.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(a.href);
}
'''
s=s.replace("// INIT\n", FN+"\n// INIT\n", 1)
open("index_new.html","w",encoding="utf-8").write(s)
print("OK extras injected;",len(s),"bytes")
