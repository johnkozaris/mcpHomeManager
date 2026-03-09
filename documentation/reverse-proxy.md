## Reverse Proxy

If you expose MCP Home Manager outside your local network, always use a reverse proxy with TLS. Below are example configurations for common reverse proxies.

### Nginx

```nginx
server {
    listen 443 ssl;
    server_name mcp.your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Caddy

```caddy
mcp.your-domain.com {
    reverse_proxy localhost:8000
}
```

Caddy automatically provisions and renews TLS certificates via Let's Encrypt.

### Traefik

If using Traefik with Docker labels, add these labels to the `app` service in your `docker-compose.yml`:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.mcp.rule=Host(`mcp.your-domain.com`)"
  - "traefik.http.routers.mcp.entrypoints=websecure"
  - "traefik.http.routers.mcp.tls.certresolver=letsencrypt"
  - "traefik.http.services.mcp.loadbalancer.server.port=8000"
```

### Important Notes

- Set `PUBLIC_URL` in your `.env` to match your external URL (e.g., `https://mcp.your-domain.com`). This is used for password reset email links.
- MCP clients that connect to the `/mcp/` endpoint also go through the reverse proxy — ensure your proxy does not strip the `Authorization` header.
- If you use Cloudflare or another CDN, ensure WebSocket support is enabled if your MCP client uses the SSE transport.
