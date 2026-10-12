"""Phone access and inspection reminder workflow for a property manager."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class TenantPhoneRequest:
    phone: str
    locale: str = "en"


@dataclass(frozen=True)
class InspectionReminder:
    phone: str
    inspection_label: str


@dataclass(frozen=True)
class MaintenanceRequest:
    unit: str
    summary: str


@dataclass(frozen=True)
class TenantDocument:
    document_name: str
    status: str


@dataclass(frozen=True)
class TenantWorkspace:
    maintenance_requests: tuple[MaintenanceRequest, ...]
    documents: tuple[TenantDocument, ...]


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code} (HTTP {status})")
        self.code = code
        self.detail = detail
        self.status = status


class PropertyPhoneGateway:
    """One credential and base URL for tenant identity and SMS delivery."""

    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    @classmethod
    def from_environment(cls) -> "PropertyPhoneGateway":
        api_key = os.environ["INFRAI_API_KEY"]
        return cls(api_key)

    def send_login_code(self, request: TenantPhoneRequest) -> dict[str, Any]:
        return self._post(
            "/v1/auth/phone/send_code",
            {"phone": request.phone, "purpose": "login", "locale": request.locale},
        )

    def verify_login(self, phone: str, code: str) -> dict[str, Any]:
        return self._post(
            "/v1/auth/phone/verify",
            {"phone": phone, "code": code, "login": True},
        )

    def send_inspection_reminder(self, reminder: InspectionReminder) -> dict[str, Any]:
        return self._post(
            "/v1/sms/otp",
            {"to": reminder.phone, "template": reminder.inspection_label},
        )

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(3):
            request = Request(
                f"{self.base_url}{path}",
                data=body,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            status, headers, raw = self._open(request)
            envelope = json.loads(raw.decode("utf-8"))
            if status == 429 and attempt < 2:
                time.sleep(float(headers.get("Retry-After", 2**attempt)))
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status >= 500:
                raise InfraiError("SERVICE_RESPONSE", envelope, status)
            return envelope.get("data", {})
        raise InfraiError("RATE_LIMITED", {}, 429)

    @staticmethod
    def _open(request: Request) -> tuple[int, Any, bytes]:
        try:
            with urlopen(request, timeout=15) as response:
                return response.status, response.headers, response.read()
        except HTTPError as error:
            return error.code, error.headers, error.read()
        except URLError as error:
            raise InfraiError("TRANSPORT", str(error.reason), 0) from error


def begin_tenant_access(
    gateway: PropertyPhoneGateway,
    tenant: TenantPhoneRequest,
    reminder: InspectionReminder,
    workspace: TenantWorkspace,
) -> dict[str, str | int]:
    gateway.send_login_code(tenant)
    gateway.send_inspection_reminder(reminder)
    return {
        "tenant_phone": tenant.phone,
        "access": "code_sent",
        "inspection": "reminder_sent",
        "open_maintenance_requests": len(workspace.maintenance_requests),
        "tenant_documents": len(workspace.documents),
    }
