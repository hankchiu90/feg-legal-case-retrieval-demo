"""本機案例檢索可視化伺服器。

執行：python server.py
開啟：http://127.0.0.1:8765
"""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "showcase_data.json"
DRAWIO_DIR = BASE_DIR / "assets" / "drawio"
HOST, PORT = "127.0.0.1", 8780


def load_data() -> dict:
    """Load the compact five-case showcase dataset bundled with this demo."""
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


DATA = load_data()


def case_payload(graph_id: str) -> dict | None:
    query = DATA["queries"].get(graph_id)
    retrieval = DATA["retrievals"].get(graph_id)
    showcase = DATA["showcase"].get(graph_id)
    if not query or not retrieval or not showcase:
        return None
    matches = []
    for rank, item in enumerate(retrieval.get("top_5_retrieved", []), 1):
        history_id = item["similar_graph_id"]
        history = DATA["histories"].get(history_id)
        if history:
            matches.append({
                "rank": rank,
                "score": item.get("score"),
                "case": history,
                "graph": DATA["graphs"].get(history_id, {"nodes": [], "edges": []}),
                "drawio_svg": "/drawio/" + showcase["references"][rank - 1]["svg"],
            })
    return {
        "query": query,
        "query_graph": DATA["graphs"].get(graph_id, {"nodes": [], "edges": []}),
        "matches": matches,
        "llm": DATA["llm"].get(graph_id),
        "drawio_query_svg": "/drawio/" + showcase["query_svg"],
    }


HTML = r'''<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>判例脈絡｜案件檢索</title>
  <style>
    :root { --ink:#172033; --muted:#5f6b7a; --line:#d9e1ea; --paper:#f7f9fc; --blue:#175cd3; --pale:#edf4ff; --green:#067647; --red:#b42318; }
    * { box-sizing:border-box } body { margin:0; color:var(--ink); background:var(--paper); font-family:"Microsoft JhengHei",system-ui,sans-serif; line-height:1.55 }
    header { background:#102a43; color:white; padding:22px max(24px,calc((100% - 1220px)/2)); } header h1 { margin:0; font-size:24px } header p { margin:4px 0 0; color:#d9eaff }
    main { max-width:1220px; margin:0 auto; padding:20px 24px 42px } select { width:100%; padding:10px; border:1px solid var(--line); border-radius:7px; background:white; font-size:15px }
    .hint { color:var(--muted); font-size:14px; margin:8px 0 18px }.meta { display:flex; gap:8px; flex-wrap:wrap; margin:8px 0 }.tag { background:var(--pale); color:var(--blue); padding:2px 8px; border-radius:999px; font-size:13px }.card { background:white; border:1px solid var(--line); border-radius:10px; padding:16px; margin:14px 0 }.grid { display:grid; grid-template-columns:1fr 1fr; gap:16px }.feg-stack { display:grid; grid-template-columns:1fr; gap:22px }.match-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:8px }.match { text-align:left; width:100%; background:white; border:1px solid var(--line); border-radius:8px; padding:10px; cursor:pointer; color:inherit }.match.active { border:2px solid var(--blue); background:var(--pale) }.score { color:var(--blue); font-weight:700 }.small { font-size:13px; color:var(--muted); overflow-wrap:anywhere }.graph { height:650px; overflow:hidden; background:#080d16; border:1px solid #202b3b; border-radius:10px; position:relative }.feg-svg { width:100%; height:100%; display:block }.legend { display:flex; gap:10px; flex-wrap:wrap; font-size:12px; color:var(--muted); margin:5px 0 }.swatch { width:10px; height:10px; display:inline-block; border-radius:50%; margin-right:3px } .graph-help { color:#c2ccda; position:absolute; right:14px; bottom:9px; z-index:2; font-size:12px; pointer-events:none } .feg-node { cursor:pointer } .feg-node circle { stroke:#e5e7eb; stroke-width:2.5 } .feg-node:hover circle { stroke:#fff; stroke-width:5 } details { border-top:1px solid var(--line); padding:10px 0 } summary { cursor:pointer; font-weight:600 } .fact { white-space:pre-wrap; font-size:14px; max-height:420px; overflow:auto; padding:10px 0 } pre { white-space:pre-wrap; overflow:auto; font-family:inherit; font-size:14px; margin:8px 0 0 } #nodeDetail { min-height:94px } #loading { padding:30px; text-align:center; color:var(--muted) }.notice { background:#fff8e8; border-color:#f0d18c; color:#513a06; font-size:13px }
    .comparison { display:grid; grid-template-columns:1fr 1fr; gap:22px; align-items:start; margin-top:10px }.comparison h2 { margin-top:0 }.drawio-graph { background:#080d16; border:1px solid #202b3b; border-radius:10px; overflow:hidden; aspect-ratio:4/3 }.drawio-graph img { display:block; width:100%; height:100%; object-fit:contain }.zoom { margin-top:8px; border:1px solid var(--blue); border-radius:7px; background:white; color:var(--blue); padding:7px 10px; cursor:pointer; font-weight:600 }.modal { position:fixed; inset:0; z-index:10; display:none; place-items:center; padding:24px; background:rgba(8,13,22,.9) }.modal.open { display:grid }.zoom-stage { width:96vw; height:86vh; position:relative; overflow:hidden; cursor:grab; touch-action:none; user-select:none }.zoom-stage.dragging { cursor:grabbing }.zoom-stage img { position:absolute; left:50%; top:50%; max-width:none; max-height:none; background:#080d16; border-radius:8px; cursor:inherit; -webkit-user-drag:none; user-select:none }.modal button { position:absolute; top:18px; right:22px; border:0; border-radius:6px; padding:8px 12px; background:white; color:#172033; cursor:pointer; font-weight:700 }.zoom-help { position:absolute; bottom:18px; color:white; font-size:13px; pointer-events:none }
    @media (max-width:850px) { .grid { grid-template-columns:1fr }.match-grid { grid-template-columns:repeat(2,1fr) } main { padding:16px } }
    @media (max-width:620px) { .comparison { grid-template-columns:1fr } }
  </style>
</head>
<body>
<header><h1>判例脈絡</h1><p>依案件事實脈絡，找出值得參考的相近判決。</p></header>
<main>
  <label for="querySelect"><strong>選擇要分析的案件</strong></label><select id="querySelect"></select>
  <p class="hint">系統會呈現五件事實結構相近的參考判決，以及案件事實圖譜與分析理由。</p>
  <div id="loading">正在載入案件資料…</div><section id="content" hidden></section>
</main>
<div class="modal" id="graphModal" role="dialog" aria-modal="true" aria-label="放大檢視事實圖譜"><button id="closeModal" type="button">關閉</button><div class="zoom-stage" id="zoomStage"><img id="modalImage" alt="放大事實圖譜" draggable="false"></div><span class="zoom-help">滾輪縮放・放大後按住圖譜左右拖曳・關閉後重設</span></div>
<script>
let current, active=0; const typeColors={"裁判書":"#cfe2cc","被告":"#cfe2cc","被害主體":"#cfe2cc","犯罪工具":"#00a000","犯罪原因":"#ffff8a","涉案行為":"#ffff8a","後果評估":"#ff7200"};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
const short=(s,n=72)=>s&&s.length>n?s.slice(0,n)+'…':s||'未提供';
const nodeSummary=(s,max=54)=>{const text=String(s||'未提供').replace(/\s+/g,' ').trim();return text.length>max?text.slice(0,max)+'…':text};
async function init(){ const list=await (await fetch('/api/queries')).json(); const sel=document.querySelector('#querySelect'); sel.innerHTML=list.map((q,i)=>`<option value="${esc(q.graph_id)}">${esc(q.charge)}｜${esc(q.id)}</option>`).join(''); sel.addEventListener('change',()=>load(sel.value)); load(list[0].graph_id); }
async function load(id){ document.querySelector('#loading').hidden=false; document.querySelector('#content').hidden=true; current=await (await fetch('/api/case?graph_id='+encodeURIComponent(id))).json(); active=0; document.querySelector('#content').hidden=false; render(); document.querySelector('#loading').hidden=true; }
function graphPanel(id){return `<div class="graph"><div id="${id}" role="img" aria-label="互動式案件事實圖譜"></div><span class="graph-help">點選圓形節點查看完整文本</span></div>`}
function showNode(kind,fullText){const box=document.querySelector('#nodeDetail');box.innerHTML=`<h3>${esc(kind)}</h3><p>${esc(fullText)}</p>`}
function nodeLines(n){const chars=Array.from(String(n.content||'未提供').replace(/\s+/g,'').trim());const text=chars.slice(0,30);const chunks=[];for(let i=0;i<text.length;i+=10)chunks.push(text.slice(i,i+10).join(''));if(chars.length>30&&chunks.length)chunks[chunks.length-1]=chunks[chunks.length-1].slice(0,9)+'…';return [n.label||'其他',...chunks.slice(0,3)]}
function renderGraph(containerId, graph){
 const container=document.getElementById(containerId);if(!container)return;const nodes=graph.nodes||[],edges=graph.edges||[];
 if(!nodes.length){container.innerHTML='<p class="hint">找不到此案的事實圖譜資料。</p>';return}
 const slots={"裁判書":[115,145],"被告":[120,500],"被害主體":[355,145],"犯罪工具":[545,325],"涉案行為":[760,500],"犯罪原因":[525,590],"後果評估":[865,150]};const fallback=[[310,340],[740,340],[850,600]];const pos={};nodes.forEach((n,i)=>pos[n.id]=slots[n.label]||fallback[i%fallback.length]);const radius=86;
 const clip=(a,b)=>{const dx=b[0]-a[0],dy=b[1]-a[1],d=Math.hypot(dx,dy)||1;return [[a[0]+dx*(radius+6)/d,a[1]+dy*(radius+6)/d],[b[0]-dx*(radius+12)/d,b[1]-dy*(radius+12)/d]]};
 const edgeSvg=edges.map(e=>{const a=pos[e.source],b=pos[e.target];if(!a||!b)return'';const [s,t]=clip(a,b),mx=(s[0]+t[0])/2,my=(s[1]+t[1])/2,label=esc(e.type||'');return `<line x1="${s[0]}" y1="${s[1]}" x2="${t[0]}" y2="${t[1]}" stroke="#aab6c5" stroke-width="2.4" marker-end="url(#arrow)"/><text x="${mx}" y="${my-7}" text-anchor="middle" fill="#f8fafc" font-size="14" font-weight="600" style="paint-order:stroke;stroke:#080d16;stroke-width:5px;stroke-linejoin:round">${label}</text>`}).join('');
 const nodeSvg=nodes.map(n=>{const [x,y]=pos[n.id],lines=nodeLines(n),color=typeColors[n.label]||'#d9e1ea',textColor=n.label==='犯罪工具'?'#fff':'#111827';return `<g class="feg-node" data-node="${esc(n.id)}"><circle cx="${x}" cy="${y}" r="${radius}" fill="${color}"/><text x="${x}" y="${y-(lines.length-1)*9}" text-anchor="middle" fill="${textColor}" font-family="Microsoft JhengHei, sans-serif"><tspan x="${x}" dy="0" font-size="17" font-weight="700">${esc(lines[0])}</tspan>${lines.slice(1).map(line=>`<tspan x="${x}" dy="17" font-size="12.5" font-weight="600">${esc(line)}</tspan>`).join('')}</text></g>`}).join('');
 container.innerHTML=`<svg class="feg-svg" viewBox="0 0 1000 700" preserveAspectRatio="xMidYMid meet"><defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#aab6c5"/></marker></defs>${edgeSvg}${nodeSvg}</svg>`;
 container.querySelectorAll('[data-node]').forEach(el=>el.addEventListener('click',()=>{const n=nodes.find(x=>String(x.id)===el.dataset.node);if(n)showNode(n.label||'其他',n.content||n.label||'未提供')}));
}
function caseHeader(c){return `<h2>${esc(c.charge)}</h2><div class="meta"><span class="tag">${esc(c.article)}</span><span class="tag">${esc(c.title)}</span></div><p class="small">${esc(c.id)}</p><p>${esc(c.main)}</p>`}
function render(){ const q=current.query,m=current.matches[active], llm=current.llm, content=document.querySelector('#content'); content.innerHTML=`
 <div class="card"><p class="small">正在分析的案件</p>${caseHeader(q)}<details><summary>查看本案完整事實</summary><div class="fact">${esc(q.fact)}</div></details></div>
 <h2>相近參考判決</h2><div class="match-grid">${current.matches.map((x,i)=>`<button class="match ${i===active?'active':''}" data-rank="${i}"><strong>參考案例 ${x.rank}</strong><br><span class="score">相近度 ${Number(x.score).toFixed(4)}</span><br><span class="small">${esc(x.case.charge)}</span></button>`).join('')}</div>
 <div class="card"><p class="small">目前比較的參考案例 ${m.rank}</p>${caseHeader(m.case)}<p><strong>事實結構相近度：</strong><span class="score">${Number(m.score).toFixed(4)}</span></p><details><summary>查看相似案例完整事實</summary><div class="fact">${esc(m.case.fact)}</div></details></div>
 <div class="legend">${Object.entries(typeColors).map(([k,v])=>`<span><i class="swatch" style="background:${v}"></i>${k}</span>`).join('')}</div><section class="comparison"><section><h2>本案事實圖譜</h2><div class="drawio-graph"><img src="${current.drawio_query_svg}" alt="本案事實圖譜（Draw.io 製作）"></div><button class="zoom" type="button" data-zoom="${current.drawio_query_svg}">放大查看本案圖譜</button></section><section><h2>參考案例 ${m.rank} 的事實圖譜</h2><div class="drawio-graph"><img src="${m.drawio_svg}" alt="參考案例事實圖譜（Draw.io 製作）"></div><button class="zoom" type="button" data-zoom="${m.drawio_svg}">放大查看相似案例圖譜</button></section></section>
 <p class="hint">左右兩圖皆由 Draw.io 匯出；可透過上方參考案例按鈕切換比較對象。</p>
 <section class="card"><h2>AI 分析結果</h2>${llm?`<div class="grid"><div><strong>建議罪名</strong><p>${esc(llm.prediction.predicted_charge||'—')}</p></div><div><strong>可能適用條文</strong><p>${esc(llm.prediction.predicted_article||'—')}</p></div></div><details><summary>查看分析理由</summary><pre>${esc(llm.reasoning)}</pre></details>`:'<p class="hint">此案件尚無可供顯示的分析結果。</p>'}</section>
 <footer class="card notice">本系統用於案件檢索與資訊整理；相近度與 AI 分析僅供輔助參考，不構成個案法律意見或裁判依據。</footer>`;
 document.querySelectorAll('[data-rank]').forEach(b=>b.addEventListener('click',()=>{active=Number(b.dataset.rank);render();})); document.querySelectorAll('[data-zoom]').forEach(b=>b.addEventListener('click',()=>{resetZoom(b.dataset.zoom);graphModal.classList.add('open')})); }
let zoomScale=1,zoomX=0,zoomY=0,zoomBaseWidth=0,zoomBaseHeight=0,dragState=null;
const graphModal=document.querySelector('#graphModal'),zoomStage=document.querySelector('#zoomStage'),modalImage=document.querySelector('#modalImage');
function drawZoom(){if(!zoomBaseWidth)return;modalImage.style.width=`${zoomBaseWidth*zoomScale}px`;modalImage.style.height=`${zoomBaseHeight*zoomScale}px`;modalImage.style.transform=`translate(-50%,-50%) translate(${zoomX}px,${zoomY}px)`;}
function fitImage(){const ratio=modalImage.naturalWidth/modalImage.naturalHeight||1,maxWidth=zoomStage.clientWidth,maxHeight=zoomStage.clientHeight;if(maxWidth/maxHeight>ratio){zoomBaseHeight=maxHeight;zoomBaseWidth=maxHeight*ratio;}else{zoomBaseWidth=maxWidth;zoomBaseHeight=maxWidth/ratio;}drawZoom();}
function resetZoom(source){zoomScale=1;zoomX=0;zoomY=0;zoomBaseWidth=0;zoomBaseHeight=0;modalImage.onload=fitImage;modalImage.src=source;if(modalImage.complete)fitImage();}
function closeZoom(){graphModal.classList.remove('open');dragState=null;zoomStage.classList.remove('dragging');}
zoomStage.addEventListener('wheel',event=>{event.preventDefault();const rect=zoomStage.getBoundingClientRect(),previous=zoomScale,next=Math.min(5,Math.max(1,previous*(event.deltaY<0?1.16:1/1.16)));if(next===previous)return;const pointerX=event.clientX-(rect.left+rect.width/2),pointerY=event.clientY-(rect.top+rect.height/2);zoomX-=pointerX*(next/previous-1);zoomY-=pointerY*(next/previous-1);zoomScale=next;drawZoom();},{passive:false});
function beginDrag(event){if(zoomScale===1)return;event.preventDefault();dragState={x:event.clientX,y:event.clientY,panX:zoomX,panY:zoomY};zoomStage.classList.add('dragging');if(event.pointerId!==undefined)zoomStage.setPointerCapture(event.pointerId);}
function moveDrag(event){if(!dragState)return;event.preventDefault();zoomX=dragState.panX+event.clientX-dragState.x;zoomY=dragState.panY+event.clientY-dragState.y;drawZoom();}
function endDrag(){dragState=null;zoomStage.classList.remove('dragging');}
zoomStage.addEventListener('pointerdown',beginDrag);zoomStage.addEventListener('pointermove',moveDrag);zoomStage.addEventListener('pointerup',endDrag);zoomStage.addEventListener('pointercancel',endDrag);
zoomStage.addEventListener('mousedown',beginDrag);window.addEventListener('mousemove',moveDrag);window.addEventListener('mouseup',endDrag);modalImage.addEventListener('dragstart',event=>event.preventDefault());
document.querySelector('#closeModal').addEventListener('click',closeZoom);
graphModal.addEventListener('click',e=>{if(e.target===graphModal)closeZoom()});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&graphModal.classList.contains('open'))closeZoom()});
init().catch(e=>{document.querySelector('#loading').textContent='載入失敗：'+e.message});
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        url = urlparse(self.path)
        if url.path.startswith("/drawio/"):
            relative = Path(url.path.removeprefix("/drawio/"))
            asset = (DRAWIO_DIR / relative).resolve()
            if DRAWIO_DIR.resolve() not in asset.parents or asset.suffix != ".svg" or not asset.is_file():
                return self.send_error(404)
            body = asset.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return self.wfile.write(body)
        if url.path == "/api/queries":
            return self.send_json(DATA["query_list"])
        if url.path == "/api/case":
            graph_id = parse_qs(url.query).get("graph_id", [""])[0]
            payload = case_payload(graph_id)
            return self.send_json(payload or {"error": "找不到案件"}, 200 if payload else 404)
        if url.path == "/":
            body = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return self.wfile.write(body)
        self.send_error(404)

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    print(f"正在載入完成。請開啟 http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
