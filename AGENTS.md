# FieldVision AI — Agent Instructions

**Stack:** Python 3.12, FastAPI, OpenCV, YOLO11, ByteTrack, PyTorch CUDA · React 18, TypeScript, Vite, Zustand, TailwindCSS · Kotlin Android (Camera2, MJPEG) · ESP32/PlatformIO

## Non-Negotiables

1. **No Docker** — runs natively on Windows
2. **No Flask** — FastAPI only
3. **No global variables** — event-driven via `EventBus` (pub/sub, thread-safe, `backend/app/core/events.py`)
4. **No blocking loops** — async/await everywhere
5. **No hardcoded values** — all config in `configs/*.yaml`
6. **Immutability** — always create new objects, never mutate
7. **No new dependency** if an existing one or stdlib covers it

## Ponytail Philosophy

**Before writing code, stop at the first rung that holds:**

1. Does this need to exist? (YAGNI)
2. Already in this codebase? Reuse it.
3. Stdlib covers it? Use it.
4. Already-installed dep solves it? Use it.
5. Can this be one line? Make it one line.

**Rules:** No unrequested abstractions. Fewest files possible. Shortest working diff. Question complex requests: "Do you actually need X?" Mark simplifications with `ponytail:`.

**Not lazy about:** understanding the problem, input validation, error handling, security, hardware calibration.

## Architecture Quick-Ref

```
backend/
  app/
    main.py        — FastAPI entry (create_app factory, CORS, lifespan)
    api/           — Routes: system, camera, servo, director, stream, websocket, output
    api/deps.py    — DI: service adapters with real/mock fallback
    core/          — EventBus, SystemStateMachine, config loader
    services/      — camera/, director/, output/, tracking/
    models/        — Pydantic models
  tests/           — 22 test files (test_*.py)
frontend/
  src/
    components/    — React components (use Zustand for state)
    services/      — API client layer
    test/setup.ts  — Vitest setup (jest-dom, fake timers)
  vite.config.ts   — Proxy /api/* → localhost:8001, port 5173
android-app/       — Kotlin Camera2 MJPEG streaming
configs/           — camera.yaml, network.yaml, servo.yaml, ai.yaml, output.yaml, stream.yaml
```

## Running the Project

```bash
# Full stack (Windows)
start.bat                          # Backend :8001 + Frontend :5173

# Backend only
cd backend
set PYTHONPATH=D:\FieldVision AI;D:\FieldVision AI\backend
python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8001 --reload

# Frontend only
cd frontend && npm run dev          # :5173, proxies /api/* to :8001
```

## Testing

**Coverage floor:** 80%. TDD mandatory (RED → GREEN → REFACTOR).

```bash
# Backend
cd backend
set PYTHONPATH=D:\FieldVision AI;D:\FieldVision AI\backend
pytest                              # 22 test files in backend/tests/
pytest --cov=app --cov-report=term-missing

# Frontend
cd frontend
npm test                            # Vitest
npm run test:coverage
npm run typecheck                   # tsc --noEmit
npm run lint                        # ESLint
```

**Backend tests:** `pytest` — no conftest, files in `backend/tests/`. Mock hardware dependencies.
**Frontend tests:** Vitest + React Testing Library + jsdom. Setup in `frontend/src/test/setup.ts`.
**Android tests:** JUnit + Espresso.

## State Machine

Defined in `backend/app/core/state.py`. States: `INIT → CONNECTING → STREAMING → TRACKING → DIRECTING → OUTPUTTING → STOPPING → ERROR`. Transitions are validated — invalid transitions raise exceptions.

## Coding Conventions

- **File organization:** many small files over few large ones
- **Error handling:** at every level, never swallow silently
- **Adapters pattern:** real services wrapped with mock fallbacks in `api/deps.py`
- **Commit format:** `<type>: <description>` (feat, fix, refactor, docs, test, chore, perf, ci)
- **Python:** PEP 8, type hints, `from __future__ import annotations`
- **TypeScript:** strict mode, no `any`, functional components

## OpenCode Config

`opencode.json` at repo root — agents (build, planner, architect, code-reviewer, debugger, tdd-engineer, implementer, etc.) and ECC skill references. Do not delete or restructure without understanding the agent wiring.

## Security

- No hardcoded secrets
- All user inputs validated at trust boundaries
- Camera permissions handled gracefully
- Network discovery validated
- CORS configured (currently `allow_origins=["*"]` — tighten for production)

## Performance Constraints

- GPU capped at 2GB VRAM, CPU at 2 cores
- Auto port discovery (8000-9999)
- Phone streaming: WebRTC → H.264 → MJPEG fallback
- Context management: avoid last 20% of context window

## ECC Agents (proactive use)

| Situation | Agent | Action |
|-----------|-------|--------|
| Complex feature | `planner` | Implementation plan |
| Code written | `code-reviewer` | Quality review |
| Bug fix | `tdd-guide` | Tests first |
| Security code | `security-reviewer` | Vulnerability check |
| Build fails | `build-error-resolver` | Fix errors |
| Python code | `python-reviewer` | Python patterns |
| Android code | `kotlin-reviewer` | Kotlin patterns |
