"""Runnable entry point for a property-management phone workflow."""

from property_phone_access import (
    InspectionReminder,
    MaintenanceRequest,
    PropertyPhoneGateway,
    TenantDocument,
    TenantPhoneRequest,
    TenantWorkspace,
    begin_tenant_access,
)


def main() -> None:
    gateway = PropertyPhoneGateway.from_environment()
    outcome = begin_tenant_access(
        gateway,
        TenantPhoneRequest(phone="+15551234567", locale="en"),
        InspectionReminder(phone="+15551234567", inspection_label="Unit 4B inspection"),
        TenantWorkspace(
            maintenance_requests=(MaintenanceRequest(unit="4B", summary="Leaking faucet"),),
            documents=(TenantDocument(document_name="lease.pdf", status="received"),),
        ),
    )
    print(outcome)


if __name__ == "__main__":
    main()
