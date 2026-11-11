export class ApiError extends Error { constructor(public status:number,message:string){super(message)} }
export async function api<T=any>(path:string,method='GET',body?:unknown):Promise<T>{
 const r=await fetch(path,{method,credentials:'same-origin',headers:body instanceof FormData?{}:{'Content-Type':'application/json'},body:body===undefined?undefined:body instanceof FormData?body:JSON.stringify(body)});
 if(!r.ok){const e=await r.json().catch(()=>({}));throw new ApiError(r.status,typeof e.detail==='string'?e.detail:r.status>=500?'The backend is unavailable. Check the service and try again.':'Please check the fields and try again.')}
 return r.json();
}
export const when=(s?:string)=>s?new Date(s).toLocaleString(undefined,{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}):'No due date';
export const iso=(s:FormDataEntryValue|null)=>s?new Date(String(s)).toISOString():null;
