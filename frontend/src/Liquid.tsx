import {useEffect,useRef} from 'react';
import {startLiquidFallback} from './liquidFallback';
/** Domain-warped caustic field. Static CSS remains visible if WebGL fails. */
export function Liquid({personal,active,enabled=true,dark=false}:{personal:boolean;active:boolean;enabled?:boolean;dark?:boolean}){
 const ref=useRef<HTMLCanvasElement>(null),fallbackRef=useRef<HTMLCanvasElement>(null),state=useRef({personal,active,dark});state.current={personal,active,dark};
 useEffect(()=>{
  const canvas=ref.current!;const fallback=fallbackRef.current!;canvas.style.display='block';fallback.style.display='none';const useFallback=()=>{canvas.style.display='none';fallback.style.display='block';return startLiquidFallback(fallback,state,enabled)};const gl=canvas.getContext('webgl',{alpha:false,antialias:false,powerPreference:'low-power'});if(!gl)return useFallback();
  const shaders:WebGLShader[]=[];let program:WebGLProgram|null=null,buffer:WebGLBuffer|null=null,frame=0;
  const compile=(kind:number,source:string)=>{const shader=gl.createShader(kind)!;shaders.push(shader);gl.shaderSource(shader,source);gl.compileShader(shader);if(!gl.getShaderParameter(shader,gl.COMPILE_STATUS))throw Error('Liquid shader compilation failed');return shader};
  try{
   const vertex=compile(gl.VERTEX_SHADER,'attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}');
   const fragment=compile(gl.FRAGMENT_SHADER,`precision highp float;
   uniform vec2 resolution;uniform float time;uniform float night;uniform float personal;uniform float energy;
   float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
   float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1.,0.)),f.x),mix(hash(i+vec2(0.,1.)),hash(i+1.),f.x),f.y);}
   float fbm(vec2 p){return .55*noise(p)+.28*noise(p*2.03)+.14*noise(p*4.01);}
   float field(vec2 p,float t){vec2 q=vec2(fbm(p+vec2(t*.13,0.)),fbm(p+vec2(4.2,-t*.1)));return fbm(p+q*2.8+vec2(t*.07,-t*.04));}
   void main(){
    vec2 uv=gl_FragCoord.xy/resolution;vec2 p=(uv-.5)*vec2(resolution.x/resolution.y,1.)*3.;float t=time*.55;
    float f=field(p,t);float f2=field(p+vec2(2.8,4.),t);
    float ribbons=sin(p.x*1.65+p.y*2.4+f*7.+t*.22);
    float rim=pow(max(0.,1.-abs(ribbons)),9.);float sheen=pow(max(0.,1.-abs(ribbons-.17)),3.);
    float dx=field(p+vec2(.018,0.),t)-f;float dy=field(p+vec2(0.,.018),t)-f;
    vec3 normal=normalize(vec3(dx*30.,dy*30.,.6));float spec=pow(max(dot(normal,normalize(vec3(-.5,.65,1.))),0.),12.);
    vec3 deep=mix(vec3(.035,.065,.18),vec3(.055,.19,.42),f2);
    deep+=vec3(.07,.19,.52)*sheen+vec3(.22,.42,.8)*rim*.65;
    deep+=vec3(.20,.06,.34)*pow(f,2.)*2.3+vec3(.06,.24,.31)*spec*.4;
    vec3 silver=mix(vec3(.28,.43,.51),vec3(.73,.84,.88),smoothstep(.2,.8,f2));
    silver+=vec3(.16,.21,.23)*sheen+vec3(.23,.25,.26)*rim+spec*.07;
    vec3 col=mix(silver,deep,night);col+=personal*vec3(.025,0.,.025);
    col+=energy*vec3(.015,.035,.055)*sheen;
    float vignette=1.-.27*length((uv-.5)*vec2(1.,.8));col*=vignette;
    gl_FragColor=vec4(col,1.);
   }`);
   program=gl.createProgram()!;gl.attachShader(program,vertex);gl.attachShader(program,fragment);gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('Liquid shader link failed');gl.useProgram(program);
   buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);const pos=gl.getAttribLocation(program,'p');gl.enableVertexAttribArray(pos);gl.vertexAttribPointer(pos,2,gl.FLOAT,false,0,0);
   const locations=Object.fromEntries(['resolution','time','night','personal','energy'].map(k=>[k,gl.getUniformLocation(program!,k)]));
   let last=0,elapsed=0,night=state.current.dark?1:0,personalValue=state.current.personal?1:0,energy=0;
   const resize=()=>{const scale=Math.min(1,1200/innerWidth);canvas.width=Math.round(innerWidth*scale);canvas.height=Math.round(innerHeight*scale);gl.viewport(0,0,canvas.width,canvas.height)};
   resize();window.addEventListener('resize',resize);const reduced=matchMedia('(prefers-reduced-motion: reduce)');
   const draw=(ms:number)=>{frame=requestAnimationFrame(draw);if(document.hidden){last=ms;return}if(ms-last<33)return;const dt=Math.min((ms-last)/1000,.05);last=ms;if(enabled&&!reduced.matches)elapsed+=dt;
    night+=(Number(state.current.dark)-night)*.07;personalValue+=(Number(state.current.personal)-personalValue)*.05;energy+=(Number(state.current.active)-energy)*.05;
    gl.uniform2f(locations.resolution,canvas.width,canvas.height);gl.uniform1f(locations.time,elapsed);gl.uniform1f(locations.night,night);gl.uniform1f(locations.personal,personalValue);gl.uniform1f(locations.energy,energy);gl.drawArrays(gl.TRIANGLES,0,6);canvas.dataset.renderer='webgl';
   };frame=requestAnimationFrame(draw);
   return()=>{cancelAnimationFrame(frame);window.removeEventListener('resize',resize);gl.deleteBuffer(buffer);gl.deleteProgram(program);shaders.forEach(s=>gl.deleteShader(s))};
  }catch{canvas.dataset.renderer='fallback';gl.deleteBuffer(buffer);gl.deleteProgram(program);shaders.forEach(s=>gl.deleteShader(s));return useFallback();}
 },[enabled]);
 return <div className="liquid-environment" aria-hidden="true"><canvas className="liquid" ref={ref}/><canvas className="liquid" ref={fallbackRef}/><div className="environment-light"/></div>;
}
