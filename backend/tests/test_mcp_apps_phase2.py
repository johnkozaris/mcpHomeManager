"""Tests for MCP Apps Phase 2: template rendering and XSS safety."""

from entrypoints.mcp.template_engine import TemplateEngine


class TestAppTemplateRendering:
    def setup_method(self):
        self.engine = TemplateEngine()

    def test_ha_entities_renders_valid_html(self):
        html = self.engine.render(
            "apps/ha_entities.html",
            domains={
                "light": [
                    {
                        "entity_id": "light.living_room",
                        "state": "on",
                        "friendly_name": "Living Room",
                    },
                    {"entity_id": "light.bedroom", "state": "off", "friendly_name": "Bedroom"},
                ],
                "sensor": [
                    {"entity_id": "sensor.temp", "state": "22.5", "friendly_name": "Temperature"},
                ],
            },
            entity_count=3,
            domain_filter=None,
        )
        assert "<!DOCTYPE html>" in html
        assert "Entity Dashboard" in html
        assert "Living Room" in html
        assert "light.living_room" in html
        assert "sensor" in html.lower()
        assert "3 entities" in html

    def test_ha_entities_with_domain_filter(self):
        html = self.engine.render(
            "apps/ha_entities.html",
            domains={
                "light": [{"entity_id": "light.test", "state": "on", "friendly_name": "Test"}]
            },
            entity_count=1,
            domain_filter="light",
        )
        assert "(light)" in html
        assert "1 entities" in html

    def test_ha_entities_empty(self):
        html = self.engine.render(
            "apps/ha_entities.html",
            domains={},
            entity_count=0,
            domain_filter=None,
        )
        assert "No entities found" in html

    def test_paperless_documents_renders_valid_html(self):
        html = self.engine.render(
            "apps/paperless_documents.html",
            documents=[
                {
                    "title": "Invoice 2024",
                    "correspondent": "ACME Corp",
                    "tags": ["finance", "2024"],
                    "created": "2024-01-15",
                },
                {"title": "Receipt", "correspondent": None, "tags": [], "created": "2024-02-01"},
            ],
            query="invoice",
            total=2,
        )
        assert "<!DOCTYPE html>" in html
        assert "Document Search" in html
        assert "Invoice 2024" in html
        assert "ACME Corp" in html
        assert "finance" in html
        assert '2 results for "invoice"' in html

    def test_paperless_documents_empty(self):
        html = self.engine.render(
            "apps/paperless_documents.html",
            documents=[],
            query="nonexistent",
            total=0,
        )
        assert 'No documents found for "nonexistent"' in html

    def test_forgejo_repos_renders_valid_html(self):
        html = self.engine.render(
            "apps/forgejo_repos.html",
            repos=[
                {
                    "name": "my-repo",
                    "full_name": "user/my-repo",
                    "description": "A test repo",
                    "stars_count": 5,
                    "forks_count": 2,
                    "updated_at": None,
                },
            ],
            owner_filter=None,
        )
        assert "<!DOCTYPE html>" in html
        assert "Repository Browser" in html
        assert "user/my-repo" in html
        assert "A test repo" in html

    def test_forgejo_repos_empty(self):
        html = self.engine.render(
            "apps/forgejo_repos.html",
            repos=[],
            owner_filter="nobody",
        )
        assert 'No repositories found for "nobody"' in html

    def test_xss_escaping_in_ha_entities(self):
        """Jinja2 autoescape should prevent XSS in entity names."""
        html = self.engine.render(
            "apps/ha_entities.html",
            domains={
                "light": [
                    {
                        "entity_id": "light.xss",
                        "state": "on",
                        "friendly_name": '<script>alert("xss")</script>',
                    },
                ],
            },
            entity_count=1,
            domain_filter=None,
        )
        # The injected XSS payload should be escaped
        assert 'alert("xss")' not in html
        assert "&lt;script&gt;" in html

    def test_xss_escaping_in_paperless(self):
        html = self.engine.render(
            "apps/paperless_documents.html",
            documents=[
                {
                    "title": "<img src=x onerror=alert(1)>",
                    "correspondent": None,
                    "tags": [],
                    "created": "",
                },
            ],
            query="test",
            total=1,
        )
        # The raw <img> tag should be escaped — it must appear as &lt;img not <img
        assert "<img src=x" not in html
        assert "&lt;img" in html

    def test_xss_escaping_in_forgejo(self):
        xss = "<script>alert(1)</script>"
        html = self.engine.render(
            "apps/forgejo_repos.html",
            repos=[
                {"name": "test", "full_name": xss, "description": xss, "updated_at": None},
            ],
            owner_filter=None,
        )
        # The raw <script> tag should be escaped
        assert "alert(1)</script>" not in html
        assert "&lt;script&gt;" in html
