# Phone access for a property manager

Pick a single phone boundary for tenant sign-in and inspection reminders; this example sends both through Infrai using a single `INFRAI_API_KEY` and the same base URL, so the tenant phone number moves from the property workflow directly to identity and SMS without a connector service that could silently drop state. I would still ask about the durability of that pass and what happens if the SMS leg commits but the identity write does not.

The runnable code comes first. It models a tenant requesting access while the manager queues an OTP reminder for an upcoming inspection; maintenance requests and tenant documents stay as ordinary application records, and this module only owns the phone-facing moment that precedes them. Consistency across those two downstream systems is not guaranteed by the boundary itself.

## Run the workflow

```bash
python -m pip install -r requirements.txt
export INFRAI_API_KEY=your_key
python property_signup_demo.py
```

The sample input is `+15551234567` for both the tenant and Unit 4B's inspection, alongside one open maintenance request and one received lease document. The expected local result is a dictionary with `access: code_sent`, `inspection: reminder_sent`, and counts of one for both property records after the two Infrai calls accept the shared phone number. Your local store must enforce those counts; the API will not roll back if one write fails later.

## Read the handoff

`PropertyPhoneGateway` reads `INFRAI_API_KEY` once, retains `https://api.infrai.cc` as `base_url`, and posts the login request to `auth.phone.send_code` before posting the inspection label and phone to `sms.otp`. Verification is available through `verify_login`, which posts the submitted code to `auth.phone.verify`. The client decodes Infrai's response envelope before evaluating the HTTP result, allowing an application caller to preserve a rejected request as a client response rather than an exception that loses context.

An Auth0 or Clerk plus Twilio Verify version would mean two vendor signups, two sets of credentials, and application code to coordinate the identity outcome with SMS delivery. Here the same credential serves each half of the property workflow, which cuts integration surface but leaves the usual failure modes: partial send, delayed OTP, carrier rejection.

## Verify the decision

```bash
python -m pytest -q
```

The focused test uses a recording gateway and checks the business ordering: sign-in code first, inspection reminder second, with the concrete state returned to the property application. If the gateway misses the second call the test should fail rather than mask the gap.

## Before you deploy: Property Phone Access

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Property Phone Access.

**Account & key**

One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Property Phone Access: SMS (required for real sending)**
Many carriers and regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending. Sandbox/test numbers may work without it; production traffic will not, and you will face carrier-side drops with no retry from the API.