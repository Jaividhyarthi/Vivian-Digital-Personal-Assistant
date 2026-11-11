"""Additive workspace API; durable jobs and owner sessions, no simulated providers."""
import asyncio
import datetime as dt
import hashlib
import json
import os
import secrets
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Literal
from fastapi import HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
import httpx

UTC = dt.timezone.utc
class Login(BaseModel):
    token: str = Field(min_length=1,max_length=512)
class Project(BaseModel):
    title: str = Field(min_length=1,max_length=250)
    description: str = Field(default='',max_length=10000)
    space: Literal['personal','professional']='professional'
    deadline: str|None=None
class MemoryPatch(BaseModel):
    content: str = Field(min_length=1,max_length=2000)
class Speech(BaseModel):
    text: str=Field(min_length=1,max_length=5000)
class ChatIn(BaseModel):
    text: str=Field(min_length=1,max_length=10000)
    space: Literal['personal','professional']='professional'
    request_id: str=Field(default_factory=lambda:secrets.token_hex(16),max_length=100)
class Automation(BaseModel):
    title: str=Field(min_length=1,max_length=250)
    due_at: dt.datetime
    space: Literal['personal','professional']='professional'
    recurrence: Literal['none','daily','weekly']='none'
class Pause(BaseModel):
    paused: bool


def migrate(g):
    with g['conn']() as c:
        for table, columns in {
            'tasks':{'space':"TEXT NOT NULL DEFAULT 'professional'",'due_at':'TEXT','category':"TEXT DEFAULT ''",'recurrence':"TEXT DEFAULT 'none'",'project_id':'TEXT'},
            'reminders':{'space':"TEXT NOT NULL DEFAULT 'professional'",'recurrence':"TEXT DEFAULT 'none'"},
            'memories':{'source':"TEXT DEFAULT 'owner'"},
        }.items():
            existing={r['name'] for r in c.execute(f'PRAGMA table_info({table})')}
            for name,definition in columns.items():
                if name not in existing:c.execute(f'ALTER TABLE {table} ADD COLUMN {name} {definition}')
        c.executescript('''
        CREATE TABLE IF NOT EXISTS schema_versions(version INTEGER PRIMARY KEY, applied_at TEXT);
        CREATE TABLE IF NOT EXISTS sessions(digest TEXT PRIMARY KEY, expires REAL);
        CREATE TABLE IF NOT EXISTS notifications(id TEXT PRIMARY KEY, source_key TEXT UNIQUE, title TEXT, space TEXT, created_at TEXT, read INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS worker_state(id INTEGER PRIMARY KEY, heartbeat TEXT);
        CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, title TEXT, description TEXT, space TEXT, deadline TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS files(id TEXT PRIMARY KEY, name TEXT, media_type TEXT, size INTEGER, space TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS automations(id TEXT PRIMARY KEY, title TEXT, due_at TEXT, space TEXT, recurrence TEXT, paused INTEGER DEFAULT 0, status TEXT DEFAULT 'scheduled', created_at TEXT);
        CREATE TABLE IF NOT EXISTS job_history(id TEXT PRIMARY KEY, source_id TEXT, scheduled_at TEXT, status TEXT, detail TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS agent_runs(id TEXT PRIMARY KEY, space TEXT, status TEXT, input TEXT, reply TEXT, error TEXT, created_at TEXT, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS tool_executions(id TEXT PRIMARY KEY, run_id TEXT, name TEXT, arguments TEXT, result TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS approval_actions(approval_id TEXT PRIMARY KEY, kind TEXT, payload TEXT);
        CREATE INDEX IF NOT EXISTS reminders_due ON reminders(status,due_at);
        CREATE INDEX IF NOT EXISTS messages_space ON messages(space,created_at);
        ''')
        c.execute('INSERT OR IGNORE INTO schema_versions VALUES(1,?)',(g['now'](),))


def tick(g, at=None):
    """Single transaction: each due occurrence produces exactly one durable inbox item."""
    at=at or dt.datetime.now(UTC)
    now=at.isoformat()
    with g['conn']() as c:
        c.execute('BEGIN IMMEDIATE')
        c.execute('INSERT OR REPLACE INTO worker_state VALUES(1,?)',(now,))
        for table,condition in [('reminders',"status='pending'"),('automations',"paused=0 AND status='scheduled'")]:
            for row in c.execute(f'SELECT * FROM {table} WHERE {condition} AND due_at<=?',(now,)).fetchall():
                key=f"{table}:{row['id']}:{row['due_at']}"
                c.execute('INSERT OR IGNORE INTO notifications(id,source_key,title,space,created_at) VALUES(?,?,?,?,?)',(g['uid'](),key,row['title'],row['space'],now))
                c.execute('INSERT INTO job_history VALUES(?,?,?,?,?,?)',(g['uid'](),row['id'],row['due_at'],'delivered','Delivered to durable Vivian inbox; OS push is not configured.',now))
                if row['recurrence']!='none':
                    step=dt.timedelta(days=1 if row['recurrence']=='daily' else 7)
                    due=dt.datetime.fromisoformat(row['due_at'])
                    # Coalesce missed occurrences, do not flood the owner after downtime.
                    due += step * (int((at-due)/step)+1)
                    c.execute(f'UPDATE {table} SET due_at=? WHERE id=?',(due.isoformat(),row['id']))
                else:
                    c.execute(f'UPDATE {table} SET status=? WHERE id=?',('delivered',row['id']))
                g['log'](c,'reminder','Reminder delivered to Vivian inbox',row['id'])
        # Recurring tasks re-open at the next due date, independently of the browser.
        for row in c.execute("SELECT * FROM tasks WHERE status='done' AND recurrence!='none' AND due_at<=?",(now,)).fetchall():
            step=dt.timedelta(days=1 if row['recurrence']=='daily' else 7)
            due=dt.datetime.fromisoformat(row['due_at'])
            if due.tzinfo is None:due=due.replace(tzinfo=UTC)
            due+=step*(int((at-due)/step)+1)
            c.execute("UPDATE tasks SET status='todo',due_at=? WHERE id=?",(due.isoformat(),row['id']))


def install(app,g):
    migrate(g)
    limits=defaultdict(deque)
    def session_valid(request):
        token=request.cookies.get('vivian_session','')
        if not token:return False
        return bool(g['rows']('SELECT digest FROM sessions WHERE digest=? AND expires>?',(hashlib.sha256(token.encode()).hexdigest(),time.time())))
    @app.middleware('http')
    async def protect(request,call_next):
        path=request.url.path
        if path in ('/health','/api/auth/login') or request.method=='OPTIONS':
            pass
        elif os.getenv('VIVIAN_DEV_NO_AUTH')=='1':pass
        elif not g['API_TOKEN']:
            return JSONResponse({'detail':'Owner authentication needs VIVIAN_API_TOKEN configuration.'},503)
        elif not (secrets.compare_digest(request.headers.get('x-vivian-token',''),g['API_TOKEN']) or session_valid(request)):
            return JSONResponse({'detail':'Sign in to your private workspace.'},401)
        origin=request.headers.get('origin')
        allowed=os.getenv('VIVIAN_ALLOWED_ORIGINS','http://localhost:5173,http://127.0.0.1:5173').split(',')
        if request.method not in ('GET','HEAD','OPTIONS') and origin and origin not in allowed:
            return JSONResponse({'detail':'Origin not allowed'},403)
        if path in ('/api/auth/login','/api/chat','/api/voice/speak'):
            bucket=(request.client.host,path);q=limits[bucket];t=time.monotonic()
            while q and q[0]<t-60:q.popleft()
            if len(q)>= (10 if path.endswith('login') else 30):return JSONResponse({'detail':'Please wait before trying again.'},429)
            q.append(t)
            if len(limits)>10000:limits.clear()
        result=await call_next(request)
        result.headers['X-Content-Type-Options']='nosniff'
        result.headers['Cache-Control']='no-store'
        return result

    @app.post('/api/auth/login')
    def login(v:Login):
        if not g['API_TOKEN'] or not secrets.compare_digest(v.token,g['API_TOKEN']):raise HTTPException(401,'Invalid owner token')
        token=secrets.token_urlsafe(48)
        with g['conn']() as c:
            c.execute('DELETE FROM sessions WHERE expires<?',(time.time(),))
            c.execute('INSERT INTO sessions VALUES(?,?)',(hashlib.sha256(token.encode()).hexdigest(),time.time()+43200))
        response=JSONResponse({'ok':True})
        response.set_cookie('vivian_session',token,httponly=True,secure=os.getenv('VIVIAN_COOKIE_SECURE','1')=='1',samesite='strict',max_age=43200,path='/')
        return response
    @app.post('/api/auth/logout')
    def logout(request:Request):
        with g['conn']() as c:c.execute('DELETE FROM sessions WHERE digest=?',(hashlib.sha256(request.cookies.get('vivian_session','').encode()).hexdigest(),))
        r=JSONResponse({'ok':True});r.delete_cookie('vivian_session');return r
    @app.get('/api/capabilities')
    def capabilities():
        w=g['rows']('SELECT heartbeat FROM worker_state WHERE id=1')
        online=bool(w and (dt.datetime.now(UTC)-dt.datetime.fromisoformat(w[0]['heartbeat'])).total_seconds()<30)
        return {'ai':{'configured':bool(os.getenv('OPENAI_API_KEY') and os.getenv('VIVIAN_MODEL')),'model':os.getenv('VIVIAN_MODEL',''),'live_test':'pending'},'voice':{'configured':bool(os.getenv('ELEVENLABS_API_KEY')),'voice_id':os.getenv('ELEVENLABS_VOICE_ID','VnvaVe7ctz87lJj9udKY'),'live_test':'pending'},'notifications':{'worker_online':online,'delivery':'durable_in_app_inbox','background_push':False},'services':{s:{'status':'not_connected','implemented':False} for s in ('gmail','calendar','drive','github','exotel')},'wake_word':{'supported':False,'fallback':'tap_to_talk'}}
    @app.get('/api/notifications')
    def notifications(space:str='professional'):return g['rows']('SELECT * FROM notifications WHERE space=? ORDER BY created_at DESC LIMIT 100',(space,))
    @app.patch('/api/notifications/{id}/read')
    def read_notification(id:str):
        with g['conn']() as c:c.execute('UPDATE notifications SET read=1 WHERE id=?',(id,))
        return {'ok':True}
    @app.get('/api/projects')
    def projects(space:str='professional'):return g['rows']('SELECT * FROM projects WHERE space=? ORDER BY created_at DESC',(space,))
    @app.post('/api/projects')
    def create_project(v:Project):
        x={'id':g['uid'](),**v.model_dump(),'created_at':g['now']()}
        with g['conn']() as c:
            c.execute('INSERT INTO projects VALUES(:id,:title,:description,:space,:deadline,:created_at)',x);g['log'](c,'project','Created project: '+v.title,x['id'])
        return x
    @app.patch('/api/projects/{id}')
    def update_project(id:str,v:Project):
        with g['conn']() as c:
            if not c.execute('SELECT id FROM projects WHERE id=?',(id,)).fetchone():raise HTTPException(404,'Project not found')
            c.execute('UPDATE projects SET title=?,description=?,deadline=? WHERE id=?',(v.title,v.description,v.deadline,id))
        return {'ok':True}
    @app.patch('/api/memories/{id}')
    def update_memory(id:str,v:MemoryPatch):
        with g['conn']() as c:
            if not c.execute('SELECT id FROM memories WHERE id=?',(id,)).fetchone():raise HTTPException(404,'Memory not found')
            c.execute('UPDATE memories SET content=? WHERE id=?',(v.content,id));g['log'](c,'memory','Updated explicit memory',id)
        return {'ok':True}
    @app.delete('/api/reminders/{id}')
    def delete_reminder(id:str):
        with g['conn']() as c:c.execute('DELETE FROM reminders WHERE id=?',(id,))
        return {'ok':True}
    @app.get('/api/automations')
    def automations(space:str='professional'):return g['rows']('SELECT * FROM automations WHERE space=? ORDER BY due_at',(space,))
    @app.post('/api/automations')
    def create_automation(v:Automation):
        if v.due_at.tzinfo is None:raise HTTPException(422,'Timezone is required')
        x={'id':g['uid'](),**v.model_dump(mode='json'),'due_at':v.due_at.astimezone(UTC).isoformat(),'created_at':g['now']()}
        with g['conn']() as c:c.execute('INSERT INTO automations(id,title,due_at,space,recurrence,created_at) VALUES(:id,:title,:due_at,:space,:recurrence,:created_at)',x)
        return x
    @app.patch('/api/automations/{id}')
    def pause(id:str,v:Pause):
        with g['conn']() as c:c.execute('UPDATE automations SET paused=? WHERE id=?',(int(v.paused),id))
        return {'ok':True}
    @app.get('/api/job-history')
    def history():return g['rows']('SELECT * FROM job_history ORDER BY created_at DESC LIMIT 100')
    @app.get('/api/files')
    def files(space:str='professional'):return g['rows']('SELECT * FROM files WHERE space=? ORDER BY created_at DESC',(space,))
    @app.post('/api/files')
    async def upload(space:Literal['personal','professional']='professional',file:UploadFile=File(...)):
        content=await file.read(10*1024*1024+1)
        if len(content)>10*1024*1024:raise HTTPException(413,'Maximum file size is 10 MB')
        id=g['uid']();root=Path(os.getenv('VIVIAN_FILES',str(g['BASE']/'private-files')));root.mkdir(parents=True,exist_ok=True)
        name=Path((file.filename or 'file').replace('\\','/')).name[:250]
        (root/id).write_bytes(content)
        with g['conn']() as c:c.execute('INSERT INTO files VALUES(?,?,?,?,?,?)',(id,name,file.content_type or 'application/octet-stream',len(content),space,g['now']()))
        return {'id':id,'name':name}
    @app.get('/api/files/{id}')
    def download(id:str):
        from fastapi.responses import FileResponse
        found=g['rows']('SELECT * FROM files WHERE id=?',(id,))
        if not found:raise HTTPException(404,'File not found')
        root=Path(os.getenv('VIVIAN_FILES',str(g['BASE']/'private-files')))
        return FileResponse(root/found[0]['id'],filename=found[0]['name'],media_type='application/octet-stream')
    @app.get('/api/files/{id}/preview')
    def preview(id:str):
        found=g['rows']('SELECT * FROM files WHERE id=?',(id,))
        if not found:raise HTTPException(404,'File not found')
        f=found[0]
        if not f['name'].lower().endswith(('.txt','.md','.csv','.json')):raise HTTPException(415,'Text preview supports TXT, Markdown, CSV and JSON. Download other formats.')
        root=Path(os.getenv('VIVIAN_FILES',str(g['BASE']/'private-files')))
        return {'text':(root/f['id']).read_text(errors='replace')[:50000]}
    @app.post('/api/voice/speak')
    async def speak(v:Speech):
        key=os.getenv('ELEVENLABS_API_KEY')
        if not key:raise HTTPException(503,'ElevenLabs is not configured. Your text reply is available.')
        voice=os.getenv('ELEVENLABS_VOICE_ID','VnvaVe7ctz87lJj9udKY')
        try:
            async with httpx.AsyncClient(timeout=45) as client:
                r=await client.post(f'https://api.elevenlabs.io/v1/text-to-speech/{voice}',headers={'xi-api-key':key},json={'text':v.text,'model_id':os.getenv('ELEVENLABS_MODEL','eleven_multilingual_v2')})
                r.raise_for_status()
            return Response(r.content,media_type='audio/mpeg')
        except httpx.HTTPError:raise HTTPException(502,'Voice provider failed. Try again or continue with text.')
    @app.post('/api/chat')
    async def chat(v:ChatIn):
        from agent import execute
        return await execute(v,g)
    @app.get('/api/agent-runs')
    def runs(space:str='professional'):return g['rows']('SELECT * FROM agent_runs WHERE space=? ORDER BY created_at DESC LIMIT 50',(space,))
