import {afterEach,describe,it,expect,vi} from 'vitest';
import {PlaybackController} from './VoiceStateController';
class Media {
 onplaying:any;onwaiting:any;onpause:any;onended:any;onerror:any;
 play=vi.fn(async()=>{});pause=vi.fn();load=vi.fn();removeAttribute=vi.fn();
}
afterEach(()=>vi.unstubAllGlobals());
function setup(){const media=new Media();vi.stubGlobal('Audio',class{constructor(){return media}});vi.stubGlobal('URL',{createObjectURL:vi.fn(()=> 'blob:test'),revokeObjectURL:vi.fn()});const state=vi.fn();return{media,state,controller:new PlaybackController(state)}}
describe('real playback lifecycle',()=>{
 it('only speaks on playing; buffering and interruption clear speaking',async()=>{const{media,state,controller}=setup();vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,blob:async()=>new Blob()})));await controller.play('hello');expect(state).not.toHaveBeenCalledWith('speaking');media.onplaying();expect(state).toHaveBeenLastCalledWith('speaking');media.onwaiting();expect(state).toHaveBeenLastCalledWith('thinking');controller.stop();expect(state).toHaveBeenLastCalledWith('idle');expect(media.pause).toHaveBeenCalled();expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:test')});
 it('never plays a response arriving after stop',async()=>{const{media,controller}=setup();let resolve!:(v:any)=>void;vi.stubGlobal('fetch',vi.fn(()=>new Promise(r=>resolve=r)));const pending=controller.play('hello');controller.stop();resolve({ok:true,blob:async()=>new Blob()});await pending;expect(media.play).not.toHaveBeenCalled();expect(URL.createObjectURL).not.toHaveBeenCalled()});
 it('stale media callbacks cannot reactivate speech',async()=>{const{media,state,controller}=setup();vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,blob:async()=>new Blob()})));await controller.play('hello');const callback=media.onplaying;controller.stop();callback();expect(state).toHaveBeenLastCalledWith('idle')});
 it('reports a provider failure without simulated playback',async()=>{const{media,state,controller}=setup();vi.stubGlobal('fetch',vi.fn(async()=>({ok:false})));await expect(controller.play('hello')).rejects.toThrow('unavailable');expect(state).toHaveBeenLastCalledWith('error');expect(media.play).not.toHaveBeenCalled()});
});
