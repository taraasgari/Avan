(() => {
  "use strict";
  const node = document.getElementById("owner-analytics-data");
  if (!node) return;
  let data;
  try { data = JSON.parse(node.textContent); } catch { return; }

  const css = getComputedStyle(document.documentElement);
  const textColor = css.getPropertyValue("--avan-text").trim() || "#111";
  const lineColor = css.getPropertyValue("--avan-line").trim() || "#ddd";
  const red = "#d50000";

  function draw(canvas, values, accent) {
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.max(1, Math.floor(rect.width * dpr));
    canvas.height = Math.max(1, Math.floor(rect.height * dpr));
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    const w = rect.width, h = rect.height, pad = 26;
    const max = Math.max(1, ...values);
    ctx.clearRect(0,0,w,h);
    ctx.strokeStyle = lineColor; ctx.lineWidth = 1;
    for (let i=0;i<4;i++) { const y=pad+(h-pad*2)*(i/3); ctx.beginPath();ctx.moveTo(pad,y);ctx.lineTo(w-pad,y);ctx.stroke(); }
    const step = (w-pad*2) / Math.max(1, values.length-1);
    ctx.strokeStyle = accent; ctx.lineWidth = 2.4; ctx.beginPath();
    values.forEach((v,i)=>{ const x=pad+i*step; const y=h-pad-(v/max)*(h-pad*2); if(i===0)ctx.moveTo(x,y); else ctx.lineTo(x,y); });
    ctx.stroke();
    ctx.fillStyle = textColor; ctx.font = "10px Arial"; ctx.textAlign = "center";
    const daily = data.daily || [];
    [0,7,14,21,29].forEach(i=>{if(daily[i]) ctx.fillText(daily[i].label,pad+i*step,h-6);});
  }

  function bars(targetId, rows) {
    const target = document.getElementById(targetId); if(!target) return;
    const max = Math.max(1, ...rows.map(r=>Number(r.count)||0));
    target.innerHTML = rows.map(r=>`<div class="s9-bar-row"><span>${String(r.status).replaceAll('_',' ').toUpperCase()}</span><div class="s9-bar-track"><i style="width:${Math.max(2,(Number(r.count)||0)/max*100)}%"></i></div><b>${Number(r.count)||0}</b></div>`).join("") || "<div class='owner-empty'>NO DATA.</div>";
  }

  function render(){
    const daily = data.daily || [];
    draw(document.getElementById("revenueChart"), daily.map(x=>Number(x.revenue)||0), red);
    draw(document.getElementById("ordersChart"), daily.map(x=>Number(x.orders)||0), textColor);
    bars("statusBars", [...(data.order_status||[]), ...(data.cart_status||[]).map(x=>({status:`cart ${x.status}`,count:x.count}))]);
    bars("shippingBars", data.shipping_status||[]);
  }
  render();
  let timer; window.addEventListener("resize",()=>{clearTimeout(timer);timer=setTimeout(render,120);});
})();
