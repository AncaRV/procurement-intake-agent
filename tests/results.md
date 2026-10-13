# Results and iteration log

The prompt was first iterated in a chat model (fast and free), then deployed on Beam. After every change the full test set was re-run, not only the failing test.

## Scores by version

| Version | Where | Critical fields correct | Routes correct | Notes |
|---|---|---|---|---|
| v1 | Chat model | 6/6 | n/a (no routing yet) | 1 real error (test 6), 1 spec gap (units) |
| v2 | Chat model | 6/6 | n/a | Tests 1 and 6 fixed; regression on test 2 |
| v3 | Chat model | 6/6 | n/a | All 6 pass |
| v3 | Beam, small default model | 1/2 run | 1/2 run | Test 2 fails on the platform |
| v3 + platform fixes | Beam, GPT 5.4 | 6/6 | 4/6 | Tests 4 and 6 need prompt changes |
| v4 | Beam, GPT 5.4 | 6/6 | 6/6 | Final version |

## Iteration log

| Version | Test | Field | Returned | Expected | Cause | Change |
|---|---|---|---|---|---|---|
| v1 | 1 | unit | null | "piece" | Spec gap: the message gives no unit, and rule 1 forbids inventing one | Rule 7: default "piece" for countable items |
| v1 | 6 | needs_human_review | true | false | Two totals (before and after discount) read as an unclear price basis | Rule 5: use the final total when a discount is explained |
| v1 | 1, 3, 4, 5 | description, review_reason | reworded | same meaning | Free-text wording, not an error | Scoring: free text judged on meaning |
| v2 | 2 | unit | "piece" | null | **Regression** from the new rule: gloves are countable, but quantity is unknown | Rule 7: "piece" only when a quantity is stated |
| v2 | 4 | department | "Design" | "Design team" | Equivalent; expected value updated | None |
| v3 | 3 | unit | "box" | "carton" | Same meaning for German "Karton" | None (production: fixed unit list from the ERP) |
| v3 (Beam) | 2 | whole step | "request too complex" | output | Small model could not produce a valid structured output with many empty values | Output fields made optional; model switched to GPT 5.4 |
| v3 (Beam) | 2 | total_amount | 0 | null | Platform turns missing numbers into 0 | Routing guard: total of 0 or less treated as missing |
| v3 (Beam) | 6 | needs_human_review | true | false | GPT 5.4 treated a vague date ("Q1 2027") as ambiguous; the chat model did not | Rule 10: a vague period does not require review on its own |
| v3 (Beam) | 4 | currency | "$" | "USD" | No ISO rule in the prompt; routing ignored currency | Rule 4: ISO codes. Routing guard: non-EUR goes to review |
| v3 (Beam) | 4 | department | null | "Design" | Team name not treated as a department | Rule 6: a named team counts as a department |
| v4 (Beam) | 4 | supplier_name, needed_by_date | text "null" | null | Third form of a missing value on the platform | None (production: normalisation step) |
| v4 (Beam) | 4 | total_amount | 1800 | null | Model annualised the monthly price | Accepted; business rule to agree with the customer |

## Final Beam runs (prompt v4, GPT 5.4)

| # | needs_human_review | total_amount | currency | Route |
|---|---|---|---|---|
| 1 | false | 2010 | EUR | department_head |
| 2 | true | 0 (missing) | missing | procurement_review |
| 3 | false | 498 | EUR | auto_approve |
| 4 | true | 1800 | USD | procurement_review |
| 5 | true | 0 (missing) | missing | procurement_review |
| 6 | false | 5400 | EUR | department_head_and_finance |

Run `python routing/route.py` to replay these through the routing code, plus two guard checks.

## Cost

| Model | Credits per extraction | Handled incomplete requests |
|---|---|---|
| Small default model | about 2 | No |
| GPT 5.4 | about 8 to 16 | Yes |
