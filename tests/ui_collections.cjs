// Optional Chromium integration check: node tests/ui_collections.cjs
// Uses an isolated browser profile, synthetic data and the real UI assets.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawn} = require('node:child_process');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
const channel = {id:'abc1230001',name:'Archive',source:null,overrides:{},profile:{}};
const regionalChannel = {id:'abc1230005',name:'Regional',source:'https://www.youtube.com/@fixture',overrides:{},profile:{}};
const playlist = {id:'abc1230002',name:'Collection'};
const state = {channels:[channel,regionalChannel],playlists:[playlist],counts:{},settings:{download_mode:'compact',quality:'720'}};
let videos = Array.from({length:65}, (_,i)=>({id:`item${String(i).padStart(7,'0')}`,title:`Video ${i}`,channel_id:channel.id,state:'ready'}));
const requests = [];
let pending = true;
const server = require('node:http').createServer((req,res)=>{
  (async()=>{
    const url = new URL(req.url,'http://localhost');
    const chunks=[];
    for await (const chunk of req) chunks.push(chunk);
    const data=chunks.length?JSON.parse(Buffer.concat(chunks)):null;
    requests.push({method:req.method,path:url.pathname,data,locale:req.headers['x-gridtube-locale']});
    const send=(type,body)=>res.writeHead(200,{'Content-Type':type,'Content-Length':Buffer.byteLength(body)}).end(body);
    const json=value=>send('application/json',JSON.stringify(value));
    if (url.pathname==='/') return send('text/html; charset=utf-8',fs.readFileSync('static/index.html','utf8').replace('</head>',"<script>if(localStorage.getItem('gridtube.ui-test.detect')!=='1')localStorage.setItem('gridtube.locale','pt-BR')</script></head>"));
    if (url.pathname==='/static/app.js') return send('text/javascript; charset=utf-8',fs.readFileSync('static/app.js'));
    if (url.pathname==='/static/style.css') return send('text/css',fs.readFileSync('static/style.css'));
    if (url.pathname==='/static/icon.svg') return send('image/svg+xml',fs.readFileSync('static/icon.svg'));
    if (url.pathname==='/favicon.ico') return send('image/x-icon',fs.readFileSync('static/favicon.ico'));
    if (url.pathname==='/api/videos/item0000099/tracks') return json({video:{id:'item0000099',title:'Test video',filename:'main.mp4',state:'ready',duration:60},jobs:[]});
    if (url.pathname==='/api/videos/item0000099/progress') return json({ok:true});
    if (url.pathname==='/api/state') return json({...state,channels:state.channels.map(row=>row===regionalChannel?{...row,
      profile:{description:req.headers['x-gridtube-locale']==='pt-BR'?'Seja bem-vindo ao meu arquivo.':'Welcome to my archive.',locale_available:true}}:row)});
    if (url.pathname==='/api/videos') {
      const scope=url.searchParams.get('scope')||'';
      const rows=scope.startsWith('channel:')?videos.filter(v=>v.channel_id===scope.slice(8)):videos;
      const start=(Number(url.searchParams.get('page')||1)-1)*60;
      return json({videos:rows.slice(start,start+60),total:rows.length});
    }
    if (url.pathname.endsWith('/delete-preview')) return json({name:'Archive',ids:videos.map(v=>v.id),shared:1});
    if (url.pathname==='/api/videos/delete') {
      if (pending) {pending=false;return json({pending:true,removed:0});}
      videos=videos.filter(v=>!data.ids.includes(v.id));
      return json({pending:false,removed:data.ids.length});
    }
    if (req.method==='POST'&&url.pathname==='/api/channels') {
      const row={...data,id:'abc1230003',source:null,profile:{}};
      state.channels.push(row);return json({id:row.id});
    }
    if (req.method==='POST'&&url.pathname.endsWith('/move')) {
      videos.find(v=>url.pathname.includes(v.id)).channel_id=data.channel;return json({ok:true});
    }
    if (req.method==='POST'&&url.pathname==='/api/playlists') {
      const row={...data,id:'abc1230004'};
      state.playlists.push(row);return json({id:row.id});
    }
    if (req.method==='DELETE'&&url.pathname==='/api/playlists/'+playlist.id) {
      state.playlists=state.playlists.filter(p=>p.id!==playlist.id);videos=[];
      return json({pending:false,removed:data.ids.length});
    }
    res.writeHead(404).end();
  })().catch(error=>{console.error(error);res.writeHead(500).end();});
});
async function until(check,reason) {
  for(let i=0;i<100;i++){try{const result=await check();if(result)return result;}catch{}await delay(100);}
  throw Error(reason);
}
async function run() {
  const temp=fs.mkdtempSync(path.join(os.tmpdir(),'gridtube-bulk-'));
  let browser,socket;
  try {
    const profile=path.join(temp,'chrome');fs.mkdirSync(profile);
    await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
    const url=`http://127.0.0.1:${server.address().port}/`;
    const chrome=process.env.GRIDTUBE_CHROME||(process.platform==='win32'?'C:/Program Files/Google/Chrome/Application/chrome.exe':'chromium');
    browser=spawn(chrome,['--headless','--disable-gpu','--no-first-run','--remote-debugging-port=0',`--user-data-dir=${profile}`,'--window-size=1280,850',url],{stdio:'ignore',windowsHide:true});
    browser.on('error',error=>{console.error(error.message);});
    const port=await until(()=>fs.readFileSync(path.join(profile,'DevToolsActivePort'),'utf8').split(/\r?\n/)[0],'No Chromium debugging port');
    const target=await until(async()=>(await fetch(`http://127.0.0.1:${port}/json/list`).then(r=>r.json())).find(p=>p.type==='page'&&p.url===url),'No test tab');
    socket=new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
    const calls=new Map();let serial=0;
    socket.onmessage=event=>{const message=JSON.parse(event.data),call=calls.get(message.id);if(call){calls.delete(message.id);message.error?call.reject(message.error):call.resolve(message.result);}};
    const cdp=(method,params={})=>new Promise((resolve,reject)=>{const id=++serial;calls.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));});
    const evaluate=async expression=>{
      const result=await cdp('Runtime.evaluate',{expression,returnByValue:true});
      if(result.exceptionDetails) throw Error(JSON.stringify(result.exceptionDetails));
      return result.result.value;
    };
    const click=selector=>evaluate(`document.querySelector(${JSON.stringify(selector)}).click()`);
    await until(()=>evaluate('document.querySelectorAll("[data-select-video]").length===60'),'Cards unavailable');
    assert.equal(await evaluate('document.querySelector(".selection-toolbar").hidden'),true);
    assert.equal(await evaluate('[...document.querySelectorAll(".video-select")].every(label=>getComputedStyle(label).display==="none")'),true);
    await click('[data-action=settings]');
    assert.equal(await evaluate('document.querySelector("[name=pref_quality]").closest("label").firstChild.textContent.trim()'),'Resolução máxima');
    await evaluate('document.querySelector("[name=pref_download_mode]").value="original"');
    assert.equal(await evaluate('document.querySelector("[name=pref_quality]").value'),'720');
    assert.equal(await evaluate('document.querySelector("#settings-downloads").textContent.includes("O limite de resolução vale para os dois modos")'),true);
    await click('[data-action=close]');
    await click('[data-value=downloads]');
    await until(()=>evaluate('Boolean(document.querySelector(".job [data-action=selectionMenu]"))'),'Download selection menu unavailable');
    await click('.job [data-action=selectionMenu]');
    await click('#video-context-menu [data-action=selectVideo]');
    assert.equal(await evaluate('document.querySelector(".selection-toolbar").hidden'),false);
    await click('[data-action=clearSelection]');
    assert.equal(await evaluate('document.querySelector(".selection-toolbar").hidden'),true);
    await click('[data-value="channel:abc1230001"]');
    await until(()=>evaluate('Boolean(document.querySelector("[data-action=edit]"))'),'Channel actions unavailable');
    assert.equal(await evaluate('Boolean(document.querySelector("#library [data-action=deleteChannel]"))'),false);
    await click('[data-action=edit]');
    assert.equal(await evaluate('document.querySelector("[name=pref_download_mode]").selectedOptions[0].textContent.includes("Compacto")'),true);
    await evaluate('document.querySelector("[name=pref_quality]").value="1080";document.querySelector("[name=pref_quality]").dispatchEvent(new Event("change",{bubbles:true}))');
    assert.equal(await evaluate('document.querySelector("[name=pref_download_mode]").value'),'');
    await evaluate('document.querySelector("#simple [name=name]").value=""');
    await click('dialog [data-action=deleteChannel]');
    await until(()=>evaluate('Boolean(document.querySelector("#remove-bulk"))'),'Deletion preview unavailable');
    assert.equal(await evaluate('document.querySelector("#remove-bulk").textContent.includes("65")'),true);
    assert.equal(await evaluate('document.querySelector("#remove-bulk").textContent.includes("outras playlists")'),true);
    assert.equal(await evaluate('getComputedStyle(document.querySelector("#remove-bulk [value=disk]")).backgroundColor'),'rgb(174, 28, 50)');
    await click('[data-action=close]');
    const point=await evaluate('(()=>{const box=document.querySelector("[data-video-id=item0000000] .visual").getBoundingClientRect();return {x:box.left+30,y:box.top+30}})()');
    await cdp('Input.dispatchMouseEvent',{type:'mousePressed',button:'right',buttons:2,clickCount:1,...point});
    await cdp('Input.dispatchMouseEvent',{type:'mouseReleased',button:'right',buttons:0,clickCount:1,...point});
    await until(()=>evaluate('Boolean(document.querySelector("#video-context-menu [data-action=selectVideo]"))'),'Right-click menu unavailable');
    assert.equal(await evaluate('location.pathname'),'/');
    await cdp('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
    await cdp('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
    assert.equal(await evaluate('Boolean(document.querySelector("#video-context-menu"))'),false);
    assert.equal(await evaluate('document.activeElement.dataset.action'),'organize');
    await evaluate('document.querySelector("[data-video-id=item0000000]").dispatchEvent(new MouseEvent("contextmenu",{bubbles:true,clientX:innerWidth-1,clientY:innerHeight-1}))');
    const menuBounds=await evaluate('(()=>{const menu=document.querySelector("#video-context-menu"),box=menu.getBoundingClientRect();return {right:box.right,bottom:box.bottom,width:box.width,height:box.height,innerWidth,innerHeight,left:menu.style.left,top:menu.style.top}})()');
    assert.ok(menuBounds.right<=menuBounds.innerWidth&&menuBounds.bottom<=menuBounds.innerHeight,JSON.stringify(menuBounds));
    await click('#video-context-menu [data-action=selectVideo]');
    assert.equal(await evaluate('document.querySelector(".selection-toolbar").hidden'),false);
    assert.equal(await evaluate('[...document.querySelectorAll(".video-select")].every(label=>getComputedStyle(label).display!=="none")'),true);
    await click('[data-select-video=item0000000]');
    assert.equal(await evaluate('document.querySelector(".selection-toolbar").hidden'),true);
    assert.equal(await evaluate('[...document.querySelectorAll(".video-select")].every(label=>label.hidden)'),true);
    await click('[data-action=organize][data-value=item0000000]');
    await click('dialog [data-action=selectVideo]');
    assert.equal(await evaluate('document.querySelector("dialog").open'),false);
    assert.equal(await evaluate('document.querySelector("#selected-count").textContent.startsWith("1 ")'),true);
    await evaluate('document.querySelector("[data-select-video=item0000002]").dispatchEvent(new MouseEvent("click",{bubbles:true,shiftKey:true}))');
    assert.equal(await evaluate('document.querySelectorAll("[data-select-video]:checked").length'),3);
    await click('[data-action=page][data-value="2"]');
    await until(()=>evaluate('document.querySelectorAll("[data-select-video]").length===5'),'Second page unavailable');
    await click('#select-page');
    assert.equal(await evaluate('document.querySelector("#selected-count").textContent.startsWith("8 ")'),true);
    await click('[data-action=deleteSelected]');
    await click('#remove-bulk [value=disk]');
    await until(()=>evaluate('!document.querySelector("dialog").open'),'Bulk deletion did not finish');
    const deletions=requests.filter(r=>r.path==='/api/videos/delete');
    assert.equal(deletions.length,2);assert.equal(deletions[1].data.ids.length,8);assert.equal(deletions[1].data.disk,true);
    await click('[data-action=organize]');
    assert.equal(await evaluate('Boolean(document.querySelector("#new-channel,#new-playlist"))'),false);
    await evaluate('const channelSelect=document.querySelector("#move select");channelSelect.value="__new__";channelSelect.dispatchEvent(new Event("change"))');
    assert.equal(await evaluate('Boolean(document.querySelector("dialog [data-action=deleteChannel]"))'),false);
    await evaluate('document.querySelector("#simple [name=name]").value="New channel";document.querySelector("#simple button[type=submit]").click()');
    await until(()=>evaluate('!document.querySelector("dialog").open'),'Create and move did not finish');
    assert.equal(requests.filter(r=>r.path.endsWith('/move')).at(-1).data.channel,'abc1230003');
    await click('[data-action=organize]');
    await evaluate('const playlistSelect=document.querySelector("#add-to select");playlistSelect.value="__new__";playlistSelect.dispatchEvent(new Event("change"))');
    await evaluate('document.querySelector("#simple [name=name]").value="New playlist";document.querySelector("#simple button[type=submit]").click()');
    await until(()=>evaluate('!document.querySelector("dialog").open'),'Create and add did not finish');
    assert.ok(requests.find(r=>r.path==='/api/playlists'&&r.method==='POST').data.video);
    await click('[data-value="playlist:abc1230002"]');
    await until(()=>evaluate('Boolean(document.querySelector("[data-action=deletePlaylist]"))'),'Playlist actions unavailable');
    await cdp('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
    assert.equal(await evaluate('document.querySelector(".selection-toolbar").hidden'),true);
    await click('[data-action=organize]');
    await click('dialog [data-action=selectVideo]');
    assert.equal(await evaluate('document.querySelector(".selection-toolbar").hidden'),false);
    await click('[data-action=clearSelection]');
    assert.equal(await evaluate('document.querySelector(".selection-toolbar").hidden'),true);
    assert.equal(await evaluate('document.documentElement.scrollWidth<=innerWidth'),true);
    await click('[data-action=deletePlaylist]');
    await until(()=>evaluate('Boolean(document.querySelector("#remove-bulk"))'),'Playlist preview unavailable');
    assert.equal(await evaluate('document.querySelector("dialog").getBoundingClientRect().right<=innerWidth'),true);
    const screenshot=await cdp('Page.captureScreenshot',{format:'png'});
    const screenshotPath=path.join(os.tmpdir(),'gridtube-bulk-mobile.png');
    fs.writeFileSync(screenshotPath,Buffer.from(screenshot.data,'base64'));
    await click('#remove-bulk [value=keep]');
    await until(()=>evaluate('!document.querySelector("dialog").open'),'Playlist deletion did not finish');
    assert.equal(requests.find(r=>r.method==='DELETE'&&r.path==='/api/playlists/'+playlist.id).data.disk,false);
    await click('[data-value="channel:abc1230005"]');
    await until(()=>evaluate('document.querySelector(".channel-description")?.textContent.includes("Seja bem-vindo")'),'PT-BR channel bio unavailable');
    await evaluate('document.querySelector("#language").value="en";document.querySelector("#language").dispatchEvent(new Event("change"))');
    await until(()=>evaluate('document.querySelector(".channel-description")?.textContent.includes("Welcome")'),'English channel bio unavailable');
    assert.ok(requests.some(r=>r.path==='/api/state'&&r.locale?.startsWith('en-')));
    await click('[data-action=edit]');
    assert.equal(await evaluate('document.querySelector("[name=pref_quality]").closest("label").firstChild.textContent.trim()'),'Maximum resolution');
    await click('[data-action=close]');
    await evaluate('document.querySelector("#language").value="pt-BR";document.querySelector("#language").dispatchEvent(new Event("change"))');
    await until(()=>evaluate('document.querySelector(".channel-description")?.textContent.includes("Seja bem-vindo")'),'PT-BR bio not restored after switching back');
    assert.equal(await evaluate('Boolean(document.querySelector("#library [data-action=deleteChannel]"))'),false);
    await click('[data-action=edit]');
    assert.equal(await evaluate('Boolean(document.querySelector("dialog [data-action=deleteChannel]"))'),true);
    await cdp('Page.enable');
    await cdp('Page.addScriptToEvaluateOnNewDocument',{source:"Object.defineProperty(navigator,'languages',{get:()=>['en-GB']});Object.defineProperty(navigator,'language',{get:()=> 'en-GB'})"});
    await evaluate("localStorage.setItem('gridtube.ui-test.detect','1');localStorage.removeItem('gridtube.locale');localStorage.removeItem('untube.locale')");
    await cdp('Page.reload',{ignoreCache:true});
    await until(()=>evaluate('document.documentElement.lang==="en"&&document.querySelector("#language")?.value==="en"'),'Browser language was not selected on first visit');
    await until(()=>requests.filter(r=>r.path==='/api/state').at(-1)?.locale==='en-GB','Browser region not sent to the server');
    await evaluate('window.gridtubeHomeMarker="same document"');
    await click('.mobile-brand');
    await until(()=>evaluate('Boolean(document.querySelector(".hero"))&&!document.querySelector(".channel-page")'),'Brand did not return to the library');
    assert.equal(await evaluate('window.gridtubeHomeMarker'),'same document');
    await click('.mobile-brand');
    await until(()=>evaluate('window.gridtubeHomeMarker===undefined&&Boolean(document.querySelector(".hero"))'),'Brand did not reload the library page');
    assert.equal(await evaluate('document.querySelector(".mobile-brand .mark").getAttribute("src")'),'/static/icon.svg');
    await until(()=>evaluate('document.querySelector(".mobile-brand .mark").naturalWidth>0'),'New icon did not load');
    assert.equal(await evaluate('document.querySelector("link[rel=icon]").getAttribute("href")'),'/favicon.ico?v=red-grid');
    await cdp('Emulation.setDeviceMetricsOverride',{width:1280,height:850,deviceScaleFactor:1,mobile:false});
    await evaluate('history.pushState({watchFromApp:true},"","/watch/item0000099");dispatchEvent(new PopStateEvent("popstate"))');
    await until(()=>evaluate('Boolean(document.querySelector("#player"))'),'Watch route unavailable');
    await click('.brand');
    await until(()=>evaluate('location.pathname==="/"&&Boolean(document.querySelector(".hero"))&&!document.querySelector("#player")'),'Desktop brand did not leave the watch route');
    const brandImage=await cdp('Page.captureScreenshot',{format:'png',clip:{x:0,y:0,width:235,height:100,scale:1}});
    fs.writeFileSync(path.join(os.tmpdir(),'gridtube-brand-preview.png'),Buffer.from(brandImage.data,'base64'));
    const ico=fs.readFileSync('static/favicon.ico');
    assert.equal(ico.readUInt16LE(2),1);assert.equal(ico.readUInt16LE(4),6);
    for(let index=0;index<6;index++){
      const entry=6+index*16,size=ico[entry]||256,length=ico.readUInt32LE(entry+8),offset=ico.readUInt32LE(entry+12);
      assert.ok(offset+length<=ico.length);assert.equal(ico.readUInt32BE(offset+16),size);assert.equal(ico.readUInt32BE(offset+20),size);
    }
    console.log('Chromium verified: brand navigation from channel/watch, full reload in library, new SVG and favicon sizes, channel editor, localized profiles, selection, bulk deletion and mobile layout.');
    console.log('Screenshot:',screenshotPath);
  } finally {
    socket?.close();
    if(browser&&browser.exitCode===null){const done=new Promise(resolve=>browser.once('exit',resolve));browser.kill();await Promise.race([done,delay(2000)]);}
    server.closeAllConnections();server.close();
    const absolute=path.resolve(temp),parent=path.resolve(os.tmpdir());
    if(absolute.startsWith(parent+path.sep)&&path.basename(absolute).startsWith('gridtube-bulk-')) {
      try{fs.rmSync(absolute,{recursive:true,force:true,maxRetries:2,retryDelay:250});}catch{}
    }
  }
}
run().catch(error=>{console.error(error);process.exitCode=1;});
