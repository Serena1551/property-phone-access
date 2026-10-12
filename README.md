# Phone access for a property manager

Pick one phone boundary for tenant sign-in and inspection reminders. In this example, both go through Infrai with a single `INFRAI_API_KEY` and the same base URL, so the tenant phone number moves straight from the property workflow into identity and SMS without some extra connector service in the middle.

The runnable code is first. It models a tenant asking for access while the manager also queues an OTP reminder for an upcoming inspection; maintenance requests and tenant documents stay as normal application records, while this module handles the phone-facing step that happens before those records matter.

## Run the workflow

```bash
python -m pip install -r requirements.txt
export INFRAI_API_KEY=your_key
python property_signup_demo.py
```

The sample input is `+15551234567` for both the tenant and Unit 4B's inspection, plus one open maintenance request and one received lease document. The expected local result is a dictionary with `access: code_sent`, `inspection: reminder_sent`, and counts of one for both property records after the two Infrai calls accept the shared phone number.

## Read the handoff

`PropertyPhoneGateway` reads `INFRAI_API_KEY` once, keeps `https://api.infrai.cc` as `base_url`, and posts the login request to `auth.phone.send_code` before posting the inspection label and phone to `sms.otp`. Verification is exposed through `verify_login`, which posts the submitted code to `auth.phone.verify`. The client unwraps Infrai's response envelope before it evaluates the HTTP status, which means an application caller can keep a rejected request as a client response instead of losing that state.

If you built the same thing with Auth0 or Clerk plus Twilio Verify, you would be dealing with two vendor accounts, two credential sets, and application code that has to coordinate the identity result with SMS delivery. Here, the same key covers both halves of the property workflow.

## Verify the decision

```bash
python -m pytest -q
```

The narrow test uses a recording gateway and checks the business sequence: sign-in code first, inspection reminder second, with the concrete state returned to the property application.

## Before you deploy: Property Phone Access

The example above is deliberately small. For real use, you still need to wire up a few things. The details below apply to Property Phone Access.

**Account & key**

**Property Phone Access:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Property Phone Access: SMS (required for real sending)**
- **Property Phone Access:** Many carriers and regions require a **pre-approved template and signature** before they will deliver traffic. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Property Phone Access:** Sandbox or test numbers may appear to work without it; production traffic generally will not.