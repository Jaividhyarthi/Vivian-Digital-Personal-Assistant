import {useState} from 'react';
import {AnimatePresence,motion,useReducedMotion} from 'motion/react';
import {ChevronDown,ChevronUp, X} from 'lucide-react';
import type {CharacterState} from './VoiceStateController';
export const panelSpring={type:'spring' as const,stiffness:180,damping:26,mass:1};
export function VivianStage({space,state,hidden,onHide,effects}:{space:'personal'|'professional';state:CharacterState;hidden:boolean;onHide:()=>void;effects:boolean}){
 const[compact,setCompact]=useState(false);const reduced=useReducedMotion();
 if(hidden)return null;
 const labels:Record<CharacterState,string>={idle:'Here when you need me',greeting:'Welcome back',listening:'Microphone active',thinking:'Processing your request',speaking:'Voice is playing',walking:'Walking',gesturing:'Gesturing',transitioning:'Changing workspace',error:'Something needs attention',offline:'Connection unavailable'};
 return <motion.aside className={'vivian-stage glass '+space+(compact?' compact':'')} data-state={state} data-effects={effects&&!reduced} aria-label="Vivian character stage" initial={reduced?false:{opacity:0}} animate={{opacity:1}} transition={panelSpring}>
  <div className="stage-toolbar"><span className="eyebrow">BY YOUR SIDE</span><div><button className="icon" aria-label={compact?'Expand character':'Minimize character'} onClick={()=>setCompact(!compact)}>{compact?<ChevronUp size={16}/>:<ChevronDown size={16}/>}</button><button className="icon" aria-label="Hide character" onClick={onHide}><X size={16}/></button></div></div>
  {!compact&&<div className="character-portrait"><div className="stage-halo"/><AnimatePresence><motion.div key={space} className={"approved-portrait "+space} role="img" aria-label={'Approved Vivian '+space+' portrait; static artwork'} initial={reduced?false:{opacity:0}} animate={{opacity:1}} exit={{opacity:0}} transition={{duration:reduced?0:.6}}/></AnimatePresence></div>}
  <div className="stage-caption"><h3>Vivian <span>✧</span></h3><p role="status">{labels[state]}</p>{!compact&&<small>Approved portrait · character animation pending</small>}</div>
 </motion.aside>
}
