# FieldVision AI — Agent Instructions

**Version:** 1.0.0
**ECC Integration:** v2.0.0

## Core Principles

1. **No Docker** — Runs natively on Windows
2. **No Flask** — FastAPI only
3. **No global variables** — Event-driven via message bus
4. **No blocking loops** — Async/await everywhere
5. **No hardcoded values** — All config in YAML files
6. **No spaghetti code** — Clean, modular architecture

## Architecture

- **Backend:** Python 3.12, FastAPI, OpenCV, YOLO11, ByteTrack, PyTorch CUDA
- **Frontend:** React 18, TypeScript, Vite, TailwindCSS
- **Mobile:** Android Kotlin, Camera2 API, MJPEG streaming
- **Hardware:** ESP32, PlatformIO (optional servo control)

## Agent Workflow

Use ECC agents proactively:

| Situation | Agent | Action |
|-----------|-------|--------|
| Complex feature | `planner` | Create implementation plan |
| Code written | `code-reviewer` | Review for quality |
| Bug fix | `tdd-guide` | Write tests first |
| Security code | `security-reviewer` | Check vulnerabilities |
| Build fails | `build-error-resolver` | Fix errors |
| Android code | `kotlin-reviewer` | Review Kotlin patterns |
| Python code | `python-reviewer` | Review Python patterns |

## Testing Requirements

- **Minimum coverage:** 80%
- **Backend:** pytest with PYTHONPATH="D:\FieldVision AI;D:\FieldVision AI\backend"
- **Android:** JUnit + Espresso
- **TDD mandatory:** Write tests before implementation

## Security Guidelines

- No hardcoded secrets (API keys, passwords, tokens)
- All user inputs validated
- Camera permissions handled gracefully
- Network discovery validated
- Rate limiting on all endpoints

## Coding Style

- **Immutability:** Always create new objects, never mutate
- **File organization:** Many small files over few large ones
- **Error handling:** Handle errors at every level
- **Input validation:** Validate all user input at boundaries

## Git Workflow

**Commit format:** `<type>: <description>`
Types: feat, fix, refactor, docs, test, chore, perf, ci

## Project Structure

```
backend/
  app/
    services/     — Business logic (camera, director, tracking, etc.)
    api/          — FastAPI routes
    core/         — Config, events, state machines
android-app/     — Phone camera app
frontend/        — React dashboard
configs/         — YAML configuration files
tests/           — Backend test suite
```

## ECC Commands Available

- `/plan` — Create implementation plan
- `/tdd` — Enforce TDD workflow
- `/code-review` — Review code quality
- `/security` — Security review
- `/build-fix` — Fix build errors
- `/refactor-clean` — Clean dead code
- `/verify` — Run verification loop
- `/learn` — Extract session patterns

## Performance

- GPU capped at 2GB VRAM, CPU at 2 cores
- Auto port discovery (8000-9999)
- Phone streaming: WebRTC → H.264 → MJPEG fallback
- Context management: Avoid last 20% of context window
