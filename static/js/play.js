(() => {
  const root = document.querySelector('[data-avan-game]');
  if (!root) return;

  const canvas = document.getElementById('avanGameCanvas');
  const ctx = canvas.getContext('2d');
  const type = root.dataset.gameType;
  const scoreEl = root.querySelector('[data-game-score]');
  const timeEl = root.querySelector('[data-game-time]');
  const pressureEl = root.querySelector('[data-game-pressure]');
  const bestEl = root.querySelector('[data-best-score]');
  const startOverlay = root.querySelector('[data-game-start-overlay]');
  const resultBox = root.querySelector('[data-game-result]');
  const resultScore = root.querySelector('[data-result-score]');
  const resultCopy = root.querySelector('[data-result-copy]');
  const resultMedal = root.querySelector('[data-result-medal]');
  const soundButton = root.querySelector('[data-game-sound]');
  const controls = new Set();

  const W = canvas.width;
  const H = canvas.height;
  let running = false;
  let runToken = '';
  let score = 0;
  let startedAt = 0;
  let lastFrame = 0;
  let raf = 0;
  let pressure = 1;
  let game = {};
  let soundEnabled = localStorage.getItem('avan_play_sound') !== 'off';
  let audioCtx = null;

  function csrf() {
    const input = document.querySelector('#avan-csrf input[name="csrfmiddlewaretoken"]') || document.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : '';
  }
  function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }
  function rand(min, max) { return min + Math.random() * (max - min); }
  function nowSeconds() { return (performance.now() - startedAt) / 1000; }
  function setScore(v) { score = Math.max(0, Math.floor(v)); scoreEl.textContent = score.toLocaleString(); }
  function addScore(v) { setScore(score + v); }
  function setPressure(v) { pressure = Math.max(1, Math.floor(v)); pressureEl.textContent = String(pressure).padStart(2, '0'); }

  function ensureAudio() {
    if (!soundEnabled) return null;
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === 'suspended') audioCtx.resume();
    return audioCtx;
  }
  function tone(freq = 440, duration = .06, gain = .035, typeName = 'sine', slide = 0) {
    const ac = ensureAudio(); if (!ac) return;
    const o = ac.createOscillator(), g = ac.createGain();
    o.type = typeName; o.frequency.setValueAtTime(freq, ac.currentTime);
    if (slide) o.frequency.exponentialRampToValueAtTime(Math.max(40, freq + slide), ac.currentTime + duration);
    g.gain.setValueAtTime(gain, ac.currentTime); g.gain.exponentialRampToValueAtTime(.0001, ac.currentTime + duration);
    o.connect(g); g.connect(ac.destination); o.start(); o.stop(ac.currentTime + duration);
  }
  const sfx = {
    click: () => tone(520, .035, .025, 'square', 60),
    good: () => { tone(640, .055, .028, 'triangle', 300); setTimeout(() => tone(920, .05, .02, 'triangle', 180), 45); },
    bad: () => tone(150, .11, .05, 'sawtooth', -60),
    start: () => { tone(260, .07, .03, 'square', 180); setTimeout(() => tone(520, .08, .03, 'square', 260), 80); },
    medal: () => { [520, 660, 880].forEach((f,i) => setTimeout(() => tone(f,.12,.03,'triangle',120), i*90)); },
  };
  function syncSoundButton() {
    if (!soundButton) return;
    soundButton.textContent = soundEnabled ? 'SOUND ON' : 'SOUND OFF';
    soundButton.setAttribute('aria-pressed', soundEnabled ? 'true' : 'false');
  }
  if (soundButton) soundButton.addEventListener('click', () => {
    soundEnabled = !soundEnabled; localStorage.setItem('avan_play_sound', soundEnabled ? 'on' : 'off'); syncSoundButton(); if (soundEnabled) sfx.click();
  });
  syncSoundButton();

  function bg() {
    const grad = ctx.createLinearGradient(0, 0, W, H);
    grad.addColorStop(0, '#090909'); grad.addColorStop(.55, '#111'); grad.addColorStop(1, '#050505');
    ctx.fillStyle = grad; ctx.fillRect(0,0,W,H);
    ctx.strokeStyle = 'rgba(255,255,255,.035)'; ctx.lineWidth = 1;
    for (let x=0;x<W;x+=60){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();}
    for (let y=0;y<H;y+=60){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}
  }
  function text(t, x, y, size=18, color='#fff', align='left', weight='700') {
    ctx.fillStyle=color; ctx.font=`${weight} ${size}px Arial, sans-serif`; ctx.textAlign=align; ctx.textBaseline='middle'; ctx.fillText(t,x,y);
  }

  async function startRun() {
    if (running) return;
    const res = await fetch(root.dataset.startUrl, {method:'POST', headers:{'X-CSRFToken':csrf(),'X-Requested-With':'XMLHttpRequest'}});
    const contentType = res.headers.get('content-type') || '';
    if (!res.ok || !contentType.includes('application/json')) { window.location.href = '/account/login/?next=' + encodeURIComponent(location.pathname); return; }
    const data = await res.json(); runToken = data.token;
    setScore(0); setPressure(1); startedAt = performance.now(); lastFrame = startedAt; running = true;
    resultBox.hidden = true; startOverlay.hidden = true; sfx.start(); initGame(); cancelAnimationFrame(raf); raf=requestAnimationFrame(loop);
  }

  async function finishRun(reason='complete') {
    if (!running) return;
    running = false; cancelAnimationFrame(raf);
    let data = {tier:'none', reward_unlocked:false};
    try {
      const res = await fetch(root.dataset.submitUrl, {method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':csrf(),'X-Requested-With':'XMLHttpRequest'}, body:JSON.stringify({score, token:runToken, reason})});
      if (res.status === 302 || res.status === 401 || res.status === 403) { window.location.href='/account/login/?next='+encodeURIComponent(location.pathname); return; }
      data = await res.json();
    } catch (e) { data={ok:false,tier:'none'}; }
    resultScore.textContent = score.toLocaleString();
    const tier=(data.tier||'none').toUpperCase();
    resultMedal.textContent = tier==='NONE' ? 'NO MEDAL' : `${tier} MEDAL`;
    resultCopy.textContent = data.ok ? (data.reward_unlocked ? 'A private reward was added to your AVAN account.' : 'Run saved. Push the score higher next time.') : 'Run finished, but the score could not be saved.';
    resultBox.hidden=false;
    if (tier!=='NONE') sfx.medal(); else sfx.bad();
    if (bestEl && (!Number(bestEl.textContent.replace(/,/g,'')) || score > Number(bestEl.textContent.replace(/,/g,'')))) bestEl.textContent=score.toLocaleString();
  }

  function loop(ts) {
    if (!running) return;
    const dt = Math.min(.034, (ts-lastFrame)/1000 || .016); lastFrame=ts;
    const elapsed = nowSeconds(); timeEl.textContent = elapsed.toFixed(1);
    updateGame(dt, elapsed); drawGame(elapsed);
    if (running) raf=requestAnimationFrame(loop);
  }

  // ---------- NEEDLE GRID ----------
  function initRunner() {
    game={needle:{x:180,y:H/2,targetY:H/2,r:11,integrity:3,inv:0},gates:[],spawn:0,combo:0};
  }
  function updateRunner(dt, elapsed) {
    const n=game.needle; n.inv=Math.max(0,n.inv-dt);
    const level=1+Math.floor(elapsed/8); setPressure(level);
    const move=390+level*26;
    if (controls.has('up')) n.targetY-=move*dt;
    if (controls.has('down')) n.targetY+=move*dt;
    n.targetY=clamp(n.targetY,35,H-35); n.y+=(n.targetY-n.y)*Math.min(1,dt*12);
    game.spawn-=dt;
    const speed=280+level*42;
    if (game.spawn<=0){
      const half=clamp(105-level*6,38,105), center=rand(half+35,H-half-35);
      game.gates.push({x:W+40,w:28,center,half,scored:false,hit:false});
      game.spawn=clamp(1.05-level*.045,.48,1.05);
    }
    for (const g of game.gates){
      g.x-=speed*dt;
      if (!g.scored && g.x+g.w<n.x-n.r){g.scored=true;game.combo=Math.min(12,game.combo+1);addScore(420*game.combo+level*90);sfx.good();}
      const overlap=n.x+n.r>g.x && n.x-n.r<g.x+g.w;
      const safe=n.y-n.r>g.center-g.half && n.y+n.r<g.center+g.half;
      if(overlap&&!safe&&!g.hit&&n.inv<=0){g.hit=true;n.integrity--;n.inv=.75;game.combo=0;sfx.bad();if(n.integrity<=0){finishRun('integrity');return;}}
    }
    game.gates=game.gates.filter(g=>g.x>-80);
    if(elapsed>=70) finishRun('time');
  }
  function drawRunner() {
    bg(); const n=game.needle;
    for(const g of game.gates){ctx.fillStyle='rgba(213,0,0,.86)';ctx.fillRect(g.x,0,g.w,g.center-g.half);ctx.fillRect(g.x,g.center+g.half,g.w,H-(g.center+g.half));ctx.fillStyle='rgba(255,255,255,.18)';ctx.fillRect(g.x-3,g.center-g.half-3,g.w+6,3);ctx.fillRect(g.x-3,g.center+g.half,g.w+6,3);}
    ctx.save();ctx.translate(n.x,n.y);ctx.fillStyle=n.inv>0&&Math.floor(n.inv*12)%2?'rgba(255,255,255,.2)':'#fff';ctx.beginPath();ctx.moveTo(-34,0);ctx.lineTo(18,-8);ctx.lineTo(36,0);ctx.lineTo(18,8);ctx.closePath();ctx.fill();ctx.fillStyle='#d50000';ctx.beginPath();ctx.arc(-22,0,5,0,Math.PI*2);ctx.fill();ctx.restore();
    text(`INTEGRITY ${'■'.repeat(n.integrity)}${'□'.repeat(3-n.integrity)}`,30,32,16,n.integrity===1?'#ff4444':'#fff'); text(`COMBO ×${game.combo}`,W-30,32,16,'#fff','right');
  }

  // ---------- PATTERN DROP (TETRIS-LIKE) ----------
  const SHAPES=[[[1,1,1,1]],[[1,1],[1,1]],[[0,1,0],[1,1,1]],[[1,0],[1,0],[1,1]],[[0,1],[0,1],[1,1]],[[1,1,0],[0,1,1]],[[0,1,1],[1,1,0]]];
  function rotateShape(a){return a[0].map((_,i)=>a.map(r=>r[i]).reverse());}
  function initCatch(){game={cols:10,rows:18,board:Array.from({length:18},()=>Array(10).fill(0)),piece:null,drop:0,combo:0,lines:0,ended:false};spawnPiece();}
  function spawnPiece(){const shape=SHAPES[Math.floor(Math.random()*SHAPES.length)].map(r=>r.slice());game.piece={shape,x:Math.floor((game.cols-shape[0].length)/2),y:-1,color:1+Math.floor(Math.random()*4)};if(collides(game.piece,0,1)){finishRun('board-lock');}}
  function collides(p,dx=0,dy=0,shape=p.shape){for(let y=0;y<shape.length;y++)for(let x=0;x<shape[y].length;x++)if(shape[y][x]){const bx=p.x+x+dx,by=p.y+y+dy;if(bx<0||bx>=game.cols||by>=game.rows||(by>=0&&game.board[by][bx]))return true;}return false;}
  function lockPiece(){const p=game.piece;for(let y=0;y<p.shape.length;y++)for(let x=0;x<p.shape[y].length;x++)if(p.shape[y][x]){const by=p.y+y,bx=p.x+x;if(by<0){finishRun('board-lock');return;}game.board[by][bx]=p.color;}let cleared=0;game.board=game.board.filter(r=>{if(r.every(Boolean)){cleared++;return false;}return true;});while(game.board.length<game.rows)game.board.unshift(Array(game.cols).fill(0));if(cleared){game.combo++;game.lines+=cleared;addScore(cleared*1400*game.combo);sfx.good();}else game.combo=0;addScore(180);spawnPiece();}
  function updateCatch(dt,elapsed){const lvl=1+Math.floor(elapsed/10)+Math.floor(game.lines/4);setPressure(lvl);game.drop-=dt;if(game.drop<=0){if(!collides(game.piece,0,1))game.piece.y++;else lockPiece();game.drop=clamp(.58-lvl*.035,.105,.58);}if(controls.has('down'))game.drop=Math.min(game.drop,.035);if(elapsed>=90)finishRun('time');}
  function drawCatch(){bg();const cell=30,bw=cell*game.cols,bh=cell*game.rows,ox=(W-bw)/2,oy=(H-bh)/2;ctx.fillStyle='rgba(255,255,255,.035)';ctx.fillRect(ox,oy,bw,bh);for(let y=0;y<game.rows;y++)for(let x=0;x<game.cols;x++){ctx.strokeStyle='rgba(255,255,255,.05)';ctx.strokeRect(ox+x*cell,oy+y*cell,cell,cell);if(game.board[y][x])drawBlock(ox+x*cell,oy+y*cell,cell,game.board[y][x]);}const p=game.piece;if(p)for(let y=0;y<p.shape.length;y++)for(let x=0;x<p.shape[y].length;x++)if(p.shape[y][x]&&p.y+y>=0)drawBlock(ox+(p.x+x)*cell,oy+(p.y+y)*cell,cell,p.color);text(`LINES ${game.lines}`,ox+bw+45,oy+30,18,'#fff');text(`COMBO ×${game.combo}`,ox+bw+45,oy+62,18,'#fff');}
  function drawBlock(x,y,s,c){const colors=['','#d50000','#fff','#8d8d8d','#4b1010'];ctx.fillStyle=colors[c]||'#fff';ctx.fillRect(x+2,y+2,s-4,s-4);ctx.strokeStyle='rgba(0,0,0,.35)';ctx.strokeRect(x+6,y+6,s-12,s-12);}
  function catchMove(dir){if(!running||type!=='catch')return;const p=game.piece;if(dir==='left'&&!collides(p,-1,0)){p.x--;sfx.click();}if(dir==='right'&&!collides(p,1,0)){p.x++;sfx.click();}if(dir==='rotate'){const r=rotateShape(p.shape);if(!collides(p,0,0,r)){p.shape=r;sfx.click();}}if(dir==='hard'){let d=0;while(!collides(p,0,1)){p.y++;d++;}addScore(d*35);lockPiece();sfx.good();}}

  // ---------- SIGNAL FORGE ----------
  function initMemory(){game={pads:6,sequence:[],input:[],level:0,strikes:0,showing:false,nextAt:performance.now()+500,flash:-1,flashUntil:0,queue:[],waiting:false};nextSignalRound();}
  function nextSignalRound(){game.level++;setPressure(game.level);game.input=[];game.sequence.push(Math.floor(Math.random()*game.pads));game.queue=[...game.sequence];game.showing=true;game.waiting=false;game.nextAt=performance.now()+500;}
  function updateMemory(dt,elapsed){const t=performance.now();if(game.showing&&t>=game.nextAt){if(game.flash>=0&&t<game.flashUntil)return;if(game.queue.length){game.flash=game.queue.shift();const speed=clamp(520-game.level*24,135,520);game.flashUntil=t+speed*.55;game.nextAt=t+speed;sfx.click();}else{game.flash=-1;game.showing=false;game.waiting=true;}}if(game.flash>=0&&t>game.flashUntil)game.flash=-1;if(elapsed>=90)finishRun('time');}
  function memoryInput(i){if(!running||type!=='memory'||!game.waiting)return;const idx=game.input.length;if(i===game.sequence[idx]){game.input.push(i);addScore(260*game.level);sfx.good();if(game.input.length===game.sequence.length){addScore(850*game.level);game.waiting=false;setTimeout(()=>{if(running)nextSignalRound();},350);}}else{game.strikes++;game.input=[];sfx.bad();if(game.strikes>=3){finishRun('strikes');return;}game.showing=true;game.queue=[...game.sequence];game.nextAt=performance.now()+550;}}
  function drawMemory(){bg();const cols=3,rows=2,gap=22,pw=220,ph=160,ox=(W-(cols*pw+(cols-1)*gap))/2,oy=(H-(rows*ph+(rows-1)*gap))/2;for(let i=0;i<game.pads;i++){const x=ox+(i%3)*(pw+gap),y=oy+Math.floor(i/3)*(ph+gap),on=game.flash===i;ctx.fillStyle=on?'#d50000':'rgba(255,255,255,.055)';ctx.strokeStyle=on?'#fff':'rgba(255,255,255,.16)';ctx.lineWidth=2;ctx.fillRect(x,y,pw,ph);ctx.strokeRect(x,y,pw,ph);text(String(i+1).padStart(2,'0'),x+pw/2,y+ph/2,48,on?'#fff':'rgba(255,255,255,.5)','center','800');}text(`LEVEL ${game.level}`,40,38,18,'#fff');text(`STRIKES ${game.strikes}/3`,W-40,38,18,game.strikes>=2?'#ff4444':'#fff','right');if(game.showing)text('READ',W/2,H-34,16,'#d50000','center');else text('REPEAT',W/2,H-34,16,'#fff','center');}
  function memoryPadAt(px,py){const cols=3,gap=22,pw=220,ph=160,ox=(W-(cols*pw+(cols-1)*gap))/2,oy=(H-(2*ph+gap))/2;for(let i=0;i<6;i++){const x=ox+(i%3)*(pw+gap),y=oy+Math.floor(i/3)*(ph+gap);if(px>=x&&px<=x+pw&&py>=y&&py<=y+ph)return i;}return -1;}

  // ---------- TAG STRIKE ----------
  function initColor(){game={target:null,decoys:[],combo:0,misses:0,spawnAt:0,life:1000};spawnTag();}
  function spawnTag(){const elapsed=nowSeconds(),lvl=1+Math.floor(elapsed/7);setPressure(lvl);game.life=clamp(1050-lvl*65,220,1050);const margin=90;game.target={x:rand(margin,W-margin),y:rand(110,H-90),r:34,born:performance.now()};game.decoys=[];const n=clamp(2+Math.floor(lvl/2),2,9);for(let i=0;i<n;i++)game.decoys.push({x:rand(margin,W-margin),y:rand(110,H-90),r:rand(25,40)});}
  function updateColor(dt,elapsed){if(game.target&&performance.now()-game.target.born>game.life){game.misses++;game.combo=0;sfx.bad();if(game.misses>=5){finishRun('misses');return;}spawnTag();}if(elapsed>=70)finishRun('time');}
  function drawColor(){bg();for(const d of game.decoys){ctx.strokeStyle='rgba(255,255,255,.14)';ctx.lineWidth=2;ctx.beginPath();ctx.arc(d.x,d.y,d.r,0,Math.PI*2);ctx.stroke();text('AV',d.x,d.y,13,'rgba(255,255,255,.25)','center');}const t=game.target;if(t){const remain=clamp(1-(performance.now()-t.born)/game.life,0,1);ctx.strokeStyle='#d50000';ctx.lineWidth=6;ctx.beginPath();ctx.arc(t.x,t.y,t.r+10, -Math.PI/2,-Math.PI/2+Math.PI*2*remain);ctx.stroke();ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(t.x,t.y,t.r,0,Math.PI*2);ctx.fill();text('A',t.x,t.y,28,'#090909','center','900');ctx.fillStyle='#d50000';ctx.beginPath();ctx.arc(t.x+t.r*.65,t.y-t.r*.65,7,0,Math.PI*2);ctx.fill();}text(`MISSES ${game.misses}/5`,40,38,18,game.misses>=4?'#ff4444':'#fff');text(`COMBO ×${game.combo}`,W-40,38,18,'#fff','right');}
  function colorHit(px,py){if(!running||type!=='color'||!game.target)return;const t=game.target;if(Math.hypot(px-t.x,py-t.y)<=t.r+12){game.combo=Math.min(20,game.combo+1);addScore(520*game.combo+pressure*160);sfx.good();spawnTag();return;}for(const d of game.decoys){if(Math.hypot(px-d.x,py-d.y)<=d.r+8){game.misses++;game.combo=0;sfx.bad();if(game.misses>=5)finishRun('decoy');else spawnTag();return;}}}

  function initGame(){ if(type==='runner')initRunner(); else if(type==='catch')initCatch(); else if(type==='memory')initMemory(); else initColor(); }
  function updateGame(dt,e){ if(type==='runner')updateRunner(dt,e); else if(type==='catch')updateCatch(dt,e); else if(type==='memory')updateMemory(dt,e); else updateColor(dt,e); }
  function drawGame(){ if(type==='runner')drawRunner(); else if(type==='catch')drawCatch(); else if(type==='memory')drawMemory(); else drawColor(); }

  function localPoint(e){const r=canvas.getBoundingClientRect();return {x:(e.clientX-r.left)/r.width*W,y:(e.clientY-r.top)/r.height*H};}
  canvas.addEventListener('pointermove',e=>{if(!running)return;const p=localPoint(e);if(type==='runner')game.needle.targetY=p.y;});
  canvas.addEventListener('pointerdown',e=>{if(!running)return;const p=localPoint(e);if(type==='memory'){const i=memoryPadAt(p.x,p.y);if(i>=0)memoryInput(i);}if(type==='color')colorHit(p.x,p.y);});

  function keyName(e){const k=e.key.toLowerCase();if(k==='arrowup'||k==='w')return'up';if(k==='arrowdown'||k==='s')return'down';if(k==='arrowleft'||k==='a')return'left';if(k==='arrowright'||k==='d')return'right';if(k===' '||k==='spacebar')return'action';return k;}
  window.addEventListener('keydown',e=>{const k=keyName(e);if(['up','down','left','right','action'].includes(k))e.preventDefault();controls.add(k);if(!running)return;if(type==='catch'){if(k==='left')catchMove('left');if(k==='right')catchMove('right');if(k==='up'||k==='action')catchMove('rotate');if(k==='down')game.drop=0;if(k==='enter')catchMove('hard');}if(type==='memory'&&/^[1-6]$/.test(k))memoryInput(Number(k)-1);});
  window.addEventListener('keyup',e=>controls.delete(keyName(e)));

  root.querySelectorAll('[data-control]').forEach(btn=>{
    const c=btn.dataset.control;
    const down=e=>{e.preventDefault();controls.add(c);if(type==='catch'){if(c==='left')catchMove('left');if(c==='right')catchMove('right');if(c==='action')catchMove('rotate');}};
    const up=e=>{e.preventDefault();controls.delete(c);};
    btn.addEventListener('pointerdown',down);btn.addEventListener('pointerup',up);btn.addEventListener('pointercancel',up);
  });

  root.querySelector('[data-game-start]')?.addEventListener('click',startRun);
  root.querySelector('[data-game-restart]')?.addEventListener('click',()=>{if(running){running=false;cancelAnimationFrame(raf);}startRun();});
  root.querySelector('[data-game-play-again]')?.addEventListener('click',startRun);
  bg();text('AVAN PLAY',W/2,H/2-10,52,'rgba(255,255,255,.1)','center','900');
})();
