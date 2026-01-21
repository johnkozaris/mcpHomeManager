from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class CallStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class AuditEntry:
    service_name: str
    tool_name: str
    input_summary: str
    status: CallStatus
    duration_ms: int
    error_message: str | None = None
    client_name: str | None = None
    id: UUID | None = None
    created_at: datetime | None = None
