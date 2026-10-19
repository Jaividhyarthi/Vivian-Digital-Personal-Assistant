import os
import tempfile
from pathlib import Path

# Isolate tests from user's real database before importing app.
os.environ['VIVIAN_DB'] = str(Path(tempfile.mkdtemp()) / 'test.db')
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_and_lists():
    for path in ['/health','/api/overview','/api/tasks','/api/notes','/api/contacts','/api/reminders','/api/export']:
        assert client.get(path).status_code == 200

def test_tasks():
    r = client.post('/api/tasks',json={'title':'Write report','priority':'high'})
    assert r.status_code == 200
    ident = r.json()['id']
    assert client.patch(f'/api/tasks/{ident}',json={'status':'done'}).status_code == 200
    assert client.delete(f'/api/tasks/{ident}').status_code == 200

def test_contacts_and_reminders():
    assert client.post('/api/contacts',json={'name':'Test','trusted':True}).status_code == 200
    assert client.post('/api/reminders',json={'title':'Meeting','due_at':'2026-10-20T09:00:00+05:30'}).status_code == 200

def test_memory():
    assert client.post('/api/memories',json={'space':'professional','content':'Use clear language'}).status_code == 200
    assert client.get('/api/memories?space=professional').status_code == 200

def test_call_simulation():
    r = client.post('/api/calls/simulate',json={'caller':'Test','reason':'urgent hospital call'})
    assert r.status_code == 200
    assert r.json()['escalate'] is True
    assert r.json()['transfer_started'] is False
