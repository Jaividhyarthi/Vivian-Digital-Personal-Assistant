import {useEffect, useRef, useState} from 'react';
export type CharacterState = 'idle'|'greeting'|'listening'|'thinking'|'speaking'|'walking'|'gesturing'|'transitioning'|'error'|'offline';
// A generation invalidates every pending provider request and media callback.
export class PlaybackController {
 private generation=0;
 private audio: HTMLAudioElement|null=null;
 private url='';
 private abort:AbortController|null=null;
 constructor(private update:(state:CharacterState)=>void){}
 stop(){
  this.generation++; this.abort?.abort(); this.abort=null;
  if(this.audio){this.audio.onplaying=this.audio.onwaiting=this.audio.onpause=this.audio.onended=this.audio.onerror=null;this.audio.pause();this.audio.removeAttribute('src');this.audio.load();this.audio=null;}
  if(this.url)URL.revokeObjectURL(this.url);this.url='';this.update('idle');
 }
 async play(text:string){
  this.stop();const turn=this.generation;this.abort=new AbortController();this.update('thinking');
  try{
   const response=await fetch('/api/voice/speak',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text}),signal:this.abort.signal});
   if(!response.ok)throw Error('Voice playback is unavailable. Continue with text.');
   const blob=await response.blob();if(turn!==this.generation)return;
   this.url=URL.createObjectURL(blob);const media=new Audio(this.url);this.audio=media;
   const change=(state:CharacterState)=>{if(turn===this.generation)this.update(state)};
   media.onplaying=()=>change('speaking');media.onwaiting=()=>change('thinking');media.onpause=()=>change('idle');
   media.onended=()=>{if(turn===this.generation)this.stop()};
   media.onerror=()=>{if(turn===this.generation){this.stop();this.update('error')}};
   await media.play();
  }catch(error){if(turn!==this.generation)return;this.stop();if((error as Error).name!=='AbortError'){this.update('error');throw error}}
 }
}
export function useVoiceState(){
 const[state,setState]=useState<CharacterState>('idle');
 const controller=useRef<PlaybackController|null>(null);
 if(!controller.current)controller.current=new PlaybackController(setState);
 useEffect(()=>()=>controller.current?.stop(),[]);
 return {state,setState,playback:controller.current};
}
