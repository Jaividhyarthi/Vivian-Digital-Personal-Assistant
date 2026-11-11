# Character and motion milestone — 2026-11-11

This is an incremental implementation, not completion of the cinematic animation brief.

## Asset compatibility assessment

Inspected with Pillow: professional.webp 1678×937, personal.webp 1536×1024, idle.gif 480×270. All three contain exactly one frame. They are flattened artwork without bones, mesh, separate facial layers, mouth shapes, animation clips or timing data. No character derivative was generated. The interface identifies the portrait as static artwork.

Recommended asset delivery: one artist-approved glTF/GLB humanoid rig (VRM 1.0 is an acceptable standardized alternative), preserving the reference face/hair/proportions, with two clothing variants on the same skeleton. Provide blink/eye/look controls and mouth blendshapes, idle/greeting/nod/explain/thinking/present/walk/turn clips. Walk clips need known stride and root displacement or verified in-place foot locking. Identity approval is required before replacing the supplied portrait.

A 2D skeleton/layered sprite approach would require new separated face, hair, torso and limb artwork, alternate views and mouth drawings. The current flattened sheets cannot provide correct occlusion when turning. A 3D rig is the proposed path for the full walking/turning brief; it is not loaded or implemented yet. Minimum next input: an approved rig + clips, or permission to prepare a rigged derivative for identity review. Approval alone does not supply a finished production rig.

Official format references:
- https://vrm.dev/en/vrm/vrm_features/
- https://vrm.dev/en/vrma/
- https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps/

ElevenLabs' timestamped output provides character alignment. Character times are not phoneme/viseme labels. The current backend returns audio only. Accurate lip-sync requires an additional phoneme alignment/viseme mapping pipeline plus facial blendshapes; it must use audio.currentTime as the clock, pause during buffering, and clear immediately on interrupt. No amplitude animation or character-to-phoneme heuristic is presented as accurate lip-sync in this milestone.

## Implemented

- Persistent right-hand stage separate from page transitions; approved portrait crossfade between workspace modes.
- Minimize/hide controls; hide/background/effects preferences persist locally; compact portrait presentation below 900px.
- Shared spring for page/modal/login entrances, sidebar collapse, task-row entrance, notification fade; MotionConfig respects system reduced motion.
- Background rendering can be disabled; resources are cleaned up, voice remains independent.
- PlaybackController owns audio and cancellation. Speaking starts on `playing`, buffering switches to processing, pause/end/stop clear speech, replaced or late responses cannot restart audio.
- Microphone state starts only on recognition `onstart`. Stale capture callbacks are ignored. Navigating/interruption invalidates pending automatic voice replies.
- Stage responds to real listening, thinking, speaking, error and disconnected states. No fabricated greeting/walk/gesture states run without real assets.
- Restrained stage glow follows real listening/playback; it is state-reactive, not audio-energy-reactive.

## Verification

- Frontend: 8 automated tests passed, including 4 new playback lifecycle tests with development-only doubles.
- Backend: 19 tests passed with `cd backend && python -m pytest -q`. Running these subprocess tests from repository root fails because their subprocess imports require the backend working directory.
- Production TypeScript/Vite build passed.
- Browser: desktop light/dark dashboard, chat transition, persistent stage, minimize/expand, Settings hide/show and background toggle inspected. Preview showed honest owner-auth configuration errors; no authenticated productivity flow or live AI was claimed in this run.
- Mobile breakpoint and system reduced-motion behavior are implemented but physical-device/browser acceptance is pending.
- No demonstration recording captured. No character motion, lip-sync, gesture, audio-energy, or foot-placement acceptance can pass with current assets.

## Still pending

All real character animation acceptance (greeting, idle body motion, walking, turn, gestures, blink, facial expression, lip-sync); GPU/performance profiling with the eventual rig; live microphone/TTS interruption acceptance; live OpenAI/ElevenLabs integration; broader Phase 2 features and reference-theme fidelity. Existing implementation status remains authoritative for other product features. No provider keys were requested or committed.
