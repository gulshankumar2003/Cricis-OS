# CrisisOS MVP PRD

## Problem statement
CrisisOS coordinates citizen emergency signals, AI-assisted analysis, human-approved dispatch, and responder status updates in one emergency operations workflow. AI can recommend but never dispatch autonomously.

## Architecture
- Expo Router mobile-first frontend with React Native components, dark tactical theme tokens, and role-based citizen, command center, and responder workspaces.
- FastAPI backend on port 8001 with MongoDB persistence, Pydantic response models, GeoJSON location fields, idempotent SOS creation, and audit events.
- Deterministic safety analysis provider for the demo path; human approval is required before assignment.

## User personas
- Citizen: sends an SOS, shares available location, and follows incident status.
- Responder: accepts an approved assignment and moves through operational states.
- Operator: reviews AI recommendations and approves dispatch.
- Administrator: represented by the role-aware command workspace in this MVP.

## Core requirements (static)
- Role-aware access for CITIZEN, RESPONDER, OPERATOR, ADMIN, ORGANIZATION_ADMIN.
- SOS with emergency type, description, affected people, idempotency key, and location source.
- Persisted incident, deterministic analysis, responder matching, approval-gated assignment, valid status transitions, location updates, analytics, and audit log.
- Clear loading, error, empty, offline/location-unknown, and confirmed acknowledgment states.

## Implemented (2026-10-07)
- Added dark CrisisOS UI with demo workspace entry, citizen SOS composer, operator queue, responder mission control, and mobile-safe layouts.
- Added MongoDB-backed FastAPI routes for demo login, SOS, incidents, responders, assignments, operational location, audit, analytics, health, ready, and demo reset.
- Verified the end-to-end API path: SOS → AI analysis → human approval → ACCEPTED → EN_ROUTE → ON_SCENE → COMPLETED/RESOLVED.

## Implemented (2026-09, test-fix iteration 2)
- P0: SOS composer wrapped in `KeyboardAwareScrollView` (react-native-keyboard-controller) so every control is scrollable/tappable at 390px viewports.
- P1: StatusCard header made shrink-safe (`statusHeading` flex + badge `flexShrink: 0`); status badge no longer clips.
- P1: Responder location watcher now uses `assignment.responder_id` instead of hardcoded `responder-alpha`.
- P2: testIDs added across role buttons, logout, SOS composer controls, approve dispatch, assignment advance, and refresh; `EXPO_BACKEND_URL` supported as fallback API base key.

## Prioritized backlog
- P0: add full JWT/refresh authentication and organization isolation.
- P1: add browser/mobile evidence upload and audio capture for SOS reports.
- P1: add alerts, analytics date filters/CSV export, and richer audit browsing.
- P2: add knowledge assistant document ingestion and citations.
- P2: modularize `app/index.tsx` into role-based component files (deferred by user).

## Implemented (2026-09, feature iteration 3)
- **Realtime**: FastAPI WebSocket bus at `/api/ws` broadcasting `incident.created`, `assignment.updated`, `responder.location`, `responder.status`, `demo.reset`. Frontend `subscribeEvents` client with backoff reconnect drives all three workspaces (debounced refresh + 30s safety poll; header pill shows LIVE / RECONNECTING).
- **Live map**: platform-split `CrisisMap` — react-native-maps on native (Expo Go, dark style), Leaflet + Esri Dark Gray Canvas raster tiles on web (no API key). Command Center shows all incidents + responder positions; Responder view shows incident + own position.
- **Offline SOS queue**: storage-backed outbox (`enqueueSos`/`flushOutbox`) keyed by idempotency keys; network-error detection queues the SOS, banner shows queued count, auto-flush on `online` event + 15s interval.
- **AI triage upgrade**: `llm_analysis()` calls OpenAI `gpt-5.6-terra` via emergentintegrations (EMERGENT_LLM_KEY), stream-accumulated JSON, sanitized against allowlists, 25s timeout with deterministic fallback; provider recorded in `ai_analysis.provider` and audit log. Human-approval gate unchanged.
- **Location**: `expo-location` service with contextual permission flow (check → ask → blocked → Open Settings), used by SOS composer and the responder mission watcher.
- **Realtime hardening (post-test)**: WS ping/pong heartbeat (15s) + browser online/offline listeners so half-open sockets flip the header pill to RECONNECTING and trigger reconnect.
- Test status: 29/29 backend pytest, full frontend E2E pass at 390×844 (iteration 3 report).

## Implemented (2026-09, feature iteration 4)
- **Real authentication (JWT)**: signup (citizen-only, 12+ char passwords), login, `/auth/me`, bcrypt hashing, role guards on every protected route (operators approve/publish, citizens see only their own incidents), seeded role accounts, session restore + 401 auto-logout, auth screen with demo-account autofill chips.
- **Photo evidence**: SOS composer camera/gallery attach (contextual permissions + Open Settings fallback), multipart upload through the backend to Emergent Object Storage (`crisisos/uploads/{user}/{uuid}`), authenticated file serving with `?token=` for web, thumbnails in citizen status card + operator review panel, media ownership enforced.
- **Alert publishing**: operators publish severity-graded alerts (optional km radius) via `AlertComposer`; citizens + responders receive them instantly over WebSocket in `AlertsStrip`; deactivate supported; audit-logged.
- **Analytics dashboard**: extended `/api/analytics` (by_type, by_severity, avg resolution minutes, active alerts, responders ready) rendered as dependency-free bar charts in the Command Center.
- 422 validation errors now render readable messages (testing-agent fix).
- Test status: 69/69 backend pytest (auth + media/alerts suites added), full frontend E2E pass (iteration 4 report).

## Implemented (2026-09, security remediation — iteration 5)
Security audit initially FAILED (1 critical, 1 high, 2 medium). All findings fixed and independently re-verified (89/89 backend tests, incl. 20-test security suite):
- **SEC-001 (critical)**: privileged demo passwords removed from the app bundle (autofill chips deleted); passwords now live in `backend/.env` (`DEMO_<ROLE>_PASSWORD`) and rotate on every startup; old passwords rejected.
- **SEC-002 (high)**: `/api/demo/reset` is ADMIN-only (401/403/200 verified).
- **SEC-003 (medium)**: WebSocket `/api/ws` requires a JWT (`?token=`, verified pre-accept, close 4401); `responder.location` GPS events are never fanned out to citizen connections.
- **SEC-004 (medium)**: raw JWT no longer accepted in file URLs; media served via 10-min HMAC-signed URLs (`/api/media/sign`, web) or Authorization header (native); citizen media access scoped to owner/own incidents.
- **Hardening**: login/signup rate-limited (10 attempts/5 min/email → 429); CORS credentials disabled.

## P0/P1/P2 remaining next tasks
- P0: test and harden concurrent idempotent SOS requests and failure recovery.
- P1: connect a real AI provider behind the existing analysis abstraction.
- P2: expand admin/resource management and production deployment documentation.