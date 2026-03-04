"""HTTP method constants used across adapters and service tooling."""

HTTP_METHODS: frozenset[str] = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})


def allowed_http_methods_csv() -> str:
    return ", ".join(sorted(HTTP_METHODS))

