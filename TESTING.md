# Testing

## Backend (Python / pytest)

### Run tests

```bash
cd backend
PYTHONPATH=src uv run pytest -x -q      # Quick run
PYTHONPATH=src uv run pytest -v          # Verbose
PYTHONPATH=src uv run pytest tests/test_service_manager.py  # Single file
```

### Test suite (69 tests)

| Test File | Tests | What's Covered |
|-----------|-------|----------------|
| `test_domain_entities.py` | 8 | ServiceConnection, ToolDefinition, AuditEntry, ServiceType |
| `test_service_manager.py` | 13 | CRUD, health checks, token handling, edge cases |
| `test_encryption.py` | 5 | Roundtrip, wrong key, empty key, unicode |
| `test_client_factory.py` | 3 | All 7 types registered, unsupported type error |
| `test_exceptions.py` | 3 | Domain error hierarchy |
| `test_config_export.py` | 8 | YAML export, redaction, round-trip, validation |
| `test_permission_profiles.py` | 7 | All service types, read-only/admin logic, frozen dataclass |
| `test_audit_client_tracking.py` | 4 | client_name in record_success/record_error |
| `test_metrics.py` | 3 | Prometheus counter, histogram, error status |
| `test_meta_tools.py` | 1 | Meta-tool registration on FastMCP |
| `test_logging_config.py` | 3 | structlog prod/debug config, noisy logger suppression |

### Architecture

Tests use **in-memory fakes** (not mocks) for all ports:
- `FakeServiceRepository` — dict-backed repository
- `FakeEncryption` — identity encryption (`enc:` prefix)
- `FakeServiceClient` — configurable health check result
- `FakeClientFactory` — returns a fixed client instance

No database or network required to run tests.

---

## Frontend (TypeScript / Vitest)

### Run tests

```bash
cd frontend
pnpm exec vitest run        # All tests
pnpm exec vitest            # Watch mode
pnpm exec tsc --noEmit      # Type check
```

### Test suite (49 tests)

| Test File | Tests | What's Covered |
|-----------|-------|----------------|
| `service-meta.test.tsx` | 9 | SERVICE_META completeness, icon rendering, color application |
| `Button.test.tsx` | 7 | Click, disabled, variants, sizes |
| `Toggle.test.tsx` | 6 | Checked/unchecked, onChange, disabled |
| `Badge.test.tsx` | 6 | All 5 variants, className passthrough |
| `ConfirmDialog.test.tsx` | 6 | Open/close, confirm/cancel, ARIA, loading state |
| `LogEntryDetail.test.tsx` | 6 | Error display, input summary, service link |
| `TerminalBlock.test.tsx` | 5 | Code rendering, label, traffic light dots, copy |
| `EmptyState.test.tsx` | 4 | Title, description, icon, optional children |

### Stack

- **Vitest** — Vite-native test runner
- **@testing-library/react** — component rendering
- **@testing-library/user-event** — user interaction simulation
- **@testing-library/jest-dom** — DOM matchers
- **jsdom** — browser DOM environment
