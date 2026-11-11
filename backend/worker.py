"""Run separately: python worker.py. Restart-safe jobs backed by the workspace DB."""
import logging
import signal
import threading
from main import conn, rows, now, uid, log
from workspace import tick
stop=threading.Event()
for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,lambda *_:stop.set())
if __name__=='__main__':
    logging.basicConfig(level=logging.INFO)
    while not stop.is_set():
        try:tick(globals())
        except Exception:logging.exception('Reminder worker failed; retrying on next tick')
        stop.wait(2)
