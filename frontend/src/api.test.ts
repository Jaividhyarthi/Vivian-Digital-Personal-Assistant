import {afterEach,describe,expect,it,vi} from 'vitest';
import {api,ApiError,iso} from './api';
afterEach(()=>vi.unstubAllGlobals());
describe('backend boundary',()=>{
 it('surfaces configuration errors without inventing replies',async()=>{vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(JSON.stringify({detail:'AI not configured'}),{status:503})));await expect(api('/api/chat','POST',{text:'Hello'})).rejects.toThrow('AI not configured')});
 it('uses session credentials and does not put secrets in headers',async()=>{const f=vi.fn().mockResolvedValue(new Response(JSON.stringify({id:'saved'})));vi.stubGlobal('fetch',f);await api('/api/tasks','POST',{title:'Task'});expect(f).toHaveBeenCalledWith('/api/tasks',expect.objectContaining({credentials:'same-origin',body:'{"title":"Task"}'}));expect(f.mock.calls[0][1].headers).not.toHaveProperty('Authorization')});
 it('reports invalid form bodies clearly',async()=>{vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(JSON.stringify({detail:[{msg:'invalid'}]}),{status:422})));await expect(api('/api/tasks')).rejects.toBeInstanceOf(ApiError)});
 it('converts explicit offsets without dropping the timezone',()=>{expect(iso('2026-11-11T10:00:00+05:30')).toBe('2026-11-11T04:30:00.000Z');expect(iso(null)).toBeNull()});
});
