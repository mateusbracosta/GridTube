// Offline player regression: builds disposable media with the current Docker image.
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawn,spawnSync}=require('node:child_process');
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(check,reason){for(let i=0;i<100;i++){try{const value=await check();if(value)return value;}catch{}await delay(80);}throw Error(reason);}
async function run(){
  const temp=fs.mkdtempSync(path.join(os.tmpdir(),'gridtube-playback-'));
  const image=process.env.GRIDTUBE_TEST_IMAGE||/image:\s*(\S+)/.exec(fs.readFileSync('compose.yaml','utf8'))[1];
  let browser,socket,server;
  try{
    const encoded=spawnSync('docker',['run','--rm','--network','none','-v',`${temp}:/fixture`,image,
      'ffmpeg','-loglevel','error','-f','lavfi','-i','color=c=black:s=160x90:r=5:d=8','-an',
      '-c:v','libvpx','-deadline','realtime','/fixture/main.webm'],{encoding:'utf8',windowsHide:true});
    assert.equal(encoded.status,0,encoded.stderr||encoded.error?.message);
    const media=fs.readFileSync(path.join(temp,'main.webm'));
    const video={id:'fixture0001',title:'Offline playback fixture',filename:'main.webm',duration:8,
      state:'ready',position:0,audio:'pt-BR',audio_tracks:{en:'extra.en.m4a'},subtitles:{}};
    server=require('node:http').createServer((req,res)=>{
      (async()=>{
        const url=new URL(req.url,'http://localhost').pathname;
        const send=(type,body)=>res.writeHead(200,{'Content-Type':type,'Content-Length':Buffer.byteLength(body)}).end(body);
        const json=value=>send('application/json',JSON.stringify(value));
        if(url==='/')return send('text/html; charset=utf-8',fs.readFileSync('static/index.html','utf8').replace('</head>',"<script>localStorage.setItem('gridtube.locale','pt-BR')</script></head>"));
        if(url==='/static/app.js')return send('text/javascript',fs.readFileSync('static/app.js'));
        if(url==='/static/style.css')return send('text/css',fs.readFileSync('static/style.css'));
        if(url==='/static/icon.svg')return send('image/svg+xml',fs.readFileSync('static/icon.svg'));
        if(url==='/favicon.ico')return send('image/x-icon',fs.readFileSync('static/favicon.ico'));
        if(url==='/api/state')return json({channels:[],playlists:[],counts:{ready:1},settings:{}});
        if(url==='/api/videos')return json({videos:[video],total:1});
        if(url==='/api/videos/fixture0001/tracks')return json({video,jobs:[]});
        if(url==='/api/videos/fixture0001/progress'){for await(const chunk of req){}return json({ok:true});}
        if(url==='/media/fixture0001/main.webm'||url==='/playback/fixture0001/en'){
          const range=/bytes=(\d+)-(\d*)/.exec(req.headers.range||'');
          const start=range?Number(range[1]):0,end=range&&range[2]?Math.min(Number(range[2]),media.length-1):media.length-1;
          res.writeHead(range?206:200,{'Content-Type':'video/webm','Accept-Ranges':'bytes','Content-Length':end-start+1,
            ...(range?{'Content-Range':`bytes ${start}-${end}/${media.length}`}:{})});return res.end(media.subarray(start,end+1));
        }
        res.writeHead(404).end();
      })().catch(error=>{console.error(error);res.writeHead(500).end();});
    });
    await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
    const url=`http://127.0.0.1:${server.address().port}/`,profile=path.join(temp,'chrome');fs.mkdirSync(profile);
    const chrome=process.env.GRIDTUBE_CHROME||(process.platform==='win32'?'C:/Program Files/Google/Chrome/Application/chrome.exe':'chromium');
    browser=spawn(chrome,['--headless','--disable-gpu','--no-first-run','--autoplay-policy=no-user-gesture-required',
      '--remote-debugging-port=0',`--user-data-dir=${profile}`,url],{stdio:'ignore',windowsHide:true});
    browser.on('error',error=>console.error(error.message));
    const port=await until(()=>fs.readFileSync(path.join(profile,'DevToolsActivePort'),'utf8').split(/\r?\n/)[0],'No browser port');
    const target=await until(async()=>(await fetch(`http://127.0.0.1:${port}/json/list`).then(r=>r.json())).find(p=>p.type==='page'&&p.url===url),'No test tab');
    socket=new WebSocket(target.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
    let serial=0;const calls=new Map();
    socket.onmessage=event=>{const result=JSON.parse(event.data),call=calls.get(result.id);if(call){calls.delete(result.id);result.error?call.reject(result.error):call.resolve(result.result);}};
    const cdp=(method,params={})=>new Promise((resolve,reject)=>{const id=++serial;calls.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));});
    const evaluate=async expression=>{const result=await cdp('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));return result.result.value;};
    await until(()=>evaluate('Boolean(document.querySelector("[data-action=watch]"))'),'Watch action unavailable');
    await evaluate('document.querySelector("[data-action=watch]").click()');
    await until(()=>evaluate('document.querySelector("#player")?.readyState>=1'),'Main media unavailable');
    await evaluate('document.querySelector("#player").pause();document.querySelector("#player").currentTime=1');
    await until(()=>evaluate('!document.querySelector("#player").seeking'),'Initial seek incomplete');
    await evaluate('const audio=document.querySelector("[name=watchAudio]");audio.value="en";audio.dispatchEvent(new Event("change",{bubbles:true}))');
    await until(()=>evaluate('document.querySelector("#player").currentSrc.includes("/playback/")&&document.querySelector("#player").readyState>=1'),'Alternate media unavailable');
    await evaluate('document.querySelector("#player").currentTime=5');
    await until(()=>evaluate('!document.querySelector("#player").seeking&&document.querySelector("#player").currentTime>=4.9'),'Alternate seek incomplete');
    await evaluate('document.querySelector("#player").dispatchEvent(new Event("error"))');
    await until(()=>evaluate('document.querySelector("#player").currentSrc.includes("/media/")&&document.querySelector("#player").readyState>=1'),'Fallback media unavailable');
    const paused=await evaluate('({position:document.querySelector("#player").currentTime,paused:document.querySelector("#player").paused})');
    assert.ok(Math.abs(paused.position-5)<0.2,`Fallback lost the current position: ${JSON.stringify(paused)}`);
    assert.equal(paused.paused,true);
    await evaluate('const nextAudio=document.querySelector("[name=watchAudio]");nextAudio.value="en";nextAudio.dispatchEvent(new Event("change",{bubbles:true}))');
    await until(()=>evaluate('document.querySelector("#player").currentSrc.includes("/playback/")&&document.querySelector("#player").readyState>=1'),'Second alternate media unavailable');
    await evaluate('document.querySelector("#player").currentTime=3');
    await until(()=>evaluate('!document.querySelector("#player").seeking'),'Second seek incomplete');
    await evaluate('document.querySelector("#player").play()');
    await until(()=>evaluate('!document.querySelector("#player").paused'),'Playback did not start');
    await evaluate('document.querySelector("#player").dispatchEvent(new Event("error"))');
    await until(()=>evaluate('document.querySelector("#player").currentSrc.includes("/media/")&&document.querySelector("#player").readyState>=2&&!document.querySelector("#player").paused'),'Playing fallback did not resume');
    const playing=await evaluate('document.querySelector("#player").currentTime');
    assert.ok(playing>=2.9&&playing<4,`Playing fallback lost position: ${playing}`);
    console.log('Chromium verified real WebM playback and alternate-audio fallback preserving current position and paused/playing state.');
  }finally{
    socket?.close();if(browser&&browser.exitCode===null){const done=new Promise(resolve=>browser.once('exit',resolve));browser.kill();await Promise.race([done,delay(2000)]);}
    if(server){server.closeAllConnections();server.close();}
    const absolute=path.resolve(temp),parent=path.resolve(os.tmpdir());
    if(absolute.startsWith(parent+path.sep)&&path.basename(absolute).startsWith('gridtube-playback-')){try{fs.rmSync(absolute,{recursive:true,force:true,maxRetries:2,retryDelay:250});}catch{}}
  }
}
run().catch(error=>{console.error(error);process.exitCode=1;});
