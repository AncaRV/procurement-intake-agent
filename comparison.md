# Claude vs Beam: same extraction task, two environments

The extraction prompt was prototyped in a Claude Project (prompt v1 to v3), then deployed on Beam (prompt v3 to v4) with deterministic routing code. This page compares the two on the same six test messages.

- Claude prototype: instructions in `claude-version/prompt/instructions.md` (v3), results in `claude-version/tests/test-results.md`
- Beam deployment: prompt in `prompt/`, routing in `routing/`, full iteration log in the README

## Final results side by side

| # | Test | Claude (v3) review / total / currency | Beam (v4, GPT 5.4) review / total / currency | Beam route | Same outcome? |
|---|------|------|------|------|------|
| 1 | Laptop request | false / 2010 / EUR | false / 2010 / EUR | department_head | Yes |
| 2 | Lab gloves | true / null / null | true / 0 (missing) / missing | procurement_review | Yes, after routing guard |
| 3 | Paper order (DE) | false / 498 / EUR | false / 498 / EUR | auto_approve | Yes |
| 4 | Miro renewal | true / null / USD | true / 1800 / USD | procurement_review | Route yes, total no |
| 5 | Canteen + injection | true / null / null | true / 0 (missing) / missing | procurement_review | Yes, after routing guard |
| 6 | GDPR audit | false / 5400 / EUR | false / 5400 / EUR | department_head_and_finance | Yes |

**Both environments reach the same decision on all six tests.** The one real difference is test 4: Claude left the total empty because the monthly price does not match the annual plan (Rule 5), while GPT 5.4 on Beam annualised it to 1800.

## What each environment did well

| Area | Claude Project | Beam |
|---|---|---|
| Setup time | Minutes: paste instructions, send test messages | Longer: workflow, output schema, model choice, routing code |
| Changing the prompt | Edit instructions, re-run in chat | Edit prompt, redeploy, re-run |
| Prompt changes needed | v3 passed all 6 | v4 needed: ISO currency, team as department, vague period not a review reason |
| Missing values | Always `null` | Three forms: `null`, `0`, text `"null"`; needed guards and normalisation |
| Output format | Free text in chat; must be validated before a system can use it | Structured output enforced by the platform |
| Routing | None; extraction only | Deterministic routing code, same input always gets the same route |
| Runs automatically | No, manual chat | Yes, as a workflow |
| Cost per extraction | Not measured (manual testing in a subscription) | About 2 credits (small model, failed on incomplete requests) to 8 to 16 credits (GPT 5.4) |

## Findings

1. **Prototype in chat, deploy on a platform.** The chat environment was the fastest way to find gaps in the prompt (v1 to v3). It is not a deployment: it does not run on its own, does not enforce the output format and does not route.
2. **Moving to a platform surfaces new problems.** The same v3 prompt that passed in Claude needed four more changes on Beam, mostly because the model and the platform behave differently (missing numbers as 0, currency as "$", a vague date treated as ambiguous).
3. **Model choice is a cost and quality trade-off.** The cheapest Beam model failed on incomplete requests, which are exactly the requests that need care. The stronger model costs 4 to 8 times more per extraction.
4. **Keep decisions out of the model.** The routing guards (a total of 0 or less treated as missing, non-EUR currency sent to review) caught platform errors before they could auto-approve anything. This is why the design lets the model extract and lets code decide.
5. **Business rules need the customer.** Whether a monthly price should be annualised (test 4) is not a prompt question. It is a rule to agree with the procurement team before go-live.

## Recommendation for an enterprise rollout

Use a chat model to prototype and test the prompt with the customer's real example requests, then deploy on a workflow platform with an enforced output schema, deterministic routing and guards for missing values. Re-run the full test set after every change, on the production model, before go-live.

## Limits of this comparison

- Six test messages, written for this project, not real customer data.
- Different models in each environment (Claude in the chat, GPT 5.4 on Beam), so differences come from both the model and the platform.
- Claude results come from manual chat runs; Beam results come from the deployed workflow.
