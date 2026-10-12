from property_phone_access import (
    InspectionReminder,
    MaintenanceRequest,
    PropertyPhoneGateway,
    TenantDocument,
    TenantPhoneRequest,
    TenantWorkspace,
    begin_tenant_access,
)
from unittest.mock import patch


class RecordingGateway:
    def __init__(self) -> None:
        self.events: list[tuple[str, str]] = []

    def send_login_code(self, request: TenantPhoneRequest) -> dict[str, str]:
        self.events.append(("login", request.phone))
        return {}

    def send_inspection_reminder(self, reminder: InspectionReminder) -> dict[str, str]:
        self.events.append(("inspection", reminder.phone))
        return {}


def test_access_workflow_sends_identity_code_before_inspection_reminder() -> None:
    gateway = RecordingGateway()
    result = begin_tenant_access(
        gateway,
        TenantPhoneRequest(phone="+15551234567"),
        InspectionReminder(phone="+15551234567", inspection_label="Unit 4B inspection"),
        TenantWorkspace(
            maintenance_requests=(MaintenanceRequest(unit="4B", summary="Leaking faucet"),),
            documents=(TenantDocument(document_name="lease.pdf", status="received"),),
        ),
    )

    assert gateway.events == [("login", "+15551234567"), ("inspection", "+15551234567")]
    assert result == {
        "tenant_phone": "+15551234567",
        "access": "code_sent",
        "inspection": "reminder_sent",
        "open_maintenance_requests": 1,
        "tenant_documents": 1,
    }


def test_inspection_reminder_uses_sms_otp_contract() -> None:
    gateway = PropertyPhoneGateway("test-key")
    with patch.object(gateway, "_post", return_value={}) as post:
        gateway.send_inspection_reminder(
            InspectionReminder(phone="+15551234567", inspection_label="Unit 4B inspection")
        )
    post.assert_called_once_with(
        "/v1/sms/otp", {"to": "+15551234567", "template": "Unit 4B inspection"}
    )
