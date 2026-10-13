"""Routing step for the Procurement Request Intake Agent (Beam Code Executor node).

Reads the fields extracted by the LLM node and returns an approval route.
No AI is involved here: the thresholds are fixed and auditable.

Guards added after testing on the platform:
  1. A total of 0 or less is treated as missing (the platform turned
     missing numbers into 0, which would otherwise be auto-approved).
  2. Any currency other than EUR goes to review (thresholds are in EUR).
"""


def execute(inputs):
    def truthy(v):
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.strip().lower() in ("true", "1", "yes", "y")
        if isinstance(v, (int, float)):
            return v != 0
        return False

    def num(v):
        if isinstance(v, bool):
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            s = v.strip().replace("EUR", "").replace("€", "").strip()
            if not s or s.lower() in ("null", "none", "nan", "n/a"):
                return None
            if "," in s and "." in s:
                s = s.replace(".", "").replace(",", ".")
            elif "," in s:
                s = s.replace(",", ".")
            try:
                return float(s)
            except ValueError:
                return None
        return None

    is_pr = truthy(inputs.get("is_purchase_request"))
    review = truthy(inputs.get("needs_human_review"))
    amount = num(inputs.get("total_amount"))
    currency = str(inputs.get("currency") or "").strip().upper()

    if review or not is_pr:
        route = "procurement_review"
        reason = "Flagged for human review or not a purchase request."
    elif amount is None or amount <= 0:
        route = "procurement_review"
        reason = "Total amount missing or unclear; routed to procurement for review."
    elif currency not in ("EUR", "€"):
        route = "procurement_review"
        reason = "Currency is not EUR; approval thresholds are in EUR."
    elif amount < 1000:
        route = "auto_approve"
        reason = "Total under 1,000 EUR; auto-approved."
    elif amount <= 5000:
        route = "department_head"
        reason = "Total between 1,000 and 5,000 EUR; routed to the department head."
    else:
        route = "department_head_and_finance"
        reason = "Total over 5,000 EUR; routed to the department head and Finance."

    return {"route": route, "route_reason": reason}


if __name__ == "__main__":
    # Final extractions from the Beam runs (prompt v4, GPT 5.4), reduced to
    # the fields this step reads. Test 2 shows the platform's 0 for a missing total.
    cases = [
        ("1 laptop", {"is_purchase_request": True, "needs_human_review": False, "total_amount": 2010, "currency": "EUR"}, "department_head"),
        ("2 gloves", {"is_purchase_request": True, "needs_human_review": True, "total_amount": 0}, "procurement_review"),
        ("3 paper", {"is_purchase_request": True, "needs_human_review": False, "total_amount": 498, "currency": "EUR"}, "auto_approve"),
        ("4 miro", {"is_purchase_request": True, "needs_human_review": True, "total_amount": 1800, "currency": "USD"}, "procurement_review"),
        ("5 canteen", {"is_purchase_request": False, "needs_human_review": True, "total_amount": 0}, "procurement_review"),
        ("6 gdpr", {"is_purchase_request": True, "needs_human_review": False, "total_amount": 5400, "currency": "EUR"}, "department_head_and_finance"),
        # Guard checks: these would have been wrong without the two guards.
        ("guard: zero total", {"is_purchase_request": True, "needs_human_review": False, "total_amount": 0, "currency": "EUR"}, "procurement_review"),
        ("guard: USD total", {"is_purchase_request": True, "needs_human_review": False, "total_amount": 3000, "currency": "USD"}, "procurement_review"),
    ]
    failures = 0
    for name, fields, expected in cases:
        got = execute(fields)["route"]
        status = "PASS" if got == expected else "FAIL"
        failures += got != expected
        print(f"{status}  {name:20} {got}")
    print(f"\n{len(cases) - failures}/{len(cases)} passed")
