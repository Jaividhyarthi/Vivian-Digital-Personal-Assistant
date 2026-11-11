import datetime as dt
import json
import os
import subprocess
import sys
import pytest
from fastapi.testclient import TestClient
import main, agent
from workspace import tick, migrate
@pytest.fixture(autouse=True)
def isolated(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'DB',tmp_path/'workspace.db')
    monkeypatch.setattr(main,'API_TOKEN','test-owner-token')
    monkeypatch.setenv('VIVIAN_COOKIE_SECURE','0')
    monkeypatch.setenv('VIVIAN_FILES',str(tmp_path/'files'))
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    monkeypatch.delenv('VIVIAN_DEV_NO_AUTH',raising=False)
    main.init();migrate(vars(main))
@pytest.fixture
def client():return TestClient(main.app,headers={'x-vivian-token':'test-owner-token'})
def test_auth_cookie_logout_and_fail_closed(client,monkeypatch):
    stranger=TestClient(main.app)
    assert stranger.get('/api/tasks').status_code==401
    assert stranger.post('/api/auth/login',json={'token':'bad'}).status_code==401
    assert stranger.post('/api/auth/login',json={'token':'test-owner-token'}).status_code==200
    assert stranger.get('/api/tasks').status_code==200
    stranger.post('/api/auth/logout')
    assert stranger.get('/api/tasks').status_code==401
    monkeypatch.setattr(main,'API_TOKEN','')
    assert stranger.get('/api/export').status_code==503

def test_origin(client):
    assert client.post('/api/tasks',headers={'origin':'https://evil.example'},json={'title':'Bad'}).status_code==403

def test_reminder_process_restart_dedup_and_timezone(client):
    r=client.post('/api/reminders',json={'title':'Review project','due_at':'2026-11-11T10:00:00+05:30','space':'personal'})
    assert r.status_code==200,r.text
    assert r.json()['due_at']=='2026-11-11T04:30:00+00:00'
    result=subprocess.run([sys.executable,'-c',"import main; from workspace import tick; import datetime as d; tick(vars(main),d.datetime(2026,11,11,5,tzinfo=d.timezone.utc))"],env={**os.environ,'VIVIAN_DB':str(main.DB)},capture_output=True)
    assert result.returncode==0,result.stderr.decode()
    tick(vars(main),dt.datetime(2026,11,11,6,tzinfo=dt.timezone.utc))
    notes=client.get('/api/notifications?space=personal').json()
    assert len(notes)==1 and notes[0]['title']=='Review project'
    assert client.get('/api/notifications?space=professional').json()==[]
    assert client.get('/api/reminders?space=personal').json()[0]['status']=='delivered'

def test_recurring_coalesces_and_pauses(client):
    r=client.post('/api/automations',json={'title':'Daily','due_at':'2026-11-01T10:00:00+00:00','recurrence':'daily'}).json()
    client.patch('/api/automations/'+r['id'],json={'paused':True})
    at=dt.datetime(2026,11,10,12,tzinfo=dt.timezone.utc);tick(vars(main),at)
    assert client.get('/api/notifications').json()==[]
    client.patch('/api/automations/'+r['id'],json={'paused':False});tick(vars(main),at);tick(vars(main),at)
    assert len(client.get('/api/notifications').json())==1
    assert client.get('/api/automations').json()[0]['due_at']=='2026-11-11T10:00:00+00:00'

def test_naive_date_rejected(client):
    assert client.post('/api/reminders',json={'title':'Ambiguous','due_at':'2026-11-11T10:00:00'}).status_code==422

def test_missing_credentials_no_fake_reply(client):
    assert client.post('/api/chat',json={'text':'Hello'}).status_code==503
    assert client.get('/api/messages').json()==[]
    assert client.post('/api/voice/speak',json={'text':'Hello'}).status_code==503

def ai(monkeypatch,outputs):
    monkeypatch.setenv('OPENAI_API_KEY','test-double-only');monkeypatch.setenv('VIVIAN_MODEL','test-model');payloads=[]
    async def fake(payload):
        payloads.append(payload);r=outputs.pop(0)
        if isinstance(r,Exception):raise r
        return {'output':r}
    monkeypatch.setattr(agent,'provider',fake);return payloads

def call(name,args):return {'type':'function_call','call_id':'call-1','name':name,'arguments':json.dumps(args)}
def answer(text):return {'type':'message','content':[{'type':'output_text','text':text}]}

def test_agent_loop_persistence_idempotency(client,monkeypatch):
    payloads=ai(monkeypatch,[[call('create_reminder',{'title':'Project','due_at':'2026-11-11T10:00:00+05:30'})],[answer('Saved reminder.')]])
    body={'text':'Remind me tomorrow at 10','space':'personal','request_id':'request-1'}
    r=client.post('/api/chat',json=body);assert r.status_code==200,r.text
    assert payloads[0]['model']=='test-model'
    assert len(client.get('/api/reminders?space=personal').json())==1
    assert client.post('/api/chat',json=body).json()['reply']==r.json()['reply']
    assert len(client.get('/api/reminders?space=personal').json())==1
    assert len(client.get('/api/messages?space=personal').json())==2

def test_memory_approval(client,monkeypatch):
    ai(monkeypatch,[[call('propose_memory',{'content':'Likes concise explanations'})],[answer('Please approve.')]])
    assert client.post('/api/chat',json={'text':'Remember preference'}).status_code==200
    assert client.get('/api/memories?space=professional').json()==[]
    a=client.get('/api/approvals').json()[0]
    assert client.patch('/api/approvals/'+a['id']+'/approved').status_code==200
    assert len(client.get('/api/memories?space=professional').json())==1
    assert client.patch('/api/approvals/'+a['id']+'/approved').status_code==409

def test_failure_after_tool_audited(client,monkeypatch):
    ai(monkeypatch,[[call('create_task',{'title':'Actual task','detail':'','priority':'normal'})],RuntimeError('down')])
    body={'text':'Add task','request_id':'fail-1'}
    assert client.post('/api/chat',json=body).status_code==502
    assert len(client.get('/api/tasks').json())==1
    assert client.get('/api/agent-runs').json()[0]['status']=='failed'
    assert client.post('/api/chat',json=body).status_code==409
    assert not any(m['role']=='assistant' for m in client.get('/api/messages').json())

def test_unknown_tool_denied(client,monkeypatch):
    p=ai(monkeypatch,[[call('send_email',{'to':'someone'})],[answer('Unavailable.')]])
    assert client.post('/api/chat',json={'text':'Send mail'}).status_code==200
    assert 'Tool is not allowed' in json.dumps(p[-1])

def test_projects_files_memory_spaces(client):
    p=client.post('/api/projects',json={'title':'Vivian','space':'personal'}).json()
    client.post('/api/tasks',json={'title':'Build','space':'personal','project_id':p['id']})
    assert client.get('/api/tasks?space=professional').json()==[]
    assert len(client.get('/api/tasks?space=personal').json())==1
    f=client.post('/api/files?space=personal',files={'file':('../../notes.txt',b'Approved context','text/plain')}).json()
    assert f['name']=='notes.txt'
    assert client.get('/api/files/'+f['id']+'/preview').json()['text']=='Approved context'
    m=client.post('/api/memories',json={'content':'Old','space':'personal'}).json()
    assert client.patch('/api/memories/'+m['id'],json={'content':'Updated'}).status_code==200
    assert client.get('/api/memories?space=personal').json()[0]['content']=='Updated'

def test_migration_preserves_records(client):
    client.post('/api/tasks',json={'title':'Keep this'});main.init();migrate(vars(main))
    assert client.get('/api/tasks').json()[0]['title']=='Keep this'

@pytest.mark.parametrize('legacy',[False,True])
def test_simultaneous_api_worker_migrations(tmp_path,legacy):
    """Start real independent imports together on fresh and older databases."""
    import sqlite3
    db=tmp_path/'concurrent.db'
    if legacy:
        with sqlite3.connect(db) as c:
            c.execute('CREATE TABLE tasks(id TEXT PRIMARY KEY,title TEXT NOT NULL)')
            c.execute("INSERT INTO tasks VALUES('existing','Preserve my task')")
    code="import sys; sys.stdin.readline(); import main; print('ready')"
    processes=[subprocess.Popen([sys.executable,'-c',code],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env={**os.environ,'VIVIAN_DB':str(db)}) for _ in range(6)]
    for process in processes:
        process.stdin.write('start\n');process.stdin.flush()
    for process in processes:
        out,err=process.communicate(timeout=30)
        assert process.returncode==0,err
        assert 'ready' in out
    with sqlite3.connect(db) as c:
        assert sum(r[1]=='source' for r in c.execute('PRAGMA table_info(memories)'))==1
        if legacy:assert c.execute("SELECT title FROM tasks WHERE id='existing'").fetchone()[0]=='Preserve my task'
