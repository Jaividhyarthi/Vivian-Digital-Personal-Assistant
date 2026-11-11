# Verification — 10 November 2026

- Backend: **17 tests passed** (`python -m pytest -q`); two dependency deprecation warnings.
- Frontend: **4 tests passed** (`npm test`).
- Production build: **passed** (`tsc --noEmit && vite build`).
- Browser: created a task and a timezone-aware reminder through the real interface; reloaded and verified persistence. Submitted chat without credentials and verified an explicit configuration error, retained input, and no simulated assistant reply.
- Worker: separate-process restart test verified persistent reminder delivery; repeated ticks produced one notification; recurrence/pause/catch-up tests passed.
- Auth: unauthenticated access denied, login/logout cookies checked, missing configuration fails closed, cross-origin mutation rejected.
- Agent: test-only provider transport exercised real tool dispatch, persisted history, duplicate request protection, proposed-memory approval, unsupported tool rejection and provider failure after a successful local write.

Not run: live OpenAI/ElevenLabs requests, real microphone/audio hardware, Android build, Docker deployment, mobile device/browser automation, external OAuth and OS push. Responsive CSS is included, but mobile usability is not claimed fully verified.

The QA database was disposable and separate from user data. No user credentials were introduced. Screenshots show QA records, not the user's actual tasks.
