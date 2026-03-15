## Security & Privacy

MCP Home Manager is designed to keep your data local and secure.

### Your data stays on your server

All service credentials, API keys, and configuration are stored in your local database (SQLite by default, or PostgreSQL if configured). Nothing is sent to external servers. The application runs entirely on your hardware.

### Credential protection

- **Service tokens** are encrypted at rest using Fernet symmetric encryption. The encryption key is auto-generated on first run and stored in the `app_data` Docker volume.
- **User passwords** are hashed with scrypt (random 16-byte salt) and never stored in plaintext.
- **API keys** are SHA-256 hashed before storage. The plaintext key is shown once at creation time and cannot be recovered.
- **SMTP passwords** (for password reset emails) are Fernet-encrypted in the database.

### Network security recommendations

- **Always use HTTPS** when exposing MCP Home Manager outside your local network. Use a reverse proxy (Nginx, Caddy, Traefik) with TLS termination. See the [Reverse Proxy guide](reverse-proxy).
- **Rate limiting** is enabled by default: 120 requests per minute per IP address, with automatic blocking after 10 failed authentication attempts per IP.
- **SSRF protection** — SSRF (Server-Side Request Forgery) protection blocks requests to cloud metadata endpoints like `169.254.169.254`, preventing credential theft if an attacker controls a service URL. DNS rebinding protection is also enabled. Private/internal IPs are still allowed for homelab use.

### Container hardening

The application container runs with multiple layers of protection:

- **Read-only filesystem** — The container filesystem is mounted read-only
- **No new privileges** — `security_opt: no-new-privileges` prevents privilege escalation
- **All capabilities dropped** — `cap_drop: ALL` removes all Linux capabilities
- **Non-root user** — Runs as `appuser`, not root

### Reporting vulnerabilities

If you discover a security vulnerability, please report it responsibly via [GitHub Security Advisories](https://github.com/johnkozaris/mcpHomeManager/security/advisories) or see `SECURITY.md` in the repository root.
