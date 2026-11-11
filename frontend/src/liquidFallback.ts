/** Low-cost animated caustic ribbons for environments without WebGL. */
export function startLiquidFallback(canvas:HTMLCanvasElement, state:{current:{dark:boolean;personal:boolean;active:boolean}},enabled:boolean){
 const ctx=canvas.getContext('2d');if(!ctx)return()=>{};
 canvas.dataset.renderer='canvas2d';let frame=0,last=0,time=0,night=state.current.dark?1:0;
 const reduced=matchMedia('(prefers-reduced-motion: reduce)');
 const resize=()=>{const scale=Math.min(.75,1100/innerWidth);canvas.width=Math.round(innerWidth*scale);canvas.height=Math.round(innerHeight*scale)};resize();addEventListener('resize',resize);
 const color=(day:number[],dark:number[],alpha=1)=>`rgba(${day.map((v,i)=>Math.round(v+(dark[i]-v)*night)).join(',')},${alpha})`;
 const draw=(ms:number)=>{frame=requestAnimationFrame(draw);if(document.hidden){last=ms;return}if(ms-last<40)return;const dt=Math.min((ms-last)/1000,.06);last=ms;if(enabled&&!reduced.matches)time+=dt;night+=(Number(state.current.dark)-night)*.08;
  const w=canvas.width,h=canvas.height,t=time*.16;ctx.clearRect(0,0,w,h);
  const base=ctx.createLinearGradient(0,0,w,h);base.addColorStop(0,color([145,168,180],[7,18,49]));base.addColorStop(.5,color([203,218,224],[24,49,106]));base.addColorStop(1,color([119,148,162],[13,19,59]));ctx.fillStyle=base;ctx.fillRect(0,0,w,h);
  for(let j=0;j<4;j++){
   const x=w*(.2+j*.24+Math.sin(t*.6+j)*.16),y=h*(.3+Math.cos(t*.7+j*2)*.3);
   const glow=ctx.createRadialGradient(x,y,0,x,y,w*.5);glow.addColorStop(0,color([242,250,252],j%2?[106,81,187]:[37,151,241],.38));glow.addColorStop(1,'transparent');ctx.fillStyle=glow;ctx.fillRect(0,0,w,h);
  }
  // Flowing broad translucent ribbons with caustic highlights and a darker underside.
  for(let j=-1;j<5;j++){
   const phase=t+j*1.1;const x=w*(j*.29+.12)+Math.sin(phase)*w*.06;
   ctx.save();ctx.translate(x,h*.48);ctx.rotate(-.45+Math.sin(phase*.47)*.22);
   ctx.beginPath();ctx.moveTo(-w*.21,-h*.85);ctx.bezierCurveTo(w*.52,-h*.35,-w*.42,h*.25,w*.23,h*.85);
   ctx.lineWidth=w*.13;ctx.strokeStyle=color([221,240,246],[101,153,236],.055);ctx.stroke();
   ctx.lineWidth=w*.035;ctx.strokeStyle=color([219,241,248],[83,155,249],.09);ctx.shadowBlur=22;ctx.shadowColor=color([235,250,255],[54,150,255],.6);ctx.stroke();
   ctx.lineWidth=1.2;ctx.strokeStyle=color([247,255,255],[168,220,255],.32);ctx.stroke();
   ctx.translate(w*.06,0);ctx.lineWidth=w*.035;ctx.strokeStyle=color([62,99,120],[1,8,31],.10);ctx.shadowBlur=20;ctx.shadowColor=ctx.strokeStyle;ctx.stroke();ctx.restore();
  }
 };
 frame=requestAnimationFrame(draw);return()=>{cancelAnimationFrame(frame);removeEventListener('resize',resize)};
}
