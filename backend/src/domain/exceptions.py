class DomainError(Exception):
    """Base exception for all domain errors."""


class ServiceNotFoundError(DomainError):
    def __init__(self, identifier: str) -> None:
        super().__init__(f"Service not found: {identifier}")
        self.identifier = identifier


class ServiceConnectionError(DomainError):
    def __init__(self, service_name: str, reason: str) -> None:
        super().__init__(f"Connection to '{service_name}' failed: {reason}")
        self.service_name = service_name
        self.reason = reason


class UnsupportedServiceError(DomainError):
    def __init__(self, service_type: str) -> None:
        super().__init__(f"Unsupported service type: {service_type}")
        self.service_type = service_type


class EncryptionError(DomainError):
    pass


class ToolExecutionError(DomainError):
    def __init__(self, tool_name: str, reason: str) -> None:
        super().__init__(f"Tool '{tool_name}' failed: {reason}")
        self.tool_name = tool_name
        self.reason = reason
