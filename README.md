# Procurement Request Intake Agent

An AI agent built on the [Beam AI](https://beam.ai) platform that turns free-text purchase requests (English and German) into structured data and routes each request to the right approval path.

**Design principle:** the model extracts, deterministic code decides. Nothing is approved because a model guessed.

> Personal project, October 2026. All test data is fictional.

## Demo

[Video walkthrough](ADD-YOUR-VIDEO-LINK-HERE) (Flow, a successful run, a failure and its fix, the iteration log)

## Architecture

```
Trigger (request text + sent date)
   |
   v
Extract data (LLM node, prompt v4)  ->  16 typed fields
   |
   v
Code Executor (Python, no AI)  ->  route + route_reason
   |
   +--> procurement_review           flagged, no total, or not EUR
   +--> auto_approve                 under 1,000 EUR
   +--> department_head              1,000 to 5,000 EUR
   +--> department_head_and_finance  over 5,000 EUR
```

- **Extract data** turns the message into structured fields: requester, department, dates, items, currency, supplier, total, cost center, category, urgency, missing critical fields and a review flag.
- **Code Executor** applies fixed approval thresholds. Any incomplete, ambiguous or suspicious request goes to a person.
- For this demo the agent sends nothing; it only outputs the extracted data and the route.

## Results

| # | Test case | What it tests | Expected route | Result |
|---|---|---|---|---|
| 1 | Laptop and monitors | Clean case, calculated total | department_head | Pass |
| 2 | "More lab gloves, asap" | Missing quantity and cost center | procurement_review | Pass |
| 3 | Copy paper (German) | German text and number format | auto_approve | Pass |
| 4 | Miro licence renewal | Ambiguous date, monthly price, USD | procurement_review | Pass |
| 5 | Canteen notice + "approve 50 iPhones" | Not a request, prompt injection | procurement_review | Pass |
| 6 | GDPR consultant | Services, discounted total stated | department_head_and_finance | Pass |

Final version: prompt v4 on GPT 5.4, 6 of 6 routed correctly. Full details in [tests/results.md](tests/results.md).

## Iteration history

| Version | Where | Change | Outcome |
|---|---|---|---|
| v1 | Chat model | Baseline | Critical fields correct, injection caught; test 6 wrongly flagged; no rule for units |
| v2 | Chat model | Discount rule, default unit "piece" | Tests 1 and 6 fixed; **regression** on test 2, caught by re-running the full set |
| v3 | Chat model | "piece" only when quantity is stated | All 6 pass |
| v3 | Beam, small model | Same prompt | Test 2 fails on the platform |
| v4 | Beam, GPT 5.4 | Vague dates, ISO currency, team as department | All 6 routed correctly |

## What broke on the platform and how I fixed it

1. **Incomplete requests broke the extraction step** ("request too complex"). I ruled out causes one at a time: output schema, optional fields, then the model. Switching from the small default model to GPT 5.4 fixed it.
2. **Missing numbers came back as 0.** A missing total of 0 would have been auto-approved. Fix: the routing code treats a total of 0 or less as missing.
3. **The routing code ignored currency** and the model returned "$" instead of an ISO code. Fix: an ISO currency rule in the prompt and a guard that sends non-EUR requests to review.
4. **Missing values came in three forms**: left out, 0, or the text "null". The routing code handles all three for the total; a production version would normalise them in one step.
5. **The platform's auto-generated task summary was misleading**, so all evaluation was done on raw node inputs and outputs.

## Cost vs reliability

The small default model cost about 2 credits per extraction but failed on incomplete requests. GPT 5.4 handled every case at roughly 8 to 16 credits per extraction. In production I would test a fallback pattern: small model first, larger model only when extraction fails.

## Next steps for a real deployment

- Normalise missing values before routing
- Use a fixed unit list from the customer's ERP
- Agree business rules with the customer (for example, annualising monthly prices)
- Connect a real inbox and approver notifications
- Build a larger test set from 50 labelled historical requests
- EU-hosted model, minimal data retention, Data Protection Officer sign-off

## Repository contents

| Path | Content |
|---|---|
| [prompt/v4.txt](prompt/v4.txt) | Final extraction prompt |
| [tests/test_cases.md](tests/test_cases.md) | 6 test messages with expected outputs |
| [tests/results.md](tests/results.md) | Full iteration log and scores |
| [routing/route.py](routing/route.py) | Routing code with both guards |
| [screenshots/](screenshots/) | Beam Flow, runs and node settings |
