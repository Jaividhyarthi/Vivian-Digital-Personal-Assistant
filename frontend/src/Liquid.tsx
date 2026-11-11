import {useEffect,useRef} from 'react';
// Low resolution, 30fps fragment shader. Pauses when hidden; static CSS fallback.
export function Liquid({personal,active}:{personal:boolean;active:boolean}){
 const ref=useRef<HTMLCanvasElement>(null);const state=useRef({personal,active});state.current={personal,active};
 useEffect(()=>{const canvas=ref.current!;const gl=canvas.getContext('webgl',{alpha:true,antialias:false,powerPreference:'low-power'});const reduced=matchMedia('(prefers-reduced-motion: reduce)');if(!gl||reduced.matches)return;
 const compile=(type:number,source:string)=>{const s=gl.createShader(type)!;gl.shaderSource(s,source);gl.compileShader(s);return s};
 const vs=compile(gl.VERTEX_SHADER,'attribute vec2 p; void main(){gl_Position=vec4(p,0.,1.);}');
 const fs=compile(gl.FRAGMENT_SHADER,`precision mediump float;uniform vec2 r;uniform vec2 mouse;uniform float t;uniform float personal;uniform float active;void main(){vec2 uv=gl_FragCoord.xy/r;vec2 p=uv*3.;float f=sin(p.x*1.5+t*.13+sin(p.y*1.9-t*.11))*cos(p.y*1.8+t*.08);float wave=sin(p.y*2.+f+mouse.x*.15+t*.06);vec3 a=mix(vec3(.81,.81,.91),vec3(.92,.82,.79),personal);vec3 b=vec3(.96,.96,.98);vec3 col=mix(a,b,.5+.5*wave);float ribbon=pow(.5+.5*sin(p.x*2.+p.y+f*1.2),12.);col+=ribbon*.09;col-=length(uv-mouse)*active*.025;gl_FragColor=vec4(col,1.);}`);
 const program=gl.createProgram()!;gl.attachShader(program,vs);gl.attachShader(program,fs);gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))return;gl.useProgram(program);
 const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);const p=gl.getAttribLocation(program,'p');gl.enableVertexAttribArray(p);gl.vertexAttribPointer(p,2,gl.FLOAT,false,0,0);
 const loc=Object.fromEntries(['r','t','mouse','personal','active'].map(k=>[k,gl.getUniformLocation(program,k)]));let pointer=[.5,.5],frame=0,last=0;
 const move=(e:PointerEvent)=>{pointer=[e.clientX/innerWidth,1-e.clientY/innerHeight]};window.addEventListener('pointermove',move,{passive:true});
 const resize=()=>{canvas.width=Math.min(1000,innerWidth);canvas.height=Math.min(700,innerHeight);gl.viewport(0,0,canvas.width,canvas.height)};resize();window.addEventListener('resize',resize);
 const draw=(ms:number)=>{frame=requestAnimationFrame(draw);if(document.hidden||ms-last<33||reduced.matches)return;last=ms;gl.uniform2f(loc.r,canvas.width,canvas.height);gl.uniform2f(loc.mouse,...pointer as [number,number]);gl.uniform1f(loc.t,ms/1000);gl.uniform1f(loc.personal,state.current.personal?1:0);gl.uniform1f(loc.active,state.current.active?1:0);gl.drawArrays(gl.TRIANGLES,0,6)};frame=requestAnimationFrame(draw);
 return()=>{cancelAnimationFrame(frame);window.removeEventListener('pointermove',move);window.removeEventListener('resize',resize);gl.deleteBuffer(buffer);gl.deleteProgram(program);gl.deleteShader(vs);gl.deleteShader(fs)};
 },[]);return <canvas className="liquid" ref={ref} aria-hidden="true"/>;
}
