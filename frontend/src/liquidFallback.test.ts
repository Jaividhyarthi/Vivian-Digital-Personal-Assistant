import {afterEach,describe,it,expect,vi} from 'vitest';
import {startLiquidFallback} from './liquidFallback';
afterEach(()=>vi.unstubAllGlobals());
function fixture(reduced=false){
 let next:FrameRequestCallback=()=>{};const gradient={addColorStop:vi.fn()};
 const ctx={clearRect:vi.fn(),createLinearGradient:()=>gradient,createRadialGradient:()=>gradient,fillRect:vi.fn(),save:vi.fn(),restore:vi.fn(),translate:vi.fn(),rotate:vi.fn(),beginPath:vi.fn(),moveTo:vi.fn(),bezierCurveTo:vi.fn(),stroke:vi.fn()};
 const canvas={dataset:{},getContext:()=>ctx,width:0,height:0} as unknown as HTMLCanvasElement;
 vi.stubGlobal('innerWidth',1440);vi.stubGlobal('innerHeight',900);vi.stubGlobal('document',{hidden:false});vi.stubGlobal('matchMedia',()=>({matches:reduced}));vi.stubGlobal('requestAnimationFrame',vi.fn((cb:FrameRequestCallback)=>{next=cb;return 1}));vi.stubGlobal('cancelAnimationFrame',vi.fn());vi.stubGlobal('addEventListener',vi.fn());vi.stubGlobal('removeEventListener',vi.fn());
 return {canvas,ctx,step:(ms:number)=>next(ms)};
}
describe('liquid fallback lifecycle',()=>{
 it('evolves without pointer input and releases its frame and resize handler',()=>{const f=fixture();const stop=startLiquidFallback(f.canvas,{current:{dark:true,personal:false,active:false}},true);f.step(100);const first=f.ctx.rotate.mock.calls[0][0];f.ctx.rotate.mockClear();f.step(160);expect(f.ctx.rotate.mock.calls[0][0]).not.toBe(first);expect(f.canvas.dataset.renderer).toBe('canvas2d');stop();expect(cancelAnimationFrame).toHaveBeenCalledWith(1);expect(removeEventListener).toHaveBeenCalledWith('resize',expect.any(Function))});
 it.each([[false,false],[true,true]])('freezes geometry when enabled=%s and reduced=%s',(enabled,reduced)=>{const f=fixture(reduced);const stop=startLiquidFallback(f.canvas,{current:{dark:false,personal:false,active:false}},enabled);f.step(100);const first=f.ctx.rotate.mock.calls[0][0];f.ctx.rotate.mockClear();f.step(160);expect(f.ctx.rotate.mock.calls[0][0]).toBe(first);stop()});
});
